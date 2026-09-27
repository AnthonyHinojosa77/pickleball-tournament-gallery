#!/usr/bin/env python3
"""Build the static gallery and ZIPs from verified deliverables; never alter originals."""
import argparse, hashlib, io, json, shutil, subprocess, zipfile
from pathlib import Path
from PIL import Image, ImageOps, ImageCms

ROOT = Path(__file__).resolve().parents[1]

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
    # Fixed timestamps and stored entries make the archive byte-for-byte reproducible on any machine.
    temp=path.with_name(path.name+'.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for src,name in items:
            info=zipfile.ZipInfo(name,date_time=(2026,9,19,12,0,0));info.external_attr=0o644<<16
            with open(src,'rb') as f, z.open(info,'w',force_zip64=True) as out:shutil.copyfileobj(f,out,2**20)
    temp.replace(path)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(items)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--delivery',type=Path,default=ROOT.parent);args=ap.parse_args()
    base=args.delivery.resolve();cfg=read(ROOT/'config.json');docs=ROOT/'docs';artifacts=ROOT/'artifacts';artifacts.mkdir(exist_ok=True)
    version=cfg['media_version']; photo_dir=f'media/photos-{version}'; preview_dir=f'media/previews-{version}'
    photo_base=cfg.get('photo_asset_base')
    if photo_base:(artifacts/'photos').mkdir(exist_ok=True)
    for folder in [photo_dir,preview_dir,'media/reels','media/posters']:(docs/folder).mkdir(parents=True,exist_ok=True)
    stills=base/'_Pipeline/action-stills.json'
    records=read(base/'_Pipeline/photos.json')+(read(stills) if stills.exists() else [])
    assert len(records)==cfg['expected_photos'],f"Expected {cfg['expected_photos']} photos, found {len(records)}"
    assert len({r['source'] for r in records})==len(records),'Duplicate photo source'
    # Lead with the group photo, then mix orientations; keep stable numbering.
    records.sort(key=lambda r:(0 if '_0086_' in r['source'] else 1,Path(r['source']).name,r.get('t',-1)))
    # Redevelopments may carry explicit numbering so photo URLs and captions stay stable.
    if all('gallery_id' in r for r in records):records.sort(key=lambda r:r['gallery_id'])
    photos=[];photo_items=[]
    for i,r in enumerate(records,1):
        src=Path(r['output']);name=f'pickleball-photo-{i:02d}.jpg';dest=(artifacts/'photos'/name) if photo_base else (docs/photo_dir/name)
        if photo_base:
            if dest.exists() or dest.is_symlink():dest.unlink()
            dest.symlink_to(src.resolve())
        else:copy(src,dest)
        with Image.open(src) as im:
            im=ImageOps.exif_transpose(im)
            if im.info.get('icc_profile'):im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile'])),ImageCms.createProfile('sRGB'),outputMode='RGB')
            else:im=im.convert('RGB')
            w,h=im.size
            for size in [480,960,2048]:
                preview_path=docs/preview_dir/f'photo-{i:02d}-{size}.webp'
                if not preview_path.exists() or preview_path.stat().st_mtime_ns<src.stat().st_mtime_ns:
                    preview=im.copy();preview.thumbnail((size,size if size==2048 else size*2));preview.save(preview_path,'WEBP',quality=88 if size==2048 else 82,method=5)
        label='On the court' if 't' in r else title(r['source']);alt=f'{label} at the Real Estate Pickleball Tournament, Corpus Christi Athletic Club. Photo {i}.'
        item={'id':i,'filename':name,'title':label,'alt':alt,'width':w,'height':h,'bytes':dest.stat().st_size,'full':f'{photo_base}/{name}' if photo_base else f'{photo_dir}/{name}','preview':f'{preview_dir}/photo-{i:02d}-960.webp','display':f'{preview_dir}/photo-{i:02d}-2048.webp','sha256':sha(dest),'source_type':'video freeze-frame' if 't' in r else 'camera RAW DNG','source_sha256':r.get('source_sha256')};photos.append(item);photo_items.append((dest,f'Photos/{name}'))
    # Films play on the page in HD; a film with a separate `download` (the 4K recap) is served from the release.
    reels=read(base/'_Pipeline/reels.json');reels.sort(key=lambda r:Path(r['source']).name)
    assert len(reels)==cfg['expected_videos'],f"Expected {cfg['expected_videos']} films, found {len(reels)}"
    if all('gallery_id' in r for r in reels):reels.sort(key=lambda r:r['gallery_id'])
    (artifacts/'films').mkdir(exist_ok=True);videos=[];video_items=[]
    for old in (docs/'media/reels').glob('pickleball-film-*.mp4'):old.unlink()
    for old in (docs/'media/posters').glob('film-*.jpg'):old.unlink()
    for old in (artifacts/'films').glob('*'):old.unlink()
    for i,r in enumerate(reels,1):
        src=Path(r['output']);name=f'pickleball-film-{i:02d}.mp4';dest=docs/'media/reels'/name;copy(src,dest)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','json',str(dest)]))
        w,h=probe['streams'][0]['width'],probe['streams'][0]['height'];duration=float(probe['format']['duration'])
        poster=docs/'media/posters'/f'film-{i:02d}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(r.get('poster_at',3)),'-i',str(dest),'-frames:v','1','-vf','scale=960:-2' if w>h else 'scale=-2:960','-q:v','3','-update','1',str(poster)],check=True)
        if r.get('download'):
            original=artifacts/'films'/f'pickleball-film-{i:02d}-4k.mp4';original.symlink_to(Path(r['download']).resolve())
            download,download_bytes,download_sha,quality=f'{photo_base}/{original.name}',original.stat().st_size,sha(original),'4K'
        else:
            download,download_bytes,download_sha,quality=f'media/reels/{name}',dest.stat().st_size,sha(dest),'HD'
        item={'id':i,'title':r.get('title','Tournament from above'),'file':f'media/reels/{name}','poster':f'media/posters/{poster.name}','width':w,'height':h,'duration':duration,'bytes':dest.stat().st_size,'sha256':sha(dest),'download':download,'download_bytes':download_bytes,'download_sha256':download_sha,'download_quality':quality,'source':r['source']};videos.append(item);video_items.append((dest,f'Films/{name}'))
    photo_zip=artifacts/'pickleball-photos.zip';complete_zip=artifacts/'pickleball-complete-gallery.zip'
    print('Creating and CRC-checking ZIP archives…',flush=True);make_zip(photo_zip,photo_items);make_zip(complete_zip,photo_items+video_items)
    zip_url=f'https://github.com/{cfg["repository"]}/releases/download/{cfg["release_tag"]}/{complete_zip.name}'
    photo_zip_url=f'https://github.com/{cfg["repository"]}/releases/download/{cfg["release_tag"]}/{photo_zip.name}'
    data={'event':cfg['event'],'photos':photos,'videos':videos,'photo_zip':photo_zip_url,'complete_zip':zip_url}
    (docs/'media.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    dump(docs/'media-manifest.json',data)
    # Superseded exports are in Git history; omit them from the deployed site.
    for obsolete in [docs/'media/photos',docs/'media/previews',*[d for d in (docs/'media').glob('previews-*') if d.name!=Path(preview_dir).name]]:
        if obsolete.exists():shutil.rmtree(obsolete)
    obsolete_zip=docs/'downloads/pickleball-photos.zip'
    if obsolete_zip.exists():obsolete_zip.unlink()
    dump(artifacts/'build.json',{'photos':len(photos),'videos':len(videos),'published_bytes':sum(p.stat().st_size for p in docs.rglob('*') if p.is_file()),'photos_zip_sha256':sha(photo_zip),'photos_zip_bytes':photo_zip.stat().st_size,'complete_zip_sha256':sha(complete_zip),'complete_zip_bytes':complete_zip.stat().st_size})
    print(f'Built {len(photos)} photos, {len(videos)} films; complete ZIP {complete_zip.stat().st_size/1e6:.1f} MB',flush=True)
if __name__=='__main__':
    main()
    from render_site import render
    render()
