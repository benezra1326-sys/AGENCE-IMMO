#!/usr/bin/env python3
"""Compose une boucle deep house calme, entièrement synthétisée ici (aucun échantillon ni droit tiers).

Usage : python3 -I outils/musique_originale.py sortie.wav [duree_s] [bpm]
Structure : intro nappe + accords, groove (kick, charleston, clap léger, basse, accords en contretemps), sortie nappe.
"""
import sys, wave
import numpy as np

out = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 112.0
SR = 48000
N = int(DUR * SR)
beat = 60.0 / BPM
bar = 4 * beat
rng = np.random.default_rng(7)
t = np.arange(N) / SR


def lp(x, fc):
    """Passe-bas 1 pôle, appliqué deux fois (12 dB/oct)."""
    a = np.exp(-2 * np.pi * fc / SR)
    for _ in range(2):
        y = np.empty_like(x); acc = 0.0
        for i in range(len(x)):
            acc = (1 - a) * x[i] + a * acc
            y[i] = acc
        x = y
    return x


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, tt, n=6):
    return sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, n + 1))


# Progression : Am9, Fmaj9, Cmaj9, G6/9 (une mesure chacun)
chords = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [48, 52, 55, 59, 62], [55, 59, 62, 64, 69]]
roots = [45, 41, 48, 43]
nbars = int(np.ceil(DUR / bar))
intro_bars, outro_start = 2, nbars - 2

pad = np.zeros(N); stab = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); hat = np.zeros(N); clap = np.zeros(N)
for b in range(nbars):
    c = chords[b % 4]
    s0 = int(b * bar * SR); s1 = min(N, int((b + 1) * bar * SR))
    if s0 >= N:
        break
    tt = t[s0:s1] - b * bar
    seg = sum(saw(note(m), tt, 4) + saw(note(m) * 1.004, tt, 4) for m in c) / (2 * len(c))
    env = np.minimum(1, tt / 0.25) * np.minimum(1, (bar - tt) / 0.25 + 0.15)
    pad[s0:s1] += seg * env
    groove = intro_bars <= b < outro_start
    for q in range(4):
        bt = b * bar + q * beat
        # accords en contretemps
        st = bt + beat / 2
        i0 = int(st * SR); i1 = min(N, i0 + int(0.45 * SR))
        if i0 < N:
            u = t[i0:i1] - st
            stab[i0:i1] += sum(saw(note(m + 12), u, 5) for m in c) / len(c) * np.exp(-u / 0.12) * (1.0 if groove else 0.6)
        if not groove:
            continue
        # kick
        i0 = int(bt * SR); i1 = min(N, i0 + int(0.4 * SR))
        u = t[i0:i1] - bt
        ph = 2 * np.pi * (45 * u + (110 - 45) * 0.05 * (1 - np.exp(-u / 0.05)))
        kick[i0:i1] += np.sin(ph) * np.exp(-u / 0.16)
        # charleston sur le contretemps
        i0 = int((bt + beat / 2) * SR); i1 = min(N, i0 + int(0.06 * SR))
        nz = np.diff(rng.standard_normal(i1 - i0 + 1))
        hat[i0:i1] += nz * np.exp(-np.arange(i1 - i0) / SR / 0.018)
        # clap léger sur 2 et 4
        if q in (1, 3):
            i0 = int(bt * SR); i1 = min(N, i0 + int(0.18 * SR))
            clap[i0:i1] += rng.standard_normal(i1 - i0) * np.exp(-np.arange(i1 - i0) / SR / 0.05)
        # basse : 1 et « et » du 3
        for off, ln in ((0.0, 0.9), (2.5, 0.4)):
            if q == 0:
                bs = bt + off * beat
                i0 = int(bs * SR); i1 = min(N, i0 + int(ln * beat * SR))
                if i0 < N:
                    u = t[i0:i1] - bs
                    f0 = note(roots[b % 4])
                    bass[i0:i1] += (np.sin(2 * np.pi * f0 * u) + 0.25 * np.sin(4 * np.pi * f0 * u)) * np.minimum(1, u / 0.01) * np.exp(-u / 0.5)

pad = lp(pad, 1400); stab = lp(stab, 2200); clap = lp(clap, 3000) - lp(clap, 700)
mix = 0.55 * pad + 0.32 * stab + 0.9 * bass + 0.95 * kick + 0.035 * lp(hat, 9000) + 0.06 * clap
fade_in = np.minimum(1, t / 1.5); fade_out = np.minimum(1, (DUR - t) / 2.5)
mix *= fade_in * np.clip(fade_out, 0, 1)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.85
stereo = np.stack([mix, np.roll(mix, 240) * 0.98], axis=1)
pcm = (stereo * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(out)
