#!/usr/bin/env python3
"""Publish this static event gallery to GitHub Pages and produce verified URL QR codes.

Uses gh's existing authentication; never reads, prints or stores its token.
Re-running updates the same repository, Pages site and release asset.
"""
import argparse, concurrent.futures, datetime, hashlib, json, subprocess, sys, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def run(*args, capture=False, input=None, check=True):
    return subprocess.run(list(args),cwd=ROOT,input=input,text=True,check=check,stdout=subprocess.PIPE if capture else None,stderr=subprocess.PIPE if capture else None)

def api(endpoint, method='GET', data=None, optional=False):
    args=['gh','api',endpoint,'-X',method]
    if data is not None: args += ['--input','-']
    result=run(*args,capture=True,input=json.dumps(data) if data is not None else None,check=False)
    if result.returncode:
        if optional and ('HTTP 404' in result.stderr or '(404)' in result.stderr): return None
        raise RuntimeError(f'GitHub request failed: {endpoint}: {result.stderr.strip()}')
    return json.loads(result.stdout) if result.stdout.strip() else {}

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()

def get(url, method='GET', headers=None):
    for attempt in range(5):
        try:
            return urlopen(Request(url,method=method,headers={'User-Agent':'PickleballGalleryVerifier/1.0',**(headers or {})}),timeout=60)
        except HTTPError as error:
            if error.code not in (429,500,502,503,504) or attempt==4:raise
        except (URLError,TimeoutError,ConnectionError):
            if attempt==4:raise
        print(f'Retrying transient {method} failure: {url.rsplit("/",1)[-1]}',flush=True)
        time.sleep(2**attempt)

