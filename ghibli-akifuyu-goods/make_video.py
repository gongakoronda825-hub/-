# ジブリの秋冬グッズ紹介 vol.1（ナレーション動画）
# 使い方: python3 make_video.py <作業フォルダ(setup.shのW)> <商品画像フォルダ(shop/alt)> <切り抜きフォルダ(akf/cut)> <ナレーションwavのフォルダ> [stills]
import sys,os,math,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S,A,CUT,NR=[a.rstrip('/')+'/' for a in sys.argv[1:5]]
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'akifuyu_vol1.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
WHITE=(255,255,255); INK=(45,40,36); GREEN=(46,125,62); ORANGE=(236,128,60); NAVY=(30,58,110); GRAY=(110,100,92); DARK=(40,36,32)

# ---------- 文字 ----------
_fc={}
def font(w,sz,kind):
    k=(w,sz,kind)
    if k not in _fc: _fc[k]=ImageFont.truetype(S+f'fonts/{kind}{w}.woff',sz)
    return _fc[k]
def segs(t):
    out=[]
    for ch in t:
        k='lat' if ord(ch)<0x2000 else 'jp'
        if out and out[-1][0]==k: out[-1][1]+=ch
        else: out.append([k,ch])
    return out
def tlen(t,sz,w=900): return sum(font(w,sz,k).getlength(s) for k,s in segs(t))
def text(L,t,sz,cx,cy,fill,w=900,stw=0,stc=WHITE,maxw=None):
    while maxw and tlen(t,sz,w)>maxw: sz-=2
    d=ImageDraw.Draw(L); x=cx-tlen(t,sz,w)/2
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
    return x-tlen(t,sz,w),tlen(t,sz,w)
def pill(L,cx,cy,t,sz,bg,fg=WHITE,pad=34,h=None,outline=WHITE):
    tw=tlen(t,sz); h=h or sz*1.6
    ImageDraw.Draw(L).rounded_rectangle((cx-tw/2-pad,cy-h/2,cx+tw/2+pad,cy+h/2),h/2,fill=bg,outline=outline,width=6 if outline else 0)
    text(L,t,sz,cx,cy,fg)
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def paste(L,img,cx,cy): L.alpha_composite(img,(int(cx-img.width/2),int(cy-img.height/2)))

# ---------- 素材 ----------
def card(name,s,rot=0,fy=0.5):
    # 商品写真を白フチ＋影のカードに
    im=Image.open(A+name+'.jpg').convert('RGB'); m=min(im.size); y0=int((im.height-m)*fy)
    im=im.crop(((im.width-m)//2,y0,(im.width+m)//2,y0+m)).resize((s,s),Image.LANCZOS).convert('RGBA'); im.putalpha(rmask(s,s,26))
    pad=14; c=Image.new('RGBA',(s+2*pad+60,s+2*pad+60),(0,0,0,0))
    sh=Image.new('L',c.size,0); ImageDraw.Draw(sh).rounded_rectangle((30,42,30+s+2*pad,42+s+2*pad),36,fill=110); c.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(14)))
    wb=Image.new('RGBA',(s+2*pad,s+2*pad),WHITE+(255,)); wb.putalpha(rmask(s+2*pad,s+2*pad,36)); c.alpha_composite(wb,(30,30)); c.alpha_composite(im,(30+pad,30+pad))
    return c.rotate(rot,Image.BICUBIC,expand=True) if rot else c
def sticker(path,bw,bh,rot=0,ow=10):
    # 切り抜き → 白フチ＋影のステッカー
    im=Image.open(path).convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<40 else v))
    s=min(bw/im.width,bh/im.height); im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    Aa=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=Aa.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(4,8)); w_=Image.new('RGBA',big.size,(255,255,255,0)); w_.putalpha(o); out.alpha_composite(w_); out.alpha_composite(big)
    return out.rotate(rot,Image.BICUBIC,expand=True) if rot else out
def chara(n,h,rot=0,ow=10):
    if ow: return sticker(S+f'cut/{n}.png',900,h,rot,ow)
    im=Image.open(S+f'cut/{n}.png').convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<40 else v))   # 白フチなし
    return im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
def pivot(img):
    # 下のまん中を支点に回せるよう、支点がキャンバスの中心に来るように置く
    c=Image.new('RGBA',(img.width+80,img.height*2+40),(0,0,0,0)); c.alpha_composite(img,(40,20+0)); return c,img.height+20
def swayed(items,g,amp=3,hz=0.5):
    # items=[(pivot画像,支点の位置,x,y下端)]：下を支点に±amp°でゆらゆら
    L=layer()
    for j,(c,cy0,x,yb) in enumerate(items):
        a=amp*math.sin(2*math.pi*hz*g+j*1.9); r=c.rotate(a,Image.BICUBIC,center=(c.width/2,cy0))
        L.alpha_composite(r,(int(x-c.width/2),int(yb-cy0)))
    return L
