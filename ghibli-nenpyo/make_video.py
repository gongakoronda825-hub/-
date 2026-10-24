# 初めて見たジブリ、何歳だった？ ジブリ年表（上から下に流れる年表）
# 使い方: python3 make_video.py <作業フォルダ(setup.shのW)> <ナレーションwavのフォルダ> [stills]
import sys,os,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S,NR=[a.rstrip('/')+'/' for a in sys.argv[1:3]]
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'ghibli_nenpyo.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
WHITE=(255,255,255); ORANGE=(236,128,60); YEL=(255,214,0); GREEN=(46,125,62); DARK=(30,26,22); GRAY=(200,195,185)

# ---------- 年表（公開年：ジブリ公式／出来事：いま20〜30代の女性が懐かしい話題。言い回しはやわらかく） ----------
#   (年, [ジブリ作品], 場面写真, その年の出来事)
TL=[(1984,['風の谷のナウシカ'],'nausicaa010','福沢諭吉の\n一万円札が出た'),(1986,['天空の城ラピュタ'],'laputa005','ドラクエが\n出た'),
(1988,['となりのトトロ','火垂るの墓'],'totoro002','東京ドームが\nできた'),(1989,['魔女の宅急便'],'majo001','ゲームボーイが\n出た年'),
(1991,['おもひでぽろぽろ'],'omoide003','ジュリアナ東京が\nオープン'),(1992,['紅の豚'],'porco002','セーラームーンが\n始まった'),
(1994,['平成狸合戦ぽんぽこ'],'tanuki010','プレステが\n出た'),(1995,['耳をすませば'],'mimi005','プリクラが\n登場'),
(1996,[],None,'たまごっち、ポケモン赤緑ブーム'),(1997,['もののけ姫'],'mononoke003','アニメの\nポケモンが\n始まった'),
(1998,[],None,'さくらちゃん、モー娘。デビュー'),(1999,['ホーホケキョ となりの山田くん'],'yamada009','おジャ魔女どれみが\n始まった'),
(2000,[],None,'ハム太郎が始まった'),(2001,['千と千尋の神隠し'],'chihiro003','USJと\nディズニーシーが\nできた'),
(2002,['猫の恩返し'],'baron002','東京ミュウミュウが\n始まった'),(2004,['ハウルの動く城'],'howl010','プリキュア、\nラブベリ登場'),
(2005,[],None,'ニンテンドッグスで犬を育ててた'),(2006,['ゲド戦記'],'ged007','Wii が\n出た年'),
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
    d=ImageDraw.Draw(L); x=x-tlen(t,sz,w)/2 if anchor=='m' else x
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
X0=70; XT=300     # 年の列・内容の列（右のいいね等を避けて x<=900）
def row(y_,films,stl,ev):
    if films:
        h=330; L=Image.new('RGBA',(W,h),(0,0,0,0)); d=ImageDraw.Draw(L)
        d.rounded_rectangle((X0-20,10,900,h-10),30,fill=(0,0,0,120))
        text(L,str(y_),78,X0,h/2,YEL,stw=8)
        x=XT
        for f in films: x=pill(L,x,62,f,40 if len(films)==1 else 34,ORANGE,maxw=600 if len(films)==1 else 300)+12
        sw,sh_=(330,186) if y_ not in SECOND else (250,141)
        L.alpha_composite(still(stl,sw,sh_),(XT,100))
        if y_ in SECOND: L.alpha_composite(still(SECOND[y_],sw,sh_),(XT+sw+24,100))
        # 出来事は写真の右（2枚の年は下）
        if y_ in SECOND: text(L,ev,30,XT,h-42,WHITE,stw=6,maxw=580)
        else:
            ls=ev.split('\n')   # 改行位置は手動
            for j,l in enumerate(ls): text(L,l,32,XT+sw+28,190+(j-(len(ls)-1)/2)*46,WHITE,stw=6,maxw=900-XT-sw-36)
        return L
    h=120; L=Image.new('RGBA',(W,h),(0,0,0,0))
    text(L,str(y_),56,X0+10,h/2,WHITE,stw=7); text(L,ev,34,XT,h/2,WHITE,stw=7,maxw=600)
    return L
def wrap(t,n):
    if len(t)<=n: return [t]
    for sep in ('／','・',' '):
        if sep in t: a,b=t.split(sep,1); return [a+('・' if sep=='・' else ''),b] if sep!=' ' else [a,b]
    return [t[:n],t[n:]]
ROWS=[row(*r[:2],r[2],r[3]) for r in TL]

# つかみ（帯のいちばん下＝最初に見える画面。そのまま下へ流れていく）
def hook_layer():
    L=Image.new('RGBA',(W,H),(0,0,0,0))
    for n,(x,y,r) in zip(['totoro002','chihiro003','majo001','mononoke003'],[(280,470,-5),(800,430,5),(280,1420,4),(800,1460,-5)]):
        c=still(n,440,248).rotate(r,Image.BICUBIC,expand=True); L.alpha_composite(c,(int(x-c.width/2),int(y-c.height/2)))
    text(L,'初めて見たジブリ',100,W/2,830,WHITE,stw=14,stc=GREEN,anchor='m')
    text(L,'何歳だった？',130,W/2,975,YEL,stw=16,stc=DARK,anchor='m')
    pill(L,W/2,1120,'ジブリ年表 1984〜2023',46,ORANGE,pad=40,h=84,anchor='m')
    text(L,'© Studio Ghibli',22,W/2,1660,WHITE,w=800,stw=3,anchor='m')
    return L
HOOK=hook_layer()
GAP=24; TOPPAD=820
hs=[r.height for r in ROWS]; STRIP_H=H+sum(hs)+GAP*len(ROWS)+TOPPAD
STRIP=Image.new('RGBA',(W,STRIP_H),(0,0,0,0))
STRIP.alpha_composite(HOOK,(0,STRIP_H-H))
y=STRIP_H-H; CEN={}
for (yr,*_),r in zip(TL,ROWS):
    y-=r.height+GAP; STRIP.alpha_composite(r,(0,y)); CEN[yr]=y+r.height/2
# 右のボタンを避けるため全体を左へ（DX）
STRIP=STRIP.crop((DX,0,W,STRIP_H)); _t=Image.new('RGBA',(W,STRIP_H),(0,0,0,0)); _t.alpha_composite(STRIP,(0,0)); STRIP=_t

# ---------- 背景：いま画面のまん中を通ったジブリ作品の場面写真（ぼかし） ----------
def blurbg(n):
    im=Image.open(S+f'gb/{n}.jpg').convert('RGB'); cw=int(im.height*W/H); x=(im.width-cw)//2
    b=im.crop((x,0,x+cw,im.height)).resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(14))
    return Image.blend(b,Image.new('RGB',(W,H),(0,0,0)),0.45)
