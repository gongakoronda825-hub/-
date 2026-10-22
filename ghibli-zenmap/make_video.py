import subprocess,wave,numpy as np
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
exec(open(S+'loc/make.py').read())
from PIL import ImageFilter
WHITE=(255,255,255)
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
cs=open(S+'imax.py').read(); exec(cs[cs.index('def kf('):cs.index('def chara(')].replace("KF,","S+'fonts/keifont.ttf',"))
WHITE=(255,255,255); FPS=30; SR=44100; V=S+'zen/'
OUTV='/home/user/-/ghibli-zenmap/zenmap.mp4'; os.makedirs(os.path.dirname(OUTV),exist_ok=True)
U='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/'
def wdur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
# intro still: screenshot on blurred bg
sc=Image.open(U+'d94ab764-image.jpg').convert('RGB')
IBG=cover(Image.open(S+'gb/kimitachi034.jpg').convert('RGB'),int(W*1.12),int(H*1.12)).filter(ImageFilter.GaussianBlur(3)); IBG=Image.blend(IBG,Image.new('RGB',IBG.size,(0,0,0)),0.15)
bg=Image.new('RGBA',(W,H),(0,0,0,0))
fg=sc.resize((900,int(sc.height*900/sc.width)),Image.LANCZOS); x0,y0=(W-900)//2-40,(H-fg.height)//2-80
sh=Image.new('L',(W,H),0); ImageDraw.Draw(sh).rounded_rectangle((x0-6,y0+14,x0+906,y0+fg.height+26),24,fill=150); bg.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(18)))
ImageDraw.Draw(bg).rounded_rectangle((x0-12,y0-12,x0+912,y0+fg.height+12),26,fill=WHITE+(255,)); bg.paste(fg,(x0,y0))
ImageDraw.Draw(bg).text((x0+900,y0+fg.height+60),'© Studio Ghibli',font=ImageFont.truetype(S+'fonts/jp800.woff',28),fill=WHITE,anchor='rs',stroke_width=3,stroke_fill=(0,0,0)); IFG=bg
POP=[0.6,0.9,1.08,1.03]
def howf(n,t0,ts):
    for k,fr_ in enumerate(introf(n,HBG,HFG)):
        im=Image.fromarray(fr_).convert('RGBA'); g=t0+k/FPS
        for (c,bb),ts_ in zip(STEPC,ts):
            if g<ts_: continue
            kk=int((g-ts_)*FPS); sc=POP[kk] if kk<4 else 1.0; cc=c if sc==1.0 else c.resize((int(c.width*sc),int(c.height*sc)),Image.BICUBIC)
            im.alpha_composite(cc,(int((bb[0]+bb[2])/2-cc.width/2),int((bb[1]+bb[3])/2-cc.height/2)))
        yield np.array(im.convert('RGB'))
def introf(n,IBG=IBG,IFG=IFG):
    for k in range(n):
        u=k/max(n-1,1); z=1.0+0.08*u
        sw,sh_=min(W*1.12/z,IBG.width),min(H*1.12/z,IBG.height); x=(IBG.width-sw)*(0.2+0.6*u); y=(IBG.height-sh_)/2
        b=IBG.resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh_)).convert('RGBA'); b.alpha_composite(IFG); yield np.array(b.convert('RGB'))
# how-to card
RF=lambda sz:ImageFont.truetype(S+'fonts/jp900.woff',sz); GREEN=(46,125,62); ORANGE=(236,128,60)
k9=Image.open(V+'kyo/08.jpg').convert('RGB'); cw=int(k9.height*W/H); cx=int(k9.width*0.42)-cw//2; HBG=cover(k9.crop((cx,0,cx+cw,k9.height)),int(W*1.12),int(H*1.12)).filter(ImageFilter.GaussianBlur(2))
pn=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(pn).rounded_rectangle((70,250,1010,1650),40,fill=(255,251,245,205)); L=pn
ImageDraw.Draw(L).text((540,1735),'© Studio Ghibli',font=ImageFont.truetype(S+'fonts/jp800.woff',20),fill=WHITE,anchor='ms',stroke_width=3,stroke_fill=(0,0,0))
ImageDraw.Draw(L).text((540,1700),'南禅寺（京都） Photo: Takeshi Kuboki / CC BY 2.0',font=ImageFont.truetype(S+'fonts/jp800.woff',20),fill=WHITE,anchor='ms',stroke_width=3,stroke_fill=(0,0,0))
exec(cs[cs.index('def chara('):cs.index('from PIL import ImageOps')].replace("f'cut/","S+f'cut/")); from PIL import ImageOps
for nm,h,r,x,y in [('kimi_mahito',230,-6,150,220),('kimi_aosagi',190,7,930,220),('kimi_himi',240,-5,140,1760),('kimi_kiriko',140,6,920,1770)]:
    c=chara(nm,h,r); L.alpha_composite(c,(int(x-c.width/2),int(y-c.height/2)))
