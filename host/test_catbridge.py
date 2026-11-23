# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for catbridge.py against fake servers: rigctld, flrig, and the tuner's line port.

Run:  cd host && python3 -m unittest -v test_catbridge
"""
import contextlib
import functools
import io
import logging
import os
import re
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
import unittest
from xmlrpc.server import SimpleXMLRPCServer

import catbridge

HERE = os.path.dirname(os.path.abspath(__file__))
logging.getLogger('catbridge').addHandler(logging.NullHandler())
logging.getLogger('catbridge').propagate = False


def xor(text):
    """The tuner's checksum, written again here so that the tests do not take catbridge's on trust."""
    return functools.reduce(lambda c, ch: c ^ ord(ch), text, 0)


def wait_until(test, seconds=5.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if test():
            return True
        time.sleep(0.01)
    return False


def tlm(text):
    return catbridge.Telemetry.parse('TLM ' + text)


class FakeRigctld(socketserver.ThreadingTCPServer):
    """rigctld's default protocol for f, m, M, l/L RFPOWER, t and T, with a rig's state behind it."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(('127.0.0.1', 0), _RigctldHandler)
        self.freq, self.mode, self.passband, self.level, self.ptt = 7_074_000, 'USB', 2400, 1.0, 0
        self.log, self.errors, self.conns = [], {}, []
        self.ignore_power = False       # L RFPOWER answers RPRT 0 and changes nothing
        self.drop_after_key = False     # the connection closes right after T 1 is answered
        self.refuse, self.refused = False, 0    # close each new connection at once, and count them
        self.lock = threading.Lock()
        threading.Thread(target=self.serve_forever, daemon=True).start()

    @property
    def addr(self):
        return '127.0.0.1:%d' % self.server_address[1]

    def answer(self, line):
        with self.lock:
            self.log.append(line)
            w = line.split()
            if w[0] in self.errors:
                return 'RPRT %d\n' % self.errors[w[0]]
            if w[0] == 'f':
                return '%d\n' % self.freq
            if w[0] == 'm':
                return '%s\n%d\n' % (self.mode, self.passband)
            if w[0] == 'M':
                self.mode, self.passband = w[1], int(w[2]) or 500
                return 'RPRT 0\n'
            if w[:2] == ['l', 'RFPOWER']:
                return '%.6f\n' % self.level
            if w[:2] == ['L', 'RFPOWER']:
                if not self.ignore_power:
                    self.level = float(w[2])
                return 'RPRT 0\n'
            if w[0] == 't':
                return '%d\n' % self.ptt
            if w[0] == 'T':
                self.ptt = int(w[1])
                return 'RPRT 0\n'
            return 'RPRT -11\n'

    def sets(self):
        """The commands that changed the rig, in order."""
        with self.lock:
            return [c for c in self.log if c[0] in 'MLT']

    def handle_error(self, request, client_address):
        pass

    def drop(self):
        for c in list(self.conns):
            with contextlib.suppress(OSError):
                c.shutdown(socket.SHUT_RDWR)

    def stop(self):
        self.shutdown()
        self.server_close()
        self.drop()


class _RigctldHandler(socketserver.StreamRequestHandler):
    def handle(self):
        if self.server.refuse:
            self.server.refused += 1
            return
        self.server.conns.append(self.connection)
        with contextlib.suppress(OSError):
            for raw in self.rfile:
                line = raw.decode().strip()
                if line:
                    self.wfile.write(self.server.answer(line).encode())
                if line == 'T 1' and self.server.drop_after_key:
                    self.server.drop_after_key = False
                    return


class FakeFlrig:
    """The flrig XML-RPC methods the bridge uses, over a Yaesu's mode table."""

    def __init__(self):
        self.freq, self.mode, self.power, self.ptt = 14_074_000, 'USB', 100, 0
        self.modes = ['LSB', 'USB', 'CW-U', 'FM', 'AM', 'RTTY-L', 'CW-L', 'DATA-L', 'RTTY-U', 'DATA-U']
        self.log = []
        self.srv = SimpleXMLRPCServer(('127.0.0.1', 0), logRequests=False)
        for name in ('get_xcvr', 'get_vfo', 'get_mode', 'get_modes', 'set_mode', 'get_power', 'set_power',
                     'get_ptt', 'set_ptt'):
            self.srv.register_function(getattr(self, name), 'rig.' + name)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = 'http://127.0.0.1:%d' % self.srv.server_address[1]

    def get_xcvr(self):
        return 'FT-991A'

    def get_vfo(self):
        return str(self.freq)

    def get_mode(self):
        return self.mode

    def get_modes(self):
        return self.modes

    def set_mode(self, mode):
        self.log.append('set_mode %s' % mode)
        if mode in self.modes:
            self.mode = mode
            return 1
        return 0

    def get_power(self):
        return self.power

    def set_power(self, watts):
        self.log.append('set_power %r' % watts)
        self.power = watts
        return 0

    def get_ptt(self):
        return self.ptt

    def set_ptt(self, on):
        self.log.append('set_ptt %r' % on)
        self.ptt = on
        return 0

    def stop(self):
        self.srv.shutdown()
        self.srv.server_close()


