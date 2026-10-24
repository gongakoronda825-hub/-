# あなたはどのジブリ作品と同い年？ ジブリ年表（上から下に流れる年表）
# 使い方: python3 make_video.py <作業フォルダ(setup.shのW)> <ナレーションwavのフォルダ> [stills]
import sys,os,math,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S,NR=[a.rstrip('/')+'/' for a in sys.argv[1:3]]
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'ghibli_nenpyo.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
WHITE=(255,255,255); ORANGE=(236,128,60); YEL=(255,214,0); GREEN=(46,125,62); DARK=(30,26,22); GRAY=(200,195,185)

# ---------- 年表（公開年：ジブリ公式／出来事：いま20〜30代の女性が懐かしい話題。言い回しはやわらかく） ----------
#   (年, [ジブリ作品], 場面写真, その年の出来事)
TL=[(1984,['風の谷のナウシカ'],'nausicaa010','福沢諭吉の\n一万円札が出た'),(1986,['天空の城ラピュタ'],'laputa005','ドラクエが\n出た'),
(1988,['となりのトトロ','火垂るの墓'],'totoro002','東京ドームが\nできた'),(1989,['魔女の宅急便'],'majo001','ゲームボーイが\n出た'),
(1991,['おもひでぽろぽろ'],'omoide003','ジュリアナ東京が\nオープン'),(1992,['紅の豚'],'porco002','セーラームーンが\n始まった'),
(1994,['平成狸合戦ぽんぽこ'],'tanuki010','プレステが\n出た'),(1995,['耳をすませば'],'mimi005','プリクラが\n登場'),
(1996,[],None,'たまごっち、ポケモン赤緑ブーム'),(1997,['もののけ姫'],'mononoke003','アニメの\nポケモンが\n始まった'),
(1998,[],None,'さくらちゃん、モー娘。デビュー'),(1999,['ホーホケキョ となりの山田くん'],'yamada009','おジャ魔女どれみが\n始まった'),
(2000,[],None,'ハム太郎が始まった'),(2001,['千と千尋の神隠し'],'chihiro003','USJと\nディズニーシーが\nできた'),
(2002,['猫の恩返し'],'baron002','東京ミュウミュウが\n始まった'),(2004,['ハウルの動く城'],'howl010','プリキュア、\nラブベリ登場'),
(2005,[],None,'ニンテンドッグスで犬を育ててた'),(2006,['ゲド戦記'],'ged007','Wii が\n出た'),
(2008,['崖の上のポニョ'],'ponyo006','iPhone が\n日本に上陸'),(2010,['借りぐらしのアリエッティ'],'karigurashi002','AKBの\nヘビロテが\nはやった'),
(2011,['コクリコ坂から'],'kokurikozaka003','LINE が\n始まった'),(2012,[],None,'スカイツリーができた'),
(2013,['風立ちぬ','かぐや姫の物語'],'kazetachinu002','「今でしょ」「じぇじぇじぇ」がはやった'),(2014,['思い出のマーニー'],'marnie006','アナ雪と\n妖怪ウォッチ'),
(2016,['レッドタートル ある島の物語'],'redturtle004','みんな\nポケモンGO\nしてた'),(2017,[],None,'「インスタ映え」がはやった'),
(2019,[],None,'タピオカの行列、令和になった'),(2020,['アーヤと魔女（テレビ）'],'aya003','鬼滅の映画が\n大ヒット'),
(2021,[],None,'東京オリンピック'),(2023,['君たちはどう生きるか'],'kimitachi003','WBCで\n日本が優勝')]
SECOND={2013:'kaguyahime004'}   # 2作品の年は写真を2枚

# ---------- 文字 ----------
_fc={}
def font(w,sz,kind):
    k=(w,sz,kind)
    if k not in _fc: _fc[k]=ImageFont.truetype(S+f'fonts/{kind}{w}.woff',sz)
    return _fc[k]
def segs(t):
    out=[]
    for ch in t:
        k='lat' if ord(ch)<0x2000 else 'jp'
        if out and out[-1][0]==k: out[-1][1]+=ch
        else: out.append([k,ch])
    return out
def tlen(t,sz,w=900): return sum(font(w,sz,k).getlength(s) for k,s in segs(t))
def text(L,t,sz,x,cy,fill,w=900,stw=0,stc=DARK,anchor='l',maxw=None):
    while maxw and tlen(t,sz,w)>maxw: sz-=2
    d=ImageDraw.Draw(L); x={'m':x-tlen(t,sz,w)/2,'r':x-tlen(t,sz,w)}.get(anchor,x)
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
    return sz
