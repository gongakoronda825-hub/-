# アリエッティをIMAXで観た人の感想（2026/10/25）ナレーション動画　約61秒
# デザイン：ポスターの黄緑のグラデーション（方眼うすく）＋ゆるく湾曲したIMAXスクリーン。文字は Zen Maru Gothic、こげ茶＋アリエッティの赤・金茶
# 使い方: python3 make_narration.py <出力先>/ → python3 make_video.py <作業フォルダ(setup.shのW)> <出力先>/narr [stills]
import json,sys,os,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
S=sys.argv[1].rstrip('/')+'/'; NR=sys.argv[2].rstrip('/')+'/'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'arrietty_imax.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
TOTAL=61.5   # 収益化の「1分以上」を超えるよう、最後のフォロー画像で尺を合わせる
CREDIT='© 2010 Mary Norton/Keiko Niwa/Studio Ghibli, NDHDMTW'
INK=(58,46,40); WHITE=(255,255,255); RED=(214,70,50); GOLD=(168,104,24); DIM=(120,110,100); SUBC=(100,88,80)

# ---------- 文字（[ ]で囲んだところを赤にする） ----------
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
def text(L,t,sz,cx,cy,fill=INK,w='Bold',acc=RED,anchor='m',maxw=900,shadow=True,track=0):
    while tlen(t,sz,w)+track*len(t)>maxw: sz-=2
    x=cx-(tlen(t,sz,w)+track*(len(t)-1))/2 if anchor=='m' else cx
    if shadow:
        sh=layer(); text(sh,t,sz,cx,cy,WHITE,w,WHITE,anchor,maxw,False,track)
        L.alpha_composite(_soft(sh))
    d=ImageDraw.Draw(L); f=font(sz,w)
    for s,c in parts(t,fill,acc):
        if track:
            for ch in s: d.text((x,cy),ch,font=f,fill=c,anchor='lm'); x+=f.getlength(ch)+track
        else: d.text((x,cy),s,font=f,fill=c,anchor='lm'); x+=f.getlength(s)
def _soft(sh):
    # 方眼の線の上でも読めるよう、文字のまわりに白いぼかしフチ
    a=sh.getchannel('A').filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6)).point(lambda v:min(255,int(v*1.6))); o=Image.new('RGBA',sh.size,(255,255,255,0)); o.putalpha(a); return o

# ---------- 写真・スクリーン ----------
def gb(n): return Image.open(S+f'gb/karigurashi{n:03d}.jpg').convert('RGB')
def cover(img,w,h,fx=0.5,fy=0.5,z=1.0):
    # 小数座標で切り取り（ズームでカクつかせない）
    s=max(w/img.width,h/img.height)*z; sw,sh=w/s,h/s; x=(img.width-sw)*fx; y=(img.height-sh)*fy
    return img.resize((w,h),Image.BICUBIC,box=(x,y,x+sw,y+sh))
def curve_mask(w,h,sag):
    # IMAXのスクリーン：左右がわずかに手前へ湾曲 → 上下のふちを弧にする
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
    def geom(s,a):
        # a：その瞬間の上書き（w,h,sag,cx,cy,z,fx,fy）
        return {k:a.get(k,getattr(s,k)) for k in ('cx','cy','w','h','sag','fx','fy')}
    def draw(s,L,u=0.0,a=None,post=None):
        a=a or {}; g=s.geom(a); w,h=int(g['w']),int(g['h']); m=cmask(w,h,g['sag'])
        im=cover(s.src,w,h,g['fx'],g['fy'],a.get('z',1.0+0.05*u))
        if post: im=post(im)
        im=im.convert('RGBA'); im.putalpha(m)
        x,y=int(g['cx']-w/2),int(g['cy']-h/2)
        # スクリーンの下にやわらかい影
        sm=Image.new('L',(w+120,h+120),0); sm.paste(m,(60,60)); sh=Image.new('RGBA',sm.size,(40,30,20,0))
        sh.putalpha(sm.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.35))); L.alpha_composite(sh,(x-60,y-48))
        L.alpha_composite(im,(x,y)); return g

# ---------- 背景（暗い館内＋場面写真をうっすら。ゆっくりズーム＋横パン） ----------
def bg_frames(B,n):
    for _ in range(n): yield B.convert('RGBA')

# ---------- キャラ（スクリーンのふちに小さく座る＝小人。紹介作品から3体） ----------
def chara(n,h,ow=7):
    im=Image.open(S+f'cut/karigurashi{n:03d}.png').convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<50 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS); pad=ow*3
    big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big); return out
