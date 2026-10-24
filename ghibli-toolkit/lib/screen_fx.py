# スクリーン演出つき解説動画の部品集（初出：arrietty-imax/。いろんな動画で使える形にしたもの）
# 使い方:
#   import sys; sys.path.insert(0,'<リポジトリ>/ghibli-toolkit/lib'); import screen_fx as fx
#   fx.init(作業フォルダS, theme=dict(ACC=(214,70,50)))   # 色は動画ごとに上書き
#   B=fx.poster_bg((214,234,180),(250,246,232))            # 作品ポスターの色に合わせた背景
#   sc=fx.Screen(写真,cx,cy,w,h); G=sc.draw(im,u,fx.expand(g))  # g＝その演出が始まってからの秒数
# 文字は Zen Maru Gothic（setup.sh で fonts/ に入る）。[ ]で囲んだ語だけ強調色になる
import os,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops,ImageEnhance
W,H=1080,1920; FPS=30
S=''; TK=os.path.dirname(os.path.abspath(__file__))+'/../assets/'
# 色（init の theme で上書き）：文字、強調、ラベル、薄い文字、補足、白
INK=(58,46,40); ACC=(214,70,50); GOLD=(168,104,24); DIM=(120,110,100); SUBC=(100,88,80); WHITE=(255,255,255)
def init(s,theme=None,tk=None):
    global S,TK
    S=s.rstrip('/')+'/'
    if tk: TK=tk.rstrip('/')+'/'
    for k,v in (theme or {}).items(): globals()[k]=v

# ---------- 文字 ----------
_fc={}
def font(sz,w='Bold'):
    k=(sz,w)
    if k not in _fc: _fc[k]=ImageFont.truetype(S+f'fonts/ZenMaru-{w}.ttf',sz)
    return _fc[k]
def parts(t,base,acc):
    out=[]; col=base; buf=''
    for ch in t:
        if ch in '[]':
            if buf: out.append((buf,col)); buf=''
            col=acc if ch=='[' else base
        else: buf+=ch
    if buf: out.append((buf,col))
    return out
def tlen(t,sz,w='Bold'): return font(sz,w).getlength(t.replace('[','').replace(']',''))
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
def text(L,t,sz,cx,cy,fill=None,w='Bold',acc=None,anchor='m',maxw=900,shadow=True,track=0):
    # shadow=True：方眼・グラデの上でも読めるよう白いぼかしフチ。白い箱の中は shadow=False
    fill=fill or INK; acc=acc or ACC
    while tlen(t,sz,w)+track*len(t)>maxw: sz-=2
    x=cx-(tlen(t,sz,w)+track*(len(t)-1))/2 if anchor=='m' else cx
    if shadow:
        sh=layer(); text(sh,t,sz,cx,cy,WHITE,w,WHITE,anchor,maxw,False,track); L.alpha_composite(_soft(sh))
    d=ImageDraw.Draw(L); f=font(sz,w)
    for s,c in parts(t,fill,acc):
        if track:
            for ch in s: d.text((x,cy),ch,font=f,fill=c,anchor='lm'); x+=f.getlength(ch)+track
        else: d.text((x,cy),s,font=f,fill=c,anchor='lm'); x+=f.getlength(s)
def _soft(sh):
    a=sh.getchannel('A').filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6)).point(lambda v:min(255,int(v*1.6))); o=Image.new('RGBA',sh.size,(255,255,255,0)); o.putalpha(a); return o
def head(L,lab,ttl,cx,y=330,maxw=640):
    # 金の英字ラベル（CHANGE 01 など）＋大きい見出し
    text(L,lab,30,cx,y,GOLD,w='Black',track=8)
    ImageDraw.Draw(L).line((cx-26,y+32,cx+26,y+32),fill=GOLD,width=3)
    text(L,ttl,76,cx,y+90,INK,w='Black',maxw=maxw)
