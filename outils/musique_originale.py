#!/usr/bin/env python3
"""Compose une bande-son « chill house » chaleureuse, entièrement synthétisée ici (aucun échantillon ni droit tiers).

Usage : python3 -I outils/musique_originale.py sortie.wav [duree_s] [bpm] [debut_groove_s]
Version 2 (10/11/2026) : la V1 crépitait (enveloppes coupées net, bruit brut). Ici chaque son finit à zéro,
les oscillateurs sont continus, les bruits sont filtrés, et un contrôle refuse un fichier qui a des sauts.
Structure : intro piano électrique + nappe, groove (kick doux, shaker, claquement léger, basse ronde, motif),
sortie nappe + piano. Réverbération par convolution, compression latérale (« pompe ») depuis le kick.
"""
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

out = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 104.0
GROOVE = float(sys.argv[4]) if len(sys.argv) > 4 else None
SR = 48000
N = int(DUR * SR)
beat = 60.0 / BPM
bar = 4 * beat
rng = np.random.default_rng(11)


def filt(x, kind, fc, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output='sos'), x)


def env_adsr(n, a, d, s, r_len):
    """Enveloppe qui finit exactement à 0 (aucun clic)."""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rn = min(n, int(r_len * SR))
    e[n - rn:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, rn)))
    return e


def add(buf, start, sig):
    i0 = int(start * SR)
    if i0 >= len(buf):
        return
    sig = sig[:len(buf) - i0]
    buf[i0:i0 + len(sig)] += sig


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ep(f, dur, vel=1.0):
    """Piano électrique (FM douce)."""
    n = int(dur * SR); t = np.arange(n) / SR
    idx = 1.4 * np.exp(-t / 0.35) + 0.15
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t)) + 0.12 * np.sin(2 * np.pi * 2 * f * t)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.2 * t)
    return vel * s * trem * env_adsr(n, 0.004, 0.9, 0.35, 0.25)


def pad_note(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * d * t + p) for d, p in ((1, 0), (1.003, 1.1), (0.997, 2.3), (2.001, 0.7)))
    return s * env_adsr(n, 0.6, 2.0, 0.8, 0.9)


# Progression en ré majeur : Gmaj9, F#m7, Em9, A6sus (une mesure chacun)
chords = [[55, 59, 62, 66, 69], [54, 57, 61, 64, 69], [52, 55, 59, 62, 66], [57, 62, 64, 66, 71]]
roots = [43, 42, 40, 45]
motif = [(0.0, 74), (1.5, 76), (2.0, 78), (3.0, 76)]  # motif discret, temps dans la mesure
nbars = int(np.ceil(DUR / bar)) + 1
g0 = int(round(GROOVE / bar)) if GROOVE is not None else 2
g1 = max(g0 + 1, int(DUR / bar) - 1)  # dernière mesure : sortie

keys = np.zeros(N); pad = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N)
shk = np.zeros(N); clap = np.zeros(N); lead = np.zeros(N); duck = np.ones(N)

