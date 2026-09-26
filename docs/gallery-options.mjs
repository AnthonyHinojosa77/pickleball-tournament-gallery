export function slideData(photo) {
  const displayWidth = Math.round(photo.width * Math.min(1, 2048 / Math.max(photo.width, photo.height)));
  const candidates = [
    [photo.preview, Math.min(960, photo.width)],
    [photo.display, displayWidth],
    [photo.full, photo.width]
  ].filter(([url]) => Boolean(url));
  return {
    src: photo.full,
    srcset: candidates.map(([url, width]) => url + ' ' + width + 'w').join(', '),
    msrc: photo.preview,
    width: photo.width,
    height: photo.height,
    alt: photo.alt,
    title: photo.title,
    filename: photo.filename,
    bytes: photo.bytes
  };
}
export const zoomOptions = {
  initialZoomLevel: 'fit',
  secondaryZoomLevel: zoom => Math.min(1, zoom.fit * 3),
  maxZoomLevel: 1,
  pinchToClose: false,
  closeOnVerticalDrag: false,
  doubleTapAction: 'zoom',
  imageClickAction: 'zoom',
  tapAction: false,
  wheelToZoom: true,
  preload: [0, 1],
  returnFocus: true,
  trapFocus: true
};