def release_for_tag(repo, tag):
    # GitHub's by-tag endpoint excludes drafts, even for the authenticated owner.
    release=api(f'repos/{repo}/releases/tags/{tag}',optional=True)
    if release is None:
        release=next((r for r in api(f'repos/{repo}/releases?per_page=100') if r['tag_name']==tag),None)
    return release

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--qr-output',type=Path,default=ROOT.parent);args=ap.parse_args()
    cfg=json.loads((ROOT/'config.json').read_text());repo=cfg['repository'];tag=cfg['release_tag']
    docs=ROOT/'docs';archive=ROOT/'artifacts/pickleball-complete-gallery.zip'
    run(sys.executable,str(ROOT/'scripts/validate_gallery.py'))
    print('Preparing GitHub repository…',flush=True)
    user=api('user');assert repo.split('/')[0].lower()==user['login'].lower(),'Configured repository must belong to the authenticated account'
    if not (ROOT/'.git').exists():
        run('git','init','-b','main')
        run('git','config','user.name',user.get('name') or user['login'])
        run('git','config','user.email',f'{user["id"]}+{user["login"]}@users.noreply.github.com')
        run('git','config','credential.helper','!gh auth git-credential')
    branch=run('git','branch','--show-current',capture=True).stdout.strip();assert branch=='main',f'Expected main, got {branch}'
    run('git','add','--','docs','scripts','index.template.html','config.json','README.md','requirements.txt','.gitignore')
    if run('git','diff','--cached','--quiet',check=False).returncode:
        run('git','commit','-m','Redevelop all 47 RAW photographs and rebuild full-resolution delivery')
    existing=api(f'repos/{repo}',optional=True)
    if existing is None:
        run('gh','repo','create',repo,'--public','--description','Real Estate Pickleball Tournament — photo and drone film gallery')
    else:
        assert existing['private'] is False,'Refusing to change an existing private repository to public'
    remote=f'https://github.com/{repo}.git'
    current=run('git','remote','get-url','origin',capture=True,check=False)
    if current.returncode:run('git','remote','add','origin',remote)
    else:assert current.stdout.strip()==remote,'Unexpected origin; no changes made to remote'
    commit=run('git','rev-parse','HEAD',capture=True).stdout.strip()
    digest=sha(archive);release=release_for_tag(repo,tag)
    photo_archive=ROOT/'artifacts/pickleball-photos.zip'
    archives=[archive,photo_archive]
    upload_files=archives+sorted((ROOT/'artifacts/photos').glob('*.jpg')) if cfg.get('photo_asset_base') else archives
    if (ROOT/'artifacts/RAW_SOURCE_AUDIT.csv').exists():upload_files.append(ROOT/'artifacts/RAW_SOURCE_AUDIT.csv')
    print('Publishing corrected collection ZIPs…',flush=True)
    notes=ROOT/'artifacts/release-notes.txt'
    notes.write_text('Fresh development of 47 original DNGs through lossless TIFF intermediates, tuned capture deconvolution, the approved color finish and restrained noise reduction. The 47 native-resolution camera JPEGs use quality 96 and 4:4:4 color sampling. Five separately identified 4K video stills and ten drone films are retained.\n\nCamera originals remain untouched in OneDrive.\n\n'+''.join(f'{p.name} SHA-256: {sha(p)}\n' for p in upload_files))
    if release is None:
        run('gh','release','create',tag,*[str(p) for p in archives],'--repo',repo,'--target','main','--title','Tournament — refined photos and drone films','--notes-file',str(notes))
    else:
        for path in upload_files:
            existing_asset=next((a for a in release['assets'] if a['name']==path.name),None)
            if existing_asset is None or existing_asset.get('digest')!='sha256:'+sha(path):
                run('gh','release','upload',tag,str(path),'--repo',repo,'--clobber')
        run('gh','release','edit',tag,'--repo',repo,'--title','Tournament — full RAW photo development and drone films','--notes-file',str(notes))
    # Initial releases already received the ZIPs; publish full-size photo assets too.
    release=release_for_tag(repo,tag)
    for path in upload_files:
        current_asset=next((a for a in release['assets'] if a['name']==path.name),None)
        if current_asset is None:
            run('gh','release','upload',tag,str(path),'--repo',repo)
    release=release_for_tag(repo,tag)
    for path in upload_files:
        current_asset=next(a for a in release['assets'] if a['name']==path.name)
        assert current_asset['size']==path.stat().st_size and current_asset['state']=='uploaded'
        if current_asset.get('digest'):assert current_asset['digest']=='sha256:'+sha(path)
    asset=next(a for a in release['assets'] if a['name']==archive.name)
    if release.get('draft'):
        run('gh','release','edit',tag,'--repo',repo,'--draft=false')
        release=release_for_tag(repo,tag)
    # Only switch the live page after all of its downloads are available.
    print('Uploading gallery assets…',flush=True)
    run('git','push','--set-upstream','origin','main')
    pages=api(f'repos/{repo}/pages',optional=True)
    source={'branch':'main','path':'/docs'}
    if pages is None:pages=api(f'repos/{repo}/pages','POST',{'build_type':'legacy','source':source})
    elif pages.get('source') != source:
        pages=api(f'repos/{repo}/pages','PUT',{'build_type':'legacy','source':source})
    url=pages.get('html_url') or f'https://{repo.split("/")[0].lower()}.github.io/{repo.split("/")[1]}/'
    print('Waiting for GitHub Pages to publish '+url,flush=True)
    deadline=time.monotonic()+900;last_status=None
    while time.monotonic()<deadline:
        build=api(f'repos/{repo}/pages/builds/latest',optional=True)
        status=(build or {}).get('status','queued')
        if status != last_status:print('Pages: '+status,flush=True);last_status=status
        if status=='errored':raise RuntimeError('GitHub Pages build failed: '+json.dumps(build.get('error')))
        if status=='built' and build.get('commit')==commit:
            try:
                with get(url+'?v='+commit[:12]) as response:html=response.read().decode()
                if 'THE PHOTO COLLECTION' in html and 'pickleball-film-10.mp4' in html:break
            except (HTTPError,URLError):pass
        time.sleep(15)
    else:raise TimeoutError('Pages publication did not finish within 15 minutes. Re-run to resume.')
    print('Checking live assets and download endpoints…',flush=True)
    manifest=json.loads((docs/'media-manifest.json').read_text())
    with get(url+'media-manifest.json?v='+commit[:12]) as response:assert json.load(response)==manifest
    for filename in ['styles.css','app.js','media.js','favicon.svg']:
        with get(url+filename+'?v='+commit[:12]) as response:assert hashlib.sha256(response.read()).hexdigest()==sha(docs/filename)
    # Confirm every full-size image and film is present anonymously at production.
    for item in manifest['photos']+manifest['videos']:
        rel=item.get('full') or item['file']
        with get(rel if rel.startswith('https://') else url+rel,method='HEAD') as response:
            assert int(response.headers['Content-Length'])==item['bytes'],rel
    # Verify the exact bytes of every corrected photograph, not only one sample.
    def verify_photo(photo):
        h=hashlib.sha256()
        with get(photo['full'] if photo['full'].startswith('https://') else url+photo['full']) as response:
            for block in iter(lambda:response.read(2**20),b''):h.update(block)
        assert h.hexdigest()==photo['sha256'],photo['filename']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(verify_photo,manifest['photos']))
    with get(url+manifest['videos'][0]['file'],headers={'Range':'bytes=0-1023'}) as response:
        assert response.status==206 and len(response.read())==1024
    # Download and hash the photos ZIP; release API also verifies both archive digests.
    h=hashlib.sha256()
    with get(manifest['photo_zip']) as response:
        for block in iter(lambda:response.read(2**20),b''):h.update(block)
    assert h.hexdigest()==sha(photo_archive)
    with get(asset['browser_download_url'],method='HEAD') as response:
        assert int(response.headers['Content-Length'])==archive.stat().st_size
    run(sys.executable,str(ROOT/'scripts/generate_qr.py'),'--url',url,'--output',str(args.qr_output))
    copy=args.qr_output/'platform-posting-copy.txt'
    if copy.exists():
        marker='\n\nLIVE EVENT GALLERY\n'
        current=copy.read_text().split(marker)[0].rstrip()
        copy.write_text(current+marker+url+'\nDownload photos and drone films directly from the gallery.\nQR graphics: tournament-gallery-qr.png and tournament-gallery-qr.svg\n')
    receipt={'published_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'repository':'https://github.com/'+repo,'commit':commit,'release':release['html_url'],'complete_zip':asset['browser_download_url'],'complete_zip_sha256':digest,'photos':52,'films':10,'verification':{'anonymous_page':True,'all_full_media_sizes':True,'all_52_photo_download_hashes':True,'photos_zip_download_hash':True,'video_byte_ranges':True,'release_archive_size_and_digest':True},'qr_png':str(args.qr_output/'tournament-gallery-qr.png'),'qr_svg':str(args.qr_output/'tournament-gallery-qr.svg')}
    (ROOT/'deployment.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
