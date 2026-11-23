# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: GPL-3.0-or-later

"""The CAT bridge (§8B.3a, §8C): the bench PC's side of band-follow and one-button tune.

Band-follow polls the rig's frequency and sends the tuner PRESET on a band change, or on a move of more
than the threshold from the last PRESET, so the elements wait near the match while the rig still
receives. One-button tune answers the tuner's want=1, a TUNE waiting for a carrier: the rig goes to a
carrier mode at low power and is keyed until the tune ends, then put back as it was.

    python3 catbridge.py run      the daemon: band-follow and one-button tune
    python3 catbridge.py tune     one tune: TUNE, the carrier, then exit

The rig is reached through Hamlib's rigctld or through flrig. Standard library only; see README.md.
"""
import argparse
import collections
import contextlib
import http.client
import logging
import re
import select
import signal
import socket
import sys
import time
import xml.parsers.expat
import xmlrpc.client
from dataclasses import dataclass

log = logging.getLogger('catbridge')

MAX_TUNE_WATTS = 50.0       # a tune carrier above this is refused, well inside the tuner's tune window (§8B.3b)
MAX_TUNE_S = 30.0           # the longest the rig is ever held keyed for one tune
TUNING = ('MEASURE', 'PROBE', 'SOLVE', 'MOVE', 'VERIFY')        # a tune under way (fsm.hpp)
# The bands PRESET takes, kBands in fw/core/src/freq.cpp. The tuner refuses anything else.
BANDS = (('160m', 1.800, 2.000), ('80m', 3.500, 4.000), ('60m', 5.330, 5.406), ('40m', 7.000, 7.300),
         ('30m', 10.100, 10.150), ('20m', 14.000, 14.350), ('17m', 18.068, 18.168), ('15m', 21.000, 21.450),
         ('12m', 24.890, 24.990), ('10m', 28.000, 29.700))
HAMLIB_ERRORS = ('ok', 'invalid parameter', 'invalid configuration', 'out of memory', 'not implemented',
                 'timed out', 'I/O error', 'internal error', 'protocol error', 'rejected by the rig',
                 'argument truncated', 'not available', 'VFO not targetable', 'bus error', 'bus collision',
                 'invalid pointer', 'invalid VFO', 'argument out of domain', 'deprecated', 'security error',
                 'rig not powered on', 'limit exceeded', 'access denied')     # RPRT -n, rig.h


class RigError(Exception):
    """The rig did not do what was asked, or its link failed."""


class LinkError(Exception):
    """The tuner's link dropped or went quiet."""


class Refused(Exception):
    """A tune the bridge will not key for."""


class Stop(BaseException):
    """SIGINT or SIGTERM. Not an Exception, so nothing that catches those swallows it."""


@dataclass
class Config:
    tuner: str = 'tuner.local:4600'
    rig: str = 'hamlib'
    rig_addr: str = ''              # '' is the backend's default
    tune_watts: float = 20.0
    rig_max_watts: float = 100.0    # what Hamlib's RFPOWER 1.0 gives on this rig
    tune_mode: str = 'RTTY'
    tune_timeout: float = 15.0
    threshold: float = 0.005        # a move of this fraction of the frequency sends PRESET again
    dry_run: bool = False
    poll_s: float = 0.5             # the rig's frequency and PTT
    preset_s: float = 2.0           # at most one PRESET this often
    tlm_hz: float = 5.0             # the SUBSCRIBE rate
    stale_s: float = 3.0            # nothing from the tuner for this long: the link is down
    carrier_s: float = 3.0          # keyed this long and the tuner still sees no carrier: unkey
    io_s: float = 3.0               # a connect, or one rig command
    retry_s: float = 1.0            # reconnect delays: this, doubling...
    retry_max_s: float = 30.0       # ...up to this
    ale: bool = False               # an ALE controller owns the rig (§8C.10): PRESET on a dwell, never key
    dwell_s: float = 1.5            # ALE: a frequency held this long is where the scan stopped
    ale_poll_s: float = 0.25        # ALE: poll faster, so a scan step and a dwell look different
    moves_per_hour: int = 60        # ALE: warn above this many PRESETs an hour (the roller wears)

    def problem(self):
        """Why the bridge refuses this configuration, or None."""
        if not 0 < self.tune_watts <= MAX_TUNE_WATTS:
            return 'the tune power must be above 0 W and at most %g W' % MAX_TUNE_WATTS
        if self.tune_watts > self.rig_max_watts:
            return 'the tune power is above the rig maximum (--rig-max-watts)'
        if not 0 < self.tune_timeout <= MAX_TUNE_S:
            return 'the tune timeout must be above 0 s and at most %g s' % MAX_TUNE_S
        if not 0 < self.threshold <= 0.05:
            return 'the threshold must be above 0 and at most 5 percent'
        if self.ale and not self.ale_poll_s * 2 <= self.dwell_s <= 30:
            return 'the dwell must span two polls (%g s) and be at most 30 s' % (2 * self.ale_poll_s)
        if not re.fullmatch(r'[A-Za-z0-9_-]+', self.tune_mode):
            return 'the tune mode must be one word, such as RTTY or FM'
        try:
            host_port(self.tuner, 4600)
            if self.rig == 'hamlib':
                host_port(self.rig_addr or 'localhost', 4532)
        except ValueError:
            return 'an address must be HOST or HOST:PORT'
        return None