def pill(L,x,cy,t,sz,bg,fg=WHITE,pad=26,h=None,anchor='l',maxw=None):
    while maxw and tlen(t,sz)+pad*2>maxw: sz-=2
    tw=tlen(t,sz); h=h or sz*1.6; x0=x-tw/2-pad if anchor=='m' else x
    ImageDraw.Draw(L).rounded_rectangle((x0,cy-h/2,x0+tw+pad*2,cy+h/2),h/2,fill=bg,outline=WHITE,width=4)
    text(L,t,sz,x0+pad,cy,fg); return x0+tw+pad*2
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def still(n,w,h):
    im=Image.open(S+f'gb/{n}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=(im.width-w)//2; y=(im.height-h)//2; c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,18))
    o=Image.new('RGBA',(w+12,h+12),(0,0,0,0)); wb=Image.new('RGBA',o.size,WHITE+(255,)); wb.putalpha(rmask(w+12,h+12,22)); o.alpha_composite(wb); o.alpha_composite(c,(6,6)); return o

# ---------- 年表の帯（上が新しい年。下から上へ積む） ----------
# いつものデザイン：方眼の背景＋縦の年表の線＋ジブリの年は白いカード（緑フチ）、ほかの年は白い札
AX=250; XC=290; XR=830       # 年表の線・内容の左端・右端（右のいいね等を避ける）
LINE=(46,125,62); INK=(45,40,36); SUBG=(120,110,100)
def card_shadow(L,box,r=30,a=110):
    sh=Image.new('RGBA',L.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((box[0]+4,box[1]+10,box[2]+4,box[3]+10),r,fill=(0,0,0,a)); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
def chara(n,h):
    im=Image.open(S+f'cut/{n}.png').convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<40 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS); ow=10; pad=30
    big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A_=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A_.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); w_=Image.new('RGBA',big.size,(255,255,255,0)); w_.putalpha(o); out.alpha_composite(w_); out.alpha_composite(big); return out
FCH={1984:'nausicaa007',1986:'laputa005',1988:'totoro018',1989:'majo018',1991:'omoide002',1992:'porco010',1994:'tanuki010',1995:'mimi032',
1997:'mononoke003',1999:'yamada010',2001:'chihiro019',2002:'baron002',2004:'howl035',2008:'ponyo003_c',2010:'karigurashi033',2011:'kok_shunumi',
2013:'kaguyahime009',2014:'marnie001_c',2023:'kimitachi027'}   # 映画の年のキャラ（場面写真の切り抜き）
OBJ={1996:('cut','tamagotchi','Photo: Nori Norisa / CC BY 2.0'),2005:('cut','ds','Photo: Evan-Amos / Public domain'),2012:('photo','skytree','Photo: Akonnchiroll / CC0')}   # Wikimedia Commons
def chara_path(p,h):
    im=Image.open(p).convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<40 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS) if im.height>=im.width else im.resize((h,int(im.height*h/im.width)),Image.LANCZOS)
    ow=10; pad=30; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A_=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A_.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); w_=Image.new('RGBA',big.size,(255,255,255,0)); w_.putalpha(o); out.alpha_composite(w_); out.alpha_composite(big); return out.rotate(-6,Image.BICUBIC,expand=True)
def still_path(p,w,h):
    im=Image.open(p).convert('RGB'); s_=max(w/im.width,h/im.height); im=im.resize((int(im.width*s_)+1,int(im.height*s_)+1),Image.LANCZOS)
    x=(im.width-w)//2; y=(im.height-h)//2; c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,16))
    o=Image.new('RGBA',(w+12,h+12),(0,0,0,0)); wb=Image.new('RGBA',o.size,WHITE+(255,)); wb.putalpha(rmask(w+12,h+12,20)); o.alpha_composite(wb); o.alpha_composite(c,(6,6)); return o.rotate(5,Image.BICUBIC,expand=True)