d=ImageDraw.Draw(L)
ctext(d,(W/2,330),'HOW TO GET',RF(40),ORANGE,sp=8)
d.text((W/2,420),'ZEN MAPの買い方',font=RF(84),fill=GREEN,anchor='mm',stroke_width=10,stroke_fill=WHITE)
steps=[('1','『禅とジブリ』公式サイトで','二次元コードを表示'),('2','セブン-イレブンの','マルチコピー機にかざす'),('3','400円を入れて','印刷すれば完成！')]
STEPS=[]
for i,(n,a,b) in enumerate(steps):
    SL=layer(); d=ImageDraw.Draw(SL); y=560+i*230; d.rounded_rectangle((120,y,960,y+190),30,fill=(255,253,249,255),outline=GREEN,width=3)
    d.ellipse((150,y+45,250,y+145),fill=GREEN); ctext(d,(200,y+95),n,RF(64),WHITE)
    d.text((290,y+62),a,font=RF(42),fill=INK,anchor='lm'); d.text((290,y+128),b,font=RF(48),fill=INK,anchor='lm')
    STEPS.append(SL)
SL=layer(); d=ImageDraw.Draw(SL)
y=1290; d.rounded_rectangle((120,y,960,y+250),30,fill=(240,230,215,255))
for i,t in enumerate(['京都で開催中『禅とジブリ』展のオリジナル','全国のセブン-イレブンで1枚400円','禅寺をめぐる京都観光マップ（日英表記）']):
    d.text((170,y+55+i*72),'・'+t,font=RF(36),fill=INK,anchor='lm')
STEPS.append(SL); d=ImageDraw.Draw(L)
STEPC=[(S_.crop(S_.getbbox()),S_.getbbox()) for S_ in STEPS]
ctext(d,(W/2,1600),'※販売期間などは公式サイトをご確認ください',RF(28),SUB)
HFG=L
import math
HC=[(chara(n,h,r),x,y) for n,h,r,x,y in [('kimi_mahito',230,-6,170,640),('kimi_aosagi',200,6,900,640),('kimi_himi',330,-5,200,1530),('kimi_kiriko',190,5,870,1560)]]
FOLLOW=np.array(Image.open(U+'6a98b9bb-image.jpg').convert('RGB').resize((W,H)))
# segments: (source, start, dur, [narr...], sfx)
SEG=[('FLASH',0.2,0.8,[],'shine2'),('IMG_0370',0,None,['zb'],'shakin2'),('INTRO',0,None,['zi'],'kira1'),('IMG_0372',0.3,None,['z3'],'pa1'),
('IMG_0374',0,None,['z4'],'cute-pose1'),('HOW',0,None,['z5','z6','z7','z9'],'sceneswitch1'),('FOLLOW',0,None,['z8'],'kira1')]
def bigimg(t):
    Lx=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): kf(Lx,l,[70,104][j],H/2+[-70,60][j],[WHITE,(255,214,0)][j],inner=(25,25,25),outer=WHITE,si=14,so=26,cx=W/2,maxw=980)
    Lx=Lx.crop(Lx.getbbox()); Lx.info.update(pop=1,y=400); return Lx
def saveimg(t):
    Lx=layer(); d=ImageDraw.Draw(Lx); F=ImageFont.truetype(S+'fonts/jp900.woff',76); ls=t.split('\n')
    d.rounded_rectangle((90,H/2-150,990,H/2+150),60,fill=(236,128,60,255),outline=WHITE,width=10)
    for j,l in enumerate(ls): d.text((W/2,H/2-55+j*110),l,font=F,fill=WHITE,anchor='mm',stroke_width=6,stroke_fill=(150,60,20))
    Lx=Lx.crop(Lx.getbbox()); Lx.info.update(pop=1,y=H/2+100); return Lx
def subimg(t):
    Lx=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): kf(Lx,l,54,H/2+(j-(len(ls)-1)/2)*78,WHITE,inner=(35,35,35),outer=(35,35,35),si=9,so=9,cx=W/2,maxw=860)
    return Lx.crop(Lx.getbbox())
SUB={'zb':'セブンのコピー機から\nジブリが出てきた…!?','zi':'禅とジブリ展の\nオリジナルマップ！\nセブンで印刷できる','z1':'ジブリの禅マップが\nセブンで印刷できるらしい！\n行ってみる！','z2':'完成！','z3':'持って帰るよ〜','z4':'こんな感じだった！\n裏には禅の解説も',
'z9':'京都に行く前に\n保存してね！','z5':None,'z6':None,'z7':None,'z8':None}
tl=[]; t=0
for src,st,fd,ns,sfx in SEG:
    d_=sum(wdur(V+f'narr/{n}.wav')+0.25 for n in ns)+0.5
    if fd: d_=fd
    elif src.startswith('IMG'):
        cd=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',V+src+'.mp4'],capture_output=True,text=True).stdout)-st
        d_=max(d_,min(cd,d_+1.5))
    if src=='HOW': d_+=1.5
    tl.append((src,st,d_,ns,sfx,t)); t+=d_
