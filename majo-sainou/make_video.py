import sys; sys.argv=['x']
exec(open('kh.py').read())
from PIL import ImageFont
OUT='/home/user/-/majo-sainou/'
RED=(206,72,80); NAVY=(40,60,110); GRAY=(110,100,92); YEL=(255,226,0)
KF='fonts/keifont.ttf'
def wdur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
def still(name,w,h,fx=0.5,fy=0.5,r=24):
    im=Image.open(f'gb/{name}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-w)*fx); y=int((im.height-h)*fy); c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,r)); return c
def fullbg(name,dark=110,fx=0.5):
    im=Image.open(f'gb/{name}.jpg').convert('RGB'); s=max(W/im.width,H/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-W)*fx); y=(im.height-H)//2; f=im.crop((x,y,x+W,y+H)).convert('RGBA'); f.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,dark))); return f
def kf(L,t,size,cy,fill,inner=(20,20,20),outer=WHITE,si=14,so=26,cx=540,rot=0,maxw=None):
    f=ImageFont.truetype(KF,size)
    while maxw and f.getlength(t)>maxw: size-=4; f=ImageFont.truetype(KF,size)
    tw=int(f.getlength(t))+so*2+40; th=int(size*1.5)+so*2
    T=Image.new('RGBA',(tw,th),(0,0,0,0)); d=ImageDraw.Draw(T); x=so+20; y=th/2
    def solid(ox,oy,sw,col):
        m=Image.new('L',T.size,0); ImageDraw.Draw(m).text((x+ox,y+oy),t,font=f,fill=255,anchor='lm',stroke_width=sw,stroke_fill=255)
        m=m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
        c=Image.new('RGBA',T.size,col); c.putalpha(m.point(lambda v:int(v*(col[3] if len(col)>3 else 255)/255))); T.alpha_composite(c)
    solid(8,10,so,(0,0,0,140)); solid(0,0,so,outer); solid(0,0,si,inner)
    d.text((x,y),t,font=f,fill=fill,anchor='lm')
    if rot: T=T.rotate(rot,resample=Image.BICUBIC,expand=True)
    L.alpha_composite(T,(int(cx-T.width/2),int(cy-T.height/2)))
CX=540; CW=880
STEPS=['機械に頼る','飛べなくなる','助言','信じ続ける']
SEC=[dict(k='majo010',kt='魔法ではなく、汽車に乗る',ks='自分で飛ばずに、機械に頼ってしまう',h='便利な機械に頼りたくなる',hs=None),
dict(k='majo039',kt='突然、飛べなくなる',ks='好きだったことが、できなくなる',h='名作なのにヒットしない時期',hs=['laputa041','totoro044']),
dict(k='majo041',kt='ウルスラに救われる',ks='「描けなくなったら休めばいい」',h='ウルスラ＝作り手の本音？',hs=['majo042']),
dict(k='majo047',kt='魔法を信じ続けて、また飛べた',ks='成功の理由：自分の魔法を信じ続けた',h='筆を動かし続けて、大ヒット！',hs=['majo050'])]
def header(i,phase):
    L=layer(); d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-CW/2,215,CX+CW/2,285),35,fill=RED); text(L,'魔女宅 × 宮崎駿の「才能論」',38,900,250,WHITE,cx=CX)
    sw=(CW-30)/4
    for j,s in enumerate(STEPS):
        x0=CX-CW/2+j*(sw+10); col=GREEN if j==i else ((150,190,160) if j<i else (215,212,205))
        d.rounded_rectangle((x0,305,x0+sw,365),30,fill=col)
        text(L,f'{j+1} {s}',26,900,335,WHITE,cx=x0+sw/2,maxw=sw-16)
    text(L,'© Studio Ghibli',18,800,385,GRAY)
    return L
