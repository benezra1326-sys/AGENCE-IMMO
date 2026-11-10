#!/usr/bin/env python3
"""Cale les coupes d'un plan de montage sur le tempo d'une chanson, et écrit la feuille de coupes.

Usage : python3 -I outils/caler_tempo.py plan.json sortie.json --bpm 120 [--temps 2] [--coupes-source 3.12,5.08,...] [--duree-source 59.72]
- Chaque passage d'un plan au suivant (milieu du fondu) tombe sur une grille de `temps` battements au tempo `bpm`.
- Un plan n'est jamais prolongé au-delà d'une coupe de la vidéo source (liste --coupes-source, obtenue avec
  ffmpeg scdet), pour ne pas faire apparaître un bout du plan voisin.
- Les textes sont recalés avec les plans (interpolation entre les coupes).
- Écrit aussi sortie.coupes.md : tempo, temps de chaque coupe, consignes pour poser la chanson dans Instagram.
"""
import json, sys

a = sys.argv[1:]
src_p, out_p = a[0], a[1]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
bpm = float(opt('--bpm', 120)); nb = float(opt('--temps', 2))
cuts = sorted(float(x) for x in opt('--coupes-source', '').split(',') if x)
cuts.append(float(opt('--duree-source', 1e9)))
plan = json.load(open(src_p))
fd = plan.get('fondu', 0.0)
step = nb * 60.0 / bpm
P = plan['plans']


def fenetre(s):
    """Plage utilisable de la source autour du plan (entre deux coupes de la source)."""
    lo = max([c for c in cuts if c <= s['debut'] + 0.05] or [0.0]) + 0.06
    hi = min([c for c in cuts if c >= s['fin'] - 0.05] or [1e9]) - 0.06
    return min(lo, s['debut']), max(hi, s['fin'])


# coupes d'origine (milieux de fondus) et fin
old_m, t = [], 0.0
for s in P[:-1]:
    d = s['fin'] - s['debut']; old_m.append(t + d - fd / 2); t += d - fd
old_end = plan['duree']

lims = [fenetre(s) for s in P]


def cherche(i, s_i, acc):
    """Recherche avec retour arrière : chaque coupe sur la grille, au plus près de l'original."""
    if i == len(P) - 1:
        return acc
    lo, hi = lims[i]
    want = round(old_m[i] / step) * step
    cands = sorted({round(want + k * step, 6) for k in range(-8, 9)}, key=lambda x: abs(x - old_m[i]))
    for m in cands:
        d = m - s_i + fd / 2
        if 1.0 <= d <= hi - lo and (not acc or m - acc[-1] >= 1.0):
            r = cherche(i + 1, m + fd / 2 - fd, acc + [m])
            if r is not None:
                return r
    return None


new_m = cherche(0, 0.0, [])
if new_m is None:
    sys.exit(f'impossible de caler toutes les coupes sur la grille ({step:.3f} s)')
starts = [0.0] + [m + fd / 2 - fd for m in new_m]
last = P[-1]; lo, hi = fenetre(last)
end = round(old_end / step) * step
while end - starts[-1] > hi - lo:
    end -= step
duree = round(end, 3)

new_plans = []
for i, s in enumerate(P):
    d = (new_m[i] + fd / 2 - starts[i]) if i < len(P) - 1 else duree - starts[i]
    lo, hi = fenetre(s)
    deb = s['debut']
    if deb + d > hi:
        deb = max(lo, hi - d)
    n = dict(s); n['debut'] = round(deb, 3); n['fin'] = round(deb + d, 3)
    n['dans_le_reel'] = [round(starts[i], 3), round(starts[i] + d, 3)]
    new_plans.append(n)

xs = [0.0] + old_m + [old_end]; ys = [0.0] + new_m + [duree]


def remap(t):
    for k in range(len(xs) - 1):
        if xs[k] <= t <= xs[k + 1]:
            return ys[k] + (t - xs[k]) * (ys[k + 1] - ys[k]) / (xs[k + 1] - xs[k])
    return min(t, duree)


textes = [dict(c, debut=round(remap(c['debut']), 3), fin=round(min(duree, remap(c['fin'])), 3)) for c in plan['textes']]
out = dict(plan, plans=new_plans, textes=textes, duree=duree,
           tempo={'bpm': bpm, 'coupe_tous_les_temps': nb, 'grille_s': round(step, 4), 'coupes_s': [round(m, 3) for m in new_m]})
json.dump(out, open(out_p, 'w'), ensure_ascii=False, indent=1)

lines = [f"# Feuille de coupes – {plan.get('bien', '')} {plan.get('version', '')}", '',
         f"- Tempo de calage : **{bpm:g} BPM**, chaque coupe tombe sur un temps (grille de {step:.3f} s).",
         f"- Durée : {duree:g} s. Marche aussi avec une chanson à {bpm / 2:g} BPM (coupes sur un temps sur deux de la chanson).",
         "- Dans Instagram : choisir un son dans cette plage de tempo, et faire démarrer l'extrait sur un premier temps "
         "fort (début de mesure, souvent un coup de grosse caisse). Les coupes tomberont alors sur la musique.",
         '', '| Coupe | Temps (s) | Battement | Passage |', '| --- | --- | --- | --- |']
for i, m in enumerate(new_m):
    lines.append(f"| {i + 1} | {m:.2f} | {m / (60 / bpm) + 1:g} | {P[i].get('note', '')} → {P[i + 1].get('note', '')} |")
lines += ['', '| Texte | Apparaît (s) | Disparaît (s) |', '| --- | --- | --- |']
lines += [f"| {c['id']} | {c['debut']:.2f} | {c['fin']:.2f} |" for c in textes]
open(out_p.rsplit('.', 1)[0] + '.coupes.md', 'w').write('\n'.join(lines) + '\n')
print(out_p, duree, [round(m, 2) for m in new_m])
