import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy import ndimage as nd
def load(src,box): return np.asarray(Image.open(f'gb/{src}.jpg').convert('RGB').crop(box)).astype(int)
def finish(a,m,name,close=3,keep=1):
    m=nd.binary_closing(m,iterations=close); m=nd.binary_fill_holes(m); m=nd.binary_opening(m,iterations=1)
    lab,n=nd.label(m); 
    if n:
        sizes=nd.sum(m,lab,range(1,n+1)); order=np.argsort(sizes)[::-1][:keep]
        m=np.isin(lab,[o+1 for o in order])
    al=Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    im=Image.fromarray(a.astype(np.uint8)); im.putalpha(al); bb=al.getbbox(); im=im.crop(bb); im.save(f'cut/c_{name}.png'); return im
def lum(a): return a[...,0]*.3+a[...,1]*.59+a[...,2]*.11
# susuwatari: dark blobs
a=load('chihiro014',(170,190,450,480)); finish(a,(lum(a)<45)|((lum(a)>150)),'susu',close=3)
a=load('chihiro014',(420,690,710,1010)); finish(a,(lum(a)<45)|((lum(a)>150)),'susu2',close=3)
# kodama: bright
a=load('mononoke023',(1090,600,1310,890)); finish(a,lum(a)>120,'kodama',close=2)
a=load('mononoke023',(380,40,560,330)); finish(a,lum(a)>120,'kodama2',close=2)
# chibi totoro white
a=load('totoro019',(950,470,1170,810)); finish(a,(lum(a)>150)&(np.abs(a[...,0]-a[...,2])<40),'chibitotoro',close=3)
# calcifer: bright warm
a=load('howl012',(560,150,1360,900)); finish(a,(a[...,0]>200)&(lum(a)>130),'calcifer',close=5)
# haedori/mouse from model cut, remove teal
from PIL import Image as I
im=np.asarray(I.open('cut/c_haedori.png').convert('RGBA')).astype(int)
teal=(im[...,1]>im[...,0]+12)&(im[...,2]>im[...,0]+5)
m=(im[...,3]>60)&~teal; finish(im[...,:3],m,'haedori',close=2)
im=np.asarray(I.open('cut/c_teto.png').convert('RGBA')).astype(int)
blue=(im[...,2]>im[...,0]+15)
m=(im[...,3]>60)&~blue; finish(im[...,:3],m,'teto',close=2)
T=260; names=['susu','susu2','kodama','kodama2','chibitotoro','calcifer','haedori','teto']
mm=Image.new('RGB',(4*(T+10),2*(T+30)),'white'); d=ImageDraw.Draw(mm)
for k,nm in enumerate(names):
    r=Image.open(f'cut/c_{nm}.png'); r.thumbnail((T,T)); bg=Image.new('RGBA',(T,T),(240,236,225,255)); bg.alpha_composite(r,((T-r.width)//2,(T-r.height)//2))
    x=(k%4)*(T+10); y=(k//4)*(T+30); mm.paste(bg.convert('RGB'),(x,y)); d.text((x+4,y+T+6),nm,fill='black')
mm.save('crt_sheet2.jpg')
