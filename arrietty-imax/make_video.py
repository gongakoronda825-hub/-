# アリエッティをIMAXで観た人の感想（2026/10/25）ナレーション動画　約61秒
# デザイン：ポスターの黄緑のグラデーション（方眼うすく）＋ゆるく湾曲したIMAXスクリーン。文字は Zen Maru Gothic、こげ茶＋アリエッティの赤・金茶
# 使い方: python3 make_narration.py <出力先>/ → python3 make_video.py <作業フォルダ(setup.shのW)> <出力先>/narr [stills]
import json,sys,os,wave,subprocess,numpy as np
from PIL import Image,ImageDraw
S=sys.argv[1].rstrip('/')+'/'; NR=sys.argv[2].rstrip('/')+'/'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'arrietty_imax.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
TOTAL=61.5   # 収益化の「1分以上」を超えるよう、最後のフォロー画像で尺を合わせる
CREDIT='© 2010 Mary Norton/Keiko Niwa/Studio Ghibli, NDHDMTW'
INK=(58,46,40); WHITE=(255,255,255); RED=(214,70,50); GOLD=(168,104,24); DIM=(120,110,100); SUBC=(100,88,80)

sys.path.insert(0,HERE+'../ghibli-toolkit/lib'); import screen_fx as fx
fx.init(S,theme=dict(INK=INK,ACC=RED,GOLD=GOLD,DIM=DIM,SUBC=SUBC),tk=TK)
from screen_fx import text,tlen,layer,Screen,POP,popped,pulse,ease
def gb(n): return Image.open(S+f'gb/karigurashi{n:03d}.jpg').convert('RGB')
def bg_frames(B,n):
    for _ in range(n): yield B.convert('RGBA')
# キャラ（スクリーンのふちに小さく座る＝小人。紹介作品から3体）
CH={n:fx.sticker(S+f'cut/karigurashi{n:03d}.png',h) for n,h in ((33,180),(12,160),(48,165))}

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

def head(L,lab,ttl): fx.head(L,lab,ttl,CX)   # 両はしのキャラと重ならない幅
def footer(L,cx=CX):
    text(L,'観た人の感想をもとに再構成',22,cx,1612,DIM,w='Bold')
    text(L,CREDIT,20,cx,1644,DIM,w='Bold')
    text(L,'ナレーション：VOICEVOX 青山龍星',16,cx,1672,DIM,w='Bold')
def row_layer(r): return fx.row(r[0],r[1],CX,0)
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
    out=[]; L=layer(); fx.big_band(L,CX,y,'IMAX上映','〜11/2（月）')
    out.append((L,0.0,'pulse'))
    L=layer(); yy=y+170; d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-400,yy,CX+400,yy+84),26,fill=(255,255,255,235),outline=DIM+(255,),width=3)
    text(L,'全国の拡大上映',28,CX-260,yy+42,SUBC,w='Black',maxw=240,shadow=False); text(L,'10/30（金）〜11/12（木）',36,CX+110,yy+42,SUBC,w='Bold',maxw=500,shadow=False); out.append((L,0.3))
    L=layer(); text(L,'※拡大上映は[IMAXではありません]（通常の上映）',30,CX,yy+125,SUBC,w='Black'); out.append((L,0.4))
    L=layer(); text(L,'[迷ってる人]に送ってあげて',52,CX,yy+215,INK,w='Black'); out.append((L,0.78))
    L=layer(); text(L,'※劇場によって設備が違います（レーザーでない劇場、2K上映の劇場あり）',22,CX,yy+285,DIM,w='Bold'); out.append((L,0.0))
    return out
def logo(name,w,border): return fx.logo(HERE+f'parts/{name}.png',w,border)
def hook():
    # サムネ：上にポスターのタイトルロゴ、まん中にスクリーン、下に「(IMAXロゴ)で観る 意味ある？」（y=240〜1680に収める）
    L=layer(); sc=Screen(gb(33),540,775,1000,430,0.55)
    t=logo('title_cut',600,[(WHITE,12)]); L.alpha_composite(t,(int(540-t.width/2),int(395-t.height/2)))
    im=logo('imax_cut',620,[(INK,3),(WHITE,9)]); L.alpha_composite(im,(int(540-im.width/2),int(1075-im.height/2)))
    text(L,'で観る[意味ある？]',112,540,1285,INK,w='Black')
    text(L,'何が変わるのか、観た人の声と一緒に',40,540,1415,SUBC)
    fx.tag(L,'IMAX上映　〜11/2（月）',540,1509); footer(L,540)
    text(L,'タイトル・IMAXロゴ：公式ポスターより',16,540,1590,DIM,w='Bold')
    return dict(base=L,scr=[sc],ch=(CH[12],'r'),rows=[])

# ---------- 演出（screen_fx の部品を、ナレーションの何割目かに合わせて使う） ----------
# fx_screen：スクリーンへの上書きと写真の加工／fx_front：手前に重ねる演出
def fx_screen(k,i,g,T):
    if k=='c1': return fx.push_in(g-T(0.35),fx=0.62,fy=0.6),None   # 「小人になってた」で寄る
    if k=='c2':   # 話している方の写真だけ大きく、もう一方は暗く
        on=(T(0)<=g<T(0.28) and i==0) or (T(0.28)<=g<T(0.5) and i==1)
        off=(T(0)<=g<T(0.28) and i==1) or (T(0.28)<=g<T(0.5) and i==0)
        sc=1.12 if on else (0.94 if off else 1.0)
        return dict(w=480*sc,h=520*sc),(fx.dimmed if off else None)
    if k=='c3': return fx.expand(g-T(0)-0.2),None   # 「大きくて、ゆるく湾曲」でぐぅーんと広がる
    if k=='c4': return dict(w=700,h=420,cy=800),None   # スピーカーを置くぶん小さめ
    if k=='c5': return {},fx.old_to_new(g-T(0.1),bright_at=T(0.3)-T(0.1))   # 昔の映像→4K→明るく
    return {},None
def fx_front(k,L,g,T,G):
    if k=='c3': fx.arrows(L,G,min(1,max(0,(g-T(0)-0.3)/0.3))*max(0,min(1,(T(0)+2.9-g)/0.4)))
    if k=='c4':
        fx.speakers(L,G,g-T(0))
        fx.floating_words(L,G,g,[('ザーッ',-250,-130,T(0.28),None),('ヒュウ',230,-150,T(0.36),None),('リーン',-200,150,T(0.44),None),('ゴロゴロ',200,140,T(0.66),RED)])
    if k=='c5': fx.wipe_line(L,G,g-T(0.1)); fx.sparkles(L,G,g-T(0.3))
    if k=='c6': fx.notes(L,G,g-T(0.3))

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
GRID=fx.poster_bg((214,234,180),(250,246,232)); BGS={k:GRID for k in KEYS}   # IMAXポスターの庭の光の色
def frame(k,P,bg,j,n,dur):
    g=j/FPS; im=bg; T=lambda fr:0.15+fr*wdur(k)
    for i,s in enumerate(P['scr']): a,post=fx_screen(k,i,g,T); G=s.draw(im,j/max(n-1,1),a,post)
    if P['ch']: fx.sit_on(im,P['ch'][0],G,P['ch'][1])
    im.alpha_composite(P['base']); fx_front(k,im,g,T,G)
    for r in P['rows']:
        L,fr=r[0],r[1]; a=int((g-(0.15+fr*wdur(k)))*FPS)
        p=pulse(L,a) if len(r)>2 and a>=0 else popped(L,a)   # 一番伝えたい帯だけゆっくり脈打つ
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