def host_port(text, port):
    """'host', 'host:port' or '[v6 address]:port' as (host, port)."""
    if text.startswith('['):
        host, _, rest = text[1:].partition(']')
        return host, int(rest[1:]) if rest.startswith(':') else port
    if text.count(':') == 1:
        host, p = text.split(':')
        return host, int(p)
    return text, port


def hamlib_error(code):
    try:
        return HAMLIB_ERRORS[abs(int(code))]
    except (ValueError, IndexError):
        return 'unknown error'


def band_of(mhz):
    """The band a frequency is in, as the tuner reckons it, or None."""
    for name, lo, hi in BANDS:
        if lo <= mhz <= hi:
            return name
    return None


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


class Telemetry(dict):
    """One TLM line as its key=value fields. Unknown fields are kept and missing ones are absent, so a
    flag that is missing (want= from older firmware, say) reads as 0."""

    @classmethod
    def parse(cls, text):
        return cls(w.split('=', 1) for w in text.split()[1:] if '=' in w)

    def flag(self, key):
        return self.get(key) == '1'

    @property
    def state(self):
        return self.get('state', '?')


class Guard:
    """Turns SIGINT and SIGTERM into Stop, held back while the rig is being unkeyed and put back."""

    def __init__(self):
        self.depth = 0
        self.pending = None

    def install(self):
        for s in (signal.SIGINT, signal.SIGTERM):
            signal.signal(s, self.on_signal)

    def on_signal(self, signum, frame=None):
        if self.depth:
            self.pending = signum
            return
        raise Stop(signal.Signals(signum).name)

    @contextlib.contextmanager
    def held(self):
        self.depth += 1
        try:
            yield
        finally:
            self.depth -= 1
            if not self.depth and self.pending is not None:
                signum, self.pending = self.pending, None
                raise Stop(signal.Signals(signum).name)


class Backoff:
    """Reconnect delays: first, doubling up to most, and back to first once the link has worked."""

    def __init__(self, first, most):
        self.first, self.most = first, most
        self.delay, self.at = first, 0.0

    def fail(self, now):
        """Schedules the next try and returns how long until it."""
        self.at, wait = now + self.delay, self.delay
        self.delay = min(2 * self.delay, self.most)
        return wait

    def reset(self):
        self.delay = self.first


