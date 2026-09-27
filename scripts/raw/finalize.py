#!/usr/bin/env python3
"""Finish one RawTherapee 16-bit TIFF: 75% area downscale, light output sharpening, sRGB JPEG with camera EXIF (GPS removed).

The drone's 50 MP quad-Bayer sensor resolves far less than 8192 px of real detail; delivering at 75% keeps
full-zoom views crisp instead of upscaling softness. Usage: finalize.py developed.tif source.DNG output.jpg
"""
import subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageCms, ImageFilter

tif, dng, dst = sys.argv[1:4]
rgb = cv2.imread(tif, cv2.IMREAD_UNCHANGED)[:, :, ::-1].astype(np.float32) / 65535
h, w = rgb.shape[:2]
small = cv2.resize(rgb, (round(w * .75), round(h * .75)), interpolation=cv2.INTER_AREA)
im = Image.fromarray(np.clip(small * 255 + .5, 0, 255).astype(np.uint8))
im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=95, threshold=3))
icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
im.save(dst, quality=95, subsampling=0, icc_profile=icc, optimize=True)
subprocess.run(['exiftool', '-q', '-q', '-overwrite_original', '-TagsFromFile', dng, '-EXIF:all', '-GPS:all=', '-Orientation=',
                '-ThumbnailImage=', '-PreviewImage=', '-Software=RawTherapee 5.10 + Pillow', dst], check=True)