class FakeTuner:
    """The tuner's line port, with a toy state machine. A TUNE waits in IDLE for a carrier, which is the
    rig's PTT; then MEASURE, MOVE and VERIFY last two ticks each before the outcome. Losing the carrier
    returns to IDLE, as the firmware does."""

    def __init__(self, rig=None):
        self.rig = rig                  # anything with .ptt: keying it is the carrier
        self.state, self.path, self.pending = 'IDLE', 'TUNE', False
        self.outcome = 'MATCHED'        # MATCHED, FAULT, IDLE (abandoned) or None (never ends)
        self.hold_in_move = False
        self.want_field = True          # False: no want= or hold=, as older firmware
        self.want = None                # not None: want= says this, whatever the state
        self.subscribe = True           # False: SUBSCRIBE brings nothing, but QUERY answers
        self.carrier = self.hold = False
        self.ticks = 0
        self.commands, self.bad, self.clients = [], [], []
        self.lock = threading.RLock()
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen(4)
        self.sock.settimeout(0.1)
        self.addr = '127.0.0.1:%d' % self.sock.getsockname()[1]
        self.running = True
        for target in (self._accept, self._tick):
            threading.Thread(target=target, daemon=True).start()

    def tlm(self):
        with self.lock:
            want = self.state == 'IDLE' and self.pending and not self.carrier and self.path == 'TUNE'
            if self.want is not None:
                want = self.want
            text = ('TLM state=%s path=%s mode=STRICT mhz=7.0740 carrier=%d swr=1.12 fwd=- c1=123.4 c2=456.7 '
                    'l=5.123 tank=31.2 hot=0 c=0000 b=0000 permit=1 bypass=0 loss=0 lim=1500 derate=0 '
                    'bit=00000 bitrun=0' % (self.state, self.path, self.carrier))
            if self.want_field:
                text += ' want=%d hold=%d' % (want, self.hold)
            text += ' ev=7 later=1'             # a field from some later firmware
            return '%s*%02X' % (text, xor(text))

    def step(self):
        with self.lock:
            self.carrier = bool(self.rig is not None and self.rig.ptt)
            if self.state == 'IDLE' and self.carrier and self.pending:
                self.state, self.pending, self.ticks = 'MEASURE', False, 0
            elif self.state in ('MEASURE', 'MOVE', 'VERIFY'):
                if not self.carrier:
                    self.state = 'IDLE'
                elif self.outcome is not None:
                    self.ticks += 1
                    if self.ticks >= 2:
                        self.ticks = 0
                        self.state = {'MEASURE': 'MOVE', 'MOVE': 'VERIFY', 'VERIFY': self.outcome}[self.state]
            elif self.state == 'MATCHED' and not self.carrier:
                self.state = 'IDLE'
            self.hold = self.hold_in_move and self.state == 'MOVE'

    def presets(self):
        with self.lock:
            return [c for c in self.commands if c.startswith('PRESET')]

    def drop(self):
        """Closes every client connection, as a tuner that restarted."""
        with self.lock:
            for c in self.clients:
                with contextlib.suppress(OSError):
                    c['conn'].shutdown(socket.SHUT_RDWR)
                    c['conn'].close()
            self.clients.clear()

    def stop(self):
        self.running = False
        with contextlib.suppress(OSError):
            self.sock.close()
        self.drop()

    def _tick(self):
        while self.running:
            self.step()
            now = time.monotonic()
            with self.lock:
                for c in list(self.clients):
                    if c['hz'] and now >= c['next']:
                        c['next'] = now + 1.0 / c['hz']
                        self._send(c, self.tlm())
            time.sleep(0.02)

    def _accept(self):
        while self.running:
            try:
                conn, _ = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            c = {'conn': conn, 'hz': 0.0, 'next': 0.0}
            with self.lock:
                self.clients.append(c)
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    def _serve(self, c):
        buf = b''
        with contextlib.suppress(OSError):
            while True:
                data = c['conn'].recv(1024)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    raw, buf = buf.split(b'\n', 1)
                    self._command(c, raw.decode().strip())
        with self.lock:
            if c in self.clients:
                self.clients.remove(c)
        c['conn'].close()

    def _command(self, c, line):
        text, star, hh = line.rpartition('*')
        if not star or int(hh, 16) != xor(text):
            self.bad.append(line)
            return self._reply(c, 'ERR checksum')
        with self.lock:
            self.commands.append(text)
            word = text.split()
            if word[0] == 'SUBSCRIBE':
                c['hz'], c['next'] = (float(word[1]) if self.subscribe else 0.0), 0.0
                self._reply(c, 'OK SUBSCRIBE')
            elif word[0] == 'QUERY':
                self._send(c, self.tlm())
            elif word[0] == 'TUNE':
                self.pending = True
                self._reply(c, 'OK TUNE')
            elif word[0] == 'PRESET' and self.state == 'IDLE' and not self.carrier:
                self._reply(c, 'OK ' + text)
            elif word[0] == 'PRESET':
                self._reply(c, 'ERR preset: only in IDLE')
            else:
                self._reply(c, 'ERR unknown command')

    def _reply(self, c, text):
        self._send(c, '%s*%02X' % (text, xor(text)))

    def _send(self, c, line):
        with contextlib.suppress(OSError):
            c['conn'].sendall((line + '\r\n').encode())


