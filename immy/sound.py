"""IMMY — процедурный звук (чиптюн-музыка + SFX) без сторонних библиотек.

Синтез WAV в памяти (wave + struct), воспроизведение:
  Windows — winsound (асинхронно, с зацикливанием для музыки),
  Linux/macOS — aplay/paplay/afplay в фоновом потоке.
Если плеера нет — игра работает молча.
"""

import io
import math
import os
import struct
import subprocess
import sys
import tempfile
import threading
import wave

from .config import MUSIC_VOL, SFX_VOL

SR = 22050
VOL = 0.32
SFX_CAP = 6


def _sq(ph, duty):
    return 1.0 if (ph % 1.0) < duty else -1.0


def _render_track(melody, bass, bpm, duty, vol=1.0):
    beat = 60.0 / bpm
    total = sum(b for _, b in melody) * beat
    n = int(total * SR)
    samples = [0.0] * n

    def add(pattern, oct_shift, amp, duty_v):
        pos = 0
        ph = 0.0
        idx = 0
        while pos < n:
            semi, beats = pattern[idx % len(pattern)]
            idx += 1
            dur = beats * beat
            cnt = int(dur * SR)
            if semi is None:
                pos += cnt
                continue
            freq = 440.0 * (2 ** ((semi + oct_shift) / 12.0))
            step = freq / SR
            for i in range(cnt):
                if pos + i >= n:
                    break
                env = 1.0 - (i / cnt) * 0.35
                samples[pos + i] += amp * env * _sq(ph, duty_v)
                ph += step
            pos += cnt

    add(melody, 0, 0.6, duty)
    add(bass, -12, 0.35, 0.5)
    return _to_wav(samples, vol)


def _to_wav(samples, vol):
    data = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s * VOL * vol)) * 32767))
                    for s in samples)
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    return bio.getvalue()


_A = 0
_C = 3
_D = 5
_E = 7
_F = 8
_G = 10

MENU_TRACK = (
    [(_A, 1), (_C, 1), (_E, 1), (12, 1), (_E, 1), (_C, 1), (_A, 1), (None, 1),
     (-2, 1), (_A, 1), (_C, 1), (10, 1), (_C, 1), (_A, 1), (-2, 1), (None, 1)],
    [(-12, 4), (-12, 4), (-17, 4), (-16, 4)],
    70, 0.25,
)

BATTLE_TRACK = (
    [(_A, 0.5), (_A, 0.5), (_C, 0.5), (_E, 0.5), (_G, 0.5), (_E, 0.5), (_C, 0.5), (_A, 0.5),
     (_F, 0.5), (_F, 0.5), (_A, 0.5), (_C + 12, 0.5), (_E + 12, 0.5), (_C + 12, 0.5), (_A, 0.5), (_F, 0.5)],
    [(-12, 0.5), (-12, 0.5), (-5, 0.5), (-7, 0.5)],
    150, 0.5,
)

TRACKS = {"menu": MENU_TRACK, "battle": BATTLE_TRACK}


def _tone(freq, dur, amp, duty=0.5, slide=0.0, decay=3.0):
    n = int(dur * SR)
    out = [0.0] * n
    ph = 0.0
    f0, f1 = freq, freq * (2 ** (slide / 12.0))
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t
        env = math.exp(-decay * t)
        out[i] = amp * env * _sq(ph, duty)
        ph += f / SR
    return out


def _noise(dur, amp, decay=6.0, lp=0.3):
    n = int(dur * SR)
    out = [0.0] * n
    prev = 0.0
    seed = 12345
    for i in range(n):
        env = math.exp(-decay * (i / n))
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        s = seed / 0x3FFFFFFF - 1.0
        prev = prev * lp + s * (1.0 - lp)
        out[i] = amp * env * prev
    return out


def _mix(*layers):
    n = max(len(x) for x in layers)
    out = [0.0] * n
    for layer in layers:
        for i, s in enumerate(layer):
            out[i] += s
    return out