CH={33:chara(33,180),12:chara(12,160),48:chara(48,165)}

# ---------- 各カット ----------
# 文字の行：('t',文,出るタイミング=ナレーションの何割目) / ('q',観た人の声) / ('s',小さい補足)
SCR=dict(cy=760,w=1000,h=520)   # スクリーンの位置（中心y・幅・高さ）
CUTS={
'c1':dict(lab='VOICE',ttl='迷ってた人ほど',ph=21,fx=0.6,bg=22,ch=(33,'r'),rows=[('t','「わざわざIMAXじゃなくても…」',0),('s','って思ってた人も',0.12),('q','[没入感]がすごくて\nちゃんと[小人]になってた',0.35)]),
'c2':dict(lab='WHY',ttl='なんでアリエッティなのか',ph=(18,7),bg=6,ch=None,rows=[('t','[小さい音]と[細かい画]が主役の映画',0),('t','IMAXで変わるのが',0.5),('t','ちょうど[その2つ]',0.72)]),
'c3':dict(lab='CHANGE 01',ttl='画面',ph=36,fx=0.45,bg=28,ch=(33,'r'),rows=[('t','大きくて、ゆるく湾曲したスクリーン',0),('t','小人から見た[部屋の広さ]が伝わる',0.32),('q','部屋がとにかく広く感じた',0.72)]),
'c4':dict(lab='CHANGE 02',ttl='音',ph=40,fx=0.7,bg=18,ch=None,rows=[('t','[横と上]にもスピーカー',0),('t','雨、風、虫の声が、まわりから',0.28),('q','普段は気にしない音がずっと聞こえてた\n[ニーヤのゴロゴロ]まで',0.62)]),
'c5':dict(lab='CHANGE 03',ttl='画質',ph=32,fx=0.4,bg=3,ch=(33,'r'),rows=[('t','ジブリ監修の[4Kリマスター版]',0),('s','昔の映像を、今の高画質で作り直したもの',0.1),('t','レーザー映写で[明るく、色が深い]',0.3),('q','[水のつぶ]や[花の色]まで見えた',0.75)]),
'c6':dict(lab='SONG',ttl='歌',ph=24,fx=0.6,bg=1,ch=(12,'l'),rows=[('t','[セシル・コルベル]の歌声も',0),('t','IMAXの音響で聴ける',0.3),('s','これ目当てでもいいと思う',0.6)]),
'c7':dict(lab='AFTER',ttl='観たあと',ph=37,fx=0.4,bg=48,ch=(48,'r'),rows=[('q','アリエッティの側で観てたはずが\n「自分は[翔の側]なんだよな」',0),('s','って気づいて、ちょっとしんどい',0.3),('t','でも、[小さい世界]ってきれいなんだな',0.6),('s','って声も',0.85)]),
'c8':dict(lab='SCHEDULE',ttl='上映期間',ph=47,fx=0.5,bg=2,ch=(12,'l'),rows=[])}

def head(L,lab,ttl):
    text(L,lab,30,CX,330,GOLD,w='Black',track=8)
    ImageDraw.Draw(L).line((CX-26,362,CX+26,362),fill=GOLD,width=3)
    text(L,ttl,76,CX,420,INK,w='Black',maxw=640)   # 両はしのキャラと重ならない幅
def footer(L,cx=CX):
    text(L,'観た人の感想をもとに再構成',22,cx,1612,DIM,w='Bold')
    text(L,CREDIT,20,cx,1644,DIM,w='Bold')
    text(L,'ナレーション：VOICEVOX 青山龍星',16,cx,1672,DIM,w='Bold')
def row_layer(r):
    # 1行（または1つの声）だけのレイヤーと高さ
    k,t=r[0],r[1]; L=layer(); ls=t.split('\n')
    if k=='t': text(L,t,52,CX,0+40,INK,w='Black'); return L,96
    if k=='s': text(L,t,38,CX,0+30,SUBC,w='Bold'); return L,72
    # 観た人の声：金の小さいラベル＋うすい枠
    lh=58; h=50+len(ls)*lh+24; w=max(tlen(l,44) for l in ls)+100; d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-w/2,14,CX+w/2,14+h),34,fill=(255,255,255,235),outline=GOLD+(255,),width=4)
    lw=tlen('観た人の声',24)+40; d.rounded_rectangle((CX-lw/2,0,CX+lw/2,30),15,fill=GOLD)
    text(L,'観た人の声',24,CX,15,WHITE,w='Bold',shadow=False)
    for j,l in enumerate(ls): text(L,l,44,CX,14+50+j*lh+lh/2-8,INK,w='Bold',shadow=False)
    return L,h+50
