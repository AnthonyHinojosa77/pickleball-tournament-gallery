#!/usr/bin/env python3
"""Publish a validated UI-only update to the existing Pages site; retain verified media and ZIPs."""
import datetime,hashlib,json,subprocess,time
from pathlib import Path
from urllib.request import urlopen,Request
from validate_presentation import validate
ROOT=Path(__file__).resolve().parents[1]
def run(*args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def api(endpoint):return json.loads(run('gh','api',endpoint))
def main():
    result=validate();cfg=json.loads((ROOT/'config.json').read_text());repo=cfg['repository']
    assert run('git','branch','--show-current')=='main'
    assert run('git','remote','get-url','origin')==f'https://github.com/{repo}.git'
    run('git','add','--','docs','scripts','index.template.html','config.json','README.md','.gitignore')
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
        print(run('git','commit','-m','Match tournament branding and add full-resolution pinch zoom'),flush=True)
    run('git','push','origin','main');commit=run('git','rev-parse','HEAD')
    print('Pushed '+commit,flush=True);url=api(f'repos/{repo}/pages')['html_url']
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        b=api(f'repos/{repo}/pages/builds/latest')
        if b['status']=='errored':raise RuntimeError(b.get('error'))
        if b['status']=='built' and b['commit']==commit:break
        time.sleep(15)
    else:raise TimeoutError('Pages build pending')
    paths=['index.html','styles.css','app.js','gallery-options.mjs','favicon.svg','brand/tournament-logo.jpg','vendor/photoswipe.css','vendor/photoswipe-lightbox.esm.min.js','vendor/photoswipe.esm.min.js','media-manifest.json']
    for name in paths:
        with urlopen(Request(url+name+'?v='+commit[:12],headers={'User-Agent':'GalleryVerifier/1.0'}),timeout=60) as response:data=response.read()
        assert hashlib.sha256(data).digest()==hashlib.sha256((ROOT/'docs'/name).read_bytes()).digest(),name
    receipt={'published_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'commit':commit,'verified_live_assets':paths,'validation':result,'media_and_zip_archives':'unchanged'}
    (ROOT/'presentation-deployment.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