def row(kind,t,cx,y,label='観た人の声'):
    # 1行ぶんのレイヤーと高さ。kind：'t'=本文／'s'=小さい補足／'q'=声の吹き出し（金フチ＋ラベル）
    L=layer(); ls=t.split('\n')
    if kind=='t': text(L,t,52,cx,y+40,INK,w='Black'); return L,96
    if kind=='s': text(L,t,38,cx,y+30,SUBC,w='Bold'); return L,72
    lh=58; h=50+len(ls)*lh+24; w=max(tlen(l,44) for l in ls)+100; d=ImageDraw.Draw(L)
    d.rounded_rectangle((cx-w/2,y+14,cx+w/2,y+14+h),34,fill=(255,255,255,235),outline=GOLD+(255,),width=4)
    lw=tlen(label,24)+40; d.rounded_rectangle((cx-lw/2,y,cx+lw/2,y+30),15,fill=GOLD)
    text(L,label,24,cx,y+15,WHITE,w='Bold',shadow=False)
    for j,l in enumerate(ls): text(L,l,44,cx,y+14+50+j*lh+lh/2-8,INK,w='Bold',shadow=False)
    return L,h+50
def tag(L,t,cx,cy,sz=32,col=None,fill=WHITE):
    # 白地＋色フチの小さい札（サムネの「IMAX上映 〜11/2」など）
    col=col or GOLD; w=tlen(t,sz)+60; ImageDraw.Draw(L).rounded_rectangle((cx-w/2,cy-sz*0.97,cx+w/2,cy+sz*0.97),sz,fill=fill,outline=col,width=3)
    text(L,t,sz,cx,cy,col,shadow=False)
def big_band(L,cx,y,lab,val,w=940,h=140,col=None):
    # 一番伝えたい1行だけの大きい色帯（pulse() でゆっくり脈打たせる）
    col=col or ACC; d=ImageDraw.Draw(L); d.rounded_rectangle((cx-w/2,y,cx+w/2,y+h),40,fill=col,outline=WHITE,width=6)
    text(L,lab,40,cx-w/2+180,y+h/2,WHITE,w='Black',shadow=False,maxw=300); text(L,val,72,cx+130,y+h/2,WHITE,w='Black',shadow=False,maxw=w-380)

# ---------- 背景 ----------
def poster_bg(top,bot,line=(120,160,100),grid=0.22,gamma=0.8):
    # 作品ポスターの色に合わせた縦グラデーション＋いつもの方眼（bg_grid.jpg）をごく薄く
    t=np.linspace(0,1,H)[:,None,None]**gamma; a=np.array(top,float); b=np.array(bot,float)
    B=Image.fromarray(np.broadcast_to(a*(1-t)+b*t,(H,W,3)).astype(np.uint8))
    if grid>0:
        lines=ImageChops.invert(Image.open(TK+'bg_grid.jpg').convert('L').resize((W,H))).point(lambda v:int(v*grid))
        B.paste(Image.new('RGB',(W,H),line),(0,0),lines)
    return B

# ---------- 写真・スクリーン ----------
def cover(img,w,h,fx=0.5,fy=0.5,z=1.0):
    # 小数座標で切り取り（ズームでカクつかせない）
    s=max(w/img.width,h/img.height)*z; sw,sh=w/s,h/s; x=(img.width-sw)*fx; y=(img.height-sh)*fy
    return img.resize((w,h),Image.BICUBIC,box=(x,y,x+sw,y+sh))
def curve_mask(w,h,sag):
    # ゆるく湾曲した大きいスクリーン：上下のふちを弧にする（sag=湾曲の深さpx、0で平ら）
    m=Image.new('L',(w,h),0); d=ImageDraw.Draw(m); xs=np.linspace(0,w,200); c=((xs/w-0.5)*2)**2
    top=[(x,sag*(1-cc)) for x,cc in zip(xs,c)]; bot=[(x,h-sag*(1-cc)) for x,cc in zip(xs[::-1],c[::-1])]
    d.polygon(top+bot,fill=255); return m.filter(ImageFilter.GaussianBlur(0.8))
