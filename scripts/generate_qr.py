#!/usr/bin/env python3
"""Generate print-ready SVG/PNG QR codes for a confirmed HTTPS deployment URL."""
import argparse,json
from pathlib import Path
from urllib.parse import urlparse
import qrcode
import qrcode.image.svg

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    parsed=urlparse(args.url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.hostname in ['localhost','127.0.0.1']:raise ValueError('Provide a live HTTPS deployment URL')
    args.output.mkdir(parents=True,exist_ok=True)
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q,box_size=14,border=4);qr.add_data(args.url);qr.make(fit=True)
    png=args.output/'tournament-gallery-qr.png';svg=args.output/'tournament-gallery-qr.svg'
    qr.make_image(fill_color='black',back_color='white').convert('RGB').save(png,dpi=(300,300))
    qr.make_image(image_factory=qrcode.image.svg.SvgPathFillImage).save(svg)
    (args.output/'deployment-url.txt').write_text(args.url+'\n')
    print(json.dumps({'url':args.url,'png':str(png),'svg':str(svg)},indent=2))
if __name__=='__main__':main()