for b in range(nbars):
    t0 = b * bar
    if t0 >= DUR:
        break
    c = chords[b % 4]
    groove = g0 <= b < g1
    for m in c[1:]:
        add(pad, t0, pad_note(hz(m), bar + 0.9) / len(c))
    # piano : accord plaqué sur 1, rappel sur le « et » du 2 et le 4 en groove
    hits = [(0.0, 0.9)] + ([(1.5, 0.55), (3.0, 0.6)] if groove else [(2.0, 0.5)])
    for q, v in hits:
        for k, m in enumerate(c):
            add(keys, t0 + q * beat + k * 0.006, ep(hz(m), 1.6, v) / len(c))
    if not groove:
        continue
    if b % 2 == 1:
        for q, m in motif:
            add(lead, t0 + q * beat, ep(hz(m), 0.9, 0.5))
    for q in range(4):
        bt = t0 + q * beat
        # kick doux
        n = int(0.45 * SR); u = np.arange(n) / SR
        ph = 2 * np.pi * (48 * u + (95 - 48) * 0.045 * (1 - np.exp(-u / 0.045)))
        add(kick, bt, np.sin(ph) * env_adsr(n, 0.002, 0.13, 0.0, 0.12))
        # pompe : creux de 35 % qui remonte en 0,22 s
        # (descente en 8 ms avant le temps, sinon le creux instantané claque)
        i0 = int((bt - 0.008) * SR); m_ = min(N - i0, int(0.23 * SR))
        if m_ > 0 and i0 >= 0:
            u = np.arange(m_) / SR
            shape = np.where(u < 0.008, 1 - 0.35 * 0.5 * (1 - np.cos(np.pi * u / 0.008)),
                             0.65 + 0.35 * np.sin(np.clip((u - 0.008) / 0.22, 0, 1) * np.pi / 2))
            duck[i0:i0 + m_] = np.minimum(duck[i0:i0 + m_], shape)
        # shaker en doubles croches, accent sur le contretemps
        for sub in range(4):
            n = int(0.07 * SR)
            add(shk, bt + sub * beat / 4, rng.standard_normal(n) * env_adsr(n, 0.006, 0.02, 0.0, 0.04) * (1.0 if sub == 2 else 0.45))
        # claquement léger sur 2 et 4
        if q in (1, 3):
            n = int(0.2 * SR)
            add(clap, bt, rng.standard_normal(n) * env_adsr(n, 0.003, 0.05, 0.0, 0.12))
    # basse ronde : 1, « et » du 2, 3
    f0 = hz(roots[b % 4])
    for q, ln in ((0.0, 1.2), (1.5, 0.45), (2.5, 1.2)):
        n = int(ln * beat * SR); u = np.arange(n) / SR
        s = np.tanh(1.6 * (np.sin(2 * np.pi * f0 * u) + 0.3 * np.sin(4 * np.pi * f0 * u)))
        add(bass, t0 + q * beat, s * env_adsr(n, 0.008, 0.35, 0.6, 0.06))

shk = filt(filt(shk, 'highpass', 6500), 'lowpass', 12000)
clap = filt(filt(clap, 'highpass', 900), 'lowpass', 5000)
pad = filt(pad, 'lowpass', 2200)
keys = filt(keys, 'lowpass', 5000)
bass = filt(bass, 'lowpass', 600)

dry = 0.42 * keys + 0.30 * pad * duck + 0.22 * lead + 0.55 * bass * duck + 0.85 * kick + 0.05 * shk + 0.07 * clap
send = 0.42 * keys + 0.30 * pad + 0.22 * lead + 0.07 * clap

# réverbération stéréo (réponse impulsionnelle de bruit décroissant, 2,4 s)
irn = int(2.4 * SR); ti = np.arange(irn) / SR
irs = [filt(rng.standard_normal(irn), 'lowpass', 6000) * np.exp(-ti / 0.55) for _ in range(2)]
irs = [ir / np.sqrt(np.sum(ir ** 2)) for ir in irs]
wet = [fftconvolve(send, ir)[:N] for ir in irs]
L = dry + 0.35 * wet[0]
R = dry + 0.35 * wet[1]
mix = np.stack([L, R], axis=1)
mix = filt(mix.T, 'highpass', 30).T

t = np.arange(N) / SR
fade = np.clip(t / 1.2, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1)
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(1.3 * mix) / np.tanh(1.3) * 0.89

# contrôle anti-clic sur les sons accordés (le bruit du shaker varie vite par nature, ce n'est pas un clic)
tonal = 0.42 * keys + 0.30 * pad * duck + 0.22 * lead + 0.55 * bass * duck + 0.85 * kick
jump = float(np.max(np.abs(np.diff(tonal))) / (np.max(np.abs(tonal)) + 1e-9))
if jump > 0.2:
    sys.exit(f'saut relatif de {jump:.3f} entre deux échantillons : clic probable, fichier refusé')
pcm = (mix * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(out, f'saut max {jump:.3f}')