def _render_sfx(name):
    if name == "click":
        s = _tone(880, 0.06, 0.5, duty=0.3, slide=4)
    elif name == "hit":
        s = _mix(_tone(180, 0.10, 0.7, duty=0.4, slide=-7, decay=8), _noise(0.08, 0.5, 10))
    elif name == "heavy":
        s = _mix(_tone(120, 0.16, 0.8, duty=0.4, slide=-9, decay=6), _noise(0.14, 0.6, 7))
    elif name == "crit":
        s = _mix(_tone(240, 0.16, 0.8, duty=0.25, slide=-12, decay=5), _noise(0.12, 0.55, 8),
                 _tone(1200, 0.08, 0.3, duty=0.2, slide=-5))
    elif name == "parry":
        s = _mix(_tone(1400, 0.10, 0.55, duty=0.2, slide=7), _tone(2100, 0.07, 0.35, duty=0.2))
    elif name == "kick":
        s = _mix(_tone(150, 0.10, 0.6, duty=0.5, slide=-5, decay=7), _noise(0.07, 0.4, 9))
    elif name == "uppercut":
        s = _mix(_tone(160, 0.18, 0.7, duty=0.4, slide=14, decay=4), _noise(0.10, 0.4, 8))
    elif name == "sweep":
        s = _mix(_tone(140, 0.16, 0.6, duty=0.5, slide=-10, decay=6), _noise(0.12, 0.45, 6))
    elif name == "jump":
        s = _tone(330, 0.12, 0.4, duty=0.35, slide=10, decay=4)
    elif name == "cast":
        s = _mix(_tone(520, 0.16, 0.45, duty=0.3, slide=12, decay=4), _tone(780, 0.12, 0.3, duty=0.3, slide=5))
    elif name == "ult":
        s = _mix(_tone(110, 0.5, 0.8, duty=0.4, slide=19, decay=2), _noise(0.4, 0.5, 3),
                 _tone(440, 0.4, 0.4, duty=0.25, slide=12))
    elif name == "ko":
        s = _mix(_tone(220, 0.4, 0.8, duty=0.4, slide=-19, decay=2.5), _noise(0.3, 0.6, 4))
    elif name == "fatal":
        s = _mix(_tone(70, 0.9, 0.9, duty=0.5, slide=-5, decay=1.5), _noise(0.7, 0.6, 2.5),
                 _tone(880, 0.5, 0.35, duty=0.2, slide=-17))
    elif name == "coin":
        s = _mix(_tone(1320, 0.07, 0.5, duty=0.2), _tone(1760, 0.12, 0.45, duty=0.2, slide=3))
    elif name == "gem":
        s = _mix(_tone(1567, 0.08, 0.45, duty=0.2), _tone(2093, 0.14, 0.4, duty=0.2, slide=5))
    elif name == "craft":
        s = _mix(_noise(0.2, 0.5, 5), _tone(392, 0.22, 0.5, duty=0.3, slide=12, decay=3),
                 _tone(523, 0.18, 0.4, duty=0.3, slide=7))
    elif name == "trap":
        s = _mix(_noise(0.18, 0.7, 5), _tone(90, 0.2, 0.7, duty=0.5, slide=-7, decay=5))
    elif name == "win":
        s = _mix(_tone(_A, 0.16, 0.5, duty=0.3), _tone(_C, 0.16, 0.5, duty=0.3),
                 _tone(_E, 0.30, 0.55, duty=0.3))
    elif name == "lose":
        s = _mix(_tone(_E, 0.2, 0.5, duty=0.4), _tone(_C, 0.2, 0.5, duty=0.4),
                 _tone(-9, 0.35, 0.55, duty=0.4))
    elif name == "combo":
        s = _tone(990, 0.09, 0.5, duty=0.25, slide=5)
    else:
        s = _tone(440, 0.06, 0.4)
    return _to_wav(s, 1.0)


