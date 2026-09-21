#!/usr/bin/env python3
"""Validate the complete static site, media hashes, video formats and ZIP contents."""
import hashlib, json, subprocess, zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''): h.update(block)
    return h.hexdigest()

class Document(HTMLParser):
    def __init__(self): super().__init__(); self.tags = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs); self.tags.append((tag, attrs))
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate element ID'
            self.ids.add(attrs['id'])

def main():
    manifest = json.loads((DOCS/'media-manifest.json').read_text())
    build = json.loads((ROOT/'artifacts/build.json').read_text())
    source = (DOCS/'index.html').read_text()
    assert '@@' not in source and '/Users/' not in source
    doc = Document(); doc.feed(source)
    local_links = 0
    for tag, attrs in doc.tags:
        for name in ['href', 'src', 'poster']:
            value = attrs.get(name)
            if not value: continue
            parsed = urlparse(value)
            if parsed.scheme: assert parsed.scheme == 'https'; continue
            if parsed.path:
                path = (DOCS/unquote(parsed.path)).resolve()
                assert path.is_relative_to(DOCS.resolve()) and path.is_file(), value
                local_links += 1
            if parsed.fragment: assert parsed.fragment in doc.ids, value
        if tag == 'img': assert 'alt' in attrs
        if tag == 'video': assert all(k in attrs for k in ['controls', 'playsinline', 'poster']) and attrs['preload'] == 'none'
    assert len([t for t,a in doc.tags if t == 'video']) == 10
    assert len([a for t,a in doc.tags if 'data-photo-index' in a]) == 52
    assert len(manifest['photos']) == 52 and len(manifest['videos']) == 10
    for p in manifest['photos']:
        path = DOCS/p['full']; assert sha(path) == p['sha256']
        with Image.open(path) as im:
            im.load(); assert im.size == (p['width'],p['height']) and im.mode == 'RGB'
            assert im.info.get('icc_profile'), f'Missing sRGB profile: {path}'
        for size in [480,960]:
            with Image.open(DOCS/f'media/previews/photo-{p["id"]:02d}-{size}.webp') as im:
                im.load(); assert im.width <= size and im.height <= size*2
    for v in manifest['videos']:
        path = DOCS/v['file']; assert sha(path) == v['sha256']
        data = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
        video = next(s for s in data['streams'] if s['codec_type']=='video')
        audio = next(s for s in data['streams'] if s['codec_type']=='audio')
        assert (video['width'],video['height']) == (1080,1920) and video['codec_name']=='h264'
        assert audio['codec_name']=='aac' and float(data['format']['duration']) <= 60.1
        with Image.open(DOCS/v['poster']) as im: im.load(); assert im.size == (540,960)
    for path, count, digest in [(DOCS/manifest['photo_zip'],52,build['photos_zip_sha256']), (ROOT/'artifacts/pickleball-complete-gallery.zip',62,build['complete_zip_sha256'])]:
        assert sha(path) == digest
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None and len(z.namelist())==count
            assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    files = [p for p in DOCS.rglob('*') if p.is_file()]
    assert all(p.stat().st_size < 100*2**20 for p in files), 'GitHub per-file limit exceeded'
    assert sum(p.stat().st_size for p in files) < 1_000_000_000, 'GitHub Pages site limit exceeded'
    subprocess.run(['node','--check',str(DOCS/'app.js')],check=True)
    subprocess.run(['node',str(ROOT/'scripts/test_lightbox.cjs')],check=True)
    result = {'passed':True,'photos':52,'videos':10,'checked_local_references':local_links,'published_files':len(files),'published_bytes':sum(p.stat().st_size for p in files),'zip_integrity':'passed','media_sha256':'passed','lightbox_logic':'passed','browser_visual_testing':'not performed'}
    (ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__': main()