def build(k):
    c=CUTS[k]; base=layer(); head(base,c['lab'],c['ttl']); footer(base)
    if isinstance(c['ph'],tuple):
        scr=[Screen(gb(n),CX+(-250 if j==0 else 250),SCR['cy'],480,SCR['h'],0.55,sag=16) for j,n in enumerate(c['ph'])]
        for j,lab in enumerate(['小さい音','細かい画']): text(base,lab,40,CX+(-250 if j==0 else 250),SCR['cy']+SCR['h']/2+50,GOLD,w='Black')
        y=SCR['cy']+SCR['h']/2+120
    else:
        scr=[Screen(gb(c['ph']),CX,SCR['cy'],SCR['w'],SCR['h'],c.get('fx',0.5))]; y=SCR['cy']+SCR['h']/2+70
    rows=[]
    for r in c['rows']:
        L,h=row_layer(r); o=layer(); o.alpha_composite(L,(0,int(y))); rows.append((o,r[2])); y+=h if r[1]!='って声も' else 0
    if k=='c8': rows=c8_rows(y)
    return dict(base=base,scr=scr,ch=(CH[c['ch'][0]],c['ch'][1]) if c['ch'] else None,rows=rows)
def c8_rows(y):
    out=[]; L=layer(); d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-470,y,CX+470,y+140),40,fill=RED,outline=WHITE,width=6)
    text(L,'IMAX上映',40,CX-290,y+70,WHITE,w='Black',shadow=False); text(L,'〜11/2（月）',72,CX+130,y+70,WHITE,w='Black',shadow=False,maxw=560)
    out.append((L,0.0,'pulse'))
    L=layer(); yy=y+170; d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-400,yy,CX+400,yy+84),26,fill=(255,255,255,235),outline=DIM+(255,),width=3)
    text(L,'全国の拡大上映',28,CX-260,yy+42,SUBC,w='Black',maxw=240,shadow=False); text(L,'10/30（金）〜11/12（木）',36,CX+110,yy+42,SUBC,w='Bold',maxw=500,shadow=False); out.append((L,0.3))
    L=layer(); text(L,'※拡大上映は[IMAXではありません]（通常の上映）',30,CX,yy+125,SUBC,w='Black'); out.append((L,0.4))
    L=layer(); text(L,'[迷ってる人]に送ってあげて',52,CX,yy+215,INK,w='Black'); out.append((L,0.78))
    L=layer(); text(L,'※劇場によって設備が違います（レーザーでない劇場、2K上映の劇場あり）',22,CX,yy+285,DIM,w='Bold'); out.append((L,0.0))
    return out
def logo(name,w,border):
    # ポスターから切り抜いたロゴ（parts/）に、ふち（border=[(色,太さ),…] 内側から）と影をつける
    im=Image.open(HERE+f'parts/{name}.png').convert('RGBA'); im=im.resize((w,int(im.height*w/im.width)),Image.LANCZOS)
    pad=sum(t for _,t in border)+16; o=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); A=Image.new('L',o.size,0); A.paste(im.getchannel('A'),(pad,pad))
    A=A.point(lambda v:255 if v>100 else 0); layers=[]; r=0
    for col,t in border: r+=t; layers.append((col,A.filter(ImageFilter.MaxFilter(2*r+1)).filter(ImageFilter.GaussianBlur(1))))
    sh=Image.new('RGBA',o.size,(40,30,20,0)); sh.putalpha(layers[-1][1].filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35))); o.alpha_composite(sh,(0,6))
    for col,m in layers[::-1]: c=Image.new('RGBA',o.size,col+(0,)); c.putalpha(m); o.alpha_composite(c)
    o.alpha_composite(im,(pad,pad)); return o
