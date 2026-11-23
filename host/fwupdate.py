# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: GPL-3.0-or-later

"""The firmware update over the network (§8C.8): a Teensy 4.1 .hex file to the tuner's line port.

The tuner writes the image to a staging area in its own flash and checks it there: every record's
checksum, the length and CRC-32 sent here, the CRC read back from the flash, and the Teensy 4.1's boot
header. It installs the image only when someone at the box answers the panel's FIRMWARE UPDATE READY
screen with a push of the left knob, and then restarts by itself. From UPDATE BEGIN until then its vote
is down, so nothing transmits through it.

    python3 fwupdate.py firmware.hex                     send it to tuner.local:4600
    python3 fwupdate.py firmware.hex --tuner 192.168.1.37 --wait
    python3 fwupdate.py --check firmware.hex             check the file; send nothing
    python3 fwupdate.py --status                         where an update stands
    python3 fwupdate.py --abort                          discard one arriving or staged

It needs Python 3.8 or later, with the standard library only. The PC must be on the tuner's own subnet,
which is all the tuner serves (§8C.7).
"""
import argparse
import select
import socket
import sys
import time
import zlib

FLASH = 0x60000000          # the Teensy 4.1's program flash, where its .hex files are addressed
RECORD = 32                 # data bytes a line: short enough for the tuner's line and frame buffers
BATCH = 64                  # records between looks for a refusal
PORT = 4600
RETRY_S = 2                 # between tries to reach the tuner after its restart


class HexError(Exception):
    pass


class Refused(Exception):
    pass


# --- The file

def read_hex(path):
    """The image an Intel HEX file describes, from FLASH, gaps as 0xFF. Every record is checked."""
    image = bytearray()
    upper = 0
    done = False
    with open(path, encoding='ascii', errors='replace') as f:
        for n, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            if done:
                raise HexError('line %d: a record after the end-of-file record' % n)
            try:
                if line[0] != ':':
                    raise ValueError
                rec = bytes.fromhex(line[1:])
            except ValueError:
                raise HexError('line %d: not an Intel HEX record' % n) from None
            if len(rec) < 5 or len(rec) != rec[0] + 5:
                raise HexError('line %d: the length does not match' % n)
            if sum(rec) & 0xFF:
                raise HexError('line %d: checksum' % n)
            count, addr, kind, body = rec[0], rec[1] << 8 | rec[2], rec[3], rec[4:-1]
            if kind == 0:
                at = upper + addr - FLASH
                if at < 0:
                    raise HexError('line %d: data below the flash at 0x%08X' % (n, upper + addr))
                if at + count > len(image):
                    image.extend(b'\xff' * (at + count - len(image)))
                image[at:at + count] = body
            elif kind == 1:
                done = True
            elif kind in (2, 4) and count == 2:
                upper = (body[0] << 8 | body[1]) << (4 if kind == 2 else 16)
            elif kind not in (3, 5):            # start addresses: the boot header has its own
                raise HexError('line %d: record type %d' % (n, kind))
    if not done:
        raise HexError('no end-of-file record')
    if not image:
        raise HexError('no data')
    return bytes(image)


def teensy41(image):
    """The Teensy 4.1's boot header: the FlexSPI configuration ("FCFB") with an 8 MB flash, and the
    image vector table at 0x1000. An image without them is not for this board."""
    def word(at):
        return int.from_bytes(image[at:at + 4], 'little')
    return len(image) >= 0x1004 and word(0) == 0x42464346 and word(0x50) == 0x00800000 and word(0x1000) == 0x432000D1


def record(kind, addr, data):
    body = bytes([len(data), addr >> 8, addr & 0xFF, kind]) + bytes(data)
    return ':%s%02X' % (body.hex().upper(), -sum(body) & 0xFF)


def records(image, size=RECORD):
    """The image as Intel HEX lines in address order, which is the order the tuner takes them: an
    extended address at each 64 KB, the data, and the end. No record crosses 64 KB, since size divides it."""
    out, upper = [], None
    for at in range(0, len(image), size):
        a = FLASH + at
        if a >> 16 != upper:
            upper = a >> 16
            out.append(record(4, 0, upper.to_bytes(2, 'big')))
        out.append(record(0, a & 0xFFFF, image[at:at + size]))
    out.append(record(1, 0, b''))
    return out


# --- The line protocol (§8C.5, fw/core/src/proto.cpp)

def checksum(text):
    """NMEA-style: the XOR of every character."""
    c = 0
    for b in text.encode('latin-1', 'replace'):
        c ^= b
    return c


def seal(cmd):
    return '%s*%02X' % (cmd, checksum(cmd))


def unseal(line):
    """The text of a tuner line before its *HH, or None if the checksum is missing or wrong."""
    text, star, hh = line.rpartition('*')
    if not star or len(hh) != 2:
        return None
    try:
        return text if int(hh, 16) == checksum(text) else None
    except ValueError:
        return None


