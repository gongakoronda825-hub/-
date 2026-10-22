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
IBG=cover(Image.open(S+'gb/chihiro011.jpg').convert('RGB'),int(W*1.12),int(H*1.12)).filter(ImageFilter.GaussianBlur(3)); IBG=Image.blend(IBG,Image.new('RGB',IBG.size,(0,0,0)),0.15)
bg=Image.new('RGBA',(W,H),(0,0,0,0))
fg=sc.resize((900,int(sc.height*900/sc.width)),Image.LANCZOS); x0,y0=(W-900)//2-40,(H-fg.height)//2-80
sh=Image.new('L',(W,H),0); ImageDraw.Draw(sh).rounded_rectangle((x0-6,y0+14,x0+906,y0+fg.height+26),24,fill=150); bg.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(18)))
ImageDraw.Draw(bg).rounded_rectangle((x0-12,y0-12,x0+912,y0+fg.height+12),26,fill=WHITE+(255,)); bg.paste(fg,(x0,y0))
ImageDraw.Draw(bg).text((x0+900,y0+fg.height+60),'© Studio Ghibli',font=ImageFont.truetype(S+'fonts/jp800.woff',28),fill=WHITE,anchor='rs',stroke_width=3,stroke_fill=(0,0,0)); IFG=bg
def introf(n):
    for k in range(n):
        u=k/max(n-1,1); z=1.0+0.08*u
        sw,sh_=int(W*1.12/z),int(H*1.12/z); x=int((IBG.width-sw)*(0.2+0.6*u)); y=(IBG.height-sh_)//2
        b=IBG.crop((x,y,x+sw,y+sh_)).resize((W,H),Image.BILINEAR).convert('RGBA'); b.alpha_composite(IFG); yield np.array(b.convert('RGB'))
# how-to card
kb=cover(Image.open(V+'kyo/02.jpg').convert('RGB'),W,H).filter(ImageFilter.GaussianBlur(2)).convert('RGBA')
pn=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(pn).rounded_rectangle((70,250,1010,1650),40,fill=(255,251,245,205)); kb.alpha_composite(pn); L=kb
ImageDraw.Draw(L).text((540,1700),'南禅寺（京都） Photo: 雷太 / CC BY 2.0',font=ImageFont.truetype(S+'fonts/jp800.woff',24),fill=WHITE,anchor='ms',stroke_width=3,stroke_fill=(0,0,0))
exec(cs[cs.index('def chara('):cs.index('from PIL import ImageOps')].replace("f'cut/","S+f'cut/")); from PIL import ImageOps
for nm,h,r,x,y in [('majo013',230,-8,150,230),('mimi032',220,7,930,230),('karigurashi012',190,-6,150,1760),('mimi049',200,6,930,1760)]:
    c=chara(nm,h,r); L.alpha_composite(c,(int(x-c.width/2),int(y-c.height/2)))
d=ImageDraw.Draw(L)
ctext(d,(W/2,330),'HOW TO GET',fi(40,600),SUB,sp=8)
ctext(d,(W/2,420),'ZEN MAPの買い方',fm(78),INK)
steps=[('1','『禅とジブリ』公式サイトで','二次元コードを表示'),('2','セブン-イレブンの','マルチコピー機にかざす'),('3','400円を入れて','印刷すれば完成！')]
for i,(n,a,b) in enumerate(steps):
    y=560+i*230; d.rounded_rectangle((120,y,960,y+190),30,fill=(255,253,249,255),outline=ACC,width=3)
    d.ellipse((150,y+45,250,y+145),fill=ACC); ctext(d,(200,y+95),n,fi(64,700),WHITE)
    d.text((290,y+62),a,font=fm(42,False),fill=INK,anchor='lm'); d.text((290,y+128),b,font=fm(48),fill=INK,anchor='lm')
y=1290; d.rounded_rectangle((120,y,960,y+250),30,fill=(240,230,215,255))
for i,t in enumerate(['💡 京都で開催中『禅とジブリ』展のオリジナルマップ','📍 全国のセブン-イレブンで販売中','🗾 禅寺をめぐる日英表記の京都観光マップ']):
    pass