# --- Pure parts

class TestProtocol(unittest.TestCase):
    def test_checksum_matches_the_firmware(self):
        self.assertEqual(catbridge.seal('TUNE'), 'TUNE*0A')         # fw/test/test_link.cpp
        self.assertEqual(catbridge.seal('PRESET 14.2000'), 'PRESET 14.2000*%02X' % xor('PRESET 14.2000'))

    def test_unseal(self):
        text = 'TLM state=IDLE want=1'
        good = '%s*%02X' % (text, xor(text))
        self.assertEqual(catbridge.unseal(good), text)
        self.assertIsNone(catbridge.unseal(text))                    # no checksum
        self.assertIsNone(catbridge.unseal('%s*%02X' % (text, xor(text) ^ 1)))
        self.assertIsNone(catbridge.unseal(text + '*ZZ'))

    def test_telemetry_fields(self):
        t = tlm('state=MATCHED path=TUNE swr=1.12 fwd=- c=0000 later=7')
        self.assertEqual((t.state, t['path'], t['swr'], t['fwd'], t['later']), ('MATCHED', 'TUNE', '1.12', '-', '7'))
        self.assertFalse(t.flag('want'))                            # missing reads as 0
        self.assertTrue(tlm('want=1').flag('want'))
        self.assertEqual(catbridge.Telemetry().state, '?')


class TestBands(unittest.TestCase):
    def test_bands_match_the_firmware(self):
        src = os.path.join(HERE, '..', 'fw', 'core', 'src', 'freq.cpp')
        if not os.path.exists(src):
            self.skipTest('no fw/ beside host/')
        with open(src) as f:
            found = re.findall(r'\{"(\w+)", ([\d.]+), ([\d.]+)\}', f.read())
        self.assertEqual([(n, float(lo), float(hi)) for n, lo, hi in found], list(catbridge.BANDS))

    def test_band_of(self):
        self.assertEqual(catbridge.band_of(14.0), '20m')
        self.assertEqual(catbridge.band_of(14.35), '20m')
        self.assertIsNone(catbridge.band_of(14.351))
        self.assertIsNone(catbridge.band_of(10.0))                   # WWV

    def test_follow(self):
        f = catbridge.BandFollow(0.005, 2.0)
        self.assertEqual(f.due(7.074, 0.0), '40m')                  # the first: always
        f.sent('40m', 7.074, 0.0)
        self.assertIsNone(f.due(7.100, 10.0))                       # 0.37 %: near enough
        self.assertEqual(f.due(7.150, 10.0), '40m')                 # 1.1 %
        self.assertIsNone(f.due(14.074, 1.0))                       # a new band, but within 2 s of the last
        self.assertEqual(f.due(14.074, 2.5), '20m')
        self.assertIsNone(f.due(10.0, 10.0))                        # off the bands: nothing to send

    def test_ale_follow_waits_for_a_dwell(self):
        # §8C.10: a scan at 2-5 channels a second sends nothing; a channel held 1.5 s sends PRESET.
        f = catbridge.AleFollow(0.005, 2.0, 1.5)
        now = 0.0
        for mhz in (3.596, 5.3715, 7.102, 10.145, 14.109, 18.106) * 3:  # a scan list, 0.25 s a channel
            self.assertIsNone(f.due(mhz, now))
            now += 0.25
        for _ in range(5):                                          # it stops on 7.102 MHz: not yet...
            self.assertIsNone(f.due(7.102, now))
            now += 0.25
        self.assertIsNone(f.due(7.10203, now))                      # (30 Hz of reading noise is the same channel)
        now += 0.25
        self.assertEqual(f.due(7.102, now), '40m')                  # ...held 1.5 s: PRESET
        f.sent('40m', 7.102, now)
        self.assertIsNone(f.due(7.102, now + 5))                    # already there
        self.assertEqual(f.per_hour(), 1)
        f.sent('20m', 14.109, now + 10)
        f.sent('40m', 7.102, now + 3605)                            # the first has aged out of the hour
        self.assertEqual(f.per_hour(), 2)


