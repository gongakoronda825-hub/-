import math,subprocess,sys
from PIL import Image,ImageDraw,ImageFilter
exec(open('otona.py').read().split('# ---- build static layers ----')[0])
G='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/gb/'
OUT='/home/user/-/ghibli-otona/'
def load(n): return Image.open(G+n+'.jpg').convert('RGB')
def cover(im,w,h,fx=0.5,fy=0.5,zoom=1.0):
    s=max(w/im.width,h/im.height)*zoom; nw,nh=int(im.width*s),int(im.height*s)
    r=im.resize((nw,nh),Image.LANCZOS)
    x=int((nw-w)*fx); y=int((nh-h)*fy); return r.crop((x,y,x+w,y+h))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
IW,IH=880,495
DX=40
films=[('kiki','魔女の宅急便',('majo024',.5),['ほうきで飛びたかった'],('majo039',.45),['13歳で知らない街に','一人で住んだキキ、強すぎる']),
('chihiro','千と千尋の神隠し',('chihiro011',.5),['湯屋がこわかった'],('chihiro024',.5),['10歳で働いて、','名前を守り抜いた千尋']),
('totoro','となりのトトロ',('totoro044',.5),['ネコバスに乗りたかった'],('totoro039',.55),['お母さんの入院中、','妹を守ってたサツキ']),
('howl','ハウルの動く城',('howl014',.5),['ハウルかっこいい'],('howl001',.6),['自分に自信がない','ソフィーの気持ち、わかる'])]
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def put(frame,L,t0,t,dur=0.45,dy=40,out=None):
    a=ease((t-t0)/dur)
    if out is not None: a*=1-ease((t-out)/0.3)
    if a<=0: return
    l=L if a>=1 else L.copy()
    if a<1:
        al=l.getchannel('A').point(lambda v:int(v*a)); l.putalpha(al)
    frame.alpha_composite(l,(0,int(dy*(1-a))))


# prebuild zoom frames lazily via cache of source resized larger
SRC={}
def panel(name,fx,t,dur=6.0):
    # Ken Burns: zoom 1.0 -> 1.08
    im=SRC.setdefault(name,load(name))
    z=1.0+0.08*min(1,max(0,t/dur))
    return cover(im,IW,IH,fx,0.5,z)
def caption_band(lines_,label,acc,adult):
    L=Image.new('RGBA',(IW,IH),(0,0,0,0)); d=ImageDraw.Draw(L)
    n=len(lines_); bh=70+n*72
    g=Image.new('L',(1,bh)); 
    for y in range(bh): g.putpixel((0,y),int(200*min(1,(y/bh)*1.6)))
    shade=Image.new('RGBA',(IW,bh),(0,0,0,255)); shade.putalpha(g.resize((IW,bh)))
    L.alpha_composite(shade,(0,IH-bh))
    fp=fonts(900,52 if adult else 54)
    for k,t in enumerate(lines_):
        tdraw(d,IW/2,IH-bh+60+k*72+(10 if n==1 else 0),t,fp,WHITE)
    lab=Image.new('RGBA',(IW,IH),(0,0,0,0)); pill(lab,150,50,label,32,acc if adult else (120,110,100),WHITE,26)
    # pill draws centered at W-based? pill uses given cx
    L.alpha_composite(lab)
    return L
CAP={}
for key,title,(k1,f1),kt,(a1,f2),at in films:
    acc=PAL[key][2]
    CAP[key]=(caption_band(kt,'子どもの頃',acc,False),caption_band(at,'大人になって',acc,True))
TITLE={}
for n,(key,title,*_) in enumerate(films):
    T=layer(); pill(T,W/2,280,title,48,PAL[key][2],WHITE,44)
    d=ImageDraw.Draw(T)
    for k in range(4):
        cx=W/2+(k-1.5)*44; d.ellipse((cx-10,1455-10,cx+10,1455+10),fill=PAL[key][2] if k==n else (205,205,205))
    TITLE[key]=T
def framed(img,cap,a):
    """img RGB IWxIH + caption -> RGBA with white border, rounded, shadow"""
    c=img.convert('RGBA'); c.alpha_composite(cap)
    pad=12; R=Image.new('RGBA',(IW+2*pad+30,IH+2*pad+30),(0,0,0,0))
    sh=Image.new('L',R.size,0); ImageDraw.Draw(sh).rounded_rectangle((15,24,15+IW+2*pad,24+IH+2*pad),40,fill=int(90*a)); sh=sh.filter(ImageFilter.GaussianBlur(10))
    R.paste((0,0,0,255),(0,0),sh)
    wb=Image.new('RGBA',(IW+2*pad,IH+2*pad),(255,255,255,255)); R.alpha_composite(wb,(15,15)) if False else None
    m=rmask(IW+2*pad,IH+2*pad,40); white=Image.new('RGBA',(IW+2*pad,IH+2*pad),(255,255,255,255)); white.putalpha(m)
    R.alpha_composite(white,(15,15))
    c.putalpha(rmask(IW,IH,30)); R.alpha_composite(c,(15+pad,15+pad))
    if a<1: R.putalpha(R.getchannel('A').point(lambda v:int(v*a)))
    return R
