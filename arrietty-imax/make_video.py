# アリエッティをIMAXで観た人の感想（2026/10/25）ナレーション動画　約61秒
# デザイン：暗い映画館＋ゆるく湾曲したIMAXスクリーン。文字は Zen Maru Gothic、白＋アリエッティの赤・ランプの金
# 使い方: python3 make_narration.py <出力先>/ → python3 make_video.py <作業フォルダ(setup.shのW)> <出力先>/narr [stills]
import json,sys,os,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S=sys.argv[1].rstrip('/')+'/'; NR=sys.argv[2].rstrip('/')+'/'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'arrietty_imax.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
TOTAL=61.5   # 収益化の「1分以上」を超えるよう、最後のフォロー画像で尺を合わせる
CREDIT='© 2010 Mary Norton/Keiko Niwa/Studio Ghibli, NDHDMTW'
BG0=(14,13,18); CREAM=(255,248,236); RED=(234,88,66); GOLD=(232,193,112); DIM=(160,150,140)

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
def text(L,t,sz,cx,cy,fill=CREAM,w='Bold',acc=RED,anchor='m',maxw=900,shadow=True,track=0):
    while tlen(t,sz,w)+track*len(t)>maxw: sz-=2
    x=cx-(tlen(t,sz,w)+track*(len(t)-1))/2 if anchor=='m' else cx
    if shadow:
        sh=layer(); text(sh,t,sz,cx,cy+4,(0,0,0),w,(0,0,0),anchor,maxw,False,track)
        L.alpha_composite(_soft(sh))
    d=ImageDraw.Draw(L); f=font(sz,w)
    for s,c in parts(t,fill,acc):
        if track:
            for ch in s: d.text((x,cy),ch,font=f,fill=c,anchor='lm'); x+=f.getlength(ch)+track
        else: d.text((x,cy),s,font=f,fill=c,anchor='lm'); x+=f.getlength(s)
def _soft(sh):
    a=sh.getchannel('A').filter(ImageFilter.GaussianBlur(7)).point(lambda v:int(v*0.7)); o=Image.new('RGBA',sh.size,(0,0,0,0)); o.putalpha(a); return o

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
class Screen:
    def __init__(s,src,cx,cy,w,h,fx=0.5,fy=0.5,sag=22):
        s.src=src; s.cx,s.cy,s.w,s.h,s.fx,s.fy=cx,cy,w,h,fx,fy; s.m=curve_mask(w,h,sag)
        # スクリーンの光がまわりにこぼれる感じ（色は写真の平均色）
        col=tuple(int(v) for v in np.asarray(src.resize((8,8))).reshape(-1,3).mean(0))
        g=Image.new('RGBA',(w+240,h+240),col+(0,)); gm=Image.new('L',g.size,0); gm.paste(s.m,(120,120))
        g.putalpha(gm.filter(ImageFilter.GaussianBlur(50)).point(lambda v:int(v*0.55))); s.glow=g
    def draw(s,L,u=0.0):
        im=cover(s.src,s.w,s.h,s.fx,s.fy,1.0+0.05*u).convert('RGBA'); im.putalpha(s.m)
        x,y=int(s.cx-s.w/2),int(s.cy-s.h/2); L.alpha_composite(s.glow,(x-120,y-120)); L.alpha_composite(im,(x,y))

# ---------- 背景（暗い館内＋場面写真をうっすら。ゆっくりズーム＋横パン） ----------
def dark_bg(n,fx=0.5):
    im=gb(n); b=cover(im,int(W*1.12),int(H*1.12),fx).filter(ImageFilter.GaussianBlur(26))
    b=Image.blend(Image.new('RGB',b.size,BG0),b,0.30)
    # 上から映写の光がさすように、上を少し明るく・下を暗く
    g=np.linspace(1.15,0.55,b.height)[:,None,None]; a=np.clip(np.asarray(b).astype(np.float32)*g,0,255).astype(np.uint8)
    return Image.fromarray(a)