TOT=t
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','23','-pix_fmt','yuv420p',V+'v.mp4'],stdin=subprocess.PIPE)
SUBS=[]
for src,st,d_,ns,sfx,t0 in tl:
    tt=t0
    for n in ns:
        if SUB.get(n): SUBS.append((tt,tt+wdur(V+f'narr/{n}.wav')+0.4,bigimg(SUB[n]) if n=='zb' else saveimg(SUB[n]) if n=='z9' else subimg(SUB[n])))
        tt+=wdur(V+f'narr/{n}.wav')+0.25
for src,st,d_,ns,sfx,t0 in tl:
    n=int(round(d_*FPS))
    if src.startswith('IMG') or src=='FLASH':
        p=subprocess.run(['ffmpeg','-v','error','-ss',str(st),'-i',V+('IMG_0374' if src=='FLASH' else src)+'.mp4','-t',str(d_),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
        fr=list(np.frombuffer(p,np.uint8).reshape(-1,H,W,3)[:n])
        while len(fr)<n: fr.append(fr[-1])
    elif src=='INTRO': fr=introf(n)
    elif src=='HOW':
        w5=wdur(V+'narr/z5.wav'); s1=t0+0.1; HT=[s1,s1+w5*0.5,s1+w5+0.25,s1+w5+wdur(V+'narr/z6.wav')+0.5]; fr=howf(n,t0,HT)
    else: fr=[{'FOLLOW':FOLLOW}[src]]*n
    for k,f in enumerate(fr):
        g=t0+k/FPS; im=None
        if src=='FLASH':
            z=1.0+0.06*k/max(n-1,1); f=np.array(Image.fromarray(f).resize((W,H),Image.BILINEAR,box=(W*(1-1/z)/2,H*(1-1/z)/2,W*(1+1/z)/2,H*(1+1/z)/2)))
        if src=='IMG_0370':
            u=min(1,(g-t0)/0.4); z=1+0.2*(1-(1-u)**3); cy=H*0.47
            im=Image.fromarray(f).resize((W,H),Image.BILINEAR,box=(W/2-W/2/z,cy-cy/z,W/2+W/2/z,cy+(H-cy)/z)).convert('RGBA')
            if k<3: im=Image.blend(im,Image.new('RGBA',(W,H),(255,255,255,255)),[0.7,0.4,0.15][k])
            for j,(c,x,y) in enumerate(HC):
                a=8*math.sin(2*math.pi*1.2*g+j*math.pi/2); r=c.rotate(a,Image.BICUBIC,expand=True,center=(c.width/2,c.height))
                im.alpha_composite(r,(int(x-r.width/2),int(y-r.height/2)))
            ImageDraw.Draw(im).text((W-80,1700),'© Studio Ghibli',font=ImageFont.truetype(S+'fonts/jp800.woff',26),fill=WHITE,anchor='rs',stroke_width=3,stroke_fill=(0,0,0))
            f=np.array(im.convert('RGB')); im=None
        for a,b,T in SUBS:
            if a<=g<b:
                kk=int((g-a)*FPS); sc=[0.9,1.08,1.03][kk] if T.info.get('pop') and kk<3 else 1.0
                TT=T if sc==1.0 else T.resize((int(T.width*sc),int(T.height*sc)),Image.BICUBIC)
                im=Image.fromarray(f).convert('RGBA'); im.alpha_composite(TT,(int(W/2-TT.width/2),int(T.info.get('y',H/2)-TT.height/2)))
        enc.stdin.write((np.array(im.convert('RGB')) if im else f).tobytes())
enc.stdin.close(); enc.wait()
N=int(TOT*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
for src,st,d_,ns,sfx,t0 in tl:
    if src.startswith('IMG'):
        a=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-ss',str(st),'-i',V+src+'.mp4','-t',str(d_),'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout,np.float32).copy()
        add(a,t0,0.18)
    tt=t0+0.1
    for n in ns: add(rd(V+f'narr/{n}.wav'),tt,1.0); tt+=wdur(V+f'narr/{n}.wav')+0.25
    if sfx: add(rd(S+f'labsfx/{sfx}.wav'),t0,0.5)
    if src=='HOW':
        for x in HT[1:]: add(rd(S+'labsfx/touch1.wav'),x,0.45)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(V+'a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',V+'v.mp4','-i',V+'a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',round(TOT,1))