class Link:
    """The tuner's line port. EVT lines are passed to on_event; replies are what wait() looks for."""

    def __init__(self, addr, timeout, on_event=None):
        self.sock = socket.create_connection(addr, timeout=timeout)
        self.buf = b''
        self.on_event = on_event or (lambda text: None)
        self.closed = False
        self.installing = self.discarded = False   # the update events seen

    def close(self):
        self.sock.close()

    def command(self, cmd):
        self.sock.sendall((seal(cmd) + '\r\n').encode('ascii'))

    def raw(self, lines):
        self.sock.sendall(''.join(s + '\r\n' for s in lines).encode('ascii'))

    def lines(self, timeout):
        """The lines that arrive within timeout seconds (none if timeout is 0 and nothing waits)."""
        end = time.monotonic() + timeout
        while True:
            while b'\n' in self.buf:
                raw, self.buf = self.buf.split(b'\n', 1)
                text = unseal(raw.decode('latin-1').strip())
                if text is None:
                    continue
                if text.startswith('EVT '):
                    self.installing |= ' update=installing ' in text + ' '
                    self.discarded |= ' update=discarded ' in text + ' '
                    self.on_event(text[4:])
                else:
                    yield text
            left = end - time.monotonic()
            if self.closed or not select.select([self.sock], [], [], max(left, 0))[0]:
                return
            chunk = self.sock.recv(4096)
            if not chunk:
                self.closed = True
                return
            self.buf += chunk

    def refusal(self):
        """An ERR already waiting, or None: a look between batches that never blocks."""
        for text in self.lines(0):
            if text.startswith('ERR '):
                return text[4:]
        return None

    def wait(self, prefix, timeout):
        """The reply to one command: its OK text, or Refused with the ERR's."""
        for text in self.lines(timeout):
            if text.startswith('ERR '):
                raise Refused(text[4:])
            if text.startswith('OK ' + prefix):
                return text[3:]
        raise Refused('no reply in %d s%s' % (timeout, ' (the connection closed)' if self.closed else ''))


# --- What it does

def send(link, image, out):
    crc = zlib.crc32(image) & 0xFFFFFFFF
    link.command('UPDATE BEGIN')
    print(link.wait('UPDATE BEGIN', 10), file=out)
    lines = records(image)
    t0, shown = time.monotonic(), 0
    for i in range(0, len(lines), BATCH):
        link.raw(lines[i:i + BATCH])
        why = link.refusal()
        if why:
            raise Refused(why)
        done = 100 * (i + BATCH) // len(lines)
        if done >= shown + 10 and done < 100:
            shown = done - done % 10
            print('  %d %%' % shown, file=out, flush=True)
    link.command('UPDATE END %d %08X' % (len(image), crc))
    print(link.wait('UPDATE END', 120), file=out)
    print('sent in %.1f s' % (time.monotonic() - t0), file=out)


def installed(link, timeout, out):
    """Waits for the answer at the panel: True once the install begins, False if it is discarded. A
    restarted tuner knows nothing of this connection, so it is asked every few seconds, which also finds
    a connection that has died."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            link.command('UPDATE')
            for text in link.lines(3):
                if text.startswith('OK UPDATE idle'):
                    return link.installing
        except OSError:
            return True                        # gone: the install restarts the tuner
        if link.installing or link.closed:
            return True
        if link.discarded:
            return False
    return False


def back_again(addr, timeout, out):
    """After the install: the tuner restarts, so wait for it to answer again."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        time.sleep(RETRY_S)
        try:
            link = Link(addr, 5)
        except OSError:
            continue
        try:
            link.command('QUERY')
            for text in link.lines(5):
                if text.startswith('TLM '):
                    print('the tuner is back: ' + text[4:60] + ' ...', file=out)
                    return True
        except OSError:
            pass
        finally:
            link.close()
    print('the tuner did not answer within %d s' % timeout, file=out)
    return False


def host_port(text):
    host, _, port = text.rpartition(':') if text.count(':') == 1 else (text, '', '')
    return host, int(port) if port else PORT


def main(argv=None, out=sys.stdout):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('hexfile', nargs='?', help='the .hex file PlatformIO wrote (fw/.pio/build/teensy41/firmware.hex)')
    p.add_argument('--tuner', default='tuner.local', help='HOST[:PORT], default tuner.local:%d' % PORT)
    p.add_argument('--check', action='store_true', help='check the file and send nothing')
    p.add_argument('--status', action='store_true', help='where an update stands')
    p.add_argument('--abort', action='store_true', help='discard an update arriving or staged')
    p.add_argument('--wait', action='store_true', help='after staging, wait for the install and the restart')
    a = p.parse_args(argv)
    addr = host_port(a.tuner)

    def event(text):
        if ' event=update ' in ' ' + text + ' ':
            print('  tuner: ' + text, file=out)

    try:
        if a.status or a.abort:
            link = Link(addr, 10, event)
            link.command('UPDATE ABORT' if a.abort else 'UPDATE')
            print(link.wait('UPDATE', 10), file=out)
            link.close()
            return 0
        if not a.hexfile:
            p.error('a .hex file, --status or --abort')
        image = read_hex(a.hexfile)
        if not teensy41(image):
            raise HexError('not a Teensy 4.1 image: its boot header is missing')
        print('%s: %d bytes, CRC-32 %08X, Teensy 4.1 header present' % (a.hexfile, len(image), zlib.crc32(image)), file=out)
        if a.check:
            return 0
        link = Link(addr, 30, event)
        try:
            send(link, image, out)
            print('Install it at the tuner within 10 minutes: FIRMWARE UPDATE READY should show CRC-32 %08X;'
                  ' push the left knob.' % zlib.crc32(image), file=out)
            if a.wait:
                if not installed(link, 660, out):
                    print('not installed: the tuner discarded it', file=out)
                    return 1
                print('installing: the tuner restarts by itself', file=out)
                return 0 if back_again(addr, 90, out) else 1
        finally:
            link.close()
        return 0
    except (HexError, Refused) as e:
        print('fwupdate: %s' % e, file=out)
        return 1
    except OSError as e:
        print('fwupdate: %s: %s' % (a.tuner, e), file=out)
        return 2


if __name__ == '__main__':
    sys.exit(main())
