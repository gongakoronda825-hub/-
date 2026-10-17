import sys; sys.argv=['x']
exec(open('kh.py').read())
OUT='/home/user/-/majo-sainou/'
RED=(196,72,52); GRAY=(110,100,92); NAVY=(40,60,110)
def wdur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
def still(name,w,h,fx=0.5,fy=0.5,r=24):
    im=Image.open(f'gb/{name}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-w)*fx); y=int((im.height-h)*fy); c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,r)); return c
def fullbg(name,dark=110,fx=0.5):
    im=Image.open(f'gb/{name}.jpg').convert('RGB'); s=max(W/im.width,H/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-W)*fx); y=(im.height-H)//2; f=im.crop((x,y,x+W,y+H)).convert('RGBA'); f.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,dark))); return f
CX=540; CW=860
SEC=[('1｜頼りたくなる','majo010','最初は汽車に乗る',None,'それでも手で描き続けた'),
('2｜飛べなくなる','majo039','突然、飛べなくなる',['laputa041','totoro044'],'名作なのにヒットしない'),
('3｜ウルスラの言葉','majo041','ウルスラに救われる',['majo042'],'ウルスラ＝作り手の本音？'),
('4｜もう一度飛ぶ','majo047','自分の力で、もう一度空へ',['majo050'],'ジブリ初の大ヒット！')]
def kiki_layer(i):
    ch,img,tel,_,_=SEC[i]; L=layer(); d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-CW/2,220,CX+CW/2,290),35,fill=(206,72,80))
    text(L,'魔女宅 × 宮崎駿の「才能論」',40,900,256,WHITE,cx=CX)
    pill(L,CX,345,ch,36,GREEN,WHITE,40)
    y0=400; ph=430
    d.rounded_rectangle((CX-CW/2-10,y0-10,CX+CW/2+10,y0+ph+10),34,fill=WHITE)
    c=still(img,CW,ph); band=Image.new('RGBA',(CW,96),(0,0,0,150)); c.alpha_composite(band,(0,ph-96)); c.putalpha(rmask(CW,ph,24))
    L.alpha_composite(c,(CX-CW//2,y0))
    pill(L,CX-CW/2+90,y0+30,'キキ',30,(206,72,80),WHITE,26)
    text(L,tel,50,900,y0+ph-48,WHITE,cx=CX,maxw=CW-40)
    d.polygon([(CX-36,y0+ph+28),(CX+36,y0+ph+28),(CX,y0+ph+68)],fill=GREEN)
    return L
def hayao_layer(i):
    _,_,_,imgs,tel=SEC[i]; L=layer(); d=ImageDraw.Draw(L)
    y0=930; hh=530
    d.rounded_rectangle((CX-CW/2,y0,CX+CW/2,y0+hh),34,fill=(255,253,246,250),outline=NAVY,width=6)
    pill(L,CX-CW/2+120,y0,'宮崎駿',32,NAVY,WHITE,30)
    text(L,tel,52,900,y0+85,NAVY,cx=CX,maxw=CW-50)
    if imgs is None:
        d.rounded_rectangle((CX-360,y0+150,CX+360,y0+460),26,fill=(240,236,226))
        text(L,'「生命に対する侮辱」',62,900,y0+270,RED,cx=CX)
        text(L,'AIに動きを学習させたCGを見て',32,800,y0+370,DARK,cx=CX)
        text(L,'2016年 NHKスペシャルより',26,800,y0+430,GRAY,cx=CX)
    else:
        n=len(imgs); gap=24; iw=(CW-60-gap*(n-1))//n; ih=330 if n==1 else 300
        for k,nm in enumerate(imgs):
            x=CX-CW//2+30+k*(iw+gap); L.alpha_composite(still(nm,iw,ih),(int(x),y0+145))
        if i==1:
            for k,lab in enumerate(['ラピュタ（1986）','トトロ（1988）']):
                x=CX-CW//2+30+k*(iw+gap)+iw/2; pill(L,x,y0+145+ih-28,lab,24,(0,0,0),WHITE,18)
        if i==3:
            pill(L,CX+250,y0+190,'1989年 邦画1位',34,RED,WHITE,30)
    return L
def compose2(bg,*Ls):
    f=bg.copy()
    for L in Ls: f.alpha_composite(shifted(L))
    return f
# opening
OPBG=fullbg('majo011',120,0.45)
def yt(L,t,size,cy,fill,inner=(20,20,20),outer=WHITE,si=14,so=26,cx=CX,rot=0,maxw=None):
    fp=fonts(900,size)
    while maxw and tlen(t,fp)>maxw: size-=4; fp=fonts(900,size)
    tw=int(tlen(t,fp))+so*2+40; th=int(size*1.6)+so*2
    T=Image.new('RGBA',(tw,th),(0,0,0,0)); d=ImageDraw.Draw(T)
    def run(ox,oy,col,sw):
        x=so+20+ox
        for s_ in segs(t):
            f=fp[1 if s_.isascii() else 0]; d.text((x,th/2+oy),s_,font=f,fill=col,anchor='lm',stroke_width=sw,stroke_fill=col); x+=f.getlength(s_)
    run(8,10,(0,0,0,150),so)   # drop shadow
    run(0,0,outer,so); run(0,0,inner,si)
    x=so+20
    for s_ in segs(t):
        f=fp[1 if s_.isascii() else 0]; d.text((x,th/2),s_,font=f,fill=fill,anchor='lm'); x+=f.getlength(s_)
    if rot: T=T.rotate(rot,resample=Image.BICUBIC,expand=True)
    L.alpha_composite(T,(int(cx-T.width/2),int(cy-T.height/2)))
O1=layer()
yt(O1,'魔女の宅急便は',86,560,WHITE,rot=3)
yt(O1,'宮崎駿の',120,720,WHITE,inner=(200,30,40),rot=3)
yt(O1,'才能論',230,920,(255,226,0),si=18,so=32,rot=3)
yt(O1,'だった！',110,1100,WHITE,inner=(200,30,40),rot=3)
O2=layer()
for k,(a,b) in enumerate([('魔法','才能'),('キキ','宮崎駿')]):
    y=1260+k*115; d=ImageDraw.Draw(O2); d.rounded_rectangle((CX-330,y-52,CX+330,y+52),52,fill=(255,255,255,235))
    text(O2,a,52,900,y,(206,72,80),cx=CX-170); text(O2,'＝',52,900,y,DARK,cx=CX); text(O2,b,52,900,y,NAVY,cx=CX+170)
def hsticker(h,ow=12):
    im=Image.open('cut/hayao.png').convert('RGBA'); im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.crop((0,0,out.width-pad,out.height-pad))
HST=hsticker(800)
OPBG.alpha_composite(HST,(W-HST.width,H-HST.height))
credit_op=layer(); text(credit_op,'© Studio Ghibli',20,800,1500,(235,235,235),cx=280); text(credit_op,'Photo: Natasha Baucas (CC BY 2.0) 加工',20,800,1530,(235,235,235),cx=280)
ENDBG=fullbg('majo001',90,0.5)
E1=layer(); text(E1,'あなたにとっての',70,900,780,WHITE); text(E1,'「魔法」は？',120,900,920,(255,226,120))
pill(E1,CX,1110,'コメントで教えてね',54,GREEN,WHITE,46)
credit=layer(); text(credit,'© Studio Ghibli　VOICEVOX:青山龍星',22,800,1500,(240,240,240))
credit2=layer(); text(credit2,'© Studio Ghibli',20,800,203,GRAY)
# timeline
G=0.1; TL=[]; t=0
TL.append(('h1',t)); t+=wdur('mjn/h1.wav')+G
TL.append(('h2',t)); t+=wdur('mjn/h2.wav')+G
for i in range(4):
    for s in 'kh': TL.append((f'{i+1}{s}',t)); t+=wdur(f'mjn/{i+1}{s}.wav')+G
TL.append(('end',t)); t+=wdur('mjn/end.wav')+0.6; DUR=t
ST={k:v for k,v in TL}
SUB={'1k':['旅立ってすぐ、キキは自分で飛ばずに','汽車に乗って眠ってしまいます'],
'1h':['宮崎駿は、便利な方法に頼らず','手で描くことにこだわり続けた人','AIに動きを学習させたCGを見せられたときは','「生命に対する侮辱」とまで語りました'],
'2k':['ある日キキは、突然、飛べなくなります'],
'2h':['宮崎駿にも、そんな時期がありました','ラピュタもトトロも、公開当時は','思ったほどヒットしなかったんです'],
'3k':['落ち込むキキに、絵描きのウルスラは言います','描けなくなったら','無理せず休めばいい、と'],
'3h':['絵を描く人の言葉','それは、作り手である宮崎駿自身の','本音のようにも聞こえます'],
'4k':['そしてキキは、自分の力を信じて','もう一度、空へ'],
'4h':['魔女の宅急便は、その年の邦画1位','ジブリ初の大ヒットになりました','キキと一緒に、宮崎駿も飛べたんです']}
SUBT=[]
for key,chunks in SUB.items():
    t0=ST[key]; dd=wdur(f'mjn/{key}.wav'); tot=sum(len(c) for c in chunks); acc=0
    for c in chunks:
        a=t0+dd*acc/tot; acc+=len(c); SUBT.append((a,t0+dd*acc/tot,c))
SUBL={}
def sub_layer(c):
    if c in SUBL: return SUBL[c]
    L=layer(); d=ImageDraw.Draw(L); fp=fonts(900,44); sz=44
    while tlen(c,fp)>880: sz-=2; fp=fonts(900,sz)
    w_=tlen(c,fp)+60; d.rounded_rectangle((CX-w_/2,1500,CX+w_/2,1572),20,fill=(0,0,0,170))
    text(L,c,sz,900,1536,WHITE,cx=CX); SUBL[c]=L; return L
KL=[kiki_layer(i) for i in range(4)]; HL=[hayao_layer(i) for i in range(4)]
def render(t):
    if t<ST['1k']:
        f=OPBG.copy(); f.alpha_composite(shifted(O1))
        if t>=ST['h2']: f.alpha_composite(shifted(O2))
        f.alpha_composite(shifted(credit_op)); return f
    if t<ST['end']:
        i=max(j for j in range(4) if t>=ST[f'{j+1}k'])
        Ls=[KL[i]]+([HL[i]] if t>=ST[f'{i+1}h'] else [])+[credit2]
        for a,b,c in SUBT:
            if a<=t<b+0.12: Ls.append(sub_layer(c)); break
        return compose2(BG,*Ls)
    f=ENDBG.copy(); f.alpha_composite(shifted(E1)); f.alpha_composite(shifted(credit)); return f
SR=44100
def build_audio():
    tot=np.zeros(int(SR*(DUR+0.5)))
    def add(p,t,g):
        with wave.open(p) as w: sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
        if sr!=SR: x=np.interp(np.arange(0,len(x),sr/SR),np.arange(len(x)),x)
        i=int(t*SR); n=min(len(x),len(tot)-i); tot[i:i+n]+=g*x[:n]
    for k,t0 in TL:
        add(f'mjn/{k}.wav',t0,1.0)
        if k.endswith('k'): add('sfx/pop.wav',t0,0.3)
        if k.endswith('h') and k!='h1' and k!='h2': add('sfx/whoosh.wav',max(0,t0-0.12),0.25)
    x=tot/np.abs(tot).max()*0.92
    with wave.open(S_+'majo_audio.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
if __name__=='__main__' and len(sys.argv)>0 and 'stills' in open('/proc/self/cmdline').read():
    pass
build_audio()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',S_+'majo_audio.wav',
 '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',OUT+'majo_sainou.mp4'],stdin=subprocess.PIPE)
for n in range(int(FPS*DUR)): p.stdin.write(render(n/FPS).convert('RGB').tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode,round(DUR,2))
render(0.3).convert('RGB').save(OUT+'cover.png')
render(ST['1h']+0.3).convert('RGB').save(S_+'mj_chk.png')