HAY=Image.open('cut/hayao.png').convert('RGBA')
def hay_icon(h):
    im=HAY.crop((0,0,HAY.width,int(HAY.height*0.55))); im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    m=Image.new('L',im.size,0); ImageDraw.Draw(m).ellipse((0,0,min(im.size)-1,min(im.size)-1),fill=255)
    c=Image.new('RGBA',(min(im.size),min(im.size)),(255,253,246,255)); sq=im.crop(((im.width-c.width)//2,0,(im.width-c.width)//2+c.width,c.height)); c.alpha_composite(sq)
    c.putalpha(m.crop((0,0,c.width,c.height))); o=Image.new('RGBA',(c.width+12,c.height+12),(0,0,0,0)); ImageDraw.Draw(o).ellipse((0,0,o.width-1,o.height-1),fill=NAVY); o.alpha_composite(c,(6,6)); return o
HI=hay_icon(130)
def kiki_big(i):
    s=SEC[i]; L=layer(); d=ImageDraw.Draw(L); y0=420; ph=640
    d.rounded_rectangle((CX-CW/2-10,y0-10,CX+CW/2+10,y0+ph+10),36,fill=WHITE)
    L.alpha_composite(still(s['k'],CW,ph),(CX-CW//2,y0))
    pill(L,CX-CW/2+95,y0+40,'キキ',34,RED,WHITE,30)
    d.rounded_rectangle((CX-CW/2,y0+ph+40,CX+CW/2,y0+ph+250),30,fill=(255,255,255,245),outline=RED,width=5)
    text(L,s['kt'],56,900,y0+ph+110,RED,cx=CX,maxw=CW-40)
    text(L,s['ks'],36,800,y0+ph+190,DARK,cx=CX,maxw=CW-40)
    return L
def both(i):
    s=SEC[i]; L=layer(); d=ImageDraw.Draw(L)
    y0=420; ph=330
    d.rounded_rectangle((CX-CW/2-8,y0-8,CX+CW/2+8,y0+ph+8),32,fill=WHITE)
    c=still(s['k'],CW,ph); band=Image.new('RGBA',(CW,90),(0,0,0,150)); c.alpha_composite(band,(0,ph-90)); c.putalpha(rmask(CW,ph,24)); L.alpha_composite(c,(CX-CW//2,y0))
    pill(L,CX-CW/2+95,y0+36,'キキ',30,RED,WHITE,26); text(L,s['kt'],46,900,y0+ph-45,WHITE,cx=CX,maxw=CW-40)
    # equals badge
    by=y0+ph+62; d.rounded_rectangle((CX-280,by-40,CX+280,by+40),40,fill=YEL,outline=WHITE,width=5)
    text(L,'＝ 作り手にも同じ誘惑が' if i==0 else '＝ 宮崎駿にも同じことが',34,900,by,DARK,cx=CX)
    y1=by+60; hh=1440-y1
    d.rounded_rectangle((CX-CW/2,y1,CX+CW/2,y1+hh),34,fill=(255,253,246,250),outline=NAVY,width=6)
    if i==0: pill(L,CX-CW/2+110,y1+60,'作り手',34,NAVY,WHITE,30)
    else:
        L.alpha_composite(HI,(int(CX-CW/2+24),int(y1+20))); text(L,'宮崎駿',30,900,y1+60,NAVY,cx=CX-CW/2+300)
    text(L,s['h'],48,900,y1+118,NAVY,cx=CX+70,maxw=CW-220)
    iy=y1+190; ih=hh-215
    if s['hs'] is None:
        d.rounded_rectangle((CX-CW/2+30,iy,CX+CW/2-30,iy+ih),26,fill=(240,236,226))
        bw=300; bh=170; cy=iy+ih*0.42
        d.rounded_rectangle((CX-bw-60,cy-bh/2,CX-60,cy+bh/2),26,fill=(255,255,255),outline=(190,185,175),width=4)
        text(L,'自分の手',46,900,cy,(170,165,155),cx=CX-60-bw/2)
        d.rounded_rectangle((CX+60,cy-bh/2,CX+60+bw,cy+bh/2),26,fill=NAVY)
        text(L,'機械・技術',46,900,cy,WHITE,cx=CX+60+bw/2)
        d.polygon([(CX-40,cy-30),(CX+40,cy),(CX-40,cy+30)],fill=RED)
        text(L,'つい、便利な方に頼りたくなる',36,900,iy+ih*0.82,RED,cx=CX)
    else:
        n=len(s['hs']); gap=20; iw=(CW-60-gap*(n-1))//n
        for k,nm in enumerate(s['hs']):
            x=CX-CW//2+30+k*(iw+gap); L.alpha_composite(still(nm,iw,ih),(int(x),int(iy)))
        if i==1:
            for k,lab in enumerate(['ラピュタ(1986)','トトロ(1988)']):
                pill(L,CX-CW//2+30+k*(iw+gap)+iw/2,iy+ih-30,lab,26,(0,0,0),WHITE,18)
            pill(L,CX,iy+40,'公開当時は伸び悩み…',30,RED,WHITE,24)
        if i==3:
            pill(L,CX,iy+50,'1989年 邦画1位・ジブリ初の大ヒット',34,RED,WHITE,28)
            d.rounded_rectangle((CX-CW/2+30,iy+ih-86,CX+CW/2-30,iy+ih),0,fill=(0,0,0,175))
            text(L,'成功の理由：自分の手で、筆を動かし続けた',32,900,iy+ih-43,YEL,cx=CX,maxw=CW-80)
    return L
# summary
ROWS=[('汽車に頼る','機械に頼る誘惑'),('飛べなくなる','ヒットしない時期'),('ウルスラの言葉','作り手の本音'),('魔法を信じ続けた','筆を動かし続けた')]
def summary(nrows):
    L=layer(); d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-CW/2,215,CX+CW/2,285),35,fill=RED); text(L,'まとめ',40,900,250,WHITE,cx=CX)
    cw2=(CW-20)/2
    pill(L,CX-cw2/2-10,370,'キキ',40,RED,WHITE,60); pill(L,CX+cw2/2+10,370,'宮崎駿',40,NAVY,WHITE,60)
    for r in range(nrows):
        a,b=ROWS[r]; y=450+r*230
        d.rounded_rectangle((CX-CW/2,y,CX-10,y+190),28,fill=(255,255,255,245),outline=RED,width=4)
        d.rounded_rectangle((CX+10,y,CX+CW/2,y+190),28,fill=(255,253,246,245),outline=NAVY,width=4)
        text(L,a,40,900,y+95,RED,cx=CX-cw2/2-10,maxw=cw2-30); text(L,b,40,900,y+95,NAVY,cx=CX+cw2/2+10,maxw=cw2-30)
        d.ellipse((CX-30,y+65,CX+30,y+125),fill=YEL,outline=WHITE,width=4); text(L,'＝',34,900,y+95,DARK,cx=CX)
    if nrows>=4:
        d.rounded_rectangle((CX-CW/2,1380,CX+CW/2,1450),35,fill=GREEN); text(L,'成功の理由は「信じて、続けること」',38,900,1415,WHITE,cx=CX)
    return L
# opening (thumbnail)
OPBG=fullbg('majo011',110,0.45)
def hsticker(h,ow=12):
    im=HAY.resize((int(HAY.width*h/HAY.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.crop((0,0,out.width-pad,out.height-pad))
HST=hsticker(800); OPBG.alpha_composite(HST,(W-HST.width,H-HST.height))
O1=layer()
kf(O1,'魔女の宅急便は',96,520,WHITE)
kf(O1,'宮崎駿の',130,690,WHITE,inner=(200,30,40))
kf(O1,'才能論',250,900,YEL,si=18,so=34)
kf(O1,'だった！',120,1090,WHITE,inner=(200,30,40))
O2=layer()
for k,(a,b) in enumerate([('魔法','才能'),('キキ','宮崎駿')]):
    y=1260+k*115; d=ImageDraw.Draw(O2); d.rounded_rectangle((CX-330,y-50,CX+330,y+50),50,fill=(255,255,255,235))
    text(O2,a,50,900,y,RED,cx=CX-170); text(O2,'＝',50,900,y,DARK,cx=CX); text(O2,b,50,900,y,NAVY,cx=CX+170)
cop=layer(); text(cop,'© Studio Ghibli',20,800,1500,(235,235,235),cx=270); text(cop,'Photo: Natasha Baucas (CC BY 2.0) 加工',20,800,1530,(235,235,235),cx=270)
ENDBG=fullbg('majo001',90,0.5)
E1=layer(); kf(E1,'あなたにとっての',90,780,WHITE); kf(E1,'「魔法」は？',150,950,YEL,si=16,so=30)
pill(E1,CX,1150,'コメントで教えてね',54,GREEN,WHITE,46)
cend=layer(); text(cend,'© Studio Ghibli　VOICEVOX:青山龍星',22,800,1500,(240,240,240))
# timeline
G=0.1; TL=[]; t=0
for k in ['h1','h2']: TL.append((k,t)); t+=wdur(f'mjn/{k}.wav')+G
for i in range(4):
    for s in 'kh': TL.append((f'{i+1}{s}',t)); t+=wdur(f'mjn/{i+1}{s}.wav')+G
TL.append(('sum',t)); t+=wdur('mjn/sum.wav')+0.4
TL.append(('end',t)); t+=wdur('mjn/end.wav')+0.6; DUR=t
ST={k:v for k,v in TL}
SUB={'1k':['旅立ってすぐ、キキは自分の魔法で飛ばずに','汽車という機械に乗って、眠ってしまいます'],
'1h':['作り手も同じです','便利な機械や技術があると','つい自分の手より','そっちに頼りたくなってしまう'],
'2k':['ある日キキは、突然、飛べなくなります'],
'2h':['宮崎駿にも、そんな時期がありました','ラピュタもトトロも、公開当時は','思ったほどヒットしなかったんです'],
'3k':['落ち込むキキに、絵描きのウルスラは言います','描けなくなったら','無理せず休めばいい、と'],
'3h':['絵を描く人の言葉','それは、作り手である宮崎駿自身の','本音のようにも聞こえます'],
'4k':['それでもキキは、汽車ではなく','自分の魔法を、信じ続けました','そして、もう一度、空へ'],
'4h':['宮崎駿も同じ','どんなときも、自分の手で','筆を動かし続けました','そして魔女の宅急便は、その年の邦画1位','ジブリ初の大ヒットに','キキと一緒に、宮崎駿も飛べたんです'],
'sum':['キキに起きた4つの出来事は','宮崎駿自身の歩みと','ぴったり重なっていたんです']}
SUBT=[]
for key,chunks in SUB.items():
    t0=ST[key]; dd=wdur(f'mjn/{key}.wav'); tot=sum(len(c) for c in chunks); acc=0
    for c in chunks: a=t0+dd*acc/tot; acc+=len(c); SUBT.append((a,t0+dd*acc/tot,c))
SUBL={}
def sub_layer(c):
    if c in SUBL: return SUBL[c]
    L=layer(); d=ImageDraw.Draw(L); sz=44; fp=fonts(900,sz)
    while tlen(c,fp)>880: sz-=2; fp=fonts(900,sz)
    w_=tlen(c,fp)+60; d.rounded_rectangle((CX-w_/2,1470,CX+w_/2,1542),20,fill=(0,0,0,180)); text(L,c,sz,900,1506,WHITE,cx=CX); SUBL[c]=L; return L
HD=[header(i,0) for i in range(4)]; KB=[kiki_big(i) for i in range(4)]; BO=[both(i) for i in range(4)]; SM=[summary(n) for n in range(5)]
def subs(t):
    for a,b,c in SUBT:
        if a<=t<b+0.12: return [sub_layer(c)]
    return []
def render(t):
    if t<ST['1k']:
        f=OPBG.copy(); f.alpha_composite(shifted(O1))
        if t>=ST['h2']: f.alpha_composite(shifted(O2))
        f.alpha_composite(shifted(cop)); return f
    if t<ST['sum']:
        i=max(j for j in range(4) if t>=ST[f'{j+1}k'])
        main=BO[i] if t>=ST[f'{i+1}h'] else KB[i]
        return compose(HD[i],main,*subs(t))
    if t<ST['end']:
        dd=wdur('mjn/sum.wav'); n=min(4,1+int((t-ST['sum'])/(dd/4.5)))
        return compose(SM[n],*subs(t))
    f=ENDBG.copy(); f.alpha_composite(shifted(E1)); f.alpha_composite(shifted(cend)); return f
SR=44100
def build_audio():
    tot=np.zeros(int(SR*(DUR+1)))
    def add(p,t,g):
        with wave.open(p) as w: sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
        if sr!=SR: x=np.interp(np.arange(0,len(x),sr/SR),np.arange(len(x)),x)
        i=int(t*SR); n=min(len(x),len(tot)-i); tot[i:i+n]+=g*x[:n]
    add('labsfx/text-impact1.wav',0,0.45)
    for k,t0 in TL: add(f'mjn/{k}.wav',t0,1.0)
    add('labsfx/shock1.wav',ST['2k'],0.4); add('labsfx/shakin2.wav',ST['4k'],0.4)
    for i in range(4): add('labsfx/flash2.wav' if i<3 else 'labsfx/correct2.wav',ST[f'{i+1}h'],0.35)
    add('labsfx/kira1.wav',ST['sum'],0.35)
    x=tot/np.abs(tot).max()*0.92
    with wave.open(S_+'majo_audio.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
if 'render' in sys.argv[0:1] or True:
    pass
build_audio()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',S_+'majo_audio.wav',
 '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',OUT+'majo_sainou.mp4'],stdin=subprocess.PIPE)
for n in range(int(FPS*DUR)): p.stdin.write(render(n/FPS).convert('RGB').tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode,round(DUR,2))
render(0.0).convert('RGB').save(OUT+'cover.png')
