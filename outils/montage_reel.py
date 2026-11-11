#!/usr/bin/env python3
"""Monte un Reel 9:16 à partir d'une vidéo 16:9 et d'un plan de montage JSON.

Usage : python3 -I outils/montage_reel.py plan.json source.mp4 dossier_textes sortie.mp4 [--audio fond.wav] [--apercu]
Le plan liste les plans (début, fin, recadrage x0 -> x1 en pixels de la source 3840 px, « zoom » facultatif : 0.06 = zoom avant de 6 %) et les cartons de texte
(PNG transparents 1080x1920, avec début et fin dans le Reel). Aucun média n'est versionné dans git.
"""
import json, subprocess, sys, os

args = sys.argv[1:]
plan_p, src, ovdir, out = args[:4]
audio = args[args.index('--audio') + 1] if '--audio' in args else None
apercu = '--apercu' in args
plan = json.load(open(plan_p))

probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                        '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.strip().split(',')
SW, SH = int(probe[0]), int(probe[1])
k = SW / 3840.0
cw = round(SH * 9 / 16 / 2) * 2
OW, OH = (540, 960) if apercu else (1080, 1920)
FPS = plan.get('fps', 25)

# Étape 1 : chaque plan est découpé et recadré à part (mémoire limitée avec une source 4K).
tmp = out + '.plans'
os.makedirs(tmp, exist_ok=True)
seg_files = []
for i, s in enumerate(plan['plans']):
    d = s['fin'] - s['debut']
    x0, x1 = s['x0'] * k, s['x1'] * k
    x0 = max(0, min(SW - cw, x0)); x1 = max(0, min(SW - cw, x1))
    sf = os.path.join(tmp, f'p{i:02d}.mp4')
    vf = (f"crop={cw}:{SH}:x='{x0:.1f}+({x1 - x0:.1f})*t/{d:.3f}':y=0,"
          f"scale={OW}:{OH}:flags=lanczos,setsar=1,fps={FPS}")
    z = s.get('zoom', plan.get('zoom', 0))
    if z:  # léger zoom avant continu sur le plan (« plan qui respire »)
        vf += (f",scale=w='trunc({OW}*(1+{z}*t/{d:.3f})/2)*2':h='trunc({OH}*(1+{z}*t/{d:.3f})/2)*2'"
               f":eval=frame:flags=bicubic,crop={OW}:{OH}")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s['debut']), '-t', f'{d:.3f}', '-i', src, '-an', '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'veryfast' if apercu else 'medium', '-crf', '28' if apercu else '14',
                    '-pix_fmt', 'yuv420p', '-threads', '2', sf], check=True)
    seg_files.append(sf)

inputs = []
for sf in seg_files:
    inputs += ['-i', sf]
n = len(seg_files)
for c in plan['textes']:
    inputs += ['-loop', '1', '-framerate', str(FPS), '-t', str(plan['duree']), '-i', os.path.join(ovdir, c['id'] + '.png')]
if audio:
    inputs += ['-i', audio]

f = []
segs = [f'[{i}:v]' for i in range(n)]
fd = plan.get('fondu', 0)
if fd:
    # fondus enchaînés : chaque plan chevauche le suivant de fd secondes
    durs = [s['fin'] - s['debut'] for s in plan['plans']]
    prev, acc = '[0:v]', durs[0]
    for i in range(1, n):
        off = acc - fd
        f.append(f"{prev}[{i}:v]xfade=transition=fade:duration={fd}:offset={off:.3f}[x{i}]")
        prev, acc = f'[x{i}]', off + durs[i]
    fi0 = plan.get('fondu_entree', 0.4)  # 0 : première image nette (accroche visible tout de suite)
    f.append(f"{prev}" + (f"fade=t=in:st=0:d={fi0}," if fi0 else "") + f"fade=t=out:st={plan['duree'] - 0.6}:d=0.6[base]")
else:
    f.append(''.join(segs) + f"concat=n={len(segs)}:v=1:a=0,fade=t=in:st=0:d=0.4,fade=t=out:st={plan['duree'] - 0.6}:d=0.6[base]")
last = 'base'
for j, c in enumerate(plan['textes']):
    fi = 0.45
    f.append(f"[{j + n}:v]scale={OW}:{OH},format=rgba,fade=t=in:st={c['debut']}:d={fi}:alpha=1,"
             f"fade=t=out:st={c['fin'] - fi}:d={fi}:alpha=1[o{j}]")
    f.append(f"[{last}][o{j}]overlay=0:0:enable='between(t,{c['debut']},{c['fin']})'[b{j}]")
    last = f'b{j}'
cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(f), '-map', f'[{last}]']
if audio:
    ai = len(plan['textes']) + n
    cmd += ['-map', f'{ai}:a', '-c:a', 'aac', '-b:a', '192k', '-af', f"afade=t=out:st={plan['duree'] - 1.5}:d=1.5"]
cmd += ['-t', str(plan['duree']), '-c:v', 'libx264', '-preset', 'veryfast' if apercu else 'slow', '-crf', '28' if apercu else '17',
        '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
print(out)