class TestConfig(unittest.TestCase):
    def test_refusals(self):
        C = catbridge.Config
        self.assertIsNone(C().problem())
        self.assertIsNone(C(tune_watts=50, tune_timeout=30).problem())
        for bad in (C(tune_watts=51), C(tune_watts=0), C(tune_watts=20, rig_max_watts=10),
                    C(tune_timeout=31), C(tune_timeout=0), C(threshold=0), C(tune_mode='USB\nT 1'),
                    C(tuner='tuner:x')):
            self.assertIsNotNone(bad.problem(), bad)

    def test_cli(self):
        cmd, cfg, verbose = catbridge.parse_args(['tune', '--tune-watts', '15', '--threshold', '1', '-v'])
        self.assertEqual((cmd, cfg.tune_watts, cfg.threshold, verbose), ('tune', 15.0, 0.01, True))
        cmd, cfg, _ = catbridge.parse_args(['run', '--ale', '--dwell', '2'])
        self.assertTrue(cfg.ale and cfg.dwell_s == 2.0)
        for bad in (['run', '--tune-watts', '60'], ['run', '--tune-timeout', '45'], ['jog'], ['tune', '--ale'],
                    ['run', '--ale', '--dwell', '0.2']):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                catbridge.parse_args(bad)


class TestTuneWatch(unittest.TestCase):
    def judge(self):
        return catbridge.TuneWatch(catbridge.Config(carrier_s=3, tune_timeout=15))

    def test_waiting_for_the_carrier(self):
        w = self.judge()
        self.assertIsNone(w.verdict(tlm('state=IDLE path=TUNE want=1'), 1.0))
        self.assertIn('no carrier', w.verdict(tlm('state=IDLE path=TUNE want=1'), 3.5))
        self.assertIn('no longer asks', self.judge().verdict(tlm('state=IDLE path=TUNE want=0'), 0.5))
        self.assertIn('no longer asks', self.judge().verdict(tlm('state=IDLE path=TUNE'), 0.5))
        self.assertIn('AUX', self.judge().verdict(tlm('state=IDLE path=AUX want=1'), 0.5))

    def test_under_way(self):
        w = self.judge()
        self.assertIsNone(w.verdict(tlm('state=MEASURE path=TUNE want=0'), 1.0))
        self.assertIsNone(w.verdict(tlm('state=MOVE path=TUNE want=0'), 5.0))   # past carrier_s is fine now
        self.assertIn('ended in IDLE', w.verdict(tlm('state=IDLE path=TUNE want=1'), 6.0))
        self.assertIn('after 15 s', self.judge().verdict(tlm('state=VERIFY'), 15.1))

    def test_endings(self):
        self.assertEqual(self.judge().verdict(tlm('state=MATCHED'), 2.0), 'MATCHED')
        self.assertEqual(self.judge().verdict(tlm('state=FAULT'), 2.0), 'FAULT')
        self.assertIn('tune window', self.judge().verdict(tlm('state=MOVE hold=1'), 2.0))
        self.assertIn('SELF-TEST', self.judge().verdict(tlm('state=SELF-TEST'), 0.5))

    def test_guard_holds_a_signal_back(self):
        g = catbridge.Guard()
        done = []
        with self.assertRaises(catbridge.Stop):
            with g.held():
                g.on_signal(signal.SIGTERM)         # while the rig is put back: later
                done.append('put back')
        self.assertEqual(done, ['put back'])
        with self.assertRaises(catbridge.Stop):
            g.on_signal(signal.SIGINT)


# --- Against the fakes

