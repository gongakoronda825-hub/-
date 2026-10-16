import math,subprocess,sys
from PIL import Image,ImageDraw,ImageFilter
src=open('otona.py').read()
exec(src.split('# ---- build static layers ----')[0])
exec(src[src.index('def ease(x)'):src.index('def render(t)')])
G='gb/'; OUT='/home/user/-/ghibli-kanji/'
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
QD=[6,6,6,6,6.5,7]
HOOK=2.5; CTA=3.5
starts=[]; t0=HOOK
for d in QD: starts.append(t0); t0+=d
DUR=t0+CTA
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
for k,(n,name,c) in enumerate(LV):
    y=1270+(k//2)*64; x=W/2+((k%2)-0.5)*420
    tdraw(d,x,y,f'{n}問 → {name}',fonts(900,34),c,8)

def compose(bgi,C): bgi.alpha_composite(C.crop((DX,0,W,H)),(0,0)); return bgi.convert('RGB')
def render(t):
    if t<HOOK:
        z=1.0+0.05*t/HOOK
        bg=cover(hookimg,W,H,0.45,0.5,z).convert('RGBA'); bg.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,120)))
        C=layer(); put(C,H1,0.0,t,dur=0.35,out=HOOK-0.25); put(C,H2,0.5,t,dur=0.35,out=HOOK-0.25)
        return compose(bg,C)
    for k,s in enumerate(starts):
        if t<s+QD[k]:
            ts=t-s; key=f'lv{k+1}'; prev='lv1' if k==0 else f'lv{k}'
            bgi=background(t,prev if ts<0.4 else key,key if ts<0.4 else None,ease(ts/0.4) if ts<0.4 else 0).convert('RGBA')
            if k==0 and ts<0.4: bgi=background(t,'lv1').convert('RGBA')
            head,K,ask,ans,P,acc,note=QL[k]; o=QD[k]-0.3; rv=3.6
            C=layer()
            put(C,head,0.05,ts,out=o); put(C,K,0.2,ts,dur=0.35,out=o)
            put(C,ask,0.4,ts,dur=0.3,out=rv-0.05)
            if 0.5<=ts<rv:
                L=layer(); e=ts-0.5; num=3-int(e); countdown(L,W/2,1230,1-(e%1),max(1,num),acc)
                put(C,L,0.5,ts,dur=0.2,out=rv-0.15)
            put(C,ans,rv,ts,dur=0.3,dy=-30,out=o); put(C,P,rv+0.15,ts,dur=0.4,out=o)
            if note: put(C,note,rv+0.4,ts,out=o)
            put(C,credit,rv,ts,out=o)
            return compose(bgi,C)
    ts=t-starts[-1]-QD[-1]
    bgi=background(t,'lv6' if ts<0.4 else 'cta','cta' if ts<0.4 else None,ease(ts/0.4) if ts<0.4 else 0).convert('RGBA')
    C=layer(); put(C,C1,0.1,ts); put(C,C2,0.6,ts); put(C,C3,1.0,ts)
    return compose(bgi,C)
if len(sys.argv)>1 and sys.argv[1]=='stills':
    ts=[1.5]+[s+1.8 for s in starts]+[s+5.2 for s in starts]+[DUR-0.5]
    for t in ts: render(t).save(OUT+f'still_{t:05.1f}.png')
    sys.exit()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart',OUT+'ghibli_kanji_quiz.mp4'],stdin=subprocess.PIPE)
for n in range(int(FPS*DUR)): p.stdin.write(render(n/FPS).tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode,DUR)