class TunerLink:
    """The tuner's line port: sealed commands out; TLM, EVT and replies in. Telemetry comes by
    SUBSCRIBE, and by QUERY whenever the subscription goes quiet."""

    name = 'tuner'

    def __init__(self, cfg):
        self.cfg = cfg
        self.addr = host_port(cfg.tuner, 4600)
        self.sock, self.buf, self.lines = None, b'', 0
        self.tlm = Telemetry()
        self.tlm_at = self.heard_at = self.query_at = 0.0

    @property
    def up(self):
        return self.sock is not None

    @property
    def fresh(self):
        return self.up and time.monotonic() - self.tlm_at < self.cfg.stale_s

    def connect(self):
        self.close()
        try:
            self.sock = socket.create_connection(self.addr, timeout=self.cfg.io_s)
        except OSError as e:
            raise LinkError('tuner at %s:%d: %s' % (self.addr + (e,))) from e
        self.buf, self.lines, self.tlm, self.tlm_at = b'', 0, Telemetry(), 0.0
        self.heard_at = self.query_at = time.monotonic()
        self.send('SUBSCRIBE %g' % self.cfg.tlm_hz)
        log.info('tuner: connected to %s:%d', *self.addr)

    def close(self):
        if self.sock is not None:
            with contextlib.suppress(OSError):
                self.sock.close()
        self.sock = None

    def send(self, cmd):
        if self.sock is None:
            raise LinkError('tuner: not connected')
        try:
            self.sock.sendall((seal(cmd) + '\r\n').encode('latin-1'))
        except OSError as e:
            self._drop('tuner: %s' % e)
        log.debug('tuner <- %s', cmd)

    def pump(self, timeout):
        """Takes in what the tuner sends, waiting up to timeout seconds for it. LinkError if the link
        has dropped or gone quiet."""
        if self.sock is None:
            raise LinkError('tuner: not connected')
        try:
            data = self.sock.recv(4096) if select.select([self.sock], [], [], max(0.0, timeout))[0] else None
        except OSError as e:
            self._drop('tuner: %s' % e)
        if data == b'':
            self._drop('the tuner closed the connection' + ('' if self.lines else
                       ': all its sessions in use, or this PC is off its subnet (§8C.7)?'))
        if data:
            *lines, self.buf = (self.buf + data).split(b'\n')
            for raw in lines:
                self._take(raw.rstrip(b'\r').decode('latin-1'))
            if len(self.buf) > 1024:            # no line is that long
                self.buf = b''
        now = time.monotonic()
        if now - self.heard_at > self.cfg.stale_s:
            self._drop('nothing from the tuner for %g s' % self.cfg.stale_s)
        if now - max(self.tlm_at, self.query_at) > 1.5 / self.cfg.tlm_hz:
            self.query_at = now                 # the subscription has gone quiet: ask
            self.send('QUERY')

    def wait(self, test, seconds):
        """Pumps until a TLM that arrives from now on passes test, for at most seconds."""
        since = time.monotonic()
        while time.monotonic() - since < seconds:
            self.pump(0.05)
            if self.tlm_at > since and test(self.tlm):
                return True
        return False

    def _take(self, line):
        text = unseal(line)
        if text is None:
            log.debug('tuner: bad checksum: %r', line)
            return
        self.heard_at = time.monotonic()
        self.lines += 1
        kind = text.split(' ', 1)[0]
        if kind == 'TLM':
            tlm = Telemetry.parse(text)
            if tlm.state != self.tlm.state:
                log.debug('tuner: %s -> %s', self.tlm.state, tlm.state)
            self.tlm, self.tlm_at = tlm, self.heard_at
        elif kind == 'ERR':
            log.warning('tuner refused: %s', text[4:])
        elif kind == 'EVT':
            log.info('tuner: %s', text)
        else:
            log.debug('tuner: %s', text)

    def _drop(self, why):
        self.close()
        raise LinkError(why)


# --- The rig. A backend has: connect(), close(), up, where; frequency() in Hz; ptt(); mode(), whose
# tuple set_mode(*it) puts back; set_mode(mode), returning the name it set; power() and set_power(w) in
# watts; set_ptt(on). Each raises RigError, and an I/O failure also closes the link. owed holds what a
# tune must put back until the rig reads back unkeyed.