BGS={yr:blurbg(st) for yr,f,st,_ in TL if f}
FIRSTBG=blurbg('nausicaa010')

# ---------- タイムライン ----------
def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
T_HOOK=0.25+wdur('hook')+0.3        # つかみを止めて見せる
WIN_START=STRIP_H-H                  # 画面の上端が帯のどこにあるか（最初はいちばん下＝つかみ）
WIN_END=CEN[2023]-700               # 2023年が y=700 あたりで止まる
SCROLL=56.0; V=(WIN_START-WIN_END)/SCROLL
T_END=0.3+wdur('end')+1.2; T_FOL=0.1+wdur('fol')+0.4
TOT=T_HOOK+SCROLL+T_END+T_FOL; print('total',round(TOT,2))
def win(t):
    if t<T_HOOK: return WIN_START
    return max(WIN_END,WIN_START-V*(t-T_HOOK))
def t_at_center(yr): return T_HOOK+(WIN_START-(CEN[yr]-H/2))/V
NARR=[('hook',0.25),('n1988',t_at_center(1988)+0.2),('n2001',t_at_center(2001)+0.2),('end',T_HOOK+SCROLL+0.3),('fol',T_HOOK+SCROLL+T_END+0.1)]
SUB={'hook':'自分の生まれた年から\n探してみて！','n1988':'トトロと火垂るの墓は\n同じ日に2本立てで公開','n2001':'千と千尋は約19年間\n日本の興行収入1位だった'}
def sub_layer(t):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); ls=t.split('\n'); d=ImageDraw.Draw(L)
    wmax=max(tlen(l,42) for l in ls); h=len(ls)*60+40; cy=1560
    d.rounded_rectangle((CX-wmax/2-36,cy-h/2,CX+wmax/2+36,cy+h/2),30,fill=(20,20,20,200))
    for j,l in enumerate(ls): text(L,l,42,CX,cy+(j-(len(ls)-1)/2)*60,WHITE,anchor='m')
    return L
SUBL={k:sub_layer(v) for k,v in SUB.items()}
ENDL=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(ENDL).rounded_rectangle((CX-420,1390,CX+420,1680),40,fill=(20,18,16,225)); pill(ENDL,CX,1500,'あなたの初ジブリは？',58,GREEN,pad=46,h=104,anchor='m'); text(ENDL,'コメントで教えてね',40,CX,1610,WHITE,stw=8,anchor='m')
CR=Image.new('RGBA',(W,H),(0,0,0,0)); text(CR,'© Studio Ghibli',22,CX,1700,WHITE,w=800,stw=3,anchor='m')
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
POP=[0.6,0.9,1.08,1.03]
def popped(L,k):
    if k>=len(POP): return L
    s=POP[k]; bb=L.getbbox(); c=L.crop(bb).resize((max(1,int((bb[2]-bb[0])*s)),max(1,int((bb[3]-bb[1])*s))),Image.BICUBIC)
    o=Image.new('RGBA',(W,H),(0,0,0,0)); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
def bg_at(top):
    # まん中の線を通りすぎた最新のジブリ作品。切り替えは0.5秒ぶんの距離でクロスフェード
    cur=None; prev=None; frac=1.0
    for yr,f,st,_ in TL:
        if f and CEN[yr]>=top+H/2: prev,cur=cur,yr; frac=min(1.0,(CEN[yr]-(top+H/2))/(V*0.5))
    if cur is None: return FIRSTBG
    a=BGS[prev] if prev else FIRSTBG
    return Image.blend(a,BGS[cur],frac) if frac<1 else BGS[cur]
def frame(t):
    if t>=T_HOOK+SCROLL+T_END: return FOLLOW
    top=win(t); im=bg_at(top).convert('RGBA')
    im.alpha_composite(STRIP.crop((0,int(top),W,int(top)+H)))
    for k,t0 in NARR:
        if k in SUBL and t0<=t<t0+wdur(k)+0.4: im.alpha_composite(SUBL[k])
    if t>=T_HOOK+SCROLL: im.alpha_composite(popped(ENDL,int((t-T_HOOK-SCROLL)*FPS)))
    if t>=T_HOOK: im.alpha_composite(CR)
    return im.convert('RGB')

if len(sys.argv)>3 and sys.argv[3]=='stills':
    frame(0).save(HERE+'thumbnail.png')
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
    if f: add(rd(S+'labsfx/touch1.wav'),t_at_center(yr)-0.6,0.18)   # ジブリの年が来るたび小さく「ポン」
add(rd(S+'labsfx/shine2.wav'),T_HOOK+SCROLL,0.4)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
