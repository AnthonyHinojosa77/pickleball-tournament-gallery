#!/usr/bin/env python3
"""Finish one RawTherapee 16-bit TIFF: per-photo crop and neutral-cast correction (adjustments.json), 75% area
downscale, output sharpening, sRGB JPEG with camera EXIF (GPS removed).

The drone's 50 MP quad-Bayer sensor resolves far less than 8192 px of real detail; delivering at 75% keeps
full-zoom views crisp instead of upscaling softness. Usage: finalize.py developed.tif source.DNG output.jpg
"""
import json, subprocess, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageCms, ImageFilter

tif, dng, dst = sys.argv[1:4]
adj = json.loads((Path(__file__).with_name('adjustments.json')).read_text())
stem = Path(dng).stem
rgb = cv2.imread(tif, cv2.IMREAD_UNCHANGED)[:, :, ::-1].astype(np.float32) / 65535
h, w = rgb.shape[:2]
left, top, right, bottom = adj['crop'].get(stem, [0, 0, 0, 0])
rgb = rgb[round(top * h):h - round(bottom * h), round(left * w):w - round(right * w)]
# The venue's white walls, grey court surround and white paint are neutral: measure their average tint and
# remove most of it in linear light, so every photo shares the same true-neutral colour balance.
lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
small = lin[::8, ::8]; enc = rgb[::8, ::8]
luma = enc @ np.array([.2126, .7152, .0722], np.float32)
neutral = ((enc.max(2) - enc.min(2)) < 0.08) & (luma > 0.25) & (luma < 0.8)
if neutral.sum() > 2000:
    mean = small[neutral].mean(0); gains = (mean.mean() / mean) ** adj['neutral_correction']
    lin = np.clip(lin * gains, 0, 1)
rgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
h, w = rgb.shape[:2]
small = cv2.resize(rgb, (round(w * .75), round(h * .75)), interpolation=cv2.INTER_AREA)
im = Image.fromarray(np.clip(small * 255 + .5, 0, 255).astype(np.uint8))
im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=95, threshold=3))
icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
im.save(dst, quality=95, subsampling=0, icc_profile=icc, optimize=True)
subprocess.run(['exiftool', '-q', '-q', '-overwrite_original', '-TagsFromFile', dng, '-EXIF:all', '-GPS:all=', '-Orientation=',
                '-ThumbnailImage=', '-PreviewImage=', '-Software=RawTherapee 5.10 + Pillow', dst], check=True)
