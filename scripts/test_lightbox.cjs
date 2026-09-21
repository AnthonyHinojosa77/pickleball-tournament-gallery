/* Focused interaction tests using lightweight event doubles; no browser required. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
class Element {
  constructor() { this.events={}; this.dataset={}; this.classList={add(){},remove(){}}; this.style={}; }
  addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
  fire(name, extra={}) { const event={preventDefault(){this.prevented=true},target:this,...extra}; for (const fn of this.events[name]||[]) fn(event); return event; }
  setAttribute(name,value) { this[name]=value; }
  focus() { this.focused=true; }
  pause() { this.paused=true; }
  showModal() { this.open=true; }
  close() { this.open=false; this.fire('close'); }
}
const selectors = ['lightbox','lightbox-image','lightbox-stage','image-status','lightbox-counter','lightbox-caption','lightbox-dimensions','lightbox-download','close-lightbox','previous-photo','next-photo'];
const elements = Object.fromEntries(selectors.map(s=>['#'+s,new Element()]));
const links = [0,1,2].map(i=>Object.assign(new Element(),{dataset:{photoIndex:String(i)}}));
const videos = [new Element(),new Element()];
const body = {style:{overflow:'auto'}};
const photos = [0,1,2].map(i=>({title:'Photo '+i,alt:'Alt '+i,width:3600,height:2400,bytes:1e6,full:'photo-'+i+'.jpg',filename:'photo-'+i+'.jpg'}));
const document = {body,querySelector:s=>elements[s],querySelectorAll:s=>s==='video'?videos:links};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../docs/app.js'),'utf8'),{document,window:{GALLERY_DATA:{photos}},Date});
const dialog=elements['#lightbox'],image=elements['#lightbox-image'];
assert.equal(links[0].fire('click',{ctrlKey:true}).prevented,undefined);
assert.equal(dialog.open,undefined);
assert.equal(links[0].fire('click').prevented,true);
assert.equal(dialog.open,true); assert.equal(body.style.overflow,'hidden');
assert.equal(image.src,'photo-0.jpg'); assert.equal(elements['#close-lightbox'].focused,true);
assert.ok(videos.every(v=>v.paused));
elements['#previous-photo'].fire('click'); assert.equal(image.src,'photo-2.jpg');
elements['#next-photo'].fire('click'); assert.equal(image.src,'photo-0.jpg');
dialog.fire('keydown',{key:'ArrowRight'}); assert.equal(image.src,'photo-1.jpg');
dialog.fire('keydown',{key:'End'}); assert.equal(image.src,'photo-2.jpg');
dialog.fire('keydown',{key:'Home'}); assert.equal(image.src,'photo-0.jpg');
const stage=elements['#lightbox-stage'];
stage.fire('touchstart',{touches:[{clientX:250,clientY:50}]});
stage.fire('touchend',{changedTouches:[{clientX:50,clientY:60}]}); assert.equal(image.src,'photo-1.jpg');
assert.equal(elements['#lightbox-download'].download,'photo-1.jpg');
image.fire('load'); assert.equal(elements['#image-status'].hidden,true);
image.fire('error'); assert.equal(elements['#image-status'].hidden,false);
elements['#close-lightbox'].fire('click'); assert.equal(dialog.open,false);
assert.equal(body.style.overflow,'auto'); assert.equal(links[0].focused,true);
videos[1].paused=false; videos[0].fire('play'); assert.equal(videos[1].paused,true);
console.log('Lightbox navigation, touch, loading/error, downloads, focus restoration and exclusive playback: passed.');
