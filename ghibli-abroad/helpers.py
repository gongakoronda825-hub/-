import json,os,math,random
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
W,H=1080,1920; S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
OUT='/home/user/-/ghibli-abroad/'
F=S+'fonts/'
def fm(sz,b=True): return ImageFont.truetype(F+('ZenOldMincho-Bold.ttf' if b else 'ZenOldMincho-Regular.ttf'),sz)
def fi(sz,wg=500):
    f=ImageFont.truetype(F+'CormorantGaramond-Italic[wght].ttf',sz)
    try: f.set_variation_by_axes([wg])
    except Exception: pass
    return f
def fs(sz): return ImageFont.truetype(F+'GreatVibes-Regular.ttf',sz)
CREAM=(246,240,231); INK=(62,48,42); SUB=(128,110,98); ACC=(196,122,92); LINE=(214,200,184)
random.seed(3)
def paper():
    im=Image.new('RGB',(W,H),CREAM)
    n=Image.effect_noise((W,H),18).convert('L').filter(ImageFilter.GaussianBlur(0.6))
    im=Image.blend(im,Image.merge('RGB',(n,n,n)),0.035)
    return im.convert('RGBA')
def ctext(d,xy,t,f,fill,anchor='mm',sp=0):
    if not sp: d.text(xy,t,font=f,fill=fill,anchor=anchor); return
    w=sum(f.getlength(c) for c in t)+sp*(len(t)-1); x=xy[0]-w/2 if anchor[0]=='m' else xy[0]
    for c in t: d.text((x,xy[1]),c,font=f,fill=fill,anchor='l'+anchor[1]); x+=f.getlength(c)+sp
def cover(img,w,h,fx=0.5,fy=0.5):
    s=max(w/img.width,h/img.height); im=img.resize((math.ceil(img.width*s),math.ceil(img.height*s)),Image.LANCZOS)
    x=int((im.width-w)*fx); y=int((im.height-h)*fy); return im.crop((x,y,x+w,y+h))
