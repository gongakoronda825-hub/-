import math,subprocess,sys
from PIL import Image,ImageDraw,ImageFilter
src=open('otona.py').read()
exec(src.split('# ---- build static layers ----')[0])
exec(src[src.index('def ease(x)'):src.index('def render(t)')])
G='gb/'; S_='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'; OUT='/home/user/-/ghibli-kanji/'
DX=40
LV=[(1,'ジブリ初心者レベル',(46,125,62)),(2,'ジブリ好きレベル',(32,128,140)),(3,'ジブリ通レベル',(56,96,180)),
    (4,'ジブリオタクレベル',(118,78,170)),(5,'ジブリ博士レベル',(206,100,36)),(6,'宮崎駿レベル',(180,36,52))]
for n,_,c in LV:
    bg=tuple(int(255-(255-v)*0.10) for v in c); PAL[f'lv{n}']=(bg,c,c)
Q=[('湯婆婆','ゆばーば','千と千尋の神隠し','chihiro016',.5,None),
   ('木霊','こだま','もののけ姫','mononoke023',.5,None),
   ('瘴気','しょうき','風の谷のナウシカ','nausicaa003',.5,None),
   ('乙事主','おっことぬし','もののけ姫','mononoke034',.5,None),
   ('蝦夷','えみし','もののけ姫','mononoke001',.5,'アシタカの一族'),
   ('饒速水小白主','にぎはやみこはくぬし','千と千尋の神隠し','chihiro045',.5,'ハクの本当の名前')]
import wave as _wv
def wdur(p):
    with _wv.open(p) as w: return w.getnframes()/w.getframerate()
NQ=[wdur(f'narr_trim/q{i}.wav') for i in range(1,7)]; NA=[wdur(f'narr_trim/a{i}.wav') for i in range(1,7)]
CS=[q+0.05 for q in NQ]; RV=[c+3.0 for c in CS]
QD=[r+0.12+a+0.3 for r,a in zip(RV,NA)]
HOOK=wdur('narr_trim/hook.wav')+0.15; CTA=wdur('narr_trim/cta.wav')+0.7
starts=[]; t0=HOOK
for d in QD: starts.append(t0); t0+=d
CTA_END=t0+CTA
FOL=wdur('narr_trim/follow.wav')+1.0
DUR=CTA_END+FOL
def load(n): return Image.open(G+n+'.jpg').convert('RGB')
def cover(im,w,h,fx=0.5,fy=0.5,zoom=1.0):
    s=max(w/im.width,h/im.height)*zoom; nw,nh=int(im.width*s),int(im.height*s)
    r=im.resize((nw,nh),Image.LANCZOS); x=int((nw-w)*fx); y=int((nh-h)*fy); return r.crop((x,y,x+w,y+h))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def fit(t,w,maxs,maxw):
    s=maxs
    while tlen(t,fonts(w,s))>maxw: s-=4
    return s
IW,IH=860,484
def put(frame,L,t0,t,dur=0.06,dy=0,out=None):
    if t<t0: return
    a=min(1,(t-t0)/0.06)
    l=L if a>=1 else L.copy()
    if a<1: l.putalpha(l.getchannel('A').point(lambda v:int(v*a)))
    frame.alpha_composite(l)