def bg_frames(B,n):
    for k in range(n):
        u=k/max(n-1,1); z=1.0+0.08*u
        sw,sh=min(W*1.12/z,B.width),min(H*1.12/z,B.height); x=(B.width-sw)*(0.3+0.4*u); y=(B.height-sh)/2
        yield B.resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh)).convert('RGBA')

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
'c2':dict(lab='WHY',ttl='なんでアリエッティなのか',ph=(18,7),bg=6,ch=(12,'l'),rows=[('t','[小さい音]と[細かい画]が主役の映画',0),('t','IMAXで変わるのが',0.5),('t','ちょうど[その2つ]',0.72)]),
'c3':dict(lab='CHANGE 01',ttl='画面',ph=36,fx=0.45,bg=28,ch=(33,'r'),rows=[('t','大きくて、ゆるく湾曲したスクリーン',0),('t','小人から見た[部屋の広さ]が伝わる',0.32),('q','部屋がとにかく広く感じた',0.72)]),
'c4':dict(lab='CHANGE 02',ttl='音',ph=40,fx=0.7,bg=18,ch=(12,'l'),rows=[('t','[横と上]にもスピーカー',0),('t','雨、風、虫の声が、まわりから',0.28),('q','普段は気にしない音がずっと聞こえてた\n[ニーヤのゴロゴロ]まで',0.62)]),
'c5':dict(lab='CHANGE 03',ttl='画質',ph=32,fx=0.4,bg=3,ch=(33,'r'),rows=[('t','ジブリ監修の[4Kリマスター版]',0),('s','昔の映像を、今の高画質で作り直したもの',0.1),('t','レーザー映写で[明るく、色が深い]',0.3),('q','[水のつぶ]や[花の色]まで見えた',0.75)]),
'c6':dict(lab='SONG',ttl='歌',ph=24,fx=0.6,bg=1,ch=(12,'l'),rows=[('t','[セシル・コルベル]の歌声も',0),('t','IMAXの音で聴ける',0.3),('s','これ目当てでもいいと思う',0.6)]),
'c7':dict(lab='AFTER',ttl='観たあと',ph=37,fx=0.4,bg=48,ch=(48,'r'),rows=[('q','アリエッティの側で観てたはずが\n「自分は[翔の側]なんだよな」',0),('s','って気づいて、ちょっとしんどい',0.3),('t','でも、[小さい世界]ってきれいなんだな',0.6)]),
'c8':dict(lab='SCHEDULE',ttl='上映期間',ph=47,fx=0.5,bg=2,ch=(12,'l'),rows=[])}

def head(L,lab,ttl):
    text(L,lab,30,CX,330,GOLD,w='Bold',track=8,shadow=False)
    ImageDraw.Draw(L).line((CX-26,362,CX+26,362),fill=GOLD,width=3)
    text(L,ttl,76,CX,420,CREAM,w='Black',maxw=640)   # 両はしのキャラと重ならない幅
def footer(L,cx=CX):
    text(L,'観た人の感想をもとに再構成',22,cx,1612,DIM,w='Medium',shadow=False)
    text(L,CREDIT,20,cx,1644,DIM,w='Medium',shadow=False)
def row_layer(r):
    # 1行（または1つの声）だけのレイヤーと高さ
    k,t=r[0],r[1]; L=layer(); ls=t.split('\n')
    if k=='t': text(L,t,52,CX,0+40,CREAM,w='Black'); return L,96
    if k=='s': text(L,t,38,CX,0+30,(225,215,200),w='Bold'); return L,72
    # 観た人の声：金の小さいラベル＋うすい枠
    lh=58; h=50+len(ls)*lh+24; w=max(tlen(l,44) for l in ls)+100; d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-w/2,14,CX+w/2,14+h),34,fill=(255,255,255,26),outline=GOLD+(200,),width=3)
    lw=tlen('観た人の声',24)+40; d.rounded_rectangle((CX-lw/2,0,CX+lw/2,30),15,fill=GOLD)
    text(L,'観た人の声',24,CX,15,BG0,w='Bold',shadow=False)
    for j,l in enumerate(ls): text(L,l,44,CX,14+50+j*lh+lh/2-8,CREAM,w='Bold')
    return L,h+50
