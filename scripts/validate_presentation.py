#!/usr/bin/env python3
"""Validate UI changes while requiring that the previously verified media is unchanged."""
import json,subprocess
from pathlib import Path
from urllib.parse import urlparse,unquote
from validate_gallery import Document
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
def validate():
    for args in [[],['--cached']]:
        changed=subprocess.check_output(['git','diff',*args,'--name-only','--','docs/media','docs/media-manifest.json','docs/media.js'],cwd=ROOT,text=True)
        assert not changed.strip(),'Use the full validator when photo/video assets change'
    doc=Document();source=(DOCS/'index.html').read_text();doc.feed(source)
    assert '@@' not in source and '/Users/' not in source
    assert 'maximum-scale=1' not in source and 'user-scalable=no' not in source
    references=[]
    for tag,a in doc.tags:
        for attr in ['href','src','poster']:
            value=a.get(attr)
            if not value:continue
            u=urlparse(value)
            if u.scheme:assert u.scheme=='https';continue
            if u.path:
                p=(DOCS/unquote(u.path)).resolve();assert p.is_relative_to(DOCS) and p.is_file(),value;references.append(value)
            if u.fragment:assert u.fragment in doc.ids,value
        if tag=='img':assert 'alt' in a
    manifest=json.loads((ROOT/'docs/media-manifest.json').read_text())
    assert len([a for t,a in doc.tags if 'data-photo-index' in a])==len(manifest['photos'])
    assert len([a for t,a in doc.tags if t=='video'])==len(manifest['videos'])
    assert any(t=='script' and a.get('type')=='module' and a['src'].startswith('app.js?') for t,a in doc.tags)
    for p in ['app.js','gallery-options.mjs','vendor/photoswipe-lightbox.esm.min.js','vendor/photoswipe.esm.min.js']:
        subprocess.run(['node','--check',str(DOCS/p)],check=True)
    subprocess.run(['node',str(ROOT/'scripts/test_lightbox.cjs')],check=True)
    files=[p for p in DOCS.rglob('*') if p.is_file()]
    size=sum(p.stat().st_size for p in files);assert size<1_000_000_000
    assert all(p.stat().st_size<100*2**20 for p in files)
    result={'passed':True,'scope':'presentation update; media unchanged from previously verified commit','local_references':len(references),'site_bytes':size,'zoom_dimensions_tested':f"{len(manifest['photos'])} photographs at 320, 390, 430 and 1440 CSS pixel widths",'physical_iphone_test':False}
    (ROOT/'presentation-validation.json').write_text(json.dumps(result,indent=2))
    return result
if __name__=='__main__':print(json.dumps(validate(),indent=2))