def shadow(L,box_img,xy,blur=18,off=(0,14),alpha=70):
    a=box_img.getchannel('A'); sh=Image.new('RGBA',box_img.size,(60,40,30,0)); sh.putalpha(a.point(lambda v:v*alpha//255))
    pad=blur*3; big=Image.new('RGBA',(box_img.width+2*pad,box_img.height+2*pad),(0,0,0,0)); big.alpha_composite(sh,(pad,pad))
    big=big.filter(ImageFilter.GaussianBlur(blur)); L.alpha_composite(big,(xy[0]-pad+off[0],xy[1]-pad+off[1]))
def arch(img,w,h,border=14,fx=0.5,fy=0.5):
    ph=cover(img,w,h,fx,fy).convert('RGBA')
    m=Image.new('L',(w,h),0); d=ImageDraw.Draw(m); r=w//2
    d.ellipse((0,0,w,w),fill=255); d.rectangle((0,r,w,h),fill=255)
    ph.putalpha(m)
    o=Image.new('RGBA',(w+2*border,h+2*border),(0,0,0,0)); mm=Image.new('L',o.size,0); dd=ImageDraw.Draw(mm)
    R=o.width//2; dd.ellipse((0,0,o.width,o.width),fill=255); dd.rectangle((0,R,o.width,o.height),fill=255)
    wb=Image.new('RGBA',o.size,(255,253,249,255)); wb.putalpha(mm); o.alpha_composite(wb); o.alpha_composite(ph,(border,border))
    return o
def stamp(img,w,h,rot=0,fx=0.5,fy=0.5):
    pad=18; r=7; sw,sh=w+2*pad,h+2*pad
    o=Image.new('RGBA',(sw,sh),(0,0,0,0)); m=Image.new('L',(sw,sh),255); d=ImageDraw.Draw(m)
    step=22
    for x in range(step//2,sw,step): d.ellipse((x-r,-r,x+r,r),fill=0); d.ellipse((x-r,sh-r,x+r,sh+r),fill=0)
    for y in range(step//2,sh,step): d.ellipse((-r,y-r,r,y+r),fill=0); d.ellipse((sw-r,y-r,sw+r,y+r),fill=0)
    base=Image.new('RGBA',(sw,sh),(255,253,249,255)); base.putalpha(m); o.alpha_composite(base)
    o.alpha_composite(cover(img,w,h,fx,fy).convert('RGBA'),(pad,pad))
    return o.rotate(rot,resample=Image.BICUBIC,expand=True)
def postmark(text,col,rot=-12,R=92):
    s=R*2+40; o=Image.new('RGBA',(s,s),(0,0,0,0)); d=ImageDraw.Draw(o); c=s/2
    d.ellipse((c-R,c-R,c+R,c+R),outline=col+(210,),width=4); d.ellipse((c-R+40,c-R+40,c+R-40,c+R-40),outline=col+(170,),width=2)
    f=fi(24,700); n=len(text)
    for i,ch in enumerate(text):
        a=2*math.pi*i/n
        x=c+(R-21)*math.sin(a); y=c-(R-21)*math.cos(a)
        g=Image.new('RGBA',(40,40),(0,0,0,0)); ImageDraw.Draw(g).text((20,20),ch,font=f,fill=col+(220,),anchor='mm')
        g=g.rotate(-math.degrees(a),resample=Image.BICUBIC); o.alpha_composite(g,(int(x-20),int(y-20)))
    for k in range(3): d.arc((c-26,c-14+k*9,c+26,c+10+k*9),200,340,fill=col+(190,),width=2)
    return o.rotate(rot,resample=Image.BICUBIC)
def dashed_path(d,pts,col,dash=14,gap=10,w=3):
    acc=0; on=True
    for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
        L=math.hypot(x2-x1,y2-y1); t=0
        while t<L:
            seg=min(dash if on else gap,L-t)
            if on: d.line((x1+(x2-x1)*t/L,y1+(y2-y1)*t/L,x1+(x2-x1)*(t+seg)/L,y1+(y2-y1)*(t+seg)/L),fill=col,width=w)
            t+=seg; on=not on
def curve(p0,p1,p2,n=40): return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(n+1)]]
def plane(col,size=34,rot=0):
    o=Image.new('RGBA',(size*2,size*2),(0,0,0,0)); d=ImageDraw.Draw(o); c=size
    d.polygon([(c+size*0.9,c),(c-size*0.6,c-size*0.12),(c-size*0.6,c+size*0.12)],fill=col)
    d.polygon([(c+size*0.1,c),(c-size*0.25,c-size*0.75),(c-size*0.4,c-size*0.75),(c-size*0.15,c)],fill=col)
    d.polygon([(c+size*0.1,c),(c-size*0.25,c+size*0.75),(c-size*0.4,c+size*0.75),(c-size*0.15,c)],fill=col)
    d.polygon([(c-size*0.5,c),(c-size*0.75,c-size*0.32),(c-size*0.85,c-size*0.32),(c-size*0.7,c)],fill=col)
    d.polygon([(c-size*0.5,c),(c-size*0.75,c+size*0.32),(c-size*0.85,c+size*0.32),(c-size*0.7,c)],fill=col)
    return o.rotate(rot,resample=Image.BICUBIC)
def tape(w=150,h=42,rot=0,col=(232,214,190)):
    o=Image.new('RGBA',(w,h),col+(200,)); d=ImageDraw.Draw(o)
    for x in range(0,w,10): d.line((x,0,x,h),fill=(255,255,255,30))
    m=Image.new('L',(w,h),255); dm=ImageDraw.Draw(m)
    for y in range(0,h,6): dm.polygon([(0,y),(5,y+3),(0,y+6)],fill=0); dm.polygon([(w,y),(w-5,y+3),(w,y+6)],fill=0)
    o.putalpha(Image.composite(o.getchannel('A'),Image.new('L',(w,h),0),m))
    return o.rotate(rot,resample=Image.BICUBIC,expand=True)
def paste_c(L,img,cx,cy): L.alpha_composite(img,(int(cx-img.width/2),int(cy-img.height/2)))
CX=495
def slide(no,en,jp,film,lines,photo,still,credit,acc,pfx=0.5,pfy=0.5,sfx=0.5,sfy=0.5,pm='',extra=None):
    L=paper(); d=ImageDraw.Draw(L)
    dd=ImageDraw.Draw(L); dashed_path(dd,curve((700,300),(800,200),(890,285)),acc+(170,),dash=10,gap=9,w=3); paste_c(L,plane(acc+(230,),26,-40),895,292)
    ctext(d,(CX,262),f'GHIBLI TRIP  —  {no}',fi(30,600),SUB,sp=6)
    ctext(d,(CX,338),en,fi(104,500),INK)
    ctext(d,(CX,418),jp,fm(32,False),SUB,sp=4)
    a=arch(Image.open(photo).convert('RGB'),700,720,fx=pfx,fy=pfy); shadow(L,a,(int(CX-a.width/2),470)); L.alpha_composite(a,(int(CX-a.width/2),470))
    st=stamp(Image.open(still).convert('RGB'),330,210,rot=5,fx=sfx,fy=sfy); x0,y0=int(285-st.width/2),int(1150-st.height/2)
    shadow(L,st,(x0,y0),blur=10,off=(0,8),alpha=80); L.alpha_composite(st,(x0,y0))
    paste_c(L,tape(130,38,-38),215,1050)
    paste_c(L,postmark(pm,acc),735,1175)
    d=ImageDraw.Draw(L)
    ctext(d,(CX,1318),'『'+film+'』',fm(46),acc)
    d.line((CX-40,1366,CX+40,1366),fill=LINE,width=2)
    for i,l in enumerate(lines): ctext(d,(CX,1410+i*52),l,fm(31,False),INK)
    ctext(d,(CX,1545),credit,fi(21,500),SUB)
    return L

def thumb(photos,stills,acc=ACC):
    L=paper(); d=ImageDraw.Draw(L)
    dashed_path(d,curve((150,330),(520,150),(860,300)),acc+(160,),dash=12,gap=10,w=3); paste_c(L,plane(acc+(230,),30,-25),868,306)
    ctext(d,(CX,440),'Ghibli Trip',fs(150),acc)
    ctext(d,(CX,585),'実在する',fm(38,False),SUB,sp=14)
    ctext(d,(CX,675),'ジブリの舞台',fm(96),INK,sp=4)
    ctext(d,(CX,775),'—  海外編  —',fm(40,False),INK,sp=6)
    xs=[(250,1110,280,400,-4),(CX,1060,300,440,0),(740,1110,280,400,4)]
    for (cx,cy,w,h,r),(p,fx,fy) in zip(xs,photos):
        a=arch(Image.open(p).convert('RGB'),w,h,border=10,fx=fx,fy=fy).rotate(r,resample=Image.BICUBIC,expand=True)
        shadow(L,a,(int(cx-a.width/2),int(cy-a.height/2))); paste_c(L,a,cx,cy)
    for (cx,cy,r),(p,fx,fy) in zip([(265,1390,-7),(720,1405,6)],stills):
        st=stamp(Image.open(p).convert('RGB'),250,160,rot=r,fx=fx,fy=fy); shadow(L,st,(int(cx-st.width/2),int(cy-st.height/2)),blur=10,off=(0,8),alpha=80); paste_c(L,st,cx,cy)
    paste_c(L,tape(120,36,30),330,1305); paste_c(L,postmark('BON VOYAGE · GHIBLI · ',acc,-10,88),CX,1440)
    d=ImageDraw.Draw(L); ctext(d,(CX,1560),'Sweden · France · Wales · Croatia · Taiwan',fi(30,600),SUB,sp=2)
    return L
