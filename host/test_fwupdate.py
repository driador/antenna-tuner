# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for fwupdate.py: the .hex reader and writer, and a send against a fake tuner line port.

Run:  cd host && python3 -m unittest -v test_fwupdate
"""
import io
import os
import socket
import tempfile
import threading
import unittest
import zlib

import fwupdate

HERE = os.path.dirname(os.path.abspath(__file__))
BUILT = os.path.join(HERE, '..', 'fw', '.pio', 'build', 'teensy41', 'firmware.hex')


def teensy_image(n):
    """n bytes that pass the Teensy 4.1 header check, the rest a pattern."""
    image = bytearray((i * 7 + 3) & 0xFF for i in range(n))
    image[0:4] = (0x42464346).to_bytes(4, 'little')
    image[0x50:0x54] = (0x00800000).to_bytes(4, 'little')
    image[0x1000:0x1004] = (0x432000D1).to_bytes(4, 'little')
    return bytes(image)


def write_hex(lines):
    f = tempfile.NamedTemporaryFile('w', suffix='.hex', delete=False)
    f.write('\n'.join(lines) + '\n')
    f.close()
    return f.name


class FakeTuner(threading.Thread):
    """The tuner's line port, as far as an update goes: records in order into an image, then END
    checked against its length and CRC. refuse_at refuses that record and drops the rest quietly, as
    the tuner does; install sends the install event after END and drops the connection, as a restart."""

    def __init__(self, refuse_at=None, install=False):
        super().__init__(daemon=True)
        self.srv = socket.socket()
        self.srv.bind(('127.0.0.1', 0))
        self.srv.listen(4)
        self.port = self.srv.getsockname()[1]
        self.refuse_at, self.install = refuse_at, install
        self.image, self.records, self.staged, self.connections = bytearray(), 0, None, 0
        self.start()

    def stop(self):
        self.srv.close()

    def run(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            self.connections += 1
            with c:
                try:
                    self.serve(c)
                except OSError:
                    pass

    def say(self, c, text):
        c.sendall((fwupdate.seal(text) + '\r\n').encode())

    def serve(self, c):
        failed, upper = None, 0
        for raw in c.makefile('rb'):
            line = raw.decode().strip()
            if line.startswith(':'):
                self.records += 1
                if failed:
                    continue
                if self.records == self.refuse_at:
                    failed = 'update: a record that does not check out'
                    self.say(c, 'ERR ' + failed)
                    continue
                rec = bytes.fromhex(line[1:])
                assert sum(rec) & 0xFF == 0 and len(rec) == rec[0] + 5
                kind, addr, body = rec[3], rec[1] << 8 | rec[2], rec[4:-1]
                if kind == 4:
                    upper = (body[0] << 8 | body[1]) << 16
                elif kind == 0:
                    at = upper + addr - fwupdate.FLASH
                    assert at >= len(self.image), 'records out of order'
                    self.image.extend(b'\xff' * (at - len(self.image)))
                    self.image += body
                continue
            text = fwupdate.unseal(line)
            if text == 'UPDATE BEGIN':
                self.say(c, 'OK UPDATE BEGIN: up to 7000 KB')
            elif text and text.startswith('UPDATE END'):
                if failed:
                    self.say(c, 'ERR ' + failed)
                    continue
                n, crc = text.split()[2:]
                if int(n) == len(self.image) and int(crc, 16) == zlib.crc32(self.image):
                    self.staged = bytes(self.image)
                    self.say(c, "OK UPDATE END: %d bytes staged and checked; install it at the tuner's panel" % int(n))
                    if self.install:
                        self.say(c, 'EVT seq=9 t=+5s event=update update=installing state=IDLE mhz=0.0000')
                        return
                else:
                    self.say(c, 'ERR update: the CRC is not the one sent: the transfer was damaged')
            elif text == 'UPDATE':
                self.say(c, 'OK UPDATE idle: room for 7000 KB')
            elif text == 'QUERY':
                self.say(c, 'TLM state=IDLE path=TUNE mode=STRICT mhz=0.0000 carrier=0 ev=1')


class Files(unittest.TestCase):
    def test_records_read_back_as_the_image(self):
        image = teensy_image(200000)
        lines = fwupdate.records(image)
        self.assertTrue(all(len(s) <= 11 + 2 * fwupdate.RECORD for s in lines))
        path = write_hex(lines)
        try:
            self.assertEqual(fwupdate.read_hex(path), image)
        finally:
            os.unlink(path)
        self.assertTrue(fwupdate.teensy41(image))
        uppers = [s for s in lines if s[7:9] == '04']
        self.assertEqual(len(uppers), (200000 + 0xFFFF) // 0x10000)    # one at each 64 KB

    def test_gaps_read_as_erased_flash(self):
        path = write_hex([fwupdate.record(4, 0, b'\x60\x00'), fwupdate.record(0, 0, b'\x01\x02'),
                          fwupdate.record(0, 0x10, b'\x03'), fwupdate.record(1, 0, b'')])
        try:
            self.assertEqual(fwupdate.read_hex(path), b'\x01\x02' + b'\xff' * 14 + b'\x03')
        finally:
            os.unlink(path)

    def test_bad_files_are_refused(self):
        good = [fwupdate.record(4, 0, b'\x60\x00'), fwupdate.record(0, 0, b'\x01\x02')]
        cases = {
            'checksum': good[:1] + [good[1][:-2] + '00'] + [fwupdate.record(1, 0, b'')],
            'no end-of-file': good,
            'below the flash': [fwupdate.record(0, 0, b'\x01'), fwupdate.record(1, 0, b'')],
            'not an Intel HEX': good + ['hello', fwupdate.record(1, 0, b'')],
            'after the end-of-file': good + [fwupdate.record(1, 0, b''), good[1]],
        }
        for why, lines in cases.items():
            path = write_hex(lines)
            try:
                with self.assertRaises(fwupdate.HexError, msg=why) as e:
                    fwupdate.read_hex(path)
                self.assertIn(why, str(e.exception))
            finally:
                os.unlink(path)

    def test_teensy40_image_is_not_for_this_board(self):
        image = bytearray(teensy_image(0x2000))
        image[0x50:0x54] = (0x00200000).to_bytes(4, 'little')            # 2 MB: a Teensy 4.0
        self.assertFalse(fwupdate.teensy41(bytes(image)))
        self.assertFalse(fwupdate.teensy41(teensy_image(0x2000)[:0x800]))

    @unittest.skipUnless(os.path.exists(BUILT), 'no firmware build (cd fw && pio run)')
    def test_the_real_build(self):
        image = fwupdate.read_hex(BUILT)
        self.assertTrue(fwupdate.teensy41(image))
        path = write_hex(fwupdate.records(image))
        try:
            self.assertEqual(fwupdate.read_hex(path), image)
        finally:
            os.unlink(path)


class Send(unittest.TestCase):
    def setUp(self):
        self.path = write_hex(fwupdate.records(teensy_image(50000), size=16))
        fwupdate.RETRY_S = 0.05

    def tearDown(self):
        os.unlink(self.path)

    def run_tool(self, tuner, *extra):
        out = io.StringIO()
        code = fwupdate.main([self.path, '--tuner', '127.0.0.1:%d' % tuner.port, *extra], out)
        return code, out.getvalue()

    def test_an_image_is_staged(self):
        tuner = FakeTuner()
        code, out = self.run_tool(tuner)
        tuner.stop()
        self.assertEqual(code, 0, out)
        self.assertEqual(tuner.staged, teensy_image(50000))
        self.assertIn('staged and checked', out)

    def test_a_refusal_stops_the_send(self):
        tuner = FakeTuner(refuse_at=10)
        code, out = self.run_tool(tuner)
        tuner.stop()
        self.assertEqual(code, 1)
        self.assertIn('a record that does not check out', out)
        self.assertIsNone(tuner.staged)

    def test_not_a_teensy41_image_is_never_sent(self):
        tuner = FakeTuner()
        path = write_hex(fwupdate.records(b'\x00' * 0x2000))
        out = io.StringIO()
        code = fwupdate.main([path, '--tuner', '127.0.0.1:%d' % tuner.port], out)
        os.unlink(path)
        tuner.stop()
        self.assertEqual(code, 1)
        self.assertIn('not a Teensy 4.1 image', out.getvalue())
        self.assertEqual(tuner.connections, 0)

    def test_wait_follows_the_install_and_the_restart(self):
        tuner = FakeTuner(install=True)
        code, out = self.run_tool(tuner, '--wait')
        tuner.stop()
        self.assertEqual(code, 0, out)
        self.assertIn('update=installing', out)
        self.assertIn('the tuner is back', out)

    def test_status(self):
        tuner = FakeTuner()
        out = io.StringIO()
        code = fwupdate.main(['--status', '--tuner', '127.0.0.1:%d' % tuner.port], out)
        tuner.stop()
        self.assertEqual(code, 0)
        self.assertIn('UPDATE idle', out.getvalue())


if __name__ == '__main__':
    unittest.main()
