from PIL import Image,ImageFilter,ImageOps
import numpy as np
def sticker(name,h,side,flip=False,ow=10):
    im=Image.open(f'cut/{name}.png').convert('RGBA')
    src=Image.open(f'gb/{name}.jpg')
    # detect which edges touch original image border via bbox from cutout saved size vs original
    al=np.array(im.getchannel('A'))
    # clean faint alpha
    al=np.where(al>40,al,0).astype(np.uint8); im.putalpha(Image.fromarray(al))
    if flip: im=ImageOps.mirror(im)
    s=h/im.height; im=im.resize((int(im.width*s),h),Image.LANCZOS)
    a=im.getchannel('A')
    pad=ow*2
    big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>60 else 0)
    o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    white=Image.new('RGBA',big.size,(255,255,255,0)); white.putalpha(o)
    sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out=Image.new('RGBA',big.size,(0,0,0,0)); out.alpha_composite(sh,(6,10)) if False else out.alpha_composite(sh)
    out.alpha_composite(white); out.alpha_composite(big)
    # crop padding on bottom so it sits flush; and on the screen-edge side
    w_,h_=out.size
    box=[0,0,w_,h_-pad]
    if side=='L': box[0]=pad
    else: box[2]=w_-pad
    return out.crop(tuple(box))