ROWCH={}
def row(y_,films,stl,ev):
    ev=ev.replace('\n','')
    if films:
        h=470; L=Image.new('RGBA',(W,h),(0,0,0,0)); d=ImageDraw.Draw(L); box=(XC,14,XR,h-14)
        if y_ in FCH:   # その映画のキャラをカードの右うしろに
            c=chara(FCH[y_],250); ROWCH[y_]=(c,XR+95,h-8)   # 帯には描かず、流れる間ゆっくりゆらゆら
        card_shadow(L,box); d.rounded_rectangle(box,30,fill=(255,253,248,255),outline=GREEN,width=5)
        text(L,'／'.join(films),46,(XC+XR)/2,72,GREEN,anchor='m',maxw=XR-XC-50)
        if y_ in SECOND:
            sw,sh_=250,140; L.alpha_composite(still(stl,sw,sh_),(XC+22,114)); L.alpha_composite(still(SECOND[y_],sw,sh_),(XR-22-sw-12,114))
        else:
            sw,sh_=480,250; L.alpha_composite(still(stl,sw,sh_),(int((XC+XR)/2-(sw+12)/2),108))
        pill(L,(XC+XR)/2,h-58,ev,30,(250,236,214),fg=INK,pad=24,h=56,anchor='m',maxw=XR-XC-40)
        d.ellipse((AX-26,h/2-26,AX+26,h/2+26),fill=ORANGE,outline=WHITE,width=6)
        text(L,str(y_),58,AX-40,h/2,ORANGE,stw=10,stc=WHITE,anchor='r')
        return L
    if y_ in OBJ:   # フリー素材の写真を右に（クレジットつき）
        kind,src,cr=OBJ[y_]; h=300; L=Image.new('RGBA',(W,h),(0,0,0,0)); d=ImageDraw.Draw(L)
        if kind=='cut': im=chara_path(NR+f'../obj/{src}.png',210)
        else: im=still_path(NR+f'../obj/{src}.jpg',170,230)
        L.alpha_composite(im,(int(XR+30-im.width/2),int(h/2-10-im.height/2)))
        text(L,cr,18,XR+30,h-14,SUBG,w=800,stw=4,stc=WHITE,anchor='m')
        ls=ev.split('、') if tlen(ev,34)>XR-XC-200 else [ev]; ls=[l+('、' if i<len(ls)-1 else '') for i,l in enumerate(ls)]
        tw=max(tlen(l,34) for l in ls); bh=36+len(ls)*24; box=(XC,h/2-bh,XC+tw+50,h/2+bh)
        card_shadow(L,box,24,70); d.rounded_rectangle(box,24,fill=(255,255,255,255))
        for i,l in enumerate(ls): text(L,l,34,XC+25,h/2+(i-(len(ls)-1)/2)*48,INK)
        d.ellipse((AX-15,h/2-15,AX+15,h/2+15),fill=WHITE,outline=GREEN,width=6); text(L,str(y_),40,AX-34,h/2,INK,stw=8,stc=WHITE,anchor='r')
        return L
    h=110; L=Image.new('RGBA',(W,h),(0,0,0,0)); d=ImageDraw.Draw(L)
    tw=min(tlen(ev,34),XR-XC-60); box=(XC,18,XC+tw+50,h-18)
    card_shadow(L,box,24,70); d.rounded_rectangle(box,24,fill=(255,255,255,255))
    text(L,ev,34,XC+25,h/2,INK,maxw=XR-XC-60)
    d.ellipse((AX-15,h/2-15,AX+15,h/2+15),fill=WHITE,outline=GREEN,width=6)
    text(L,str(y_),40,AX-34,h/2,INK,stw=8,stc=WHITE,anchor='r')
    return L
ROWS=[row(*r[:2],r[2],r[3]) for r in TL]

# つかみ（帯のいちばん下＝最初に見える画面。そのまま下へ流れていく）
HOOKCH=[]
def hook_layer():
    L=Image.new('RGBA',(W,H),(0,0,0,0))
    # 上下3体ずつ、作品のキャラ（切り抜き）＋公開年
    for n,yr,x,y,h in [('totoro018',1988,190,560,300),('majo018',1989,540,560,240),('mimi032',1995,890,560,310),
                       ('chihiro019',2001,190,1340,300),('howl035',2004,540,1345,290),('ponyo003_c',2008,890,1340,250)]:
        c=chara(n,h); HOOKCH.append((c,x,y+c.height/2))   # キャラは帯に描かず、別に重ねてゆらゆら
        pill(L,x,(y-c.height/2+14) if y<960 else (y+c.height/2-14),f'{yr}年',36,ORANGE,pad=22,h=62,anchor='m')   # 上の段は頭の上、下の段は足もとに
    text(L,'あなたはどの',92,W/2,830,GREEN,stw=16,stc=WHITE,anchor='m')
    text(L,'ジブリ作品と同い年？',104,W/2,975,ORANGE,stw=18,stc=WHITE,anchor='m',maxw=1000)
    pill(L,W/2,1120,'ジブリ年表 1984〜2023',46,GREEN,pad=40,h=84,anchor='m')
    text(L,'© Studio Ghibli',22,W/2,1700,SUBG,w=800,stw=4,stc=WHITE,anchor='m')
    return L