def sway_item(img,x,cy):
    c,cy0=pivot(img); return (c,cy0,x,cy+img.height/2)
def scene_bg(n):
    im=Image.open(S+f'gb/{n}.jpg').convert('RGB'); cw=int(im.height*W/H); x=(im.width-cw)//2
    b=im.crop((x,0,x+cw,im.height)).resize((int(W*1.1),int(H*1.1)),Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))
    return Image.blend(b,Image.new('RGB',b.size,(0,0,0)),0.22)
def zoomed(B,u):
    z=1.0+0.08*u; sw,sh=B.width/z,B.height/z; x=(B.width-sw)*(0.3+0.4*u); y=(B.height-sh)/2
    return B.resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh))
GRID=Image.open(TK+'bg_autumn_leaves.jpg').convert('RGB').resize((W,H),Image.LANCZOS)   # 最後のまとめ：石畳の落ち葉
GREENGRID=Image.open(TK+'bg_grid.jpg').convert('RGB').resize((W,H))   # まとめカードの地：いつもの緑の方眼
def cover(img,w,h):
    s_=max(w/img.width,h/img.height); im=img.resize((int(img.width*s_+0.5),int(img.height*s_+0.5)),Image.LANCZOS); x=(im.width-w)//2; y=(im.height-h)//2; return im.crop((x,y,x+w,y+h))
LEAVES=cover(Image.open(os.environ.get('THUMB_BG',TK+'bg_autumn_leaves2.jpg')).convert('RGB'),W,H)
LEAVES=Image.blend(LEAVES,Image.new('RGB',(W,H),(0,0,0)),0.22)   # 商品と見出しが浮くよう少し暗く   # サムネ（つかみ）：落ち葉、9:16

# ---------- 商品ページ ----------
#   (ナレーション, 作品名, 商品名, 価格, 写真, 背景の場面写真, キャラ(左下,右下), 字幕)
PAGES=[('p1','となりのトトロ／魔女の宅急便','ボタン付ストール','各5,280円',['1_2','2_1'],'totoro040',['totoro018','majo018'],'ボタンで留めれば\nポンチョみたいに羽織れる！'),
('p2','となりのトトロ／ハウルの動く城','ちいさな加湿器','各5,280円',['65_2','67_2'],'howl016',['totoro044','howl035'],'オカリナやフライパンから\nミストが出てくる！'),
('p3','となりのトトロ','カーディガン 夜空','13,200円',['64_1','64_3'],'totoro001',['totoro004','totoro018'],'背中には\nコマで夜空を飛ぶトトロ'),
('p4','魔女の宅急便','ウルスラのブランケット','16,500円',['20_2','20_7'],'majo002',['majo011','majo044'],'ウール100％の\nハーフ毛布'),
('p5','となりのトトロ','ひざ掛け「星夜の音」','3,300円',['4_1'],'totoro029',['totoro044','totoro018'],'星空の下で\nオカリナを吹くトトロたち'),
('p6','となりのトトロ','大トトロ ふわふわトート','5,280円',['55_1','55_8'],'totoro044',['totoro044','totoro004'],'荷物を入れると\nまんまるに！'),
('p7','となりのトトロ','おさんぽスリッパ','各3,080円',['37_1','38_1'],'totoro018',['totoro044','totoro004'],'低反発＆丸洗いOK'),
('p8','となりのトトロ／魔女の宅急便','毛布ソックス','各1,650円',['43_2','44_2'],'majo040',['totoro018','majo018'],'丈が長くて\n色々な履き方ができる')]
def page_layers(i,pg):
    k,work,name,price,photos,bg,chs,_=pg
    C=[sway_item(chara(n,250),[150,820][j],1560) for j,n in enumerate(chs)]   # キャラ（いちばん後ろ・ゆらゆら）
    P=layer()   # 見出し＋写真
    d=ImageDraw.Draw(P); d.ellipse((CX-430,385,CX-330,485),fill=ORANGE,outline=WHITE,width=6); text(P,f'{i+1:02d}',50,CX-380,435,WHITE)
    pill(P,CX+40,435,work,32,NAVY,pad=26,h=62)
    text(P,name,76,CX,545,GREEN,stw=14,maxw=860)
    if len(photos)==1: paste(P,card(photos[0],620),CX,930)
    else:
        paste(P,card(photos[0],420,4),CX-205,880); paste(P,card(photos[1],420,-4),CX+205,1000)
    R=layer(); pill(R,CX,1300,price+'（税込）',54,ORANGE,pad=40,h=96)
    CR=layer(); text(CR,'画像：どんぐり共和国　© Studio Ghibli',22,CX,1700,WHITE,w=800,stw=3,stc=(0,0,0))
    return C,P,R,CR
