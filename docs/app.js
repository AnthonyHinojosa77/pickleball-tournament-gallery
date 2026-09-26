import PhotoSwipeLightbox from './vendor/photoswipe-lightbox.esm.min.js';
import { slideData, zoomOptions } from './gallery-options.mjs';

const photos = window.GALLERY_DATA.photos;
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
      const download = document.createElement('a'); download.className = 'pswp__download'; download.textContent = 'Download JPEG ↓';
      copy.append(title, detail, original); el.append(copy, download);
      instance.on('change', () => {
        const p = photos[instance.currIndex];
        title.textContent = p.title;
        detail.textContent = p.width.toLocaleString() + ' × ' + p.height.toLocaleString() + ' px · ' + (p.bytes/1e6).toFixed(1) + ' MB';
        original.href = p.full; original.setAttribute('aria-label', 'Open original photo ' + (instance.currIndex+1) + ' in a new tab');
        download.href = p.full; download.download = p.filename;
        download.setAttribute('aria-label', 'Download photo ' + (instance.currIndex+1) + ': ' + p.title);
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
