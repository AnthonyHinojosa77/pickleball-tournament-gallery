#!/usr/bin/env python3
"""Stage the gallery's large downloads as a DRAFT GitHub release from GitHub Actions.

`prepare` (on the build machine) copies the finished full-size JPEGs into release-staging/ and records the
expected SHA-256 and size of every release asset. `stage` (on the Actions runner) rebuilds the ZIPs, remuxes
the 4K camera films from their shared Google Drive originals, refuses any asset that does not match the
recorded checksum, and uploads everything to a draft release. Publishing the draft is a separate step.
"""
import hashlib, json, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'release-staging'
sys.path.insert(0, str(ROOT / 'scripts'))
from build_gallery import make_zip  # same reproducible ZIP writer as the build


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(2**20), b''): h.update(block)
    return h.hexdigest()


def remux(src, dst):
    # Lossless: copy the camera's HEVC stream, drop telemetry/location tracks and metadata.
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-map', '0:v:0', '-c', 'copy', '-tag:v', 'hvc1',
                    '-map_metadata', '-1', '-movflags', '+faststart', str(dst)], check=True)


def zip_items(manifest, photo_dir):
    photos = [(photo_dir / p['filename'], f'Photos/{p["filename"]}') for p in manifest['photos']]
    films = [(ROOT / 'docs' / v['file'], f'Films/{Path(v["file"]).name}') for v in manifest['videos']]
    return photos, photos + films


def prepare(drive_ids_file):
    cfg = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'docs/media-manifest.json').read_text())
    build = json.loads((ROOT / 'artifacts/build.json').read_text())
    drive = dict(line.split()[::-1] for line in Path(drive_ids_file).read_text().split('\n') if line.strip())
    if STAGE.exists(): shutil.rmtree(STAGE)
    (STAGE / 'photos').mkdir(parents=True)
    assets = []
    for p in manifest['photos']:
        src = ROOT / 'artifacts/photos' / p['filename']; dst = STAGE / 'photos' / p['filename']
        shutil.copyfile(src, dst); assert sha(dst) == p['sha256']
        assets.append({'name': p['filename'], 'sha256': p['sha256'], 'bytes': dst.stat().st_size, 'from': 'staged'})
    for v in manifest['videos']:
        assets.append({'name': Path(v['download']).name, 'sha256': v['download_sha256'], 'bytes': v['download_bytes'],
                       'from': 'drive', 'drive_id': drive[v['source']]})
    for name, key in [('pickleball-photos.zip', 'photos_zip'), ('pickleball-complete-gallery.zip', 'complete_zip')]:
        assets.append({'name': name, 'sha256': build[f'{key}_sha256'], 'bytes': build[f'{key}_bytes'], 'from': 'zip'})
    notes = (f'All {len(manifest["photos"])} photos from September 19, freshly developed from the camera RAW files '
             f'(6,138 × 3,450 JPEG), and all {len(manifest["videos"])} drone films as untouched 4K camera originals. '
             'The complete ZIP includes the films in 1080p.\n')
    (STAGE / 'assets.json').write_text(json.dumps({'tag': cfg['release_tag'], 'repository': cfg['repository'],
        'title': 'Tournament — client-ready photos and drone films', 'notes': notes, 'assets': assets}, indent=1) + '\n')
    print(f'Staged {len(manifest["photos"])} photos; {len(assets)} release assets recorded')


def gh(*args, capture=False):
    return subprocess.run(['gh', *args], check=True, text=True, capture_output=capture).stdout


def stage():
    spec = json.loads((STAGE / 'assets.json').read_text())
    manifest = json.loads((ROOT / 'docs/media-manifest.json').read_text())
    repo, tag = spec['repository'], spec['tag']
    work = Path('/tmp/release'); work.mkdir(exist_ok=True)
    existing = subprocess.run(['gh', 'release', 'view', tag, '--repo', repo, '--json', 'isDraft,assets'],
                              text=True, capture_output=True)
    if existing.returncode:
        notes = work / 'notes.txt'; notes.write_text(spec['notes'])
        gh('release', 'create', tag, '--repo', repo, '--draft', '--target', 'main', '--title', spec['title'],
           '--notes-file', str(notes))
        uploaded = {}
    else:
        info = json.loads(existing.stdout); assert info['isDraft'], 'Refusing to modify a published release'
        uploaded = {a['name']: a['size'] for a in info['assets']}
    photo_zip, complete_zip = zip_items(manifest, STAGE / 'photos')
    for asset in spec['assets']:
        name = asset['name']
        if uploaded.get(name) == asset['bytes']: print('already uploaded', name, flush=True); continue
        if asset['from'] == 'staged': path = STAGE / 'photos' / name
        elif asset['from'] == 'zip':
            path = work / name; make_zip(path, photo_zip if name == 'pickleball-photos.zip' else complete_zip)
        else:
            original = work / 'original.mp4'; path = work / name
            url = f'https://drive.usercontent.google.com/download?id={asset["drive_id"]}&export=download&confirm=t'
            subprocess.run(['curl', '-sSL', '--fail', '--retry', '4', '-o', str(original), url], check=True)
            remux(original, path); original.unlink()
        actual = sha(path)
        assert actual == asset['sha256'] and path.stat().st_size == asset['bytes'], f'{name}: checksum mismatch {actual}'
        gh('release', 'upload', tag, str(path), '--repo', repo, '--clobber')
        print('uploaded', name, flush=True)
        if asset['from'] != 'staged': path.unlink()
    info = json.loads(gh('release', 'view', tag, '--repo', repo, '--json', 'isDraft,assets', capture=True))
    sizes = {a['name']: a['size'] for a in info['assets']}
    missing = [a['name'] for a in spec['assets'] if sizes.get(a['name']) != a['bytes']]
    assert not missing, f'Missing or wrong-size assets: {missing}'
    print(f'Draft release {tag} holds all {len(spec["assets"])} verified assets; still unpublished: {info["isDraft"]}')


if __name__ == '__main__':
    prepare(sys.argv[2]) if sys.argv[1] == 'prepare' else stage()
