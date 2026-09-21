#!/usr/bin/env python3
"""Build the static gallery and ZIPs from verified deliverables; never alter originals."""
import argparse, hashlib, html, json, shutil, subprocess, zipfile
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 3v12m-5-5 5 5 5-5M5 16v5h14v-5"/></svg>'

def read(p): return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def title(source):
    stem=Path(source).stem
    if 'Lucha' in stem:return 'The courtside soundtrack'
    try:ident=int(stem.split('_')[-2])
    except (ValueError,IndexError):return 'Tournament day from above'
    if ident in [86,87,88]:return 'The tournament community'
    if ident in [105,107,108,117,118,119,120]:return 'The courtside soundtrack'
    if ident>=126:return 'The people behind the event'
    return 'Tournament day from above'
def copy(src,dst):
    if not dst.exists() or src.stat().st_size!=dst.stat().st_size or src.stat().st_mtime_ns>dst.stat().st_mtime_ns:shutil.copy2(src,dst)
def make_zip(path,items):
    temp=path.with_name(path.name+'.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for src,name in items:z.write(src,name)
    temp.replace(path)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(items)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--delivery',type=Path,default=ROOT.parent);args=ap.parse_args()
    base=args.delivery.resolve();cfg=read(ROOT/'config.json');docs=ROOT/'docs';artifacts=ROOT/'artifacts';artifacts.mkdir(exist_ok=True)
    for folder in ['media/photos','media/previews','media/reels','media/posters','downloads']:(docs/folder).mkdir(parents=True,exist_ok=True)
    records=read(base/'_Pipeline/photos.json')+read(base/'_Pipeline/action-stills.json')
    assert len(records)==52,'Expected 47 corrected photos plus five action stills'
    # Lead with the group photo, then mix orientations; keep stable numbering.
    records.sort(key=lambda r:(0 if '_0086_' in r['source'] else 1,Path(r['source']).name,r.get('t',-1)))
    photos=[];photo_cards=[];photo_items=[]
    for i,r in enumerate(records,1):
        src=Path(r['output']);name=f'pickleball-photo-{i:02d}.jpg';dest=docs/'media/photos'/name;copy(src,dest)
        with Image.open(src) as im:
            im=ImageOps.exif_transpose(im).convert('RGB');w,h=im.size
            for size in [480,960]:
                preview=im.copy();preview.thumbnail((size,size*2));preview.save(docs/'media/previews'/f'photo-{i:02d}-{size}.webp','WEBP',quality=79,method=5)
        label='On the court' if 't' in r else title(r['source']);alt=f'{label} at the Real Estate Pickleball Tournament, Corpus Christi Athletic Club. Photo {i}.'
        item={'id':i,'filename':name,'title':label,'alt':alt,'width':w,'height':h,'bytes':dest.stat().st_size,'full':f'media/photos/{name}','preview':f'media/previews/photo-{i:02d}-960.webp','sha256':sha(dest)};photos.append(item);photo_items.append((dest,f'Photos/{name}'))
        photo_cards.append(f'''<figure class="photo-card"><a class="photo-open" href="{item['full']}" data-photo-index="{i-1}" aria-label="Open photo {i}: {html.escape(label)}"><img src="media/previews/photo-{i:02d}-480.webp" srcset="media/previews/photo-{i:02d}-480.webp 480w, media/previews/photo-{i:02d}-960.webp 960w" sizes="(max-width:760px) 50vw, (max-width:1100px) 33vw, 25vw" width="{w}" height="{h}" alt="{html.escape(alt)}" loading="{'eager' if i<=4 else 'lazy'}" decoding="async"></a><figcaption><span class="photo-number">{i:02d}</span><span class="photo-caption">{html.escape(label)}</span><a class="tile-download" href="{item['full']}" download="{name}" aria-label="Download photo {i}, {w} by {h} pixels" title="Download {max(w,h):,} px JPEG">{ICON}<span>JPG</span></a></figcaption></figure>''')
    reels=read(base/'_Pipeline/reels.json');reels.sort(key=lambda r:(0 if '_0104_' in r['source'] else 1,Path(r['source']).name));videos=[];film_cards=[];video_items=[]
    for i,r in enumerate(reels,1):
        src=Path(r['output']);name=f'pickleball-film-{i:02d}.mp4';dest=docs/'media/reels'/name;copy(src,dest);poster=docs/'media/posters'/f'film-{i:02d}.jpg'
        if not poster.exists():subprocess.run(['ffmpeg','-v','error','-y','-ss','3','-i',str(src),'-frames:v','1','-vf','scale=540:960','-update','1',str(poster)],check=True)
        duration=float(r['duration']);label='Courtside fly-through' if '_0104_' in r['source'] else 'Tournament from above';seconds=round(duration)
        item={'id':i,'title':label,'file':f'media/reels/{name}','poster':f'media/posters/{poster.name}','duration':duration,'bytes':dest.stat().st_size,'sha256':r['sha256']};videos.append(item);video_items.append((dest,f'Films/{name}'))
        film_cards.append(f'''<figure class="film-card"><video controls playsinline preload="none" poster="{item['poster']}" width="1080" height="1920" aria-label="Film {i}: {label}, {seconds} seconds, no recorded sound"><source src="{item['file']}" type="video/mp4"><p>Your browser cannot play this video. <a href="{item['file']}" download>Download MP4</a>.</p></video><figcaption><div><h3>{i:02d} / {label}</h3><p>{seconds}s · 1080 × 1920</p></div><a class="tile-download" href="{item['file']}" download="{name}" aria-label="Download film {i} MP4">{ICON}<span>MP4</span></a></figcaption></figure>''')
    photo_zip=docs/'downloads/pickleball-photos.zip';complete_zip=artifacts/'pickleball-complete-gallery.zip'
    print('Creating and CRC-checking ZIP archives…',flush=True);make_zip(photo_zip,photo_items);make_zip(complete_zip,photo_items+video_items)
    zip_url=f'https://github.com/{cfg["repository"]}/releases/download/{cfg["release_tag"]}/{complete_zip.name}'
    template=(ROOT/'index.template.html').read_text()
    for token,value in {'@@PHOTO_CARDS@@':'\n'.join(photo_cards),'@@FILM_CARDS@@':'\n'.join(film_cards),'@@PHOTO_ZIP_SIZE@@':f'{photo_zip.stat().st_size/1e6:.0f} MB','@@COMPLETE_ZIP_SIZE@@':f'{complete_zip.stat().st_size/1e6:.0f} MB','@@COMPLETE_ZIP_URL@@':zip_url}.items():template=template.replace(token,value)
    assert '@@' not in template;(docs/'index.html').write_text(template)
    data={'event':cfg['event'],'photos':photos,'videos':videos,'photo_zip':'downloads/pickleball-photos.zip','complete_zip':zip_url}
    (docs/'media.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    dump(docs/'media-manifest.json',data)
    dump(artifacts/'build.json',{'photos':len(photos),'videos':len(videos),'published_bytes':sum(p.stat().st_size for p in docs.rglob('*') if p.is_file()),'photos_zip_sha256':sha(photo_zip),'complete_zip_sha256':sha(complete_zip),'complete_zip_bytes':complete_zip.stat().st_size})
    print(f'Built {len(photos)} photos, {len(videos)} films; complete ZIP {complete_zip.stat().st_size/1e6:.1f} MB',flush=True)
if __name__=='__main__':main()