HOOK=hook_layer()
GAP=18; TOPPAD=820
hs=[r.height for r in ROWS]; STRIP_H=H+sum(hs)+GAP*len(ROWS)+TOPPAD
STRIP=Image.new('RGBA',(W,STRIP_H),(0,0,0,0))
y=STRIP_H-H; CEN={}; POS=[]
for (yr,*_),r in zip(TL,ROWS):
    y-=r.height+GAP; POS.append(y); CEN[yr]=y+r.height/2
# 年表の線（いちばん古い年の少し下から、いちばん新しい年まで）
d=ImageDraw.Draw(STRIP); d.line((AX,CEN[2023],AX,CEN[1984]+260),fill=WHITE,width=18); d.line((AX,CEN[2023],AX,CEN[1984]+260),fill=LINE,width=8)
for r,y_ in zip(ROWS,POS): STRIP.alpha_composite(r,(0,y_))
CHABS=[(c,x-DX,POS[i]+yb) for i,(yr,*_) in enumerate(TL) if yr in ROWCH for c,x,yb in [ROWCH[yr]]]   # 帯の上の位置（下端）
STRIP.alpha_composite(HOOK,(0,STRIP_H-H))
STRIP=STRIP.crop((DX,0,W,STRIP_H)); _t=Image.new('RGBA',(W,STRIP_H),(0,0,0,0)); _t.alpha_composite(STRIP,(0,0)); STRIP=_t   # 全体を左へ（DX）

# ---------- 背景：いつもの緑の方眼。すみのキャラは年代で入れ替え ----------
GRID=Image.open(TK+'bg_grid.jpg').convert('RGB').resize((W,H))
# ---------- タイムライン ----------
def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
T_HOOK=0.25+wdur('hook')+0.15       # つかみを止めて見せる（「生まれた年から」で流れ始める）
WIN_START=STRIP_H-H                  # 画面の上端が帯のどこにあるか（最初はいちばん下＝つかみ）
WIN_END=CEN[2023]-700               # 2023年が y=700 あたりで止まる
# 一定の速さで流し、その年がまん中に来たときに話せる解説だけを選ぶ（重なるものは入れない）
CAND=(1984,1988,1992,1995,2001,2008,2013,2016,2023)   # 雑学ではなく「懐かしさ」に寄せた解説
T_END=0.3+wdur('end')+0.5; T_FOL=0.1+wdur('fol')+0.4; TARGET=61.0; GAPN=0.5
def plan(SC):
    V=(WIN_START-WIN_END)/SC; tc=lambda yr: T_HOOK+(WIN_START-(CEN[yr]-H*0.45))/V
    sel=[]; e=T_HOOK+wdur('hook2')+GAPN
    for yr in CAND:
        t0=tc(yr)-0.4
        if yr==2023:
            while sel and t0<sel[-1][1]+wdur(f'n{sel[-1][0]}')+GAPN: sel.pop()
            t0=max(t0,sel[-1][1]+wdur(f'n{sel[-1][0]}')+GAPN if sel else e)
        elif t0<e:
            if e-t0>1.0: continue   # 1秒以上遅れるなら入れない
            t0=e
        sel.append((yr,t0)); e=t0+wdur(f'n{yr}')+GAPN
    tend=max(T_HOOK+SC+0.3,e-GAPN+0.3)
    narr=[('hook',0.25),('hook2',T_HOOK)]+[(f'n{yr}',t0) for yr,t0 in sel]+[('end',tend),('fol',tend+T_END+0.1)]
    return narr,V,tend,tend+T_END+T_FOL
lo,hi=30.0,80.0
for _ in range(40):
    SCROLL=(lo+hi)/2
    if plan(SCROLL)[3]>TARGET: hi=SCROLL
    else: lo=SCROLL