def hook():
    # サムネ：上にポスターのタイトルロゴ、まん中にスクリーン、下に「(IMAXロゴ)で観る 意味ある？」（y=240〜1680に収める）
    L=layer(); sc=Screen(gb(33),540,775,1000,430,0.55)
    t=logo('title_cut',600,[(WHITE,12)]); L.alpha_composite(t,(int(540-t.width/2),int(395-t.height/2)))
    im=logo('imax_cut',620,[(INK,3),(WHITE,9)]); L.alpha_composite(im,(int(540-im.width/2),int(1075-im.height/2)))
    text(L,'で観る[意味ある？]',112,540,1285,INK,w='Black')
    text(L,'何が変わるのか、観た人の声と一緒に',40,540,1415,SUBC)
    d=ImageDraw.Draw(L); t='IMAX上映　〜11/2（月）'; w=tlen(t,32)+60; d.rounded_rectangle((540-w/2,1478,540+w/2,1540),31,fill=WHITE,outline=GOLD,width=3)
    text(L,t,32,540,1509,GOLD,shadow=False); footer(L,540)
    text(L,'タイトル・IMAXロゴ：公式ポスターより',16,540,1590,DIM,w='Bold')
    return dict(base=L,scr=[sc],ch=(CH[12],'r'),rows=[])

# ---------- 演出 ----------
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def back(x):
    x=min(max(x,0),1); c=1.7; return 1+(c+1)*(x-1)**3+c*(x-1)**2