class Bench(unittest.TestCase):
    """A fake rig and a fake tuner, wired so that keying the rig is the tuner's carrier."""

    def setUp(self):
        self.rig = FakeRigctld()
        self.tuner = FakeTuner(self.rig)
        self.addCleanup(self.rig.stop)
        self.addCleanup(self.tuner.stop)

    def config(self, **kw):
        c = dict(tuner=self.tuner.addr, rig_addr=self.rig.addr, poll_s=0.05, preset_s=0.3, tlm_hz=20,
                 stale_s=1.0, carrier_s=0.6, tune_timeout=2.0, io_s=1.0, retry_s=0.05, retry_max_s=0.2)
        c.update(kw)
        return catbridge.Config(**c)

    def ends(self, cfg):
        rig = catbridge.Rigctld(cfg.rig_addr, cfg.rig_max_watts, cfg.io_s)
        link = catbridge.TunerLink(cfg)
        self.addCleanup(link.close)
        self.addCleanup(rig.close)
        return rig, link

    def bridge(self, **kw):
        cfg = self.config(**kw)
        return catbridge.Bridge(cfg, *self.ends(cfg), catbridge.Guard())

    def run_until(self, bridge, test, seconds=5.0):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            bridge.step()
            if test():
                return True
        return False

    def when(self, test, action):
        """Does action from another thread once test passes, while the bridge is busy in a tune."""
        t = threading.Thread(target=lambda: wait_until(test) and action(), daemon=True)
        t.start()
        self.addCleanup(t.join, 2)

    def assertPutBack(self):
        self.assertEqual(self.rig.ptt, 0)
        self.assertEqual((self.rig.mode, self.rig.passband, self.rig.level), ('USB', 2400, 1.0))


class TestRigctld(Bench):
    def hamlib(self, max_watts=100):
        r = catbridge.Rigctld(self.rig.addr, max_watts, 1.0)
        r.connect()
        self.addCleanup(r.close)
        return r

    def test_commands(self):
        r = self.hamlib()
        self.assertEqual(r.frequency(), 7_074_000)
        self.assertEqual(r.mode(), ('USB', '2400'))
        self.assertFalse(r.ptt())
        self.assertAlmostEqual(r.power(), 100.0)
        self.assertEqual(r.set_mode('RTTY'), 'RTTY')
        r.set_power(20)
        r.set_ptt(True)
        self.assertTrue(r.ptt())
        r.set_ptt(False)
        r.set_mode('USB', '2400')
        self.assertEqual(self.rig.sets(), ['M RTTY 0', 'L RFPOWER 0.200000', 'T 1', 'T 0', 'M USB 2400'])
        self.assertEqual((self.rig.mode, self.rig.passband), ('USB', 2400))

    def test_rig_max_scales_rfpower(self):
        self.hamlib(max_watts=200).set_power(20)
        self.assertAlmostEqual(self.rig.level, 0.1)

    def test_errors(self):
        r = self.hamlib()
        self.rig.errors['L'] = -11
        with self.assertRaisesRegex(catbridge.RigError, 'RPRT -11, not available'):
            r.set_power(20)
        self.rig.errors['m'] = -5
        with self.assertRaisesRegex(catbridge.RigError, 'timed out'):
            r.mode()
        self.assertTrue(r.up)                       # an RPRT is the rig's answer, not a dead link
        self.assertEqual(r.frequency(), 7_074_000)  # and the link is still in step

    def test_dropped_link(self):
        r = self.hamlib()
        r.frequency()
        self.rig.drop()
        with self.assertRaises(catbridge.RigError):
            r.frequency()
        self.assertFalse(r.up)
        r.connect()
        self.assertEqual(r.frequency(), 7_074_000)


class TestFlrig(unittest.TestCase):
    def setUp(self):
        self.flrig = FakeFlrig()
        self.addCleanup(self.flrig.stop)
        self.r = catbridge.Flrig(self.flrig.url, 100, 1.0)
        self.r.connect()
        self.addCleanup(self.r.close)

    def test_commands(self):
        self.assertEqual(self.r.frequency(), 14_074_000)
        self.assertEqual(self.r.mode(), ('USB',))
        self.assertEqual(self.r.power(), 100)
        self.assertFalse(self.r.ptt())
        self.assertEqual(self.r.set_mode('RTTY'), 'RTTY-L')        # the rig's own name for it
        self.r.set_power(20.4)
        self.assertEqual(self.flrig.power, 20)
        self.assertIsInstance(self.flrig.power, int)
        self.r.set_ptt(True)
        self.assertEqual(self.flrig.ptt, 1)
        self.r.set_ptt(False)
        self.assertEqual(self.flrig.ptt, 0)

    def test_mode_names(self):
        self.flrig.modes = ['LSB', 'USB', 'CW', 'FM', 'AM', 'FSK', 'CW-R', 'FSK-R']    # a Kenwood
        self.assertEqual(self.r.set_mode('RTTY'), 'FSK')
        self.assertEqual(self.r.set_mode('fm'), 'FM')
        self.flrig.modes = ['LSB', 'USB']
        with self.assertRaisesRegex(catbridge.RigError, 'no RTTY mode; it has LSB, USB'):
            self.r.set_mode('RTTY')

    def test_unreachable(self):
        r = catbridge.Flrig('127.0.0.1:1', 100, 0.5)
        with self.assertRaises(catbridge.RigError):
            r.connect()
        self.assertFalse(r.up)

    def test_keyed_tune(self):
        tuner = FakeTuner(self.flrig)
        self.addCleanup(tuner.stop)
        cfg = catbridge.Config(rig='flrig', tuner=tuner.addr, tlm_hz=20, stale_s=1.0, carrier_s=0.6, tune_timeout=2.0)
        link = catbridge.TunerLink(cfg)
        link.connect()
        self.addCleanup(link.close)
        tuner.pending = True
        self.assertTrue(link.wait(lambda t: t.flag('want'), 2.0))
        self.assertEqual(catbridge.keyed_tune(self.r, link, cfg, catbridge.Guard()), 'MATCHED')
        self.assertEqual(self.flrig.log, ['set_mode RTTY-L', 'set_power 20', 'set_ptt 1', 'set_ptt 0',
                                          'set_mode USB', 'set_power 100'])
        self.assertEqual((self.flrig.ptt, self.flrig.mode, self.flrig.power), (0, 'USB', 100))


