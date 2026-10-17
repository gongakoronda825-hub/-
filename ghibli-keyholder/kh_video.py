exec(open('kh.py').read())
def wdur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
HOOK=wdur('khn/hook.wav')+0.35
P0,T0=thumb_layers(); HOOKF=compose(P0,T0)
TL=[]; t=HOOK
for p,pg in enumerate(PAGES):
    st=t; its=[]
    for k,it in enumerate(pg):
        its.append((t,k,it)); t+=wdur(f'khn/{it[0]}.wav')+0.3
    t+=0.3; TL.append((st,t,p,its))
CTA_T=t; CTA=wdur('khn/cta.wav')+0.9; DUR=CTA_T+CTA
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
    if t<HOOK: return HOOKF
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
        for t0,k,it in its: add('sfx/pop.wav',t0,0.35); add(f'khn/{it[0]}.wav',t0+0.08,1.0)
    add('sfx/pinpon.wav',CTA_T,0.3); add('khn/cta.wav',CTA_T+0.1,1.0)
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