from PIL import ImageEnhance
def old_film(im):
    # 昔の映像っぽく：解像度を落としてくすませる
    w,h=im.size; o=im.resize((w//9,h//9),Image.BILINEAR).resize((w,h),Image.NEAREST)
    return ImageEnhance.Contrast(ImageEnhance.Color(o).enhance(0.55)).enhance(0.8)
def speaker(L,x,y,rot):
    sp=Image.new('RGBA',(110,150),(0,0,0,0)); d=ImageDraw.Draw(sp)
    d.rounded_rectangle((10,8,100,142),18,fill=WHITE,outline=INK,width=6)
    d.ellipse((30,62,80,112),outline=INK,width=6); d.ellipse((47,79,63,95),fill=INK); d.ellipse((46,24,64,42),outline=INK,width=4)
    sp=sp.rotate(rot,Image.BICUBIC,expand=True); L.alpha_composite(sp,(int(x-sp.width/2),int(y-sp.height/2)))
def waves(L,x,y,ang,t):
    # スピーカーから音の波が広がる（3本、外へ行くほど薄く）
    d=ImageDraw.Draw(L)
    for i in range(3):
        r=60+((t*90+i*45)%135); al=int(255*max(0,1-(r-60)/135))
        d.arc((x-r,y-r,x+r,y+r),ang-38,ang+38,fill=GOLD+(al,),width=8)
def sparkle(L,x,y,r,al):
    st=Image.new('RGBA',(int(4*r)+4,int(4*r)+4),(0,0,0,0)); d=ImageDraw.Draw(st); c=st.width/2
    d.polygon([(c,c-2*r),(c+r*0.28,c-r*0.28),(c+2*r,c),(c+r*0.28,c+r*0.28),(c,c+2*r),(c-r*0.28,c+r*0.28),(c-2*r,c),(c-r*0.28,c-r*0.28)],fill=(255,250,215,int(255*al)))
    L.alpha_composite(st.filter(ImageFilter.GaussianBlur(0.6)),(int(x-c),int(y-c)))
def onoma(L,t,x,y,al,col=INK,sz=46):
    o=layer(); text(o,t,sz,x,y,col,w='Black')
    if al<1: o.putalpha(o.getchannel('A').point(lambda v:int(v*al)))
    L.alpha_composite(o)
# 各カットの動き。返り値：スクリーンへの上書き（とポスト処理）、手前に重ねるレイヤー
def fx_screen(k,i,g,T):
    if k=='c1':
        z=1.05+0.30*ease((g-T(0.35))/1.4); return dict(z=z,fx=0.62,fy=0.6),None
    if k=='c2':
        on=(T(0)<=g<T(0.28) and i==0) or (T(0.28)<=g<T(0.5) and i==1)
        off=(T(0)<=g<T(0.28) and i==1) or (T(0.28)<=g<T(0.5) and i==0)
        sc=1.12 if on else (0.94 if off else 1.0)
        return dict(w=480*sc,h=520*sc),(lambda im:ImageEnhance.Brightness(im).enhance(0.45)) if off else None
    if k=='c3':
        # 小さくて平らなスクリーン →「大きくて、ゆるく湾曲」でぐわっと広がる
        u=min(max((g-T(0)-0.2)/2.6,0),1); x=u*u*(3-2*u); return dict(w=640+460*x,h=380+150*x,sag=2+44*x),None
    if k=='c4': return dict(w=700,h=420,cy=800),None
    if k=='c5':
        x0=T(0.1); p=ease((g-x0)/1.1); bright=ease((g-T(0.3))/0.6)
        def post(im,p=p,b=bright):
            w,h=im.size; cut=int(w*p)
            if cut<w: o=old_film(im); o.paste(im.crop((0,0,cut,h)),(0,0)); im=o
            if b>0: im=ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(1+0.12*b)).enhance(1+0.25*b)
            return im
        return {},post
    return {},None
def fx_front(k,L,g,T,G):
    cx,cy,w,h=G['cx'],G['cy'],G['w'],G['h']
    if k=='c3' and g>T(0)+0.3:
        al=min(1,max(0,(g-T(0)-0.3)/0.3))*max(0,min(1,(T(0)+2.9-g)/0.4))
        if al>0:
            o=layer(); d=ImageDraw.Draw(o)
            for sgn in (-1,1):
                x=cx+sgn*(w/2-60); pts=[(x+sgn*34,cy),(x-sgn*20,cy-40),(x-sgn*20,cy+40)]
                d.polygon(pts,fill=GOLD+(255,),outline=WHITE+(255,),width=6)
            o.putalpha(o.getchannel('A').point(lambda v:int(v*al))); L.alpha_composite(o)
    if k=='c4':
        sp=[(cx-w/2-70,cy,0,0,0),(cx+w/2+70,cy,0,180,0),(cx-w/2+90,cy-h/2-80,0,60,0.6),(cx+w/2-90,cy-h/2-80,0,120,0.6)]
        for x,y,rot,ang,dl in sp:
            a=g-T(0)-dl
            if a<0: continue
            s_=POP[min(int(a*FPS),len(POP)-1)] if a*FPS<len(POP) else 1.0
            o=layer(); waves(o,x,y,ang,a); speaker(o,x,y,rot)
            if s_!=1.0:
                bb=o.getbbox(); c=o.crop(bb).resize((max(1,int((bb[2]-bb[0])*s_)),max(1,int((bb[3]-bb[1])*s_)))); o=layer(); o.alpha_composite(c,(int(x-c.width/2),int(y-c.height/2)))
            L.alpha_composite(o)
        for t,x,y,fr in [('ザーッ',cx-250,cy-130,0.28),('ヒュウ',cx+230,cy-150,0.36),('リーン',cx-200,cy+150,0.44),('ゴロゴロ',cx+200,cy+140,0.66)]:
            a=g-T(fr)
            if a>0: onoma(L,t,x+8*np.sin(a*3),y-10*ease(a/0.6),min(1,a/0.3),INK if t!='ゴロゴロ' else RED,50)
    if k=='c5':
        p=ease((g-T(0.1))/1.1)
        if 0<p<1:
            x=cx-w/2+w*p; o=layer(); ImageDraw.Draw(o).rectangle((x-6,cy-h/2+10,x+6,cy+h/2-10),fill=(255,255,255,230)); L.alpha_composite(o.filter(ImageFilter.GaussianBlur(4)))
        b=g-T(0.3)
        if b>0:
            for j,(px,py) in enumerate([(0.18,0.3),(0.4,0.65),(0.72,0.25),(0.86,0.7),(0.55,0.15)]):
                tw=0.5+0.5*np.sin(b*5+j*1.7); sparkle(L,cx-w/2+w*px,cy-h/2+h*py,18+8*tw,min(1,b/0.3)*(0.5+0.5*tw))
    if k=='c6' and g>T(0.3):
        a=g-T(0.3)
        for j in range(6):
            ph=(a*0.55+j/6)%1.0; x=cx-w/2+w*(0.1+0.16*j)+20*np.sin((a+j)*2.2); y=cy-h/2+40-ph*260
            onoma(L,'♪',x,y,min(1,a/0.4)*np.sin(np.pi*ph),RED if j%2 else GOLD,54)

# ---------- タイムライン ----------
def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
KEYS=['hook','c1','c2','c3','c4','c5','c6','c7','c8','fol']
DUR={'hook':2.9}
tl=[]; t=0
for k in KEYS:
    d_=max(DUR.get(k,0),0.15+wdur(k)+0.45); tl.append([t,d_,k]); t+=d_
tl[-1][1]+=max(0,TOTAL-t); TOT=sum(x[1] for x in tl); print('total',round(TOT,2))
def poster_bg():
    # 背景：IMAXポスターの庭の光に合わせた黄緑→生成りのグラデーション＋いつもの方眼をごく薄く
    t=np.linspace(0,1,H)[:,None,None]**0.8; top=np.array((214,234,180),float); bot=np.array((250,246,232),float)
    B=Image.fromarray(np.broadcast_to(top*(1-t)+bot*t,(H,W,3)).astype(np.uint8))
    lines=ImageChops.invert(Image.open(TK+'bg_grid.jpg').convert('L').resize((W,H))).point(lambda v:int(v*0.22))
    B.paste(Image.new('RGB',(W,H),(120,160,100)),(0,0),lines); return B
GRID=poster_bg(); BGS={k:GRID for k in KEYS}
POP=[0.6,0.9,1.08,1.03]
def popped(F,j):
    if j<0: return None
    if j>=len(POP): return F
    s=POP[j]; bb=F.getbbox(); c=F.crop(bb); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
_bb={}
def scaled(F,s):
    k=id(F)
    if k not in _bb: _bb[k]=F.getbbox()
    bb=_bb[k]; c=F.crop(bb).resize((int((bb[2]-bb[0])*s),int((bb[3]-bb[1])*s)),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
def frame(k,P,bg,j,n,dur):
    g=j/FPS; im=bg; T=lambda fr:0.15+fr*wdur(k)
    for i,s in enumerate(P['scr']): a,post=fx_screen(k,i,g,T); G=s.draw(im,j/max(n-1,1),a,post)
    if P['ch']:
        ch,side=P['ch']; cx=G['cx']+(G['w']/2-60 if side=='r' else -G['w']/2+60); im.alpha_composite(ch,(int(cx-ch.width/2),int(G['cy']-G['h']/2-ch.height+70)))
    im.alpha_composite(P['base']); fx_front(k,im,g,T,G)
    for r in P['rows']:
        L,fr=r[0],r[1]; a=int((g-(0.15+fr*wdur(k)))*FPS)
        if len(r)>2 and a>=len(POP): p=scaled(L,1+0.035*np.sin(np.pi*(a-len(POP))/FPS*1.6)**2)   # 一番伝えたい帯だけゆっくり脈打つ
        else: p=popped(L,a)
        if p is not None: im.alpha_composite(p)
    return im
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
if len(sys.argv)>3 and sys.argv[3]=='stills':
    os.makedirs(S+'../stills',exist_ok=True)
    for i,(t0,d_,k) in enumerate(tl[:-1]):
        P=hook() if k=='hook' else build(k); n=int(d_*FPS)
        frame(k,P,next(bg_frames(BGS[k],1)),n-1,n,d_).convert('RGB').save(S+f'../stills/{i:02d}_{k}.jpg',quality=88)
    sys.exit()
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',NR+'../v.mp4'],stdin=subprocess.PIPE)
for t0,d_,k in tl:
    n=int(round((t0+d_)*FPS))-int(round(t0*FPS))
    if k=='fol':
        for _ in range(n): enc.stdin.write(np.asarray(FOLLOW).tobytes())
        continue
    P=hook() if k=='hook' else build(k)
    for j,bg in enumerate(bg_frames(BGS[k],n)): enc.stdin.write(np.asarray(frame(k,P,bg,j,n,d_).convert('RGB')).tobytes())
enc.stdin.close(); enc.wait()
# ---------- 音 ----------
N=int(TOT*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
SFX={'hook':('kira1',0.35),'c8':('shine2',0.3)}
for t0,d_,k in tl:
    add(rd(NR+k+'.wav'),t0+0.15,1.0)
    if k in SFX: add(rd(S+f'labsfx/{SFX[k][0]}.wav'),t0,SFX[k][1])
    elif k!='fol': add(rd(S+'labsfx/sceneswitch1.wav'),t0,0.22)
    T=lambda fr,k=k,t0=t0:t0+0.15+fr*wdur(k)
    if k=='c3': add(rd(S+'labsfx/nyu1.wav'),T(0)+0.3,0.3)
    if k=='c4':
        for dl in (0,0.6): add(rd(S+'labsfx/pa1.wav'),T(0)+dl,0.22)
    if k=='c5': add(rd(S+'labsfx/shakin1.wav'),T(0.1),0.25); add(rd(S+'labsfx/kira1.wav'),T(0.3),0.25)
    for r in CUTS.get(k,{}).get('rows',[]):
        if r[0]=='q': add(rd(S+'labsfx/pa1.wav'),t0+0.15+r[2]*wdur(k),0.25)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