class TestBandFollow(Bench):
    def test_presets_on_band_changes(self):
        b = self.bridge()
        self.assertTrue(self.run_until(b, lambda: self.tuner.presets() == ['PRESET 7.0740']))
        self.rig.freq = 7_080_000                           # 0.08 %: nothing
        self.run_until(b, lambda: False, 0.5)
        self.assertEqual(self.tuner.presets(), ['PRESET 7.0740'])
        self.rig.freq = 7_250_000                           # 2.5 %
        self.assertTrue(self.run_until(b, lambda: self.tuner.presets()[-1] == 'PRESET 7.2500'))
        self.rig.freq = 10_000_000                          # off the bands
        self.run_until(b, lambda: False, 0.5)
        self.assertEqual(len(self.tuner.presets()), 2)
        self.assertEqual(self.tuner.bad, [])                # every command carried a good checksum
        self.assertEqual(self.rig.sets(), [])               # band-follow never touches the rig

    def test_not_while_transmitting(self):
        b = self.bridge()
        self.assertTrue(self.run_until(b, lambda: self.tuner.presets()))
        self.tuner.rig = None                               # SSB: the tuner sees no steady carrier
        self.rig.ptt, self.rig.freq = 1, 14_074_000
        self.run_until(b, lambda: False, 0.6)
        self.assertEqual(len(self.tuner.presets()), 1)
        self.rig.ptt = 0
        self.assertTrue(self.run_until(b, lambda: self.tuner.presets()[-1] == 'PRESET 14.0740'))

    def test_waits_for_idle(self):
        self.tuner.state = 'FAULT'
        b = self.bridge()
        self.run_until(b, lambda: False, 0.6)
        self.assertEqual(self.tuner.presets(), [])
        self.tuner.state = 'IDLE'
        self.assertTrue(self.run_until(b, lambda: self.tuner.presets() == ['PRESET 7.0740']))

    def test_dry_run(self):
        self.tuner.pending = True
        b = self.bridge(dry_run=True)
        with self.assertLogs('catbridge', 'INFO') as logs:
            self.run_until(b, lambda: False, 0.8)
        self.assertEqual((self.tuner.presets(), self.rig.sets()), ([], []))
        text = '\n'.join(logs.output)
        self.assertIn('would send PRESET 7.0740 (40m)', text)
        self.assertIn('would key RTTY at 20 W', text)
        self.assertEqual(text.count('would key'), 1)        # once for the request

    def test_reconnects(self):
        b = self.bridge()
        self.assertTrue(self.run_until(b, lambda: b.rig.up and b.link.tlm_at))
        self.rig.drop()
        self.tuner.drop()
        self.assertTrue(self.run_until(b, lambda: not b.rig.up or not b.link.up, 2.0))
        polls = len(self.rig.log)
        self.assertTrue(self.run_until(b, lambda: b.rig.up and b.link.up and len(self.rig.log) > polls + 4))
        self.assertTrue(self.run_until(b, lambda: self.tuner.commands.count('SUBSCRIBE 20') == 2))

    def test_unreachable_ends(self):
        self.rig.stop()
        self.tuner.stop()
        b = self.bridge()
        with self.assertLogs('catbridge', 'WARNING') as logs:
            self.run_until(b, lambda: False, 0.5)
        self.assertIn('retrying in', '\n'.join(logs.output))