_mc={}
def cmask(w,h,sag):
    k=(w,h,int(sag))
    if k not in _mc:
        if len(_mc)>64: _mc.clear()
        _mc[k]=curve_mask(w,h,sag)
    return _mc[k]
class Screen:
    def __init__(s,src,cx,cy,w,h,fx=0.5,fy=0.5,sag=22):
        s.src=src; s.cx,s.cy,s.w,s.h,s.fx,s.fy,s.sag=cx,cy,w,h,fx,fy,sag
    def geom(s,a): return {k:a.get(k,getattr(s,k)) for k in ('cx','cy','w','h','sag','fx','fy')}
    def draw(s,L,u=0.0,a=None,post=None):
        # u：カットの進み具合0〜1（写真がゆっくり5%寄る）。a：その瞬間の上書き（w,h,sag,cx,cy,z,fx,fy）
        # post：写真への加工（old_to_new など）。返り値＝その瞬間の位置・大きさ（キャラや演出の位置合わせに使う）
        a=a or {}; g=s.geom(a); w,h=int(g['w']),int(g['h']); m=cmask(w,h,g['sag'])
        im=cover(s.src,w,h,g['fx'],g['fy'],a.get('z',1.0+0.05*u))
        if post: im=post(im)
        im=im.convert('RGBA'); im.putalpha(m); x,y=int(g['cx']-w/2),int(g['cy']-h/2)
        sm=Image.new('L',(w+120,h+120),0); sm.paste(m,(60,60)); sh=Image.new('RGBA',sm.size,(40,30,20,0))
        sh.putalpha(sm.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.35))); L.alpha_composite(sh,(x-60,y-48))
        L.alpha_composite(im,(x,y)); return g
def sit_on(L,ch,G,side='r',inset=60,sink=70):
    # キャラをスクリーンの上のふちに小さく座らせる（スクリーンが動いてもついていく）
    cx=G['cx']+(G['w']/2-inset if side=='r' else -G['w']/2+inset); L.alpha_composite(ch,(int(cx-ch.width/2),int(G['cy']-G['h']/2-ch.height+sink)))

# ---------- ステッカー・ロゴ ----------
def sticker(path,h,ow=7):
    # 切り抜き（cutout.py の cut/*.png）を高さhにして白フチ
    im=Image.open(path).convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<50 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS); pad=ow*3
    big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big); return out
def logo(path,w,border):
    # ポスターから切り抜いたロゴ（cut_logo.py）に、ふち border=[(色,太さ),…]（内側から）と影をつける
    im=Image.open(path).convert('RGBA'); im=im.resize((w,int(im.height*w/im.width)),Image.LANCZOS)
    pad=sum(t for _,t in border)+16; o=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); A=Image.new('L',o.size,0); A.paste(im.getchannel('A'),(pad,pad))
    A=A.point(lambda v:255 if v>100 else 0); layers=[]; r=0
    for col,t in border: r+=t; layers.append((col,A.filter(ImageFilter.MaxFilter(2*r+1)).filter(ImageFilter.GaussianBlur(1))))
    sh=Image.new('RGBA',o.size,(40,30,20,0)); sh.putalpha(layers[-1][1].filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35))); o.alpha_composite(sh,(0,6))
    for col,m in layers[::-1]: c=Image.new('RGBA',o.size,col+(0,)); c.putalpha(m); o.alpha_composite(c)
    o.alpha_composite(im,(pad,pad)); return o