class Rigctld:
    """Hamlib's rigctld in its default protocol, started without --vfo. A get answers with its values,
    one per line, or RPRT <n> on error; a set answers RPRT <n>, where 0 is done. RFPOWER runs 0..1 of
    the rig's maximum, which max_watts gives."""

    name = 'rigctld'
    owed = None

    def __init__(self, addr, max_watts, timeout):
        self.addr = host_port(addr or 'localhost', 4532)
        self.where = '%s:%d' % self.addr
        self.max_watts, self.timeout = max_watts, timeout
        self.sock, self.buf = None, b''

    @property
    def up(self):
        return self.sock is not None

    def connect(self):
        self.close()
        try:
            self.sock = socket.create_connection(self.addr, timeout=self.timeout)
        except OSError as e:
            raise RigError('rigctld at %s: %s' % (self.where, e)) from e
        self.buf = b''
        log.info('rig: rigctld at %s', self.where)

    def close(self):
        if self.sock is not None:
            with contextlib.suppress(OSError):
                self.sock.close()
        self.sock = None

    def ask(self, cmd, lines):
        """Sends cmd and returns its answer: lines of it for a get, [] for a set (lines=0)."""
        if self.sock is None:
            raise RigError('rigctld: not connected')
        try:
            while select.select([self.sock], [], [], 0)[0]:     # an answer left over from before
                if not self.sock.recv(4096):
                    raise OSError('rigctld closed the connection')
            self.buf = b''
            self.sock.sendall(cmd.encode('ascii') + b'\n')
            got = [self._line()]
            if not got[0].startswith('RPRT'):
                got += [self._line() for _ in range(lines - 1)]
        except OSError as e:
            self.close()
            raise RigError('rigctld %r: %s' % (cmd, e)) from e
        if got[0].startswith('RPRT'):
            code = got[0][4:].strip()
            if code == '0' and not lines:
                return []
            raise RigError('rigctld %r: RPRT %s, %s' % (cmd, code, hamlib_error(code)))
        if not lines:
            self.close()                        # out of step: start over
            raise RigError('rigctld %r: answered %r' % (cmd, got[0]))
        return got

    def _line(self):
        while b'\n' not in self.buf:
            data = self.sock.recv(1024)
            if not data:
                raise OSError('rigctld closed the connection')
            self.buf += data
        line, self.buf = self.buf.split(b'\n', 1)
        return line.decode('latin-1').strip()

    def _number(self, cmd, kind=float):
        text = self.ask(cmd, 1)[0]
        try:
            return kind(text)
        except ValueError:
            raise RigError('rigctld %r: answered %r' % (cmd, text)) from None

    def frequency(self):
        return self._number('f')

    def ptt(self):
        return self._number('t', int) != 0      # 1 TX, 2 TX mic, 3 TX data

    def mode(self):
        return tuple(self.ask('m', 2))          # the mode and its passband, as M takes them back

    def set_mode(self, mode, passband='0'):     # passband 0: the rig's default for the mode
        self.ask('M %s %s' % (mode, passband), 0)
        return mode

    def power(self):
        return self._number('l RFPOWER') * self.max_watts

    def set_power(self, watts):
        self.ask('L RFPOWER %.6f' % min(1.0, max(0.0, watts / self.max_watts)), 0)

    def set_ptt(self, on):
        self.ask('T %d' % bool(on), 0)


class _Timeout(xmlrpc.client.Transport):
    """xmlrpc.client's transport, with the timeout it lacks."""

    def __init__(self, timeout):
        super().__init__()
        self._timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        conn.timeout = self._timeout
        return conn


class Flrig:
    """flrig's XML-RPC server. Power is in watts, and a mode is one of the rig's own names
    (rig.get_modes), so RTTY is looked up: RTTY on an Icom, RTTY-L on a Yaesu, FSK on a Kenwood."""

    name = 'flrig'
    owed = None

    def __init__(self, addr, max_watts, timeout):
        addr = addr or 'http://localhost:12345'
        self.where = addr if '://' in addr else 'http://' + addr
        self.timeout = timeout
        self.proxy = None

    @property
    def up(self):
        return self.proxy is not None

    def connect(self):
        self.close()
        self.proxy = xmlrpc.client.ServerProxy(self.where, transport=_Timeout(self.timeout))
        log.info('rig: flrig at %s, %s', self.where, self.call('rig.get_xcvr'))

    def close(self):
        if self.proxy is not None:
            with contextlib.suppress(Exception):
                self.proxy('close')()
        self.proxy = None

    def call(self, method, *args):
        if self.proxy is None:
            raise RigError('flrig: not connected')
        try:
            return getattr(self.proxy, method)(*args)
        except xmlrpc.client.Fault as e:
            raise RigError('flrig %s: %s' % (method, e.faultString)) from e
        except (OSError, http.client.HTTPException, xmlrpc.client.Error, xml.parsers.expat.ExpatError) as e:
            self.close()
            raise RigError('flrig %s: %s' % (method, e)) from e

    def _number(self, method, kind=float):
        value = self.call(method)
        try:
            return kind(value)
        except (TypeError, ValueError):
            raise RigError('flrig %s: answered %r' % (method, value)) from None

    def frequency(self):
        return self._number('rig.get_vfo')      # a string of Hz

    def ptt(self):
        return self._number('rig.get_ptt', int) != 0

    def mode(self):
        return (str(self.call('rig.get_mode')),)

    def set_mode(self, mode):
        name = self._name(mode)
        self.call('rig.set_mode', name)
        return name

    def power(self):
        return self._number('rig.get_power')

    def set_power(self, watts):
        self.call('rig.set_power', int(round(watts)))   # flrig takes whole watts, as an int

    def set_ptt(self, on):
        self.call('rig.set_ptt', int(bool(on)))

    def _name(self, mode):
        try:
            modes = [str(m) for m in self.call('rig.get_modes')]
        except RigError:
            if not self.up:
                raise
            return mode                         # an flrig without get_modes: the name as given
        for want in [mode.upper()] + (['FSK'] if mode.upper() == 'RTTY' else []):
            for m in modes:                     # the name itself, else the first that starts with it
                if m.upper() == want:
                    return m
            for m in modes:
                if m.upper().startswith(want):
                    return m
        raise RigError('flrig: the rig has no %s mode; it has %s' % (mode, ', '.join(modes)))


