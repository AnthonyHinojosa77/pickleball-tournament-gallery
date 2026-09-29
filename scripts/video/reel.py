#!/usr/bin/env python3
"""Vertical 9:16 Reel of the tournament recap, cut from the same shots as the widescreen recap (edl.json).

Every shot is a 4K landscape frame, so each one is cropped to a portrait window that pans slowly across the
frame (pan start/end per shot are in edl.json under "reel"). Each shot keeps its middle part so the film
lands under 90 seconds. Same grade, title/end cards and licensed music as the recap.
Usage: reel.py SOURCE_DIR OUT_FILE
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edit

W, H = 1080, 1920
SRC_W, SRC_H = 3840, 2160
CROP_W = SRC_H * 9 // 16  # 1215: the widest 9:16 window in a 4K frame


def card(path, lines):
    """Title/end card in portrait: the tournament logo on its own paper colour, with optional lines of text."""
    logo = Image.open(edit.ROOT / 'docs/brand/tournament-logo.jpg').convert('RGB')
    im = Image.new('RGB', (W, H), logo.getpixel((4, 4)))
    logo = logo.resize((round(W * 0.92), round(logo.height * W * 0.92 / logo.width)), Image.LANCZOS)
    top = (H - logo.height) // 2 - (110 if lines else 0)
    im.paste(logo, ((W - logo.width) // 2, top))
    draw = ImageDraw.Draw(im)
    y = top + logo.height + 70
    for text, size in lines:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
        draw.text(((W - draw.textlength(text, font=font)) / 2, y), text, fill=edit.INK, font=font)
        y += round(size * 1.7)
    im.save(path)


def render(shots, pans, out, cards, encode):
    args, chains, lengths = ['ffmpeg', '-v', 'error', '-y'], [], []
    items = [('card', cards[0], 3.0)] + [('shot', s, None) for s in shots] + [('card', cards[1], 4.0)]
    pan = iter(pans)
    for i, (kind, spec, length) in enumerate(items):
        if kind == 'card':
            args += ['-loop', '1', '-framerate', edit.FPS, '-t', str(length), '-i', str(spec)]
            chains.append(f'[{i}:v]scale={W}:{H},format=yuv420p,settb=AVTB,setsar=1[v{i}]')
        else:
            src, a, b = spec; length = b - a; u0, u1 = next(pan)
            args += ['-ss', f'{a:.3f}', '-t', f'{length:.3f}', '-i', str(src)]
            x = f'round({SRC_W - CROP_W}*({u0}+({u1}-{u0})*t/{length:.3f}))'
            chains.append(f'[{i}:v]fps={edit.FPS},setpts=PTS-STARTPTS,crop={CROP_W}:{SRC_H}:x=\'{x}\':y=0,'
                          f'scale={W}:{H}:flags=lanczos,{edit.GRADE.format(fine=0.45)},'
                          f'format=yuv420p,settb=AVTB,setsar=1,setpts=PTS-STARTPTS[v{i}]')
        lengths.append(length)
    label, offset = 'v0', lengths[0]
    for i in range(1, len(items)):
        offset -= edit.FADE
        chains.append(f'[{label}][v{i}]xfade=transition=fade:duration={edit.FADE}:offset={offset:.3f}[x{i}]')
        label, offset = f'x{i}', offset + lengths[i]
    chains.append(f'[{label}]fade=t=in:st=0:d={edit.FADE},fade=t=out:st={offset - edit.FADE:.3f}:d={edit.FADE}[out]')
    args += ['-filter_complex', ';'.join(chains), '-map', '[out]', '-an', *encode,
             '-map_metadata', '-1', '-movflags', '+faststart', str(out)]
    subprocess.run(args, check=True)
    return offset


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    edl = json.loads((edit.HERE / 'edl.json').read_text()); reel = edl['reel']
    shots = []
    for f, a, b in edl['recap']:
        keep = (b - a) * reel['keep']; start = a + (b - a - keep) / 2
        shots.append((src / f, round(start, 2), round(start + keep, 2)))
    tmp = out.parent
    title, end = tmp / 'reel-title.png', tmp / 'reel-end.png'
    card(title, [])
    card(end, [('Corpus Christi Athletic Club', 52), ('September 19, 2026', 42)])
    seconds = sum(b - a for _, a, b in shots) + 7
    total = render(shots, reel['pans'], out, (title, end), edit.web_encode(seconds, ceiling_mb=70, max_kbps=7000))
    edit.add_music(out, edl['music'])
    print(f'{out.name}: {total:.1f}s, {W}x{H}, with music')


if __name__ == '__main__':
    main()