# ---------- 出し方（ポンッ・脈打つ） ----------
POP=[0.6,0.9,1.08,1.03]
def scaled(F,s):
    bb=F.getbbox()
    if not bb: return F
    c=F.crop(bb).resize((max(1,int((bb[2]-bb[0])*s)),max(1,int((bb[3]-bb[1])*s))),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
def popped(F,j):
    # j＝出てからのフレーム数。負なら出さない（None）
    if j<0: return None
    return F if j>=len(POP) else scaled(F,POP[j])
def pulse(F,j,amp=0.035,speed=1.6):
    # 出たあと、一番伝えたい部分だけゆっくり脈打つ
    if j<len(POP): return popped(F,j)
    return scaled(F,1+amp*np.sin(np.pi*(j-len(POP))/FPS*speed)**2)

# ---------- 動きのカーブ ----------
def clamp(x): return min(max(x,0),1)
def ease(x): x=clamp(x); return 1-(1-x)**3
def smooth(x): x=clamp(x); return x*x*(3-2*x)

# ---------- 演出（g＝その演出が始まってからの秒数） ----------
def expand(g,dur=2.6,a=(640,380,2),b=(1100,530,46)):
    # 「大きい・湾曲」：小さく平らなスクリーンがゆっくりぐぅーんと広がる（はね返りなし）。a/b=(幅,高さ,湾曲)
    x=smooth(g/dur); return dict(w=a[0]+(b[0]-a[0])*x,h=a[1]+(b[1]-a[1])*x,sag=a[2]+(b[2]-a[2])*x)
def push_in(g,dur=1.4,z0=1.05,z1=1.35,fx=0.5,fy=0.5):
    # 「〜になった」「入り込む」：写真の中の一点へゆっくり寄る
    return dict(z=z0+(z1-z0)*ease(g/dur),fx=fx,fy=fy)
def dimmed(im,k=0.45): return ImageEnhance.Brightness(im).enhance(k)
def old_film(im):
    # 昔の映像っぽく：解像度を落としてくすませる
    w,h=im.size; o=im.resize((max(1,w//9),max(1,h//9)),Image.BILINEAR).resize((w,h),Image.NEAREST)
    return ImageEnhance.Contrast(ImageEnhance.Color(o).enhance(0.55)).enhance(0.8)
def old_to_new(g,dur=1.1,bright_at=None):
    # 「高画質・リマスター」：粗い昔の映像 → 光の線が左から右へ通って高画質に（post に渡す）
    # bright_at：何秒後に「明るく・色が深く」するか（None でしない）
    p=ease(g/dur); b=ease((g-bright_at)/0.6) if bright_at is not None else 0
    def post(im):
        w,h=im.size; cut=int(w*p)
        if cut<w: o=old_film(im); o.paste(im.crop((0,0,cut,h)),(0,0)); im=o
        if b>0: im=ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(1+0.12*b)).enhance(1+0.25*b)
        return im
    return post
def wipe_line(L,G,g,dur=1.1):
    p=ease(g/dur)
    if 0<p<1:
        x=G['cx']-G['w']/2+G['w']*p; o=layer(); ImageDraw.Draw(o).rectangle((x-6,G['cy']-G['h']/2+10,x+6,G['cy']+G['h']/2-10),fill=(255,255,255,230)); L.alpha_composite(o.filter(ImageFilter.GaussianBlur(4)))
def arrows(L,G,al,col=None):
    # 左右に広がる矢印（expand と一緒に）
    if al<=0: return
    col=col or GOLD; o=layer(); d=ImageDraw.Draw(o); cx,cy,w=G['cx'],G['cy'],G['w']
    for sgn in (-1,1):
        x=cx+sgn*(w/2-60); d.polygon([(x+sgn*34,cy),(x-sgn*20,cy-40),(x-sgn*20,cy+40)],fill=col+(255,),outline=WHITE+(255,),width=6)
    o.putalpha(o.getchannel('A').point(lambda v:int(v*al))); L.alpha_composite(o)
def speaker_icon(L,x,y):
    sp=Image.new('RGBA',(110,150),(0,0,0,0)); d=ImageDraw.Draw(sp)
    d.rounded_rectangle((10,8,100,142),18,fill=WHITE,outline=INK,width=6)
    d.ellipse((30,62,80,112),outline=INK,width=6); d.ellipse((47,79,63,95),fill=INK); d.ellipse((46,24,64,42),outline=INK,width=4)
    L.alpha_composite(sp,(int(x-sp.width/2),int(y-sp.height/2)))
def waves(L,x,y,ang,t,col=None):
    # 音の波（3本、外へ行くほど薄く）。ang＝向き（0=右、90=下、180=左）
    col=col or GOLD; d=ImageDraw.Draw(L)
    for i in range(3):
        r=60+((t*90+i*45)%135); al=int(255*max(0,1-(r-60)/135)); d.arc((x-r,y-r,x+r,y+r),ang-38,ang+38,fill=col+(al,),width=8)
def speakers(L,G,g,top_delay=0.6):
    # 「横と上にスピーカー」：左右→上にスピーカーがポンッと出て、スクリーンへ音の波
    cx,cy,w,h=G['cx'],G['cy'],G['w'],G['h']
    for x,y,ang,dl in [(cx-w/2-70,cy,0,0),(cx+w/2+70,cy,180,0),(cx-w/2+90,cy-h/2-80,60,top_delay),(cx+w/2-90,cy-h/2-80,120,top_delay)]:
        a=g-dl
        if a<0: continue
        o=layer(); waves(o,x,y,ang,a); speaker_icon(o,x,y)
        j=int(a*FPS); L.alpha_composite(o if j>=len(POP) else scaled(o,POP[j]))
def onoma(L,t,x,y,al,col=None,sz=46):
    o=layer(); text(o,t,sz,x,y,col or INK,w='Black')
    if al<1: o.putalpha(o.getchannel('A').point(lambda v:int(v*al)))
    L.alpha_composite(o)
def floating_words(L,G,g,items,sz=50):
    # 擬音・ことばがスクリーンのまわりにふわっと出る。items=[(文字,dx,dy,出る秒,色 or None),…]（dx,dyはスクリーン中心から）
    for t,dx,dy,t0,col in items:
        a=g-t0
        if a>0: onoma(L,t,G['cx']+dx+8*np.sin(a*3),G['cy']+dy-10*ease(a/0.6),min(1,a/0.3),col,sz)
def sparkle(L,x,y,r,al):
    st=Image.new('RGBA',(int(4*r)+4,int(4*r)+4),(0,0,0,0)); d=ImageDraw.Draw(st); c=st.width/2
    d.polygon([(c,c-2*r),(c+r*0.28,c-r*0.28),(c+2*r,c),(c+r*0.28,c+r*0.28),(c,c+2*r),(c-r*0.28,c+r*0.28),(c-2*r,c),(c-r*0.28,c-r*0.28)],fill=(255,250,215,int(255*al)))
    L.alpha_composite(st.filter(ImageFilter.GaussianBlur(0.6)),(int(x-c),int(y-c)))
def sparkles(L,G,g,pts=((0.18,0.3),(0.4,0.65),(0.72,0.25),(0.86,0.7),(0.55,0.15))):
    # 「きれい・明るい」：スクリーンの上でキラキラがまたたく（pts＝スクリーン内の割合座標）
    if g<=0: return
    for j,(px,py) in enumerate(pts):
        tw=0.5+0.5*np.sin(g*5+j*1.7); sparkle(L,G['cx']-G['w']/2+G['w']*px,G['cy']-G['h']/2+G['h']*py,18+8*tw,min(1,g/0.3)*(0.5+0.5*tw))
def notes(L,G,g,n=6,cols=None):
    # 「歌・音楽」：♪がスクリーンの上からゆらゆら上がる
    if g<=0: return
    cols=cols or (GOLD,ACC)
    for j in range(n):
        ph=(g*0.55+j/n)%1.0; x=G['cx']-G['w']/2+G['w']*(0.1+0.8*j/max(n-1,1))+20*np.sin((g+j)*2.2); y=G['cy']-G['h']/2+40-ph*260
        onoma(L,'♪',x,y,min(1,g/0.4)*np.sin(np.pi*ph),cols[j%len(cols)],54)