# --- Band-follow (§8B.3a)

class BandFollow:
    """When to send PRESET: on a new band, or after a move of more than threshold (a fraction of the
    frequency) from the last PRESET sent, and at most once every interval seconds."""

    def __init__(self, threshold, interval):
        self.threshold, self.interval = threshold, interval
        self.band = self.mhz = self.at = None

    def due(self, mhz, now):
        """The band to PRESET for, or None for nothing to send yet."""
        band = band_of(mhz)
        if band is None:
            return None
        if band == self.band and abs(mhz - self.mhz) <= self.threshold * self.mhz:
            return None
        if self.at is not None and now - self.at < self.interval:
            return None
        return band

    def sent(self, band, mhz, now):
        self.band, self.mhz, self.at = band, mhz, now


class AleFollow(BandFollow):
    """Band-follow under an ALE controller (§8C.10). The controller scans two to five channels a second,
    far faster than the elements can follow, so a frequency counts only once it has held for dwell
    seconds: the scan has stopped there, to take a call or to make one. Then the band-follow rule
    applies as usual. It also counts the PRESETs, since every channel change wears the roller."""

    def __init__(self, threshold, interval, dwell):
        super().__init__(threshold, interval)
        self.dwell = dwell
        self.seen = self.since = None
        self.moves = collections.deque()

    def due(self, mhz, now):
        if self.seen is None or abs(mhz - self.seen) > 50e-6:   # a new channel: 50 Hz is the same one
            self.seen, self.since = mhz, now
        if now - self.since < self.dwell:
            return None
        return super().due(mhz, now)

    def sent(self, band, mhz, now):
        super().sent(band, mhz, now)
        self.moves.append(now)
        while self.moves and now - self.moves[0] > 3600:
            self.moves.popleft()

    def per_hour(self):
        return len(self.moves)


# --- One-button tune