SCROLL=lo; NARR,V,_tend,TOT=plan(SCROLL); print('total',round(TOT,2),'scroll',round(SCROLL,1),'narr',[k for k,_ in NARR])
def win(t):
    if t<T_HOOK: return WIN_START
    return max(WIN_END,WIN_START-V*(t-T_HOOK))
def t_at_center(yr): return T_HOOK+(WIN_START-(CEN[yr]-H/2))/V
SUB={'hook2':'生まれた年から\n探してみてください','n1984':'ナウシカは\nジブリ誕生前の作品','n1986':'ジブリ最初の作品が\nラピュタ','n1988':'トトロと火垂るの墓は\n2本立てで公開',
'n1989':'キキの声は\n高山みなみさん','n1997':'もののけ姫は\n当時の興行記録を塗り替えた','n2001':'千と千尋は19年間\n興行収入1位だった',
'n2004':'ハウルの声は\n木村拓哉さん','n2008':'ポニョの歌は\n大橋のぞみちゃんと藤岡藤巻','n2013':'風立ちぬは\n引退作と言われた',
'n2023':'君たちはどう生きるかは\nアカデミー賞を受賞','n1992':'紅の豚の主人公は\nブタになった飛行機乗り','n1995':'耳をすませばの監督は\n近藤喜文さん','n2010':'アリエッティは\n米林宏昌さんの初監督作品','n2016':'レッドタートルは\n海外の監督と組んだ作品'}
def sub_layer(t):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); ls=t.split('\n'); d=ImageDraw.Draw(L)
    wmax=max(tlen(l,42) for l in ls); h=len(ls)*60+40; cy=1560
    card_shadow(L,(CX-wmax/2-36,cy-h/2,CX+wmax/2+36,cy+h/2)); d.rounded_rectangle((CX-wmax/2-36,cy-h/2,CX+wmax/2+36,cy+h/2),30,fill=(255,253,248,250),outline=ORANGE,width=5)
    for j,l in enumerate(ls): text(L,l,42,CX,cy+(j-(len(ls)-1)/2)*60,INK,anchor='m')
    return L
SUBL={k:sub_layer(v) for k,v in SUB.items()}
ENDL=Image.new('RGBA',(W,H),(0,0,0,0)); card_shadow(ENDL,(CX-400,1380,CX+400,1680)); ImageDraw.Draw(ENDL).rounded_rectangle((CX-400,1380,CX+400,1680),40,fill=(255,253,248,255),outline=GREEN,width=6); text(ENDL,'同い年の作品はどれだった？',54,CX,1490,GREEN,anchor='m'); pill(ENDL,CX,1600,'コメントで教えてね',40,ORANGE,pad=34,h=74,anchor='m')
CR=Image.new('RGBA',(W,H),(0,0,0,0)); text(CR,'© Studio Ghibli',22,CX,1720,SUBG,w=800,stw=4,stc=WHITE,anchor='m')
MIYA=Image.open(HERE+'obj/miyazaki.png').convert('RGBA'); MIYA=MIYA.resize((int(MIYA.width*820/MIYA.height),820),Image.LANCZOS)
_b=Image.new('RGBA',(MIYA.width+60,MIYA.height+60),(0,0,0,0)); _b.alpha_composite(MIYA,(30,30)); _o=_b.getchannel('A').point(lambda v:255 if v>90 else 0).filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(1.2))
_w=Image.new('RGBA',_b.size,(255,255,255,0)); _w.putalpha(_o); _w.alpha_composite(_b); MIYA=_w   # 白フチ（はみ出させて揺れても隙間が出ないように）
MIYA_CR=Image.new('RGBA',(W,H),(0,0,0,0)); text(MIYA_CR,'宮崎駿監督　Photo: Natasha Baucas / CC BY 2.0',20,330,H-40,SUBG,w=800,stw=4,stc=WHITE,anchor='m')
BYRS=[(1990,185,668),(1995,540,650),(2000,895,668),(1993,185,1212),(1998,540,1230),(2003,895,1212)]   # 生まれ年の帯（つかみで順に出る）
BYL=[]
for yr,x,y in BYRS:
    L=Image.new('RGBA',(W,H),(0,0,0,0)); pill(L,x,y,f'{yr}年生まれ',42,[ORANGE,GREEN,(206,72,80)][len(BYL)%3],pad=26,h=76,anchor='m'); BYL.append(L)
