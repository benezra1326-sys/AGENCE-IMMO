#!/usr/bin/env python3
"""Bande-son « piano cinématique » douce, sans batterie, synthétisée ici (aucun échantillon ni droit tiers).
Usage : python3 -I outils/musique_piano.py sortie.wav [duree_s] [bpm]
Autre couleur que musique_originale.py (chill house) : arpèges de piano, nappe de cordes, basse tenue. 12/11/2026.
"""
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
out = sys.argv[1]; DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0; BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 76.0
SR = 48000; N = int(DUR * SR); beat = 60 / BPM; bar = 4 * beat; rng = np.random.default_rng(5)
filt = lambda x, k, f: sosfilt(butter(2, f, k, fs=SR, output='sos'), x)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def env(n, a, d, s, r):
    t = np.arange(n) / SR; e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / d)); rn = min(n, int(r * SR))
    e[n - rn:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, rn))); return e
def add(b, st, sig):
    i = int(st * SR)
    if i < len(b): sig = sig[:len(b) - i]; b[i:i + len(sig)] += sig
def piano(f, dur, v):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.2 + h * 0.9)) for h, a in ((1, 1), (2, .45), (3, .22), (4, .1)))
    return v * s * env(n, 0.003, 1.2, 0.0, 0.3)
def strings(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * d * t + p) for d, p in ((1, 0), (1.004, 1.3), (.996, 2.1)))
    return s * env(n, 1.2, 3.0, .85, 1.2)
# La mineur lumineux : Fmaj7, C/E, Am7, Gsus -> douce et posée
ch = [[53, 57, 60, 64], [52, 55, 60, 64], [57, 60, 64, 67], [55, 60, 62, 67]]; roots = [41, 40, 45, 43]
pno = np.zeros(N); pad = np.zeros(N); bas = np.zeros(N)
for b in range(int(np.ceil(DUR / bar)) + 1):
    t0 = b * bar
    if t0 >= DUR: break
    c = ch[b % 4]
    for m in c: add(pad, t0, strings(hz(m), bar + 1.2) / 4)
    add(bas, t0, strings(hz(roots[b % 4]), bar + 0.6) * 0.5)
    arp = [c[0] + 12, c[1] + 12, c[2] + 12, c[3] + 12, c[2] + 12, c[1] + 12, c[2] + 12, c[3] + 12]
    for k, m in enumerate(arp): add(pno, t0 + k * beat / 2, piano(hz(m), 2.2, .55 if k % 2 else .75))
    if b % 2 == 1: add(pno, t0 + 2 * beat, piano(hz(c[3] + 24), 2.5, .35))
pad = filt(pad, 'lowpass', 1800); bas = filt(bas, 'lowpass', 300); pno = filt(pno, 'lowpass', 6000)
dry = .5 * pno + .32 * pad + .3 * bas
irn = int(3.0 * SR); ti = np.arange(irn) / SR
irs = [filt(rng.standard_normal(irn), 'lowpass', 5000) * np.exp(-ti / .8) for _ in range(2)]; irs = [i / np.sqrt(np.sum(i ** 2)) for i in irs]
wet = [fftconvolve(.5 * pno + .2 * pad, i)[:N] for i in irs]
mix = np.stack([dry + .45 * wet[0], dry + .45 * wet[1]], 1); mix = filt(mix.T, 'highpass', 35).T
t = np.arange(N) / SR; mix *= (np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 3, 0, 1))[:, None]
mix /= np.max(np.abs(mix)) + 1e-9; mix *= .89
jump = float(np.max(np.abs(np.diff(dry))) / (np.max(np.abs(dry)) + 1e-9))
if jump > 0.2: sys.exit(f'saut {jump:.3f} : clic probable, fichier refusé')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print(out, f'saut max {jump:.3f}')