def build(k):
    c=CUTS[k]; base=layer(); head(base,c['lab'],c['ttl']); footer(base)
    if isinstance(c['ph'],tuple):
        scr=[Screen(gb(n),CX+(-250 if j==0 else 250),SCR['cy'],480,SCR['h'],0.55,sag=16) for j,n in enumerate(c['ph'])]
        for j,lab in enumerate(['小さい音','細かい画']): text(base,lab,40,CX+(-250 if j==0 else 250),SCR['cy']+SCR['h']/2+50,GOLD,w='Black')
        y=SCR['cy']+SCR['h']/2+120
    else:
        scr=[Screen(gb(c['ph']),CX,SCR['cy'],SCR['w'],SCR['h'],c.get('fx',0.5))]; y=SCR['cy']+SCR['h']/2+70
    n,side=c['ch']; ch=CH[n]; cx=CX+(SCR['w']/2-60 if side=='r' else -SCR['w']/2+60)
    chpos=(int(cx-ch.width/2),int(SCR['cy']-SCR['h']/2-ch.height+70))
    rows=[]
    for r in c['rows']:
        L,h=row_layer(r); o=layer(); o.alpha_composite(L,(0,int(y))); rows.append((o,r[2])); y+=h
    if k=='c8': rows=c8_rows(y)
    return dict(base=base,scr=scr,ch=(ch,chpos),rows=rows)
def c8_rows(y):
    out=[]
    for j,(lab,dt) in enumerate([('IMAX','〜11/2（月）'),('全国の拡大上映','10/30（金）〜11/12（木）')]):
        L=layer(); yy=y+j*120; d=ImageDraw.Draw(L)
        d.rounded_rectangle((CX-460,yy,CX+460,yy+100),28,fill=(255,255,255,22),outline=(255,255,255,60),width=2)
        text(L,lab,32,CX-300,yy+50,GOLD,w='Black',maxw=280); text(L,dt,46,CX+130,yy+50,CREAM,w='Black',maxw=560); out.append((L,0.0 if j==0 else 0.3))
    L=layer(); text(L,'[迷ってる人]に送ってあげて',54,CX,y+300,CREAM,w='Black'); out.append((L,0.68))
    L=layer(); text(L,'※劇場によって設備が違います（レーザーでない劇場、2K上映の劇場あり）',24,CX,y+380,DIM,w='Medium',shadow=False); out.append((L,0.0))
    return out
def hook():
    L=layer(); sc=Screen(gb(33),540,640,1000,500,0.55)
    text(L,'借りぐらしのアリエッティ',34,540,330,GOLD,track=4,shadow=False)
    text(L,'IMAXで観る',118,540,1040,CREAM,w='Black')
    text(L,'[意味ある？]',150,540,1200,CREAM,w='Black')
    text(L,'何が変わるのか、観た人の声と一緒に',40,540,1345,(225,215,200))
    d=ImageDraw.Draw(L); t='IMAX上映　〜11/2（月）'; w=tlen(t,32)+60; d.rounded_rectangle((540-w/2,1420,540+w/2,1482),31,outline=GOLD,width=3)
    text(L,t,32,540,1451,GOLD,shadow=False); footer(L,540)
    return dict(base=L,scr=[sc],ch=(CH[12],(int(540+500-170-CH[12].width/2),int(640-250-CH[12].height+60))),rows=[])

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
BGS={k:dark_bg(CUTS[k]['bg']) for k in CUTS}; BGS['hook']=dark_bg(33)
POP=[0.6,0.9,1.08,1.03]
def popped(F,j):
    if j<0: return None
    if j>=len(POP): return F
    s=POP[j]; bb=F.getbbox(); c=F.crop(bb); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
def frame(k,P,bg,j,n,dur):
    g=j/FPS; im=bg
    for s in P['scr']: s.draw(im,j/max(n-1,1))
    ch,pos=P['ch']; im.alpha_composite(ch,pos); im.alpha_composite(P['base'])
    for L,fr in P['rows']:
        a=int((g-(0.15+fr*wdur(k)))*FPS); p=popped(L,a)
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
    for r in CUTS.get(k,{}).get('rows',[]):
        if r[0]=='q': add(rd(S+'labsfx/pa1.wav'),t0+0.15+r[2]*wdur(k),0.25)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