for i,t in enumerate(['京都で開催中『禅とジブリ』展のオリジナル','全国のセブン-イレブンで1枚400円','禅寺をめぐる京都観光マップ（日英表記）']):
    d.text((170,y+55+i*72),'・'+t,font=fm(36,False),fill=INK,anchor='lm')
ctext(d,(W/2,1600),'※販売期間などは公式サイトをご確認ください',fm(28,False),SUB)
HOW=np.array(L.convert('RGB'))
FOLLOW=np.array(Image.open(U+'6a98b9bb-image.jpg').convert('RGB').resize((W,H)))
# segments: (source, start, dur, [narr...], sfx)
SEG=[('IMG_0370',0,None,['zb'],'shock1'),('INTRO',0,None,['zi'],'kira1'),('IMG_0372',0.3,None,['z3'],'pa1'),
('IMG_0374',0,None,['z4'],'cute-pose1'),('HOW',0,None,['z5','z6','z7'],'sceneswitch1'),('FOLLOW',0,None,['z8'],'kira1')]
def bigimg(t):
    Lx=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): kf(Lx,l,[70,104][j],H/2+[-70,60][j],[WHITE,(255,214,0)][j],inner=(25,25,25),outer=WHITE,si=14,so=26,cx=W/2,maxw=980)
    return Lx.crop(Lx.getbbox())
def subimg(t):
    Lx=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): kf(Lx,l,54,H/2+(j-(len(ls)-1)/2)*78,WHITE,inner=(35,35,35),outer=(35,35,35),si=9,so=9,cx=W/2,maxw=860)
    return Lx.crop(Lx.getbbox())
SUB={'zb':'セブンのコピー機から\nジブリが出てきた…!?','zi':'禅とジブリ展の\nオリジナルマップ！\nセブンで印刷できる','z1':'ジブリの禅マップが\nセブンで印刷できるらしい！\n行ってみる！','z2':'完成！','z3':'持って帰るよ〜','z4':'こんな感じだった！\n裏には禅の解説も',
'z5':None,'z6':None,'z7':None,'z8':None}
tl=[]; t=0
for src,st,_,ns,sfx in SEG:
    d_=sum(wdur(V+f'narr/{n}.wav')+0.25 for n in ns)+0.5
    if src.startswith('IMG'):
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
        if SUB.get(n): SUBS.append((0 if tt==0 else tt,tt+wdur(V+f'narr/{n}.wav')+0.4,bigimg(SUB[n]) if n=='zb' else subimg(SUB[n])))
        tt+=wdur(V+f'narr/{n}.wav')+0.25
for src,st,d_,ns,sfx,t0 in tl:
    n=int(round(d_*FPS))
    if src.startswith('IMG'):
        p=subprocess.run(['ffmpeg','-v','error','-ss',str(st),'-i',V+src+'.mp4','-t',str(d_),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
        fr=list(np.frombuffer(p,np.uint8).reshape(-1,H,W,3)[:n])
        while len(fr)<n: fr.append(fr[-1])
    elif src=='INTRO': fr=introf(n)
    else: fr=[{'HOW':HOW,'FOLLOW':FOLLOW}[src]]*n
    for k,f in enumerate(fr):
        g=t0+k/FPS; im=None
        for a,b,T in SUBS:
            if a<=g<b:
                kk=int((g-a)*FPS); sc=[0.9,1.08,1.03][kk] if a==0 and kk<3 else 1.0
                TT=T if sc==1.0 else T.resize((int(T.width*sc),int(T.height*sc)),Image.BICUBIC)
                im=Image.fromarray(f).convert('RGBA'); im.alpha_composite(TT,(int(W/2-TT.width/2),int(H/2-TT.height/2)))
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
    if sfx: add(rd(S+f'labsfx/{sfx}.wav'),t0,0.3)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(V+'a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',V+'v.mp4','-i',V+'a.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',round(TOT,1))