# static per-question layers
QL=[]
for k,(kan,yomi,film,img,fx,hint) in enumerate(Q):
    n,name,acc=LV[k]
    head=layer(); pill(head,W/2,300,f'Lv.{n}',52,acc,WHITE,50)
    d=ImageDraw.Draw(head); tdraw(d,W/2,392,name,fonts(900,50),acc,10)
    for j in range(6):
        cx=W/2+(j-2.5)*58; r=16
        d.ellipse((cx-r,452-r,cx+r,452+r),fill=acc if j<n else (215,212,205),outline=WHITE,width=4)
    K=layer(); s=fit(kan,900,250,860); lines(K,660,[kan],s,DARK,stroke=18)
    ask=layer(); d=ImageDraw.Draw(ask)
    tdraw(d,W/2,850,'なんて読む？',fonts(900,56),DARK,10)
    h=f'ヒント：{film}'+(f'（{hint}）' if hint else '')
    tdraw(d,W/2,935,h,fonts(800,fit(h,800,34,820)),(110,100,92),8)
    ans=layer(); d=ImageDraw.Draw(ans)
    fs=fit(yomi,900,80,800); fp=fonts(900,fs); w_=tlen(yomi,fp)+90
    d.rounded_rectangle((W/2-w_/2,850-fs*0.9,W/2+w_/2,850+fs*0.9),fs,fill=acc,outline=WHITE,width=8)
    tdraw(d,W/2,850,yomi,fp,WHITE)
    # photo card
    c=cover(load(img),IW,IH,fx).convert('RGBA')
    band=Image.new('RGBA',(IW,90),(0,0,0,150)); c.alpha_composite(band,(0,IH-90))
    tdraw(ImageDraw.Draw(c),IW/2,IH-45,film,fonts(900,40),WHITE)
    c.putalpha(rmask(IW,IH,30))
    P=layer(); pd=ImageDraw.Draw(P)
    x0=int(W/2-IW/2); y0=975
    pd.rounded_rectangle((x0-12,y0-12,x0+IW+12,y0+IH+12),40,fill=WHITE)
    P.alpha_composite(c,(x0,y0))
    note=None
    if kan=='蝦夷':
        note=layer(); tdraw(ImageDraw.Draw(note),W/2,1495,'※「えぞ」とも読みますが、作中では「エミシ」',fonts(800,30),(110,100,92),6)
    QL.append((head,K,ask,ans,P,acc,note))
def countdown(L,cx,cy,frac,num,acc):
    d=ImageDraw.Draw(L); r=120
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,255,255,235))
    d.arc((cx-r+8,cy-r+8,cx+r-8,cy+r-8),-90,-90+360*frac,fill=acc,width=18)
    tdraw(d,cx,cy+4,str(num),fonts(900,130),acc)
