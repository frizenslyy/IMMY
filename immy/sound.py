"""IMMY — процедурная фоновая музыка (чиптюн) без сторонних библиотек.

Синтез WAV в памяти (wave + struct), воспроизведение:
  Windows — winsound (асинхронно, с зацикливанием),
  Linux/macOS — aplay/paplay/afplay в фоновом потоке.
Если плеера нет — игра работает молча.
"""

import io
import struct
import subprocess
import sys
import threading
import wave

SR = 22050
VOL = 0.32


def _sq(ph, duty):
    return 1.0 if (ph % 1.0) < duty else -1.0


def _render_track(melody, bass, bpm, duty):
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
            env = 1.0
            for i in range(cnt):
                if pos + i >= n:
                    break
                env = 1.0 - (i / cnt) * 0.35
                samples[pos + i] += amp * env * _sq(ph, duty_v)
                ph += step
            pos += cnt

    add(melody, 0, 0.6, duty)
    add(bass, -12, 0.35, 0.5)
    data = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s * VOL)) * 32767)) for s in samples)
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


class Music:
    def __init__(self):
        self.enabled = True
        self.current = None
        self._cache = {}
        self._thread = None

    def _data(self, name):
        if name not in self._cache:
            self._cache[name] = _render_track(*TRACKS[name])
        return self._cache[name]

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
            import tempfile
            import os
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
