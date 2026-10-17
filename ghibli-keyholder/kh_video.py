exec(open('kh.py').read())
def wdur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
HOOK=wdur('khn/hook.wav')+0.1
P0,T0=thumb_layers()
def grid_bg(t):
    im=Image.new('RGB',(W,H),(244,242,236)); d=ImageDraw.Draw(im); ph=t*1.4; ln=(46,125,62)
    for i in range(-1,11):
        x0=i*118+20; d.line([(x0+30*math.sin(y/260+i*1.7+ph)+14*math.sin(y/97+i+ph*0.7),y) for y in range(-20,H+40,40)],fill=ln,width=6,joint='curve')
    for j in range(-1,18):
        y0=j*118+30; d.line([(x,y0+28*math.sin(x/230+j*1.3+ph*0.8)+10*math.sin(x/83+j+ph*0.6)) for x in range(-20,W+40,40)],fill=ln,width=6,joint='curve')
    return im.convert('RGBA')
SW=[]
xs=[200,435,670,900]
for k,(n,r) in enumerate([(1,-7),(5,5),(6,-5),(7,7)]): SW.append((cut_sticker(n,250,400,0),xs[k],505+(30 if k%2 else 0),r,k*0.9))
for k,(n,r) in enumerate([(9,6),(10,-5),(14,5),(15,-7)]): SW.append((cut_sticker(n,260,400,0),xs[k],1345-(30 if k%2 else 0),r,k*0.9+0.5))
def swing_layer(t):
    L=layer()
    for st,cx,cy,base,ph in SW:
        ang=base+6*math.sin(2*math.pi*t/1.5+ph)
        c=Image.new('RGBA',(st.width,st.height*2),(0,0,0,0)); c.alpha_composite(st,(0,st.height))
        r=c.rotate(ang,resample=Image.BICUBIC,expand=True)
        top=cy-st.height/2  # pivot = top center of sticker
        L.alpha_composite(r,(int(cx-r.width/2),int(top-r.height/2)))
    return L
def hook_frame(t):
    f=BG.copy(); f.alpha_composite(shifted(swing_layer(t))); f.alpha_composite(shifted(T0)); return f
TL=[]; t=HOOK
for p,pg in enumerate(PAGES):
    st=t; its=[]
    for k,it in enumerate(pg):
        its.append((t,k,it)); t+=wdur(f'khn/{it[0]}.wav')+0.08
    t+=0.1; TL.append((st,t,p,its))
CTA_T=t; CTA=wdur('khn/cta.wav')+0.5; DUR=CTA_T+CTA
HEAD=[head_layer(p) for p in range(len(PAGES))]
ILS={(p,k):item_layer(k,it) for p,pg in enumerate(PAGES) for k,it in enumerate(pg)}
# CTA layers
C=layer(); d=ImageDraw.Draw(C)
text(C,'どれが欲しい？',100,900,560,DARK,14)
pill(C,W/2,720,'コメントで教えてね',54,GREEN,WHITE,46)
mini=layer(); xs=[215,445,675,905]
for k,(n,*_) in enumerate(ITEMS[:4]): paste(mini,photo(n,190,[-5,4,-4,5][k]),xs[k],950)
fp=fonts(900,62); tx='フォローしてね'; w_=tlen(tx,fp)+190; x0=W/2-w_/2; y0=1220
d.rounded_rectangle((x0,y0-60,x0+w_,y0+60),60,fill=GREEN,outline=WHITE,width=8)
cx=x0+70; d.ellipse((cx-33,y0-33,cx+33,y0+33),fill=WHITE); d.rectangle((cx-18,y0-5,cx+18,y0+5),fill=GREEN); d.rectangle((cx-5,y0-18,cx+5,y0+18),fill=GREEN)
text(C,tx,62,900,y0,WHITE,cx=x0+w_/2+40)
CHS=[sticker('totoro019',360,'L'),sticker('totoro044',330,'R')]
CTAF=compose(mini,C)
for j,st in enumerate(CHS):
    if st.width>520: CHS[j]=st.resize((520,int(st.height*520/st.width)),Image.LANCZOS)
for j,st in enumerate(CHS): CTAF.alpha_composite(st,(0 if j==0 else W-st.width,H-st.height+8))
def pop(L,a):
    if a>=1: return L
    s=0.75+0.25*a; bb=L.getbbox(); cx=(bb[0]+bb[2])/2; cy=(bb[1]+bb[3])/2
    c=L.crop(bb); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s)))); o=layer(); o.alpha_composite(c,(int(cx-c.width/2),int(cy-c.height/2))); return o
def render(t):
    if t<HOOK: return hook_frame(t)
    for st,en,p,its in TL:
        if t<en:
            f=BG.copy(); L=layer(); L.alpha_composite(HEAD[p])
            for t0,k,it in its:
                if t>=t0: L.alpha_composite(pop(ILS[(p,k)],min(1,(t-t0)/0.12)))
            f.alpha_composite(shifted(L)); return f
    return CTAF
SR=44100
def build_audio():
    tot=np.zeros(int(SR*(DUR+0.5)))
    def add(p,t,g):
        with wave.open(p) as w: sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
        if sr!=SR: x=np.interp(np.arange(0,len(x),sr/SR),np.arange(len(x)),x)
        i=int(t*SR); n=min(len(x),len(tot)-i); tot[i:i+n]+=g*x[:n]
    add('khn/hook.wav',0.0,1.0)
    for st,en,p,its in TL:
        for t0,k,it in its: add('sfx/pop.wav',t0,0.35); add(f'khn/{it[0]}.wav',t0+0.02,1.0)
    add('sfx/pinpon.wav',CTA_T,0.3); add('khn/cta.wav',CTA_T+0.03,1.0)
    x=tot/np.abs(tot).max()*0.92
    with wave.open(S_+'kh_audio.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
build_audio()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',S_+'kh_audio.wav',
 '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',OUT+'keyholder_vol1.mp4'],stdin=subprocess.PIPE)
cache={}
for n in range(int(FPS*DUR)):
    fr=render(n/FPS); key=id(fr)
    p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode,round(DUR,2))
render(CTA_T+0.5).convert('RGB').save(S_+'kh_cta.png')
