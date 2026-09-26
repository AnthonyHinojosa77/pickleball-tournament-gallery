const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const { slideData, zoomOptions } = await import('../docs/gallery-options.mjs');
  const { default: ZoomLevel } = await import('./vendor-zoom-level.mjs');
  const manifest = JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/media-manifest.json')));
  // Exercise PhotoSwipe's actual zoom calculation with all real image orientations
  // at small-phone, modern-phone and desktop sizes.
  for (const width of [320,390,430,1440]) {
    for (const photo of manifest.photos) {
      const data=slideData(photo);
      assert.equal(data.src,photo.full);
      assert.equal(data.width,photo.width);
      assert.equal(data.height,photo.height);
      const candidates=data.srcset.split(', ').map(s=>{const [url,w]=s.split(' ');return {url,width:Number(w.slice(0,-1))};});
      assert.equal(candidates.at(-1).url,photo.full);
      assert.equal(candidates.at(-1).width,photo.width);
      for (const c of candidates) {
        const file=c.url.startsWith('https://')
          ? path.join(__dirname,'../artifacts/photos',photo.filename)
          : path.join(__dirname,'../docs',c.url);
        if (c.url.startsWith('https://')) assert.equal(c.url,photo.full);
        assert.ok(fs.existsSync(file),'Missing responsive image: '+c.url);
      }
      for (let i=1;i<candidates.length;i++) assert.ok(candidates[i].width>candidates[i-1].width,'Responsive sources must increase, including portrait previews');
      const levels=new ZoomLevel(zoomOptions,data,0);
      levels.update(photo.width,photo.height,{x:width-16,y:614});
      assert.ok(levels.secondary>levels.initial,'Double tap must enlarge the photo');
      assert.equal(levels.max,1,'Pinch zoom must reach native image detail');
      assert.ok(levels.max>levels.secondary);
    }
  }
  assert.equal(zoomOptions.doubleTapAction,'zoom');
  assert.equal(zoomOptions.pinchToClose,false);
  assert.equal(zoomOptions.returnFocus,true);
  const html=fs.readFileSync(path.join(__dirname,'../docs/index.html'),'utf8');
  assert.ok(!/user-scalable\s*=\s*no|maximum-scale\s*=\s*1/.test(html));
  const app=fs.readFileSync(path.join(__dirname,'../docs/app.js'),'utf8');
  assert.ok(!app.includes("addEventListener('touchend'"),'Legacy swipe handler must not intercept pinch/pan gestures');
  console.log('52 photos × 4 viewport sizes: native zoom, double-tap levels, portrait srcsets and source paths passed.');
})().catch(error=>{console.error(error);process.exit(1)});