BY0,BYD=0.5,0.22   # 出始め・間隔（秒）
def bylayer(t,fade=1.0):
    o=Image.new('RGBA',(W,H),(0,0,0,0))
    for j,L in enumerate(BYL):
        k=int((t-BY0-j*BYD)*FPS)
        if k<0: continue
        p_=popped(L,k)
        if fade<1: p_=p_.copy(); p_.putalpha(p_.getchannel('A').point(lambda v:int(v*fade)))
        o.alpha_composite(p_)
    return o
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
POP=[0.6,0.9,1.08,1.03]
def popped(L,k):
    if k>=len(POP): return L
    s=POP[k]; bb=L.getbbox(); c=L.crop(bb).resize((max(1,int((bb[2]-bb[0])*s)),max(1,int((bb[3]-bb[1])*s))),Image.BICUBIC)
    o=Image.new('RGBA',(W,H),(0,0,0,0)); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
def frame(t):
    if t>=dict(NARR)['fol']-0.1: return FOLLOW   # 締めのナレーションが終わってから
    top=win(t); im=GRID.convert('RGBA')
    for j,(c,x,yb) in enumerate(CHABS):   # 映画のキャラ：下を支点に±2°でゆっくりゆらゆら（カードの後ろ）
        y=yb-top
        if -50<y<H+c.height:
            ang=2*math.sin(2*math.pi*0.35*t+j*1.1); r=c.rotate(ang,Image.BICUBIC,expand=True,center=(c.width/2,c.height))
            im.alpha_composite(r,(int(x-r.width/2),int(y-r.height+(r.height-c.height)/2)))
    dy=WIN_START-top   # つかみのキャラ：下を支点に±3°でゆらゆら（帯と一緒に流れる）
    if dy<H:
        for j,(c,x,yb) in enumerate(HOOKCH):
            ang=3*math.sin(2*math.pi*0.55*t+j*1.3); r=c.rotate(ang,Image.BICUBIC,expand=True,center=(c.width/2,c.height))
            im.alpha_composite(r,(int(x-DX-r.width/2),int(yb+dy-r.height+(r.height-c.height)/2)))
    im.alpha_composite(STRIP.crop((0,int(top),W,int(top)+H)))
    tm=dict(NARR)['n2023']   # 「アカデミー賞を受賞しました」で宮崎駿監督が下からニョキッ＋ゆらゆら
    te=dict(NARR)['end']
    if tm<=t<te:   # 締めのカードが出るまで
        u=min(1,(t-tm)/0.45); u=1-(1-u)**3; ang=3*math.sin(2*math.pi*0.6*(t-tm))
        r=MIYA.rotate(ang,Image.BICUBIC,center=(MIYA.width/2,MIYA.height))
        im.alpha_composite(r,(int(330-r.width/2),int(H+40-r.height*u)))
        im.alpha_composite(MIYA_CR)
    for k,t0 in NARR:
        if k=='n2023' and k in SUBL and t0<=t<t0+wdur(k)+0.4:   # 字幕はアカデミー賞の解説だけ
            im.alpha_composite(SUBL[k])
    if t>=te: im.alpha_composite(popped(ENDL,int((t-te)*FPS)))
    if WIN_START-top>300: im.alpha_composite(CR)   # つかみのクレジットと重ならないように
    return im.convert('RGB')

if len(sys.argv)>3 and sys.argv[3]=='stills':
    frame(0).save(HERE+'thumbnail.png')   # サムネは最初の画面（キャラ＋公開年）
    for j,t in enumerate([T_HOOK+1.0,t_at_center(1988),t_at_center(2001),T_HOOK+SCROLL+1.0]): frame(t).save(NR+f'../still{j}.jpg',quality=85)
    sys.exit()
N=int(round(TOT*FPS))
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',NR+'../v.mp4'],stdin=subprocess.PIPE)
for k in range(N): enc.stdin.write(np.asarray(frame(k/FPS)).tobytes())
enc.stdin.close(); enc.wait()
M=int(TOT*SR)+SR; mix=np.zeros(M,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:M-i]; mix[i:i+len(a)]+=a*g
for k,t0 in NARR: add(rd(NR+k+'.wav'),t0,1.0)
add(rd(S+'labsfx/kira1.wav'),0.1,0.4)
for yr,f,*_ in TL:
    pass
add(rd(S+'labsfx/shine2.wav'),dict(NARR)['end'],0.4)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