class Music:
    def __init__(self):
        self.enabled = True
        self.volume = MUSIC_VOL
        self.current = None
        self._cache = {}
        self._thread = None

    def set_volume(self, v):
        v = max(0.0, min(1.0, float(v)))
        if v == self.volume:
            return
        self.volume = v
        if self.current:
            name = self.current
            self.current = None
            self.play(name)

    def _data(self, name):
        key = (name, round(self.volume, 2))
        if key not in self._cache:
            self._cache.clear()
            self._cache[key] = _render_track(*TRACKS[name], vol=self.volume)
        return self._cache[key]

    def play(self, name):
        if not self.enabled or name == self.current:
            return
        self.stop()
        if not self.enabled:
            return
        self.current = name
        data = self._data(name)
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_LOOP)
            except Exception:
                pass
        else:
            self._thread = threading.Thread(target=self._loop_unix, args=(data,), daemon=True)
            self._thread.start()

    def _loop_unix(self, data):
        try:
            fd, path = tempfile.mkstemp(suffix=".wav")
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            players = (["paplay"], ["aplay", "-q"], ["afplay"])
            while self.enabled and self.current:
                played = False
                for cmd in players:
                    try:
                        subprocess.run(cmd + [path], check=False,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        played = True
                        break
                    except FileNotFoundError:
                        continue
                    except Exception:
                        continue
                if not played:
                    break
            try:
                os.unlink(path)
            except OSError:
                pass
        except Exception:
            pass

    def stop(self):
        self.current = None
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            name = self.current or "menu"
            self.current = None
            self.play(name)
        else:
            self.stop()
        return self.enabled


class Sfx:
    """Короткие одноразовые звуки: синтезируются один раз, играются асинхронно."""

    def __init__(self):
        self.enabled = True
        self.volume = SFX_VOL
        self._cache = {}
        self._active = 0
        self._lock = threading.Lock()
        self._tmpdir = None

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, float(v)))

    def _data(self, name):
        if name not in self._cache:
            self._cache[name] = _render_sfx(name)
        return self._cache[name]

    def play(self, name):
        if not self.enabled or self.volume <= 0.01:
            return
        with self._lock:
            if self._active >= SFX_CAP:
                return
            self._active += 1
        try:
            data = self._data(name)
            if sys.platform == "win32":
                def _w():
                    try:
                        import winsound
                        winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC
                                           | winsound.SND_NODEFAULT)
                    except Exception:
                        pass
                    finally:
                        with self._lock:
                            self._active -= 1
                threading.Thread(target=_w, daemon=True).start()
            else:
                def _u():
                    try:
                        if self._tmpdir is None:
                            self._tmpdir = tempfile.mkdtemp(prefix="immy_sfx_")
                        path = os.path.join(self._tmpdir, "%s.wav" % name)
                        if not os.path.exists(path):
                            with open(path, "wb") as f:
                                f.write(data)
                        for cmd in (["paplay"], ["aplay", "-q"], ["afplay"]):
                            try:
                                subprocess.run(cmd + [path], check=False,
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                break
                            except FileNotFoundError:
                                continue
                            except Exception:
                                break
                    except Exception:
                        pass
                    finally:
                        with self._lock:
                            self._active -= 1
                threading.Thread(target=_u, daemon=True).start()
        except Exception:
            with self._lock:
                self._active = max(0, self._active - 1)


class Audio:
    """Музыка + SFX с общими настройками громкости и бесшумным режимом."""

    def __init__(self, settings=None):
        self.music = Music()
        self.sfx = Sfx()
        self.apply(settings or {})

    def apply(self, settings):
        mute = bool(settings.get("mute", False))
        self.music.volume = max(0.0, min(1.0, float(settings.get("music", MUSIC_VOL))))
        self.sfx.volume = max(0.0, min(1.0, float(settings.get("sfx", SFX_VOL))))
        self.music.enabled = not mute
        self.sfx.enabled = not mute
        if self.music.current and self.music.enabled:
            name = self.music.current
            self.music.current = None
            self.music.play(name)

    def play(self, name):
        self.sfx.play(name)
