"""Deterministic, non-generative finishing of profile-corrected photographs.
Works from a preserved baseline, never from a previous output of this script.
"""
from pathlib import Path
import cv2, numpy as np, io
from PIL import Image, ImageCms, ImageOps, ImageFilter
ROOT=Path(__file__).resolve().parent
ICC=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
# Normalized, feathered subject regions identified from visual review.
REGIONS={
1:[(.49,.43,.43,.28)],7:[(.50,.42,.43,.25)],8:[(.52,.43,.43,.26)],
2:[(.535,.41,.115,.20)],23:[(.58,.11,.10,.09)],24:[(.49,.53,.09,.12)],25:[(.48,.26,.10,.16)],
32:[(.50,.38,.18,.12)],33:[(.51,.41,.18,.12)],34:[(.485,.46,.105,.14)],35:[(.48,.46,.11,.15)],
40:[(.53,.11,.15,.10)],41:[(.48,.16,.14,.14)],42:[],43:[(.32,.12,.13,.10),(.58,.24,.10,.08)],44:[(.31,.13,.13,.10),(.58,.23,.1,.08)],45:[(.20,.15,.14,.13),(.59,.28,.12,.10)],46:[(.21,.16,.15,.14),(.60,.28,.13,.10)],47:[(.47,.12,.15,.09),(.80,.16,.14,.1)],48:[(.33,.22,.3,.12)],49:[(.33,.38,.25,.09)],50:[(.32,.27,.21,.08)],51:[(.32,.27,.21,.08)],52:[(.39,.19,.25,.11)]}
DJ={2,23,24,25,32,33,34,35}
# Conservative corrections for frames already bright in the prior pass.
BRIGHT={15,16,17,18,19,20,21,22,26,27,28,30,31,36,37,38,39,40,41,42,43,44,45,46,47,48}

def render(im, ident, strength=1.0):
    im=ImageOps.exif_transpose(im)
    if im.info.get('icc_profile'):
        im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile'])),ImageCms.createProfile('sRGB'),outputMode='RGB')
    else: im=im.convert('RGB')
    rgb=np.asarray(im,dtype=np.float32)/255
    h,w=rgb.shape[:2]
    # Slight green cast reduction; keep the existing camera-profile hues.
    rgb[:,:,1]*=.988
    lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2Lab)
    l=lab[:,:,0]/100
    # Re-establish a black point and bright, open midtones; roll off whites.
    xx=np.array([0,.04,.10,.20,.35,.50,.65,.80,.92,1],np.float32)
    yy=np.array([0,.016,.058,.156,.335,.555,.735,.868,.954,1],np.float32)
    if ident in BRIGHT: yy=np.array([0,.012,.05,.14,.30,.505,.68,.825,.935,1],np.float32)
    mapped=np.interp(l,xx,yy).astype(np.float32)
    # Restrained adaptive contrast, blended rather than used as a full HDR map.
    small=cv2.resize((l*255).astype(np.uint8),(min(1400,w),max(1,round(h*min(1400,w)/w))),interpolation=cv2.INTER_AREA)
    clahe=cv2.createCLAHE(clipLimit=1.25,tileGridSize=(8,8)).apply(small).astype(np.float32)/255
    delta=cv2.resize(clahe-small.astype(np.float32)/255,(w,h),interpolation=cv2.INTER_LINEAR)
    mapped+=delta*.18*np.clip(l*5,0,1)*np.clip((1-l)*5,0,1)
    # Manually located broad subject regions, with Gaussian falloff and tonal protection.
    ys,xs=np.ogrid[0:1:complex(h),0:1:complex(w)];mask=np.zeros((h,w),np.float32)
    for cx,cy,rx,ry in REGIONS.get(ident,[]):
        region=np.exp(-2*((xs-cx)**2/rx**2+(ys-cy)**2/ry**2)).astype(np.float32)
        mask=np.maximum(mask,region)
    lift=.15 if ident in DJ else .10
    mapped+=lift*mask*np.clip(l/.18,0,1)*np.clip((.92-l)/.30,0,1)
    # Keep lit rafters from overwhelming court scenes; do not invent clipped detail.
    if ident not in DJ and ident not in {1,7,8,40,41,42,43,44,45,46,47}:
        top=np.clip((.40-ys)/.30,0,1).astype(np.float32)
        mapped-=.075*top*np.clip((l-.62)/.30,0,1)
    if ident in DJ:
        top=np.clip((.30-ys)/.25,0,1).astype(np.float32)
        mapped-=.05*top*np.clip((l-.70)/.22,0,1)
    # Local contrast in the subject, with native-scale sharpening kept separate.
    lout=np.clip(l+(mapped-l)*strength,0,1)
    lab[:,:,0]=lout*100
    chroma=np.sqrt(lab[:,:,1]**2+lab[:,:,2]**2)
    vibrance=1.10-.06*np.clip(chroma/65,0,1)
    # Blue courts and mask already carry strong chroma; protect them from excess.
    blue=(lab[:,:,2]<-8)&(lab[:,:,1]<28)
    vibrance[blue]=1.015
    lab[:,:,1]*=vibrance;lab[:,:,2]*=vibrance
    out=np.clip(cv2.cvtColor(lab,cv2.COLOR_Lab2RGB),0,1)
    # Fine detail enhancement only; this cannot recover defocus or motion blur.
    result=Image.fromarray(np.uint8(out*255+.5))
    result=result.filter(ImageFilter.UnsharpMask(radius=max(.65,min(1.25,w/6500)),percent=70,threshold=3))
    return result