_sl={}
def sub_layer(t):
    if t not in _sl:
        L=layer(); ls=t.split('\n')
        for j,l in enumerate(ls): text(L,l,44,CX,1415+(j-(len(ls)-1)/2)*60,WHITE,stw=8,stc=(20,20,20))
        _sl[t]=L
    return _sl[t]

# ---------- サムネ（つかみの最初のフレーム） ----------
def thumb_layers():
    xs=[200,435,670,900]
    top=[('65_8',-7),('1_8',5),('55_1',-5),('67_8',7)]; bot=[('37_1',6),('4_7',-5),('64_8',5),('44_4',-7)]
    P=[sway_item(sticker(CUT+n+'.png',250,330,r),xs[k],520+(30 if k%2 else 0)) for k,(n,r) in enumerate(top)]
    P+=[sway_item(sticker(CUT+n+'.png',250,330,r),xs[k],1350-(30 if k%2 else 0)) for k,(n,r) in enumerate(bot)]
    CH=layer(); paste(CH,chara('totoro018',290,ow=0),105,395); paste(CH,chara('majo018',300,ow=0),930,1520)   # 左上・右下のキャラ（白フチなし）
    T=layer()
    x,tw=text(T,'どんぐり共和国で買える！',70,W/2,795,DARK,stw=12)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-66,x-32),(x+tw+66,x+tw+32)): d.line((sx,758,ex,832),fill=WHITE,width=21); d.line((sx,758,ex,832),fill=DARK,width=9)
    # 「秋冬」だけ紅葉色で少し大きく
    parts=[('ジブリの',92,GREEN),('秋冬',112,(214,78,24)),('グッズ紹介',92,GREEN)]
    x=W/2-sum(tlen(t,z) for t,z,_ in parts)/2
    for t,z,c in parts:
        text(T,t,z,x+tlen(t,z)/2,925,c,stw=18); x+=tlen(t,z)
    pill(T,W/2,1062,'vol.1',58,ORANGE,pad=60,h=100)
    return CH,P,T
TCH,TP,TT=thumb_layers(); TPL=swayed(TP,0,amp=0)   # サムネの商品は動かさない