# hook / cta assets
hookimg=load('totoro029')
def hook_frame(t):
    z=1.0+0.06*t/2
    bg=cover(hookimg,W,H,0.42,0.5,z).filter(ImageFilter.GaussianBlur(0)).convert('RGBA')
    dark=Image.new('RGBA',(W,H),(0,0,0,110)); bg.alpha_composite(dark)
    L=layer(); lines(L,700,['大人になって','ジブリ見たら、'],96,WHITE,stroke=0)
    L2=layer(); lines(L2,960,['泣く場所が','変わってた'],124,(255,226,120))
    C=layer(); put(C,L,0.0,t,dur=0.3,out=1.75); put(C,L2,0.4,t,dur=0.35,out=1.75)
    bg.alpha_composite(C.crop((DX,0,W,H)),(0,0)); return bg
cta_imgs=[load('majo001'),load('chihiro050'),load('totoro041'),load('howl048')]
CW,CH=410,231
ctagrid=layer()
for k,im in enumerate(cta_imgs):
    c=cover(im,CW,CH).convert('RGBA'); c.putalpha(rmask(CW,CH,24))
    x=W/2-CW-14+(k%2)*(CW+28); y=330+(k//2)*(CH+28)
    wb=Image.new('RGBA',(CW+16,CH+16),(255,255,255,0)); m=rmask(CW+16,CH+16,30); wb=Image.new('RGBA',(CW+16,CH+16),(255,255,255,255)); wb.putalpha(m)
    ctagrid.alpha_composite(wb,(int(x-8),int(y-8))); ctagrid.alpha_composite(c,(int(x),int(y)))
cta1=layer(); lines(cta1,1010,['あなたが大人になって','変わった作品は？'],80,DARK,stroke=12,gap=1.3)
cta2=layer(); d=ImageDraw.Draw(cta2); acc=PAL['cta'][2]
cx,cy=W/2-250,1230
d.rounded_rectangle((cx-62,cy-46,cx+62,cy+40),30,fill=acc); d.polygon([(cx-22,cy+34),(cx-40,cy+70),(cx+4,cy+38)],fill=acc)
for k in (-30,0,30): d.ellipse((cx+k-9,cy-9,cx+k+9,cy+9),fill=WHITE)
pill(cta2,W/2+60,1225,'コメントで教えてね',50,acc,WHITE,44)
credit=layer(); dd=ImageDraw.Draw(credit); tdraw(dd,W/2,1482,'© Studio Ghibli',fonts(800,26),(120,112,104))

def shiftL(fr,bgimg):
    # move whole content DX px left, keeping background unshifted
    c=Image.new('RGBA',(W,H),(0,0,0,0)); c.alpha_composite(fr.crop((DX,0,W,H)),(0,0))
    out=bgimg.convert('RGBA'); out.alpha_composite(c); return out
def render(t):
    if t<2: return hook_frame(t).convert('RGB')
    if t<26:
        i=int((t-2)//6); ts=(t-2)-i*6; key,title,(k1,f1),kt,(a1,f2),at=films[i]
        prev='hook' if i==0 else films[i-1][0]
        bgi=background(t,key if ts>0.4 else prev,None if ts>0.4 else key,0 if ts>0.4 else ease(ts/0.4)).convert('RGBA'); fr=layer()
        o=5.7
        put(fr,TITLE[key],0.05,ts,out=o)
        a=ease((ts-0.15)/0.45)*(1-ease((ts-o)/0.3))
        if a>0:
            P=framed(panel(k1,f1,ts),CAP[key][0],a); fr.alpha_composite(P,(int(W/2-P.width/2),int(330+40*(1-a))))
        b=ease((ts-2.0)/0.45)*(1-ease((ts-o)/0.3))
        if b>0:
            P=framed(panel(a1,f2,max(0,ts-2.0),4.0),CAP[key][1],b); fr.alpha_composite(P,(int(W/2-P.width/2),int(880+60*(1-b))))
        put(fr,credit,0.2,ts,out=o)
        bgi.alpha_composite(fr.crop((DX,0,W,H)),(0,0)); return bgi.convert('RGB')
    ts=t-26
    bgi=background(t,'cta' if ts>0.4 else films[-1][0],None if ts>0.4 else 'cta',0 if ts>0.4 else ease(ts/0.4)).convert('RGBA'); fr=layer()
    put(fr,ctagrid,0.1,ts); put(fr,cta1,0.6,ts); put(fr,cta2,1.1,ts); put(fr,credit,0.1,ts)
    bgi.alpha_composite(fr.crop((DX,0,W,H)),(0,0)); return bgi.convert('RGB')

if len(sys.argv)>1 and sys.argv[1]=='stills':
    for t in [1.5,6.5,12.5,18.5,24.5,29]:
        render(t).save(OUT+f'still_{t:05.1f}.png')
    sys.exit()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart',OUT+'ghibli_otona_v2.mp4'],stdin=subprocess.PIPE)
for n in range(FPS*DUR): p.stdin.write(render(n/FPS).tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode)
