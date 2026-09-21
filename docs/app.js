/* No framework, tracking, cookies or remote scripts. */
(() => {
  'use strict';
  const photos = window.GALLERY_DATA.photos;
  const dialog = document.querySelector('#lightbox');
  const image = document.querySelector('#lightbox-image');
  const stage = document.querySelector('#lightbox-stage');
  const status = document.querySelector('#image-status');
  const counter = document.querySelector('#lightbox-counter');
  const caption = document.querySelector('#lightbox-caption');
  const dimensions = document.querySelector('#lightbox-dimensions');
  const download = document.querySelector('#lightbox-download');
  const closeButton = document.querySelector('#close-lightbox');
  let selected = 0;
  let opener = null;
  let oldOverflow = '';
  let touch = null;
  let lastSwipe = 0;

  function showPhoto(index) {
    selected = (index + photos.length) % photos.length;
    const photo = photos[selected];
    stage.classList.add('is-loading');
    status.hidden = false;
    status.textContent = 'Loading photo…';
    counter.textContent = `PHOTO ${String(selected + 1).padStart(2, '0')} / ${photos.length}`;
    caption.textContent = photo.title;
    dimensions.textContent = `${photo.width.toLocaleString()} × ${photo.height.toLocaleString()} px · JPEG · ${(photo.bytes / 1e6).toFixed(1)} MB`;
    download.href = photo.full;
    download.download = photo.filename;
    download.setAttribute('aria-label', `Download photo ${selected + 1}: ${photo.title}`);
    image.alt = photo.alt;
    image.src = photo.full;
  }

  image.addEventListener('load', () => { stage.classList.remove('is-loading'); status.hidden = true; });
  image.addEventListener('error', () => { stage.classList.remove('is-loading'); status.hidden = false; status.textContent = 'This photo could not load. Try the download button or move to the next photo.'; });
  document.querySelectorAll('[data-photo-index]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || typeof dialog.showModal !== 'function') return;
      event.preventDefault();
      opener = link;
      oldOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      document.querySelectorAll('video').forEach(video => video.pause());
      showPhoto(Number(link.dataset.photoIndex));
      dialog.showModal();
      closeButton.focus();
    });
  });
  closeButton.addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { document.body.style.overflow = oldOverflow; if (opener) opener.focus({preventScroll: true}); });
  document.querySelector('#previous-photo').addEventListener('click', () => showPhoto(selected - 1));
  document.querySelector('#next-photo').addEventListener('click', () => showPhoto(selected + 1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowRight') { event.preventDefault(); showPhoto(selected + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); showPhoto(selected - 1); }
    if (event.key === 'Home') { event.preventDefault(); showPhoto(0); }
    if (event.key === 'End') { event.preventDefault(); showPhoto(photos.length - 1); }
  });
  stage.addEventListener('click', event => { if (event.target === stage && Date.now() - lastSwipe > 350) dialog.close(); });
  stage.addEventListener('touchstart', event => { if (event.touches.length === 1) touch = {x:event.touches[0].clientX,y:event.touches[0].clientY}; else touch = null; }, {passive:true});
  stage.addEventListener('touchend', event => {
    if (!touch || !event.changedTouches.length) return;
    const dx = event.changedTouches[0].clientX - touch.x;
    const dy = event.changedTouches[0].clientY - touch.y;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.4) { lastSwipe = Date.now(); showPhoto(selected + (dx < 0 ? 1 : -1)); }
    touch = null;
  }, {passive:true});

  document.querySelectorAll('video').forEach(video => {
    video.addEventListener('play', () => { document.querySelectorAll('video').forEach(other => {if (other !== video) other.pause();}); });
    video.addEventListener('error', () => {
      if (video.parentElement.querySelector('.film-error')) return;
      const message = document.createElement('p');
      message.className = 'film-error';
      message.textContent = 'Playback is unavailable. Use Download MP4 below to watch this film.';
      video.insertAdjacentElement('afterend', message);
    });
  });
})();