# ---------- 最後：まとめ ----------
def end_layer():
    L=layer(); d=ImageDraw.Draw(L)
    X0,Y0,X1,Y1=int(CX-440),390,int(CX+440),1340
    sh=layer(); ImageDraw.Draw(sh).rounded_rectangle((X0+4,Y0+16,X1+4,Y1+16),44,fill=(0,0,0,140)); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    g=GREENGRID.crop((X0,Y0,X1,Y1)).convert('RGBA'); g.putalpha(rmask(X1-X0,Y1-Y0,44)); L.alpha_composite(g,(X0,Y0))
    d.rounded_rectangle((X0,Y0,X1,Y1),44,outline=WHITE,width=10)
    for j in range(8):   # 商品名・価格が方眼に埋もれないよう白い札を敷く
        x=CX-330+(j%4)*220; y=640+(j//4)*330; d.rounded_rectangle((x-104,y+100,x+104,y+170),16,fill=(255,255,255,235))
    text(L,'ジブリの秋冬グッズ',58,CX,470,GREEN,stw=12)
    for j,pg in enumerate(PAGES):
        x=CX-330+(j%4)*220; y=640+(j//4)*330
        im=Image.open(A+pg[4][0]+'.jpg').convert('RGB'); m=min(im.size); im=im.crop(((im.width-m)//2,(im.height-m)//2,(im.width+m)//2,(im.height+m)//2)).resize((190,190),Image.LANCZOS).convert('RGBA'); im.putalpha(rmask(190,190,20))
        paste(L,im,x,y); d.ellipse((x-100,y-110,x-50,y-60),fill=ORANGE); text(L,str(j+1),30,x-75,y-85,WHITE)
        text(L,pg[2].split('「')[0],22,x,y+120,INK,maxw=205); text(L,pg[3],24,x,y+152,ORANGE)
    text(L,'画像：どんぐり共和国　© Studio Ghibli',20,CX,1305,GRAY,w=800,stw=4)
    return L
QL=layer(); pill(QL,CX,1450,'あなたはどれが欲しい？',50,ORANGE,pad=40,h=92)
CTAL=layer(); pill(CTAL,CX,1570,'保存して冬じたくの参考に！',46,GREEN,pad=40,h=86)

# ---------- タイムライン ----------
def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
MIN=5.9; TAIL=0.6
tl=[]; t=0
d_=0.3+wdur('hook')+0.5; tl.append(('hook',t,d_,None)); t+=d_
for i,pg in enumerate(PAGES):
    d_=max(0.25+wdur(pg[0])+TAIL,MIN); tl.append(('page',t,d_,i)); t+=d_
TARGET=61.0   # 全体の尺（秒）。まとめの余白で合わせる
fd=0.1+wdur('fol')+0.4
d_=max(0.2+wdur('q')+0.25+wdur('cta')+0.6,TARGET-fd-t); tl.append(('end',t,d_,None)); t+=d_
d_=fd; tl.append(('fol',t,d_,None)); t+=d_
TOT=t; print('total',round(TOT,2))

POP=[0.6,0.9,1.08,1.03]
def popped(L,k,delay=0):
    k=k-delay
    if k<0: return None
    if k>=len(POP): return L
    s=POP[k]; bb=L.getbbox(); c=L.crop(bb); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
ENDL=end_layer()
_cb=chara('totoro044',210)   # ネコバスは横長なので、画面からはみ出ないよう左端から置く
ENDC=[sway_item(_cb,_cb.width/2+15,1610),sway_item(chara('majo018',260),830,1600)]   # 最後のキャラ（ゆらゆら）
def frames(kind,n,i):
    if kind=='fol':
        for _ in range(n): yield FOLLOW
        return
    if kind=='hook':
        # 最初のフレーム＝サムネ。商品はゆらゆら、見出しは0.35秒後に「ポンッ」と弾む
        for k in range(n):
            im=LEAVES.convert('RGBA'); im.alpha_composite(TCH); im.alpha_composite(swayed(TP,k/FPS))
            im.alpha_composite(TT if k<int(0.35*FPS) else popped(TT,k,int(0.35*FPS))); yield im.convert('RGB')
        return
    if kind=='end':
        for k in range(n):
            im=GRID.convert('RGBA'); im.alpha_composite(swayed(ENDC,k/FPS)); im.alpha_composite(popped(ENDL,k))
            g=k/FPS; tq=0.2; tc=tq+wdur('q')+0.25
            if g>=tq: im.alpha_composite(popped(QL,int((g-tq)*FPS)))
            if g>=tc: im.alpha_composite(popped(CTAL,int((g-tc)*FPS)))
            yield im.convert('RGB')
        return
    pg=PAGES[i]; B=scene_bg(pg[5]); C,P,R,CR=page_layers(i,pg); ST=sub_layer(pg[7]); nd=wdur(pg[0])
    for k in range(n):
        g=k/FPS; im=zoomed(B,k/max(n-1,1)).convert('RGBA')
        c=popped(swayed(C,g),k,3); im.alpha_composite(c) if c else None
        im.alpha_composite(popped(P,k))
        r=popped(R,k,int(0.5*FPS)); im.alpha_composite(r) if r else None
        if 0.25<=g<0.25+nd+0.3: im.alpha_composite(ST)
        im.alpha_composite(CR); yield im.convert('RGB')

if len(sys.argv)>5 and sys.argv[5]=='stills':
    for j,(kind,t0,d_,i) in enumerate(tl):
        if kind=='fol': continue
        n=int(d_*FPS); fr=list(frames(kind,n,i)); fr[min(n-1,int(2.5*FPS))].save(NR+f'../still{j:02d}.jpg',quality=85)
        if kind=='hook': fr[0].save(os.environ.get('THUMB_OUT',HERE+'thumbnail.png'))
    sys.exit()
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',NR+'../v.mp4'],stdin=subprocess.PIPE)
for kind,t0,d_,i in tl:
    n=int(round((t0+d_)*FPS))-int(round(t0*FPS))
    for f in frames(kind,n,i):
        if kind=='hook' and t0==0 and f is not None: pass
        enc.stdin.write(np.asarray(f).tobytes())
enc.stdin.close(); enc.wait()
N=int(TOT*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
for kind,t0,d_,i in tl:
    if kind=='hook': add(rd(NR+'hook.wav'),t0+0.3,1.0); add(rd(S+'labsfx/kira1.wav'),t0+0.3,0.45)
    elif kind=='page': add(rd(NR+PAGES[i][0]+'.wav'),t0+0.25,1.0); add(rd(S+'labsfx/sceneswitch1.wav'),t0,0.35); add(rd(S+'labsfx/pa1.wav'),t0+0.5,0.4)
    elif kind=='end': add(rd(NR+'q.wav'),t0+0.2,1.0); add(rd(NR+'cta.wav'),t0+0.2+wdur('q')+0.25,1.0); add(rd(S+'labsfx/shine2.wav'),t0,0.4)
    else: add(rd(NR+'fol.wav'),t0+0.1,1.0)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