class TestOneButton(Bench):
    def test_matched(self):
        self.tuner.pending = True
        b = self.bridge()
        with self.assertLogs('catbridge', 'INFO') as logs:
            self.assertTrue(self.run_until(b, lambda: 'T 0' in self.rig.log))
        self.assertEqual(self.rig.sets(), ['M RTTY 0', 'L RFPOWER 0.200000', 'T 1', 'T 0', 'M USB 2400',
                                           'L RFPOWER 1.000000'])
        self.assertPutBack()
        text = '\n'.join(logs.output)
        self.assertIn('tune: MATCHED, SWR 1.12; unkeying', text)
        self.assertIn('back to USB 2400 at 100 W', text)

    def test_query_when_the_subscription_is_silent(self):
        self.tuner.subscribe = False        # as the subscribed TLM is now, too long for push()'s buffer
        self.tuner.pending = True
        b = self.bridge()
        with self.assertLogs('catbridge', 'INFO') as logs:
            self.assertTrue(self.run_until(b, lambda: 'T 0' in self.rig.log))
        self.assertIn('QUERY', self.tuner.commands)
        self.assertIn('tune: MATCHED', '\n'.join(logs.output))
        self.assertPutBack()

    def outcome(self, why, **kw):
        self.tuner.pending = True
        b = self.bridge(**kw)
        with self.assertLogs('catbridge', 'INFO') as logs:
            self.assertTrue(self.run_until(b, lambda: 'T 0' in self.rig.log))
        self.assertIn(why, '\n'.join(logs.output))
        self.assertPutBack()
        return b

    def test_fault(self):
        self.tuner.outcome = 'FAULT'
        self.outcome('tune: FAULT; unkeying')

    def test_abandoned(self):
        self.tuner.outcome = 'IDLE'
        self.outcome('the tune ended in IDLE')

    def test_hold(self):
        self.tuner.hold_in_move = True
        self.outcome('above its tune window')

    def test_timeout(self):
        self.tuner.outcome = None
        t0 = time.monotonic()
        self.outcome('no result after 0.8 s', tune_timeout=0.8)
        self.assertGreater(time.monotonic() - t0, 0.8)

    def test_no_carrier(self):
        self.tuner.rig = None               # the rig makes no carrier the tuner can see
        self.outcome('the tuner sees no carrier after 0.6 s')

    def test_withdrawn(self):
        self.tuner.rig = None
        self.when(lambda: self.rig.ptt == 1, lambda: setattr(self.tuner, 'pending', False))
        self.outcome('no longer asks for a carrier')

    def test_once_per_request(self):
        self.tuner.rig = None               # the tuner never sees the carrier, so it keeps asking
        b = self.outcome('no carrier')
        self.run_until(b, lambda: False, 1.0)
        self.assertEqual(self.rig.log.count('T 1'), 1)

    def test_power_readback(self):
        self.rig.ignore_power = True        # the rig stays at 100 W whatever it is told
        self.outcome('reads back RTTY at 100 W after RTTY at 20 W was set; not keying')
        self.assertNotIn('T 1', self.rig.log)

    def test_not_over_the_operator(self):
        self.tuner.rig = None               # SSB: no steady carrier, so the tuner still asks
        self.rig.ptt = 1
        self.tuner.pending = True
        b = self.bridge()
        self.run_until(b, lambda: False, 0.5)
        self.assertEqual(self.rig.sets(), [])
        self.rig.ptt = 0
        self.assertTrue(self.run_until(b, lambda: 'T 1' in self.rig.log))

    def test_tune_path_only(self):
        self.tuner.path, self.tuner.want = 'AUX', True
        b = self.bridge()
        self.run_until(b, lambda: False, 0.5)
        self.assertEqual(self.rig.sets(), [])

    def test_older_firmware(self):
        self.tuner.want_field = False       # no want=: read as 0, so never keyed
        self.tuner.pending = True
        b = self.bridge()
        self.run_until(b, lambda: False, 0.5)
        self.assertEqual(self.rig.sets(), [])

    def test_tuner_drops_mid_tune(self):
        self.tuner.outcome = None
        self.tuner.pending = True
        b = self.bridge()
        self.when(lambda: self.rig.ptt == 1, self.tuner.drop)
        self.assertTrue(self.run_until(b, lambda: 'T 0' in self.rig.log))
        self.assertPutBack()
        self.assertTrue(self.run_until(b, lambda: b.link.up and b.link.tlm_at))   # and back again

    def test_rig_drops_after_key(self):
        self.rig.drop_after_key = True      # the rig stays keyed, and its link is gone
        self.tuner.pending = True
        b = self.bridge()
        self.assertTrue(self.run_until(b, lambda: 'T 0' in self.rig.log))
        self.assertPutBack()

    def test_unkey_owed_until_the_rig_is_back(self):
        self.tuner.outcome = None
        self.tuner.pending = True
        b = self.bridge(tune_timeout=0.5)

        def away():                         # rigctld gone for all four of the unkey's tries
            self.rig.refuse = True
            self.rig.drop()
            wait_until(lambda: self.rig.refused >= 3, 10.0)
            time.sleep(0.2)
            self.rig.refuse = False

        self.when(lambda: self.rig.ptt == 1, away)
        with self.assertLogs('catbridge', 'INFO') as logs:
            self.assertTrue(self.run_until(b, lambda: 'T 0' in self.rig.log, 10.0))
        self.assertIn('the rig may still be keyed', '\n'.join(logs.output))
        self.assertPutBack()
        self.assertIsNone(b.rig.owed)

    def test_rearms_while_the_rig_is_away(self):
        self.tuner.rig = None
        b = self.outcome('no carrier')      # one carrier, and the tuner still asks
        b.rig.close()
        b.retry['rigctld'].at = time.monotonic() + 60
        self.tuner.pending = False          # the request ends while the rig is away
        self.assertTrue(self.run_until(b, lambda: b.armed, 2.0))
        b.retry['rigctld'].at = 0.0
        self.tuner.pending = True           # a new TUNE from the page
        self.assertTrue(self.run_until(b, lambda: self.rig.log.count('T 1') == 2))

    def test_stop_mid_tune(self):
        self.tuner.outcome = None
        self.tuner.pending = True
        b = self.bridge()
        pump = b.link.pump

        def signaled(timeout):
            if self.rig.ptt:
                b.guard.on_signal(signal.SIGTERM)       # as the handler does when SIGTERM comes
            return pump(timeout)

        b.link.pump = signaled
        with self.assertRaises(catbridge.Stop):
            self.run_until(b, lambda: False)
        self.assertPutBack()

    def test_exception_mid_tune(self):
        self.tuner.outcome = None
        self.tuner.pending = True
        b = self.bridge()
        pump = b.link.pump

        def broken(timeout):
            if self.rig.ptt:
                raise RuntimeError('a bug')
            return pump(timeout)

        b.link.pump = broken
        with self.assertRaises(RuntimeError):
            self.run_until(b, lambda: False)
        self.assertPutBack()


