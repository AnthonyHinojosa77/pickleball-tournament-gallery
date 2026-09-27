#!/usr/bin/env python3
"""Rebuild presentation from the existing verified media, without re-encoding or rebuilding ZIPs."""
from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parents[1]
ICON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 3v12m-5-5 5 5 5-5M5 16v5h14v-5"/></svg>'
def render():
    cfg=json.loads((ROOT/'config.json').read_text());m=json.loads((ROOT/'docs/media-manifest.json').read_text());build=json.loads((ROOT/'artifacts/build.json').read_text())
    photos=[];films=[]
    for p in m['photos']:
        base=Path(p['preview']);small=str(base.with_name(f'photo-{p["id"]:02d}-480.webp'));label=html.escape(p['title']);alt=html.escape(p['alt'])
        photos.append(f'<figure class="photo-card"><a class="photo-open" href="{p["full"]}" data-photo-index="{p["id"]-1}" data-pswp-width="{p["width"]}" data-pswp-height="{p["height"]}" aria-label="Open photo {p["id"]}: {label}"><img src="{small}" srcset="{small} 480w, {p["preview"]} 960w" sizes="(max-width:760px) 50vw, (max-width:1100px) 33vw, 25vw" width="{p["width"]}" height="{p["height"]}" alt="{alt}" loading="{"eager" if p["id"]<=4 else "lazy"}" decoding="async"></a><figcaption><span class="photo-number">{p["id"]:02d}</span><span class="photo-caption">{label}</span><a class="tile-download" href="{p["full"]}" download="{p["filename"]}" aria-label="Download photo {p["id"]}, {p["width"]} by {p["height"]} pixels">{ICON}<span>JPG</span></a></figcaption></figure>')
    for v in m['videos']:
        label=html.escape(v['title']);seconds=round(v['duration']);length=f'{seconds//60}:{seconds%60:02d}';filename=Path(v['download']).name
        films.append(f'<figure class="film-card"><video controls playsinline preload="none" poster="{v["poster"]}" width="{v["width"]}" height="{v["height"]}" aria-label="Film {v["id"]}: {label}, {length}, no recorded sound"><source src="{v["file"]}" type="video/mp4"><p>Your browser cannot play this video. <a href="{v["download"]}" download>Download MP4</a>.</p></video><figcaption><div><h3>{v["id"]:02d} / {label}</h3><p>{length} · 4K original</p></div><a class="tile-download" href="{v["download"]}" download="{filename}" aria-label="Download film {v["id"]}, 4K MP4, {v["download_bytes"]/1e6:.0f} MB">{ICON}<span>4K</span></a></figcaption></figure>')
    # Archive byte counts are in the media build receipt; no need to hydrate ZIPs to restyle the site.
    photo_bytes=build['photos_zip_bytes'];all_bytes=build['complete_zip_bytes']
    tokens={'MEDIA_VERSION':cfg['media_version'],'UI_VERSION':cfg.get('ui_version',cfg['media_version']),'PHOTO_CARDS':'\n'.join(photos),'FILM_CARDS':'\n'.join(films),'PHOTO_ZIP_URL':m['photo_zip'],'COMPLETE_ZIP_URL':m['complete_zip'],'PHOTO_ZIP_SIZE':f'{photo_bytes/1e6:.0f} MB','COMPLETE_ZIP_SIZE':f'{all_bytes/1e6:.0f} MB','PHOTO_COUNT':str(len(m['photos'])),'FILM_COUNT':str(len(m['videos']))}
    s=(ROOT/'index.template.html').read_text()
    for key,value in tokens.items():s=s.replace('@@'+key+'@@',value)
    assert '@@' not in s
    (ROOT/'docs/index.html').write_text(s)
    print(f'Rendered branded gallery from {len(m["photos"])} photos and {len(m["videos"])} films')
if __name__=='__main__':render()
