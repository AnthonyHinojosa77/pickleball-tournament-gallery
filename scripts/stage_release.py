#!/usr/bin/env python3
"""Stage the gallery's large downloads as a DRAFT GitHub release from GitHub Actions.

`prepare` (on the build machine) copies the finished full-size JPEGs into release-staging/, splits large films
into parts under GitHub's 100 MB file limit and records the expected SHA-256 and size of every release asset.
`stage` (on the Actions runner) rebuilds the ZIPs and films, refuses any asset that does not match the
recorded checksum, and uploads everything to a draft release. Publishing the draft is a separate step.
"""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'release-staging'
PART = 95 * 2**20  # stay under GitHub's 100 MB per-file limit
sys.path.insert(0, str(ROOT / 'scripts'))
from build_gallery import make_zip  # same reproducible ZIP writer as the build


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(2**20), b''): h.update(block)
    return h.hexdigest()


def zip_items(manifest, photo_dir):
    photos = [(photo_dir / p['filename'], f'Photos/{p["filename"]}') for p in manifest['photos']]
    films = [(ROOT / 'docs' / v['file'], f'Films/{Path(v["file"]).name}') for v in manifest['videos']]
    return photos, photos + films


def prepare():
    cfg = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'docs/media-manifest.json').read_text())
    build = json.loads((ROOT / 'artifacts/build.json').read_text())
    if STAGE.exists(): shutil.rmtree(STAGE)
    (STAGE / 'photos').mkdir(parents=True)
    assets = []
    for p in manifest['photos']:
        src = ROOT / 'artifacts/photos' / p['filename']; dst = STAGE / 'photos' / p['filename']
        shutil.copyfile(src, dst); assert sha(dst) == p['sha256']
        assets.append({'name': p['filename'], 'sha256': p['sha256'], 'bytes': dst.stat().st_size, 'from': 'staged'})
    (STAGE / 'films').mkdir()
    for v in manifest['videos']:
        if not v['download'].startswith('https://'): continue  # served from the page itself
        name = Path(v['download']).name; parts = []
        with open(ROOT / 'artifacts/films' / name, 'rb') as f:
            for n, block in enumerate(iter(lambda: f.read(PART), b'')):
                part = STAGE / 'films' / f'{name}.part{n:02d}'; part.write_bytes(block); parts.append(part.name)
        assets.append({'name': name, 'sha256': v['download_sha256'], 'bytes': v['download_bytes'], 'from': 'parts', 'parts': parts})
    for name, key in [('pickleball-photos.zip', 'photos_zip'), ('pickleball-complete-gallery.zip', 'complete_zip')]:
        assets.append({'name': name, 'sha256': build[f'{key}_sha256'], 'bytes': build[f'{key}_bytes'], 'from': 'zip'})
    notes = (f'All {len(manifest["photos"])} photos from September 19, developed from the camera RAW files '
             '(6,138 × 3,450 JPEG), and the color-graded 4K tournament recap film. '
             'The complete ZIP adds the recap and every trimmed, color-graded drone clip in HD.\n')
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
            path = work / name
            with open(path, 'wb') as out:
                for part in asset['parts']: out.write((STAGE / 'films' / part).read_bytes())
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
    prepare() if sys.argv[1] == 'prepare' else stage()