class TestOneShot(Bench):
    def tune(self, **kw):
        cfg = self.config(**kw)
        return catbridge.tune_once(cfg, *self.ends(cfg), catbridge.Guard())

    def test_tune(self):
        self.assertEqual(self.tune(), 0)
        self.assertIn('TUNE', self.tuner.commands)
        self.assertEqual(self.rig.log.count('T 1'), 1)
        self.assertPutBack()

    def test_fault(self):
        self.tuner.outcome = 'FAULT'
        self.assertEqual(self.tune(), 1)
        self.assertPutBack()

    def test_tuner_not_asking(self):
        self.tuner.path = 'AUX'             # a TUNE off the TUNE path asks for nothing
        with self.assertLogs('catbridge', 'ERROR') as logs:
            self.assertEqual(self.tune(), 1)
        self.assertIn('does not ask for a carrier: state IDLE, path AUX', '\n'.join(logs.output))
        self.assertEqual(self.rig.sets(), [])

    def test_dry_run(self):
        self.assertEqual(self.tune(dry_run=True), 0)
        self.assertNotIn('TUNE', self.tuner.commands)
        self.assertEqual(self.rig.sets(), [])


class TestSignals(Bench):
    """The real program, stopped by a signal while it holds the rig keyed."""

    def stop_keyed(self, sig):
        self.tuner.outcome = None           # the tune never ends by itself
        self.tuner.pending = True
        p = subprocess.Popen([sys.executable, os.path.join(HERE, 'catbridge.py'), 'run', '--tuner', self.tuner.addr,
                              '--rig-addr', self.rig.addr], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
        try:
            self.assertTrue(wait_until(lambda: self.rig.ptt == 1, 10.0), 'never keyed')
            p.send_signal(sig)
            out = p.communicate(timeout=15)[0]
        finally:
            if p.poll() is None:
                p.kill()
                p.communicate()
        self.assertEqual(p.returncode, 0, out)
        self.assertPutBack()
        self.assertIn('stopped by %s' % sig.name, out)

    def test_sigterm(self):
        self.stop_keyed(signal.SIGTERM)

    def test_sigint(self):
        self.stop_keyed(signal.SIGINT)


if __name__ == '__main__':
    unittest.main()