credit=layer(); tdraw(ImageDraw.Draw(credit),W/2,1540,'© Studio Ghibli',fonts(800,26),(120,112,104))
hookimg=load('chihiro045')
H1=layer(); lines(H1,780,['ジブリ','漢字クイズ'],150,WHITE,gap=1.15)
H2=layer(); dd=ImageDraw.Draw(H2)
pill(H2,W/2,1080,'全問読めたら宮崎駿レベル',56,(180,36,52),WHITE,46)
C1=layer(); lines(C1,820,['あなたは','何問読めた？'],110,DARK,stroke=16,gap=1.25)
C2=layer(); d=ImageDraw.Draw(C2); acc=(46,125,62)
cx,cy=W/2-260,1120
d.rounded_rectangle((cx-62,cy-46,cx+62,cy+40),30,fill=acc); d.polygon([(cx-22,cy+34),(cx-40,cy+70),(cx+4,cy+38)],fill=acc)
for k in (-30,0,30): d.ellipse((cx+k-9,cy-9,cx+k+9,cy+9),fill=WHITE)
pill(C2,W/2+60,1115,'コメントで教えてね',52,acc,WHITE,44)
C3=layer(); d=ImageDraw.Draw(C3)
tdraw(d,W/2,1520,'© Studio Ghibli ／ VOICEVOX:青山龍星',fonts(800,26),(120,112,104))
for k,(n,name,c) in enumerate(LV):
    y=1270+(k//2)*64; x=W/2+((k%2)-0.5)*420
    tdraw(d,x,y,f'{n}問 → {name}',fonts(900,34),c,8)

exec(open('chars.py').read())
CHARS={0:[('chihiro021','L',False),('chihiro049','R',False)],1:[('mononoke049','L',False),('mononoke029','R',True)],
 2:[('nausicaa025','L',False),('nausicaa050','R',False)],3:[('mononoke014','L',False),('mononoke041','R',True)],
 4:[('mononoke030','L',False),('mononoke047','R',False)],5:[('chihiro022','L',False),('chihiro050','R',True)],
 'cta':[('totoro019','L',False),('totoro044','R',False)]}
CH_IMG={}
for k,lst in CHARS.items():
    CH_IMG[k]=[]
    for n,side,fl in lst:
        st=sticker(n,520,side,fl)
        if st.width>560: st=st.resize((560,int(st.height*560/st.width)),Image.LANCZOS)
        CH_IMG[k].append((st,side))
def csticker(name,h,ow=9,rot=0):
    im=Image.open(f'cut/c_{name}.png').convert('RGBA'); im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>60 else 0)
    o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(8)).point(lambda v:int(v*0.3)))
    out.alpha_composite(sh,(0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
CRE={0:('susu2','haedori'),1:('susu','chibitotoro'),2:('teto','susu2'),3:('kodama2','haedori'),4:('chibitotoro','calcifer'),5:('haedori','susu')}
CRE_IMG={k:(csticker(a,215,rot=8),csticker(b,215,rot=-8)) for k,(a,b) in CRE.items()}
def draw_creatures(C,k,ts):
    l,r=CRE_IMG[k]
    for j,(st,cx) in enumerate(((l,225),(r,935))):
        p=min(1,max(0,(ts-0.03*j)/0.12)); sc=0.6+0.4*(1-(1-p)**3)
        img=st if sc>=1 else st.resize((max(1,int(st.width*sc)),max(1,int(st.height*sc))))
        bob=7*math.sin(ts*3+j*1.7)
        C.alpha_composite(img,(int(cx-img.width/2),int(400-img.height/2+bob)))
def draw_chars(bgi,key,ts):
    for j,(st,side) in enumerate(CH_IMG[key]):
        p=min(1,max(0,(ts-0.0-0.05*j)/0.15)); p=1-(1-p)**3
        bob=6*math.sin((ts+j)*2.2)
        x=0 if side=='L' else W-st.width
        y=int(H-st.height+ (1-p)*st.height*0.6 + bob+8)
        bgi.alpha_composite(st,(x,max(0,y)) if y>=0 else (x,0))
def compose(bgi,C): bgi.alpha_composite(C.crop((DX,0,W,H)),(0,0)); return bgi.convert('RGB')
U='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/'
POSTS=[U+'b4ce95c0-image.jpg',U+'fc7817dd-image.jpg']
FW,FH=400,520
FG=layer()
lines(FG,360,['こんな投稿も','してるよ'],84,DARK,stroke=14,gap=1.2)
for k,p in enumerate(POSTS):
    c=cover(Image.open(p).convert('RGB'),FW,FH,0.5,0.4).convert('RGBA'); c.putalpha(rmask(FW,FH,26))
    x=int(W/2+(k-0.5)*(FW+40)-FW/2); y=560
    tmp=layer(); fd=ImageDraw.Draw(tmp); fd.rounded_rectangle((x-10,y-10,x+FW+10,y+FH+10),32,fill=WHITE); tmp.alpha_composite(c,(x,y))
    FG.alpha_composite(tmp.rotate([-3,3][k],resample=Image.BICUBIC,center=(x+FW/2,y+FH/2)))
DECO=[]
for n,side,fl,h,y in [('majo001','L',False,230,120),('howl048','R',True,300,110),('mononoke049','L',False,300,1130),('nausicaa050','R',False,280,1150)]:
    st=sticker(n,h,side,fl)
    if st.width>420: st=st.resize((420,int(st.height*420/st.width)),Image.LANCZOS)
    DECO.append((st,0 if side=='L' else W-st.width,y))
FB=layer(); d=ImageDraw.Draw(FB); acc=(46,125,62); fp=fonts(900,64); tx='フォローしてね'
w_=tlen(tx,fp)+190; x0=W/2-w_/2; y0=1180
d.rounded_rectangle((x0,y0-62,x0+w_,y0+62),62,fill=acc,outline=WHITE,width=8)
cx=x0+70; d.ellipse((cx-34,y0-34,cx+34,y0+34),fill=WHITE); d.rectangle((cx-18,y0-5,cx+18,y0+5),fill=acc); d.rectangle((cx-5,y0-18,cx+5,y0+18),fill=acc)
tdraw(d,x0+w_/2+40,y0,tx,fp,WHITE)
def follow_frame(t,ts):
    bgi=background(t,'cta').convert('RGBA'); draw_chars(bgi,'cta',ts+5)
    for st,x,y in DECO: bgi.alpha_composite(st,(x,int(y+6*math.sin(ts*2.2+x))))
    C=layer(); put(C,FG,0,ts)
    sc=1+0.06*max(0,math.sin(ts*5)) if ts>1.2 else 1
    L=FB if sc==1 else FB.resize((int(W*sc),int(H*sc)),Image.BILINEAR).crop((int((W*sc-W)/2),int((1180*sc-1180)),int((W*sc-W)/2)+W,int((1180*sc-1180))+H))
    put(C,L,1.2,ts)
    return compose(bgi,C)
def render(t):
    if t>=CTA_END: return follow_frame(t,t-CTA_END)
    if t<HOOK:
        z=1.0+0.05*t/HOOK
        bg=cover(hookimg,W,H,0.45,0.5,z).convert('RGBA'); bg.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,120)))
        C=layer(); put(C,H1,0.0,t); put(C,H2,0.0,t)
        return compose(bg,C)
    for k,s in enumerate(starts):
        if t<s+QD[k]:
            ts=t-s; key=f'lv{k+1}'; prev='lv1' if k==0 else f'lv{k}'
            bgi=background(t,prev if ts<0 else key,key if ts<0 else None,ease(ts/0.4) if ts<0 else 0).convert('RGBA')
            if k==0 and ts<0.4: bgi=background(t,'lv1').convert('RGBA')
            head,K,ask,ans,P,acc,note=QL[k]; o=QD[k]-0.3; rv=RV[k]; cs=CS[k]
            draw_chars(bgi,k,ts)
            C=layer()
            draw_creatures(C,k,ts)
            put(C,head,0,ts); put(C,K,0,ts)
            (put(C,ask,0,ts) if ts<rv else None)
            if cs<=ts<rv:
                L=layer(); e=ts-cs; num=3-int(e); countdown(L,W/2,1230,1-(e%1),max(1,num),acc)
                put(C,L,cs,ts)
            put(C,ans,rv,ts); put(C,P,rv,ts)
            if note: put(C,note,rv,ts)
            put(C,credit,rv,ts)
            return compose(bgi,C)
    ts=t-starts[-1]-QD[-1]
    bgi=background(t,'lv6' if ts<0 else 'cta','cta' if ts<0 else None,ease(ts/0.4) if ts<0 else 0).convert('RGBA')
    draw_chars(bgi,'cta',ts)
    C=layer(); put(C,C1,0,ts); put(C,C2,0,ts); put(C,C3,0,ts)
    return compose(bgi,C)