class TuneWatch:
    """Judges each TLM while the rig is keyed for a tune: stay keyed, or why not."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.started = False                    # the tuner has left IDLE: the tune is under way

    def verdict(self, t, keyed_s):
        """None to stay keyed, else why to unkey. keyed_s: seconds keyed so far."""
        if t.state in ('MATCHED', 'FAULT'):
            return t.state
        if t.flag('hold'):
            return 'the tuner holds its move: the forward power is above its tune window'
        if keyed_s > self.cfg.tune_timeout:
            return 'no result after %g s' % self.cfg.tune_timeout
        if t.state in TUNING:
            self.started = True
            return None
        if t.state != 'IDLE':
            return 'the tuner is in %s' % t.state
        if self.started:
            return 'the tune ended in IDLE: the carrier was lost or the tune abandoned'
        if t.get('path') != 'TUNE':
            return 'the tuner is on its %s path' % t.get('path', '?')
        if not t.flag('want'):
            return 'the tuner no longer asks for a carrier'
        if keyed_s > self.cfg.carrier_s:        # want=1 means the tuner still sees no carrier
            return 'the tuner sees no carrier after %g s' % self.cfg.carrier_s
        return None


def keyed_tune(rig, link, cfg, guard):
    """Keys a carrier for the tune the tuner is waiting for, and returns why the tune ended ('MATCHED'
    for a match). However it ends, the rig is unkeyed and its mode and power are put back."""
    mode, watts = rig.mode(), rig.power()
    if rig.ptt():
        raise Refused('the rig is transmitting')
    if cfg.dry_run:
        log.info('dry run: would key %s at %g W until the tune ends, then put back %s at %.0f W',
                 cfg.tune_mode, cfg.tune_watts, ' '.join(mode), watts)
        return 'dry run'
    rig.owed = (mode, watts)
    try:
        name = rig.set_mode(cfg.tune_mode)
        rig.set_power(cfg.tune_watts)
        settled(rig, name, cfg)
        rig.set_ptt(True)
        log.info('tune: keyed, %s at %g W', name, cfg.tune_watts)
        return watch(link, cfg, time.monotonic())
    finally:
        with guard.held():
            restore(rig)


def settled(rig, mode, cfg):
    """Waits up to a second for the rig to read back the tune mode and power (flrig applies a change
    in its own time). Anything else is RigError, before the key-down."""
    most = cfg.tune_watts + max(2.0, 0.05 * cfg.rig_max_watts)
    since = time.monotonic()
    while True:
        now_mode, watts = rig.mode()[0], rig.power()
        if now_mode.upper() == mode.upper() and watts <= most:
            return
        if time.monotonic() - since > 1.0:
            raise RigError('the rig reads back %s at %.0f W after %s at %g W was set; not keying'
                           % (now_mode, watts, mode, cfg.tune_watts))
        time.sleep(0.2)


def watch(link, cfg, keyed_at):
    """Holds the carrier until the tuner's telemetry ends the tune, and returns why it ended. A dropped
    tuner link raises LinkError, which unkeys like any other way out."""
    judge = TuneWatch(cfg)
    while True:
        link.pump(0.05)
        why = judge.verdict(link.tlm, time.monotonic() - keyed_at)
        if why:
            log.info('tune: %s%s; unkeying', why, ', SWR %s' % link.tlm.get('swr') if why == 'MATCHED' else '')
            return why


def restore(rig, tries=4):
    """Unkeys the rig, reopening its link if that is what failed, then puts its mode and power back.
    rig.owed is cleared once the rig reads back unkeyed; until then the daemon tries again whenever it
    reconnects."""
    if not rig.owed:
        return
    mode, watts = rig.owed
    for n in range(1, tries + 1):
        try:
            if not rig.up:
                rig.connect()
            rig.set_ptt(False)
            if rig.ptt():
                raise RigError('PTT still reads on')
            break
        except RigError as e:
            log.error('unkey: %s (try %d of %d)', e, n, tries)
            if n < tries:
                time.sleep(0.5 * n)
    else:
        log.critical('the rig may still be keyed: unkey it by hand')
        return
    rig.owed = None
    try:
        rig.set_mode(*mode)
        rig.set_power(watts)
        log.info('unkeyed; the rig is back to %s at %.0f W', ' '.join(mode), watts)
    except RigError as e:
        log.error('unkeyed, but %s: set %s at %.0f W by hand', e, ' '.join(mode), watts)


# --- The daemon, and the one-shot tune

class Bridge:
    """catbridge.py run: band-follow and one-button tune, reconnecting to either end as needed."""

    def __init__(self, cfg, rig, link, guard):
        self.cfg, self.rig, self.link, self.guard = cfg, rig, link, guard
        self.follow = (AleFollow(cfg.threshold, cfg.preset_s, cfg.dwell_s) if cfg.ale
                       else BandFollow(cfg.threshold, cfg.preset_s))
        self.worn = 0               # ALE: the PRESETs an hour last warned about
        self.retry = {end.name: Backoff(cfg.retry_s, cfg.retry_max_s) for end in (rig, link)}
        self.armed = True           # a want=1 may be answered; a tune disarms it until want=0 is seen
        self.mhz, self.ptt = None, False        # the rig as last polled
        self.next_poll = 0.0
        self.trouble = None         # the last rig error logged, so a steady one is logged once

    def run(self):
        while True:
            try:
                self.step()
            except Exception:
                log.exception('unexpected error; carrying on')
                time.sleep(1.0)

    def step(self):
        self._connect()
        wait = min(0.1, max(0.0, self.next_poll - time.monotonic()))
        if self.link.up:
            try:
                self.link.pump(wait)
            except LinkError as e:
                self._lost(self.link, e)
        else:
            time.sleep(wait)
        if self.link.up and self.link.tlm_at:
            self.retry[self.link.name].reset()
            self._answer_want()
        if time.monotonic() >= self.next_poll:
            self.next_poll = time.monotonic() + (self.cfg.ale_poll_s if self.cfg.ale else self.cfg.poll_s)
            self._poll()

    def _connect(self):
        now = time.monotonic()
        for end in (self.link, self.rig):
            retry = self.retry[end.name]
            if end.up or now < retry.at:
                continue
            try:
                end.connect()
            except (RigError, LinkError, OSError) as e:
                log.warning('%s; retrying in %g s', e, retry.fail(now))
                continue
            if end is self.rig and self.rig.owed:       # a tune's unkey that could not reach the rig
                with self.guard.held():
                    restore(self.rig)

    def _lost(self, end, e):
        end.close()
        log.warning('%s; reconnecting in %g s', e, self.retry[end.name].fail(time.monotonic()))

    def _poll(self):
        if not self.rig.up:
            return
        try:
            self.mhz = self.rig.frequency() / 1e6
            self.ptt = self.rig.ptt()
        except RigError as e:
            if not self.rig.up:
                return self._lost(self.rig, e)
            if str(e) != self.trouble:
                log.warning('%s', e)
            self.trouble = str(e)
            return
        self.retry[self.rig.name].reset()
        self.trouble = None
        if self.ptt:
            return                              # never while transmitting
        band = self.follow.due(self.mhz, time.monotonic())
        if band is None or not self._preset_ok():
            return
        cmd = 'PRESET %.4f' % self.mhz
        if self.cfg.dry_run:
            log.info('dry run: would send %s (%s)', cmd, band)
        else:
            try:
                self.link.send(cmd)
            except LinkError as e:
                return self._lost(self.link, e)
            log.info('%s (%s)', cmd, band)
        self.follow.sent(band, self.mhz, time.monotonic())
        if self.cfg.ale:
            n = self.follow.per_hour()
            if n > self.cfg.moves_per_hour and n > self.worn:
                log.warning('ALE: %d channel changes in the last hour; each moves the elements and wears the '
                            'roller (limit the scan list or the sounding)', n)
                self.worn = n
            elif n <= self.cfg.moves_per_hour:
                self.worn = 0

    def _preset_ok(self):
        """PRESET is taken only in IDLE, receiving, on the TUNE path, with the bypass off and no self-test
        running (§8B.3a). Until the telemetry says all that, a PRESET waits."""
        t = self.link.tlm
        return (self.link.fresh and t.state == 'IDLE' and t.get('path') == 'TUNE' and not t.flag('carrier')
                and not t.flag('bypass') and not t.flag('bitrun'))

    def _answer_want(self):
        t = self.link.tlm
        if self.cfg.ale:
            return                              # the ALE controller owns the rig: the tuner tunes on its carrier
        if not t.flag('want'):
            self.armed = True
            return
        if not self.armed or not self.rig.up or self.ptt or t.get('path') != 'TUNE' or not self.link.fresh:
            return                              # one carrier per request, and never over the operator
        self.armed = False
        log.info('tune: the tuner asks for a carrier')
        try:
            why = keyed_tune(self.rig, self.link, self.cfg, self.guard)
        except Refused as e:
            log.warning('tune: not keying: %s', e)
        except RigError as e:
            log.error('tune: %s', e)
            if not self.rig.up:
                self._lost(self.rig, e)
        except LinkError as e:
            self._lost(self.link, e)
        else:
            band = band_of(self.mhz) if self.mhz else None
            if why == 'MATCHED' and band:       # the elements now sit at the match for this frequency
                self.follow.sent(band, self.mhz, time.monotonic())


def tune_once(cfg, rig, link, guard):
    """catbridge.py tune: TUNE, the carrier the tuner then asks for, and exit. Returns the exit status,
    0 for a match."""
    rig.connect()
    link.connect()
    if not link.wait(lambda t: True, cfg.stale_s):
        raise LinkError('no telemetry from the tuner')
    if cfg.dry_run:
        log.info('dry run: would send TUNE')
    else:
        link.send('TUNE')
        if not link.wait(lambda t: t.flag('want') and t.get('path') == 'TUNE', cfg.carrier_s):
            t = link.tlm
            log.error('the tuner does not ask for a carrier: state %s, path %s, bypass %s',
                      t.state, t.get('path', '?'), t.get('bypass', '?'))
            return 1
    return 0 if keyed_tune(rig, link, cfg, guard) in ('MATCHED', 'dry run') else 1


def parse_args(argv):
    p = argparse.ArgumentParser(prog='catbridge.py', description='The CAT bridge: band-follow and one-button '
                                'tune for the tuner. See README.md.')
    p.add_argument('command', choices=('run', 'tune'), help='run: the daemon; tune: one tune, then exit')
    p.add_argument('--tuner', default='tuner.local:4600', metavar='HOST[:PORT]', help='default %(default)s')
    p.add_argument('--rig', choices=('hamlib', 'flrig'), default='hamlib', help='default %(default)s')
    p.add_argument('--rig-addr', default='', metavar='ADDR',
                   help='rigctld HOST[:PORT] (localhost:4532) or the flrig URL (http://localhost:12345)')
    p.add_argument('--tune-watts', type=float, default=20.0, metavar='W',
                   help='the tune carrier, at most 50 W (default %(default)g)')
    p.add_argument('--rig-max-watts', type=float, default=100.0, metavar='W',
                   help="the rig's power at Hamlib RFPOWER 1.0 (default %(default)g)")
    p.add_argument('--tune-mode', default='RTTY', metavar='MODE', help='the carrier mode (default %(default)s)')
    p.add_argument('--tune-timeout', type=float, default=15.0, metavar='S',
                   help='the longest key-down for one tune, at most 30 s (default %(default)g)')
    p.add_argument('--threshold', type=float, default=0.5, metavar='PCT',
                   help='PRESET again after a move of this percent of the frequency (default %(default)g)')
    p.add_argument('--ale', action='store_true',
                   help='an ALE controller owns the rig: PRESET when the scan dwells, never key (design log 8C.10)')
    p.add_argument('--dwell', type=float, default=1.5, metavar='S',
                   help='ALE: a frequency held this long is a channel the scan stopped on (default %(default)g)')
    p.add_argument('--dry-run', action='store_true', help='read both ends, log what would be sent, key nothing')
    p.add_argument('-v', '--verbose', action='store_true', help='debug logging')
    a = p.parse_args(argv)
    cfg = Config(tuner=a.tuner, rig=a.rig, rig_addr=a.rig_addr, tune_watts=a.tune_watts,
                 rig_max_watts=a.rig_max_watts, tune_mode=a.tune_mode, tune_timeout=a.tune_timeout,
                 threshold=a.threshold / 100, dry_run=a.dry_run, ale=a.ale, dwell_s=a.dwell)
    why = cfg.problem()
    if why:
        p.error(why)
    if cfg.ale and a.command == 'tune':
        p.error('tune keys the rig, and under ALE the controller owns it')
    return a.command, cfg, a.verbose


def main(argv=None):
    command, cfg, verbose = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    guard = Guard()
    guard.install()
    rig = (Flrig if cfg.rig == 'flrig' else Rigctld)(cfg.rig_addr, cfg.rig_max_watts, cfg.io_s)
    link = TunerLink(cfg)
    level = ' (RFPOWER %.3f)' % (cfg.tune_watts / cfg.rig_max_watts) if cfg.rig == 'hamlib' else ''
    log.info('%s: tuner %s, %s at %s, tune %s at %g W%s, at most %g s%s', command, cfg.tuner, rig.name, rig.where,
             cfg.tune_mode, cfg.tune_watts, level, cfg.tune_timeout, ', dry run' if cfg.dry_run else '')
    if cfg.ale:
        log.info('ALE mode: PRESET once a channel holds %g s; one-button tune off', cfg.dwell_s)
    try:
        if command == 'run':
            Bridge(cfg, rig, link, guard).run()     # until a signal
        return tune_once(cfg, rig, link, guard)
    except Stop as e:
        log.info('stopped by %s', e)
        return 0 if command == 'run' else 1
    except (RigError, LinkError, Refused, OSError) as e:
        log.error('%s', e)
        return 1
    finally:
        with contextlib.suppress(Stop), guard.held():
            restore(rig)
        link.close()
        rig.close()


if __name__ == '__main__':
    sys.exit(main())
