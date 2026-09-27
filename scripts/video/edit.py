#!/usr/bin/env python3
"""Cut, grade and encode the drone films from edl.json. Camera files are only read.

Outputs in OUT_DIR:
  clip-NN.mp4       each camera clip trimmed of dead moments, graded, 1080p (fits GitHub's 100 MB file limit)
  recap-4k.mp4      ~2 minute recap film, 3840x2160
  recap-1080.mp4    the same film for playback on the page
The recap carries the licensed music track from edl.json (credited in the file metadata and on the page).
Usage: edit.py SOURCE_DIR OUT_DIR [clips|recap|music|all]
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FPS = '30000/1001'
FADE = 0.5  # seconds for dissolves and fades
# Same intent as the photo finish: firmer blacks, open mids, rolled-off highlights, gentle vibrance, local contrast.
GRADE = ("curves=master='0/0 0.06/0.035 0.25/0.215 0.5/0.5 0.75/0.79 0.93/0.945 1/0.985',"
         "vibrance=intensity=0.18,eq=saturation=1.06,unsharp=13:11:0.30:5:5:0.0,unsharp=5:5:{fine}")
INK = (23, 55, 43)


def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)]))


def is_vertical(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height:stream_side_data=rotation', '-of', 'json', str(path)])
    s = json.loads(out)['streams'][0]
    rotated = any(abs(int(d.get('rotation', 0))) == 90 for d in s.get('side_data_list', []))
    return (s['height'] > s['width']) != rotated


def card(path, size, lines):
    """Branded title/end card: tournament logo on the site's paper colour, optional lines of text."""
    w, h = size
    logo = Image.open(ROOT / 'docs/brand/tournament-logo.jpg').convert('RGB')
    im = Image.new('RGB', size, logo.getpixel((4, 4)))  # match the logo's own background so no box shows
    scale = (h * (0.62 if lines else 0.78)) / logo.height
    logo = logo.resize((round(logo.width * scale), round(logo.height * scale)), Image.LANCZOS)
    top = round(h * (0.08 if lines else 0.11))
    im.paste(logo, ((w - logo.width) // 2, top))
    draw = ImageDraw.Draw(im)
    y = top + logo.height + round(h * 0.05)
    for text, rel in lines:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', round(h * rel))
        tw = draw.textlength(text, font=font)
        draw.text(((w - tw) / 2, y), text, fill=INK, font=font)
        y += round(h * rel * 1.6)
    im.save(path)


def render(segments, out, size, encode, cards=None):
    """segments: [(file, start, end)]; joins them with dissolves, fades in/out, grades and encodes."""
    w, h = size
    fine = 0.45 if w <= 1920 else 0.35
    args, chains, lengths = ['ffmpeg', '-v', 'error', '-y'], [], []
    items = []
    if cards: items.append(('card', cards[0], 3.5))
    items += [('clip', s, None) for s in segments]
    if cards: items.append(('card', cards[1], 4.5))
    for i, (kind, spec, length) in enumerate(items):
        if kind == 'card':
            args += ['-loop', '1', '-framerate', FPS, '-t', str(length), '-i', str(spec)]
            chains.append(f'[{i}:v]scale={w}:{h},format=yuv420p,settb=AVTB,setsar=1[v{i}]')
        else:
            src, a, b = spec; length = b - a
            args += ['-ss', f'{a:.3f}', '-t', f'{length:.3f}', '-i', str(src)]
            chains.append(f'[{i}:v]fps={FPS},scale={w}:{h}:flags=lanczos,{GRADE.format(fine=fine)},'
                          f'format=yuv420p,settb=AVTB,setsar=1,setpts=PTS-STARTPTS[v{i}]')
        lengths.append(length)
    label, offset = 'v0', lengths[0]
    for i in range(1, len(items)):
        offset -= FADE
        chains.append(f'[{label}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[x{i}]')
        label, offset = f'x{i}', offset + lengths[i]
    total = offset
    chains.append(f'[{label}]fade=t=in:st=0:d={FADE},fade=t=out:st={total - FADE:.3f}:d={FADE}[out]')
    args += ['-filter_complex', ';'.join(chains), '-map', '[out]', '-an', *encode,
             '-map_metadata', '-1', '-movflags', '+faststart', str(out)]
    subprocess.run(args, check=True)
    return total


def web_encode(seconds, ceiling_mb=88):
    # Capped so every page video stays under GitHub's 100 MB per-file limit.
    rate = min(9000, int(ceiling_mb * 8 * 1000 / seconds))
    return ['-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', f'{rate}k', '-bufsize', f'{rate * 2}k',
            '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p']


def add_music(film, music):
    """Lay the licensed track under a finished film: trimmed to length, fades, web loudness, video copied untouched."""
    seconds = duration(film); fade = music['fade_out']; tmp = film.with_suffix('.music.mp4')
    audio = (f"atrim=0:{seconds:.3f},afade=t=in:st=0:d=0.5,afade=t=out:st={seconds - fade:.3f}:d={fade},"
             f"loudnorm=I={music['loudness_lufs']}:TP=-1.5:LRA=11,aresample=48000")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(film), '-i', str(HERE / music['file']), '-map', '0:v:0', '-map', '1:a:0',
                    '-c:v', 'copy', '-af', audio, '-c:a', 'aac', '-b:a', '192k', '-shortest', '-metadata', f"comment=Music: {music['credit']}",
                    '-movflags', '+faststart', str(tmp)], check=True)
    tmp.replace(film)


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2]); what = sys.argv[3] if len(sys.argv) > 3 else 'all'
    out.mkdir(parents=True, exist_ok=True)
    edl = json.loads((HERE / 'edl.json').read_text())
    if what in ('clips', 'all'):
        for n, clip in enumerate(edl['clips'], 1):
            f = src / clip['source']; size = (1080, 1920) if is_vertical(f) else (1920, 1080)
            segs = [(f, a, b) for a, b in clip['keep']]
            seconds = sum(b - a for a, b in clip['keep'])
            total = render(segs, out / f'clip-{n:02d}.mp4', size, web_encode(seconds))
            print(f'clip-{n:02d}: {clip["source"]} -> {total:.1f}s', flush=True)
    if what in ('recap', 'all'):
        segs = [(src / f, a, b) for f, a, b in edl['recap']]
        for label, size, encode in [
            ('recap-1080.mp4', (1920, 1080), None),
            ('recap-4k.mp4', (3840, 2160), ['-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-maxrate', '40M', '-bufsize', '80M',
                                           '-profile:v', 'high', '-level', '5.1', '-pix_fmt', 'yuv420p'])]:
            w, h = size
            title, end = out / f'title-{h}.png', out / f'end-{h}.png'
            card(title, size, [])
            card(end, size, [('Corpus Christi Athletic Club', 0.045), ('September 19, 2026', 0.035)])
            seconds = sum(b - a for _, a, b in segs) + 8
            total = render(segs, out / label, size, encode or web_encode(seconds), cards=(title, end))
            add_music(out / label, edl['music'])
            print(f'{label}: {total:.1f}s with music', flush=True)
    if what == 'music':  # add or replace the soundtrack on already-rendered recaps
        for label in ('recap-1080.mp4', 'recap-4k.mp4'):
            add_music(out / label, edl['music']); print(f'{label}: music added', flush=True)


if __name__ == '__main__':
    main()
