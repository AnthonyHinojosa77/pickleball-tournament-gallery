import PhotoSwipeLightbox from './vendor/photoswipe-lightbox.esm.min.js';
import { slideData, zoomOptions } from './gallery-options.mjs';

const photos = window.GALLERY_DATA.photos;

// On phones that can share files (iPhone Safari/Chrome), "Save photo" hands the JPEG to the share sheet,
// whose "Save Image" puts it straight into Photos. Elsewhere the links stay ordinary same-site downloads.
const shareFiles = (() => {
  try { return matchMedia('(pointer: coarse)').matches && !!navigator.canShare && navigator.canShare({ files: [new File([''], 'x.jpg', { type: 'image/jpeg' })] }); }
  catch { return false; }
})();
const blobs = new Map();
const fetchPhoto = p => {
  if (!blobs.has(p.full)) {
    if (blobs.size >= 3) blobs.delete(blobs.keys().next().value);
    blobs.set(p.full, fetch(p.full).then(r => { if (!r.ok) throw new Error(r.status); return r.blob(); })
      .catch(error => { blobs.delete(p.full); throw error; }));
  }
  return blobs.get(p.full);
};
const toast = text => {
  let el = document.querySelector('.save-toast');
  if (!el) { el = document.createElement('div'); el.className = 'save-toast'; el.setAttribute('role', 'status'); document.body.append(el); }
  el.textContent = text; el.classList.add('is-visible');
  clearTimeout(el.timer); el.timer = setTimeout(() => el.classList.remove('is-visible'), 2600);
};
const download = p => { const a = document.createElement('a'); a.href = p.full; a.download = p.filename; document.body.append(a); a.click(); a.remove(); };
async function savePhoto(event, p) {
  if (!shareFiles) return;
  event.preventDefault();
  let blob;
  try { blob = await fetchPhoto(p); } catch { download(p); return; }
  try { await navigator.share({ files: [new File([blob], p.filename, { type: 'image/jpeg' })] }); }
  catch (error) {
    if (error.name === 'AbortError') return;
    // The share sheet needs a fresh tap if the photo took a moment to load; it is ready now.
    if (error.name === 'NotAllowedError') toast('Photo ready — tap Save again');
    else download(p);
  }
}
document.querySelectorAll('#photo-wall .tile-download').forEach(link => {
  const p = photos[Number(link.closest('.photo-card').querySelector('.photo-open').dataset.photoIndex)];
  if (shareFiles) { link.querySelector('span').textContent = 'Save'; link.setAttribute('aria-label', 'Save photo ' + p.id + ' to your phone'); }
  link.addEventListener('click', event => savePhoto(event, p));
});
const lightbox = new PhotoSwipeLightbox({
  gallery: '#photo-wall',
  children: '.photo-open',
  ...zoomOptions,
  bgOpacity: 1,
  zoom: false,
  showHideAnimationType: 'fade',
  showAnimationDuration: 150,
  hideAnimationDuration: 150,
  paddingFn: viewport => ({
    top: viewport.x < 760 ? 100 : 85,
    bottom: viewport.x < 760 ? 130 : 115,
    left: viewport.x < 760 ? 8 : 64,
    right: viewport.x < 760 ? 8 : 64
  }),
  pswpModule: () => import('./vendor/photoswipe.esm.min.js')
});
lightbox.addFilter('itemData', (item, index) => ({ ...item, ...slideData(photos[index]) }));
let opener = null;
document.querySelector('#photo-wall').addEventListener('click', event => {
  opener = event.target.closest('.photo-open') || opener;
}, true);
lightbox.on('beforeOpen', () => document.querySelectorAll('video').forEach(video => video.pause()));
lightbox.on('destroy', () => opener?.focus({ preventScroll: true }));
lightbox.on('uiRegister', () => {
  const pswp = lightbox.pswp;
  const changeZoom = factor => {
    const slide = pswp.currSlide;
    if (!slide) return;
    pswp.zoomTo(Math.max(slide.zoomLevels.fit, Math.min(slide.zoomLevels.max, slide.currZoomLevel * factor)), undefined, 180);
  };
  pswp.ui.registerElement({name:'zoom-out',order:8,isButton:true,ariaLabel:'Zoom out',title:'Zoom out',html:'−',onClick:() => changeZoom(1/1.6)});
  pswp.ui.registerElement({name:'zoom-in',order:9,isButton:true,ariaLabel:'Zoom in',title:'Zoom in',html:'+',onClick:() => changeZoom(1.6)});
  pswp.ui.registerElement({name:'fit',order:11,isButton:true,ariaLabel:'Fit photo to screen',title:'Fit photo to screen',html:'Fit',onClick:() => {
    if (pswp.currSlide) pswp.zoomTo(pswp.currSlide.zoomLevels.fit, undefined, 180);
  }});
  pswp.ui.registerElement({
    name:'zoom-hint',appendTo:'root',html:'Pinch or double-tap to zoom · drag to explore',
    onInit: el => el.setAttribute('aria-hidden','true')
  });
  pswp.ui.registerElement({
    name:'caption-bar',appendTo:'root',
    onInit: (el, instance) => {
      const copy = document.createElement('div'); copy.className = 'pswp__caption-copy';
      const title = document.createElement('strong');
      const detail = document.createElement('small');
      const original = document.createElement('a'); original.className = 'pswp__original';
      original.textContent = 'Open original ↗'; original.target = '_blank'; original.rel = 'noopener';
      const save = document.createElement('a'); save.className = 'pswp__download'; save.textContent = shareFiles ? 'Save photo ↓' : 'Download JPEG ↓';
      save.addEventListener('click', event => savePhoto(event, photos[instance.currIndex]));
      copy.append(title, detail, original); el.append(copy, save);
      instance.on('change', () => {
        const p = photos[instance.currIndex];
        title.textContent = p.title;
        detail.textContent = p.width.toLocaleString() + ' × ' + p.height.toLocaleString() + ' px · ' + (p.bytes/1e6).toFixed(1) + ' MB';
        original.href = p.full; original.setAttribute('aria-label', 'Open original photo ' + (instance.currIndex+1) + ' in a new tab');
        save.href = p.full; save.download = p.filename;
        save.setAttribute('aria-label', (shareFiles ? 'Save photo ' : 'Download photo ') + (instance.currIndex+1) + ': ' + p.title);
        if (shareFiles) fetchPhoto(p).catch(() => {});  // warm the file so Save opens the share sheet instantly
      });
    }
  });
});
lightbox.on('afterInit', () => lightbox.pswp.element.setAttribute('aria-label', 'Full-screen photo viewer'));
lightbox.on('openingAnimationEnd', () => lightbox.pswp.element.querySelector('.pswp__button--close')?.focus());
lightbox.init();

document.querySelectorAll('video').forEach(video => {
  video.addEventListener('play', () => document.querySelectorAll('video').forEach(other => { if (other !== video) other.pause(); }));
  video.addEventListener('error', () => {
    if (video.parentElement.querySelector('.film-error')) return;
    const message = document.createElement('p');
    message.className = 'film-error';
    message.textContent = 'Playback is unavailable. Use Download MP4 below to watch this film.';
    video.insertAdjacentElement('afterend', message);
  });
});