SOURCE_PHOTO_IDS = {'DJI_20260919101351_0086_D.DNG': 1, 'DJ Lucha.DNG': 2, 'DJI_20260919093621_0084_D.DNG': 4, 'DJI_20260919101356_0087_D.DNG': 7, 'DJI_20260919101401_0088_D.DNG': 8, 'DJI_20260919113407_0090_D.DNG': 11, 'DJI_20260919113412_0091_D.DNG': 12, 'DJI_20260919113423_0092_D.DNG': 13, 'DJI_20260919113438_0093_D.DNG': 14, 'DJI_20260919113504_0094_D.DNG': 15, 'DJI_20260919113609_0096_D.DNG': 16, 'DJI_20260919113617_0097_D.DNG': 17, 'DJI_20260919113636_0099_D.DNG': 18, 'DJI_20260919113642_0100_D.DNG': 19, 'DJI_20260919113651_0101_D.DNG': 20, 'DJI_20260919113656_0102_D.DNG': 21, 'DJI_20260919113703_0103_D.DNG': 22, 'DJI_20260919113819_0105_D.DNG': 23, 'DJI_20260919114113_0107_D.DNG': 24, 'DJI_20260919114120_0108_D.DNG': 25, 'DJI_20260919133119_0110_D.DNG': 26, 'DJI_20260919133138_0111_D.DNG': 27, 'DJI_20260919133144_0112_D.DNG': 28, 'DJI_20260919133150_0113_D.DNG': 29, 'DJI_20260919133206_0114_D.DNG': 30, 'DJI_20260919133214_0115_D.DNG': 31, 'DJI_20260919133324_0117_D.DNG': 32, 'DJI_20260919133330_0118_D.DNG': 33, 'DJI_20260919133338_0119_D.DNG': 34, 'DJI_20260919133347_0120_D.DNG': 35, 'DJI_20260919133415_0122_D.DNG': 36, 'DJI_20260919133429_0123_D.DNG': 37, 'DJI_20260919133436_0124_D.DNG': 38, 'DJI_20260919133441_0125_D.DNG': 39, 'DJI_20260919154040_0126_D.DNG': 40, 'DJI_20260919154047_0127_D.DNG': 41, 'DJI_20260919154055_0128_D.DNG': 42, 'DJI_20260919154115_0129_D.DNG': 43, 'DJI_20260919154134_0130_D.DNG': 44, 'DJI_20260919154144_0131_D.DNG': 45, 'DJI_20260919154152_0132_D.DNG': 46, 'DJI_20260919154224_0133_D.DNG': 47, 'DJI_20260919154235_0134_D.DNG': 48, 'DJI_20260919154257_0135_D.DNG': 49, 'DJI_20260919154328_0136_D.DNG': 50, 'DJI_20260919154335_0137_D.DNG': 51, 'DJI_20260919154348_0138_D.DNG': 52}