def build_audio():
    import numpy as np
    SR=44100; tot=np.zeros(int(SR*(DUR+0.5)))
    def rd(p):
        with _wv.open(p) as w:
            sr=w.getframerate(); ch=w.getnchannels(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
        if ch==2: x=x.reshape(-1,2).mean(1)
        if sr!=SR: x=np.interp(np.arange(0,len(x),sr/SR),np.arange(len(x)),x)
        return x
    def add(p,t,g):
        x=rd(p)*g; i=int(t*SR); n=min(len(x),len(tot)-i); tot[i:i+n]+=x[:n]
    add('narr_trim/hook.wav',0.0,1.0)
    for k,st in enumerate(starts):
        add(f'narr_trim/q{k+1}.wav',st,1.0)
        for j in range(3): add('sfx/tick.wav',st+CS[k]+j,0.4)
        add('sfx/pinpon.wav',st+RV[k],0.5); add(f'narr_trim/a{k+1}.wav',st+RV[k]+0.12,1.0)
    ce=starts[-1]+QD[-1]; add('narr_trim/cta.wav',ce,1.0); add('narr_trim/follow.wav',CTA_END,1.0)
    tot=tot/max(1e-9,np.abs(tot).max())*0.92
    with _wv.open(S_+'quiz_audio.wav','wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((tot*32767).astype(np.int16).tobytes())
if len(sys.argv)>1 and sys.argv[1]=='audio': build_audio(); print('audio',DUR); sys.exit()
if len(sys.argv)>1 and sys.argv[1]=='stills':
    ts=[1.5]+[s+1.8 for s in starts]+[s+5.2 for s in starts]+[DUR-0.5]
    for t in ts: render(t).save(OUT+f'still_{t:05.1f}.png')
    sys.exit()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart',S_+'quiz_video_noaudio.mp4'],stdin=subprocess.PIPE)
for n in range(int(FPS*DUR)): p.stdin.write(render(n/FPS).tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode,DUR)
