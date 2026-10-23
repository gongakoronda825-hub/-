# 江戸東京たてもの園×ジブリ ナレーション動画（元写真 → キャラがポンッと出てくる）
# 使い方: python3 make_video.py <作業フォルダ(setup.shのW)> <align.pyの出力フォルダ> <ナレーションwavのフォルダ> [stills]
import sys,os,math,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S=sys.argv[1].rstrip('/')+'/'; AL=sys.argv[2].rstrip('/')+'/'; NR=sys.argv[3].rstrip('/')+'/'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
UP='/root/.claude/uploads/e8d6fde2-cc10-5a5b-97f9-6bcb99a3b93e/'
OUTV=HERE+'tatemono.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
WHITE=(255,255,255); NAVY=(30,58,110); GREEN=(46,125,62); ORANGE=(236,128,60)

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
def text(L,t,sz,cx,cy,fill,w=900,stw=0,stc=WHITE,anchor='m'):
    d=ImageDraw.Draw(L); x={'m':cx-tlen(t,sz,w)/2,'l':cx,'r':cx-tlen(t,sz,w)}[anchor]
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
def pill(L,cx,cy,t,sz,bg,fg=WHITE,pad=30,h=None):
    tw=tlen(t,sz); h=h or sz*1.55
    ImageDraw.Draw(L).rounded_rectangle((cx-tw/2-pad,cy-h/2,cx+tw/2+pad,cy+h/2),h/2,fill=bg,outline=WHITE,width=5)
    text(L,t,sz,cx,cy,fg)
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))

# ---------- 素材 ----------
def big(img): return img.convert('RGB').resize((int(W*1.08),int(H*1.08)),Image.LANCZOS)
def zoomed(B,u,pan=(0.3,0.4)):
    # ゆっくりズーム（約8%）＋少し横パン。切り取りは小数座標
    z=1.0+0.08*u; sw,sh=min(W*1.08/z,B.width),min(H*1.08/z,B.height); x=(B.width-sw)*(pan[0]+pan[1]*u); y=(B.height-sh)/2
    return B.resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh))
def pieces(name):
    # キャラ部分（差分マスク）を塊ごとに分けて、ポンッと出せるようにする
    C=Image.open(AL+name+'_chars.png').convert('RGBA'); A=np.array(C.getchannel('A'))
    import cv2
    n,lab,st,_=cv2.connectedComponentsWithStats((A>20).astype(np.uint8))
    out=[]
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if a<1500: continue
        m=np.where(lab[y:y+h,x:x+w]==i,A[y:y+h,x:x+w],0).astype(np.uint8)
        p=C.crop((x,y,x+w,y+h)); p.putalpha(Image.fromarray(m)); out.append((p,x+w/2,y+h/2))
    return out
def prep_kokuriko():
    # 大和屋本店：元写真と合成画像（make_kokuriko.py）は同じ座標なので、そのまま差分でキャラを抜く。9:16は上下をぼかしで埋める
    def canvas(img):
        img=img.convert('RGB'); fg=img.resize((W,int(img.height*W/img.width)),Image.LANCZOS)
        bg=img.resize((int(img.width*H/img.height),H),Image.LANCZOS); x=(bg.width-W)//2; bg=bg.crop((x,0,x+W,H)).filter(ImageFilter.GaussianBlur(18))
        bg=Image.blend(bg,Image.new('RGB',bg.size,(0,0,0)),0.25); bg.paste(fg,(0,(H-fg.height)//2)); return bg
    b=canvas(Image.open(UP+'084e440f-image.jpg').resize((1206,1612),Image.LANCZOS)); a=canvas(Image.open(HERE+'kokuriko_yamatoya.png'))
    b.save(AL+'kokuriko_before.jpg',quality=95); a.save(AL+'kokuriko_after.jpg',quality=95)
    dd=np.abs(np.asarray(a,np.int16)-np.asarray(b,np.int16)).max(2); m=Image.fromarray(((dd>18)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    c=a.convert('RGBA'); c.putalpha(m); c.save(AL+'kokuriko_chars.png')
prep_kokuriko()
def prep_sento():
    # 銭湯は合成画像の人にモザイクがあるので、元写真もキャラ以外は合成画像の画素を使う（最初からモザイクあり）
    b=Image.open(AL+'sento_before.jpg').convert('RGB'); a=Image.open(AL+'sento_after.jpg').convert('RGB')
    m=Image.open(AL+'sento_chars.png').getchannel('A').point(lambda v:255 if v>100 else 0)
    o=Image.composite(b,a,m)
    for bx in [(176,1050,266,1160)]:   # 合成ではキャラに隠れていた人の顔
        r=o.crop(bx); r=r.resize((max(1,r.width//16),max(1,r.height//16)),Image.BILINEAR).resize(r.size,Image.NEAREST); o.paste(r,bx[:2])
    o.save(AL+'sento_before_mosaic.jpg',quality=95)
prep_sento()
SCENES=[('drawers','武居三省堂（文具店）'),('izakaya','鍵屋（居酒屋）'),('kokuriko','大和屋本店（乾物屋）'),('sento','子宝湯（銭湯）'),('engawa','縁側'),('bus','ボンネットバス'),('garden','縁側から見た庭'),('doma','農家の土間'),('gate','木の門')]
SUB={'hook':'東京に、ジブリの世界\nそのままの場所があるって\n知ってた？','drawers':'壁一面の引き出しは\n釜爺のボイラー室にそっくり！','izakaya':'千尋のお父さんとお母さんが\n夢中で食べてそう','sento':'まるで油屋の大浴場！',
'engawa':'サツキとメイが走り回った\nあの家みたい','bus':'となりでトトロが\n雨宿りしてそう','garden':'カオナシもひと休み','doma':'もののけ姫の世界\nジコ坊の雑炊が食べたくなる','kokuriko':'俊と海がコロッケを買った\nあの商店街みたい！','garden':'カオナシもひと休み\n夏休みのおばあちゃんちみたい','gate':'門の奥には\nこだまやトトロが…？',
'q':'あなたはどの場所に\n行きたい？','cta':'入場料は一般400円\n保存して行くときの参考に！'}
def sub_layer(t):
    L=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): text(L,l,48,CX,H/2+(j-(len(ls)-1)/2)*66,WHITE,stw=8,stc=(20,20,20))
    return L
CR=layer(); d=ImageDraw.Draw(CR); text(CR,'© Studio Ghibli　写真：撮影者本人',22,CX,1640,WHITE,w=800,stw=3,stc=(0,0,0))
def label_layer(t): L=layer(); pill(L,CX,1560,t,36,NAVY,pad=30,h=66); return L

def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
REVEAL=1.4; MIN=3.9; TAIL=0.3   # 1場面の最短秒数・読み終わりの間（ちょうど1分に合わせて詰めた）
tl=[]; t=0
d_=0.15+wdur('hook')+0.35; tl.append(('hook',t,d_)); t+=d_
for n,_ in SCENES:
    d_=max(0.2+wdur(n)+TAIL,MIN); tl.append((n,t,d_)); t+=d_
d_=0.15+wdur('cta')+0.25+wdur('q')+0.6; tl.append(('end',t,d_)); t+=d_
d_=0.1+wdur('fol')+0.35; tl.append(('fol',t,d_)); t+=d_
TOT=t; print('total',round(TOT,2))

MONT=[big(Image.open(AL+k+'_after.jpg')) for k in ('bus','engawa','izakaya','sento')]
def thumb_layer():
    # サムネ＝最初のフレーム。見出しの型（＼○○／小さめ黒＋大きい緑＋オレンジ帯）、中央そろえ・y=240〜1680の内側
    L=layer(); INK=(40,36,32)
    text(L,'\\ 東京にあった /',70,W/2,770,INK,stw=12)
    text(L,'ジブリの世界',150,W/2,905,GREEN,stw=20)
    text(L,'まるで',46,W/2-tlen('ジブリの世界',150)/2+6,818,ORANGE,stw=9,anchor='l')
    pill(L,W/2,1065,'江戸東京たてもの園',72,ORANGE,pad=44,h=120); return L
THUMB=thumb_layer()
def sticker(name,h,ow=10):
    im=Image.open(S+f'cut/{name}.png').convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<50 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS); pad=ow*3
    big_=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big_.alpha_composite(im,(pad,pad))
    A=big_.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big_.size,(0,0,0,0)); w_=Image.new('RGBA',big_.size,(255,255,255,0)); w_.putalpha(o); out.alpha_composite(w_); out.alpha_composite(big_); return out
def sky_card(w,h,r=44):
    # 料金表の地：青空＋雲＋下に草の生えた地面
    import random; rnd=random.Random(7)
    sky=np.zeros((h,w,3),np.float32); t=np.linspace(0,1,h)[:,None]
    sky[:]=(np.array([96,178,236])*(1-t)+np.array([200,234,250])*t)[:,None,:].reshape(h,1,3)
    C=Image.fromarray(sky.astype(np.uint8)).convert('RGBA')
    cl=Image.new('RGBA',(w,h),(0,0,0,0)); dc=ImageDraw.Draw(cl)
    for cx,cy,sc in [(140,120,1.0),(720,90,1.2),(470,230,0.8),(820,420,0.9),(90,520,0.8),(600,640,1.0),(250,820,0.9)]:
        for dx,dy,rx,ry in [(-60,10,55,38),(-15,-15,60,48),(40,0,58,42),(85,15,45,32),(10,20,90,30)]:
            dc.ellipse((cx+dx*sc-rx*sc,cy+dy*sc-ry*sc,cx+dx*sc+rx*sc,cy+dy*sc+ry*sc),fill=(255,255,255,235))
    C.alpha_composite(cl.filter(ImageFilter.GaussianBlur(2)))
    gr=Image.new('RGBA',(w,h),(0,0,0,0)); dg=ImageDraw.Draw(gr); top=h-190
    pts=[(x,top+18*math.sin(x/90)+10*math.sin(x/37)) for x in range(0,w+1,6)]
    dg.polygon(pts+[(w,h),(0,h)],fill=(110,184,72,255))
    dg.polygon([(x,y+45) for x,y in pts]+[(w,h),(0,h)],fill=(86,160,58,255))
    for _ in range(420):
        x=rnd.uniform(0,w); y0=top+18*math.sin(x/90)+10*math.sin(x/37)+rnd.uniform(-2,90); hgt=rnd.uniform(14,34); lean=rnd.uniform(-8,8)
        col=rnd.choice([(70,140,50,255),(130,200,85,255),(96,170,64,255)])
        dg.line((x,y0,x+lean,y0-hgt),fill=col,width=3)
    C.alpha_composite(gr)
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); C.putalpha(m); return C
def fee_layer():
    # 最後：観覧料を表にしたカード
    L=layer(); d=ImageDraw.Draw(L); X0,X1,Y0,Y1=CX-450,CX+450,330,1400; INK=(45,40,36); GRAY=(120,110,100); RED=(206,72,80)
    sh=layer(); ImageDraw.Draw(sh).rounded_rectangle((X0+4,Y0+16,X1+4,Y1+16),44,fill=(0,0,0,130)); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    L.alpha_composite(sky_card(int(X1-X0),int(Y1-Y0)),(int(X0),int(Y0))); d=ImageDraw.Draw(L); d.rounded_rectangle((X0,Y0,X1,Y1),44,outline=WHITE,width=10)
    pill(L,CX,Y0,'江戸東京たてもの園',46,ORANGE,pad=40,h=84)
    text(L,'個人観覧料',72,CX,Y0+130,GREEN,stw=12); text(L,'（通常）',30,CX,Y0+196,INK,stw=6)
    text(L,'料金',28,CX+170,Y0+262,INK,anchor='r',stw=6); text(L,'団体',28,X1-50,Y0+262,INK,anchor='r',stw=6)
    rows=[('一般（大人）','400円','320円'),('大学生・専修・各種学校','320円','250円'),('高校生','200円','160円'),('65歳以上','200円','160円'),('中学生以下','無料',None)]
    for j,(a,b,c) in enumerate(rows):
        y=Y0+300+j*140; R_=layer(); ImageDraw.Draw(R_).rounded_rectangle((X0+36,y,X1-36,y+120),28,fill=(255,252,246,210)); L.alpha_composite(R_)
        text(L,a,38 if len(a)<8 else 32,X0+66,y+60,INK,anchor='l')
        if c: text(L,b,52,CX+170,y+60,ORANGE,anchor='r'); text(L,c,32,X1-66,y+60,GRAY,anchor='r')
        else: pill(L,CX+150,y+60,'無料！',46,RED,pad=40,h=82)
    text(L,'出典：江戸東京たてもの園 公式サイト',22,CX,Y1-34,WHITE,w=800,stw=4,stc=(40,80,30))
    # カードのすみにキャラ（カードの後ろ）
    B=layer()
    for n,h,x,y in [('totoro044',230,X1-60,Y0-70),('totoro018',260,X0+40,Y1+90),('chihiro019',280,X1-40,Y1+100)]:
        c=sticker(n,h); B.alpha_composite(c,(int(x-c.width/2),int(y-c.height/2)))
    B.alpha_composite(L); return B
FEE=fee_layer()
QL=layer(); pill(QL,CX,1530,'あなたはどの場所に行きたい？',48,GREEN,pad=40,h=92)
ENDBG=big(Image.open(UP+'eaca8b03-image.jpg').crop((0,900,1206,2144))).filter(ImageFilter.GaussianBlur(6))
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
POP=[0.6,0.9,1.08,1.03]
def frames(kind,n):
    if kind=='fol':
        for _ in range(n): yield FOLLOW
        return
    if kind in ('hook','end'):
        if kind=='hook':
            for k in range(n):
                g=k/FPS; HI=n/FPS/len(MONT); i=min(int(g/HI),len(MONT)-1); B=MONT[i]; im=zoomed(B,min(1,(g-i*HI)/HI)*0.5).convert('RGBA')
                if i>0 and g-i*HI<2/FPS: im=Image.blend(im,Image.new('RGBA',im.size,(255,255,255,255)),0.5)
                im.alpha_composite(THUMB); yield im.convert('RGB')
            return
        B=ENDBG
        q0=0.15+wdur('cta')+0.25
        def popl(T,kk):
            if kk>=len(POP): return T
            s=POP[kk]; bb=T.getbbox(); c=T.crop(bb).resize((int((bb[2]-bb[0])*s),int((bb[3]-bb[1])*s)),Image.BICUBIC); o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
        for k in range(n):
            g=k/FPS; im=zoomed(B,k/max(n-1,1)).convert('RGBA')
            im=Image.blend(im,Image.new('RGBA',im.size,(0,0,0,255)),0.3)
            im.alpha_composite(popl(FEE,k))
            if g>=q0: im.alpha_composite(popl(QL,int((g-q0)*FPS)))
            yield im.convert('RGB')
        return
    Bb=big(Image.open(AL+kind+('_before_mosaic.jpg' if kind=='sento' else '_before.jpg'))); Ba=big(Image.open(AL+kind+'_after.jpg')); P=pieces(kind)
    LB=label_layer(dict(SCENES)[kind]); ST=sub_layer(SUB[kind]); PAN=(0.15,0.0) if kind=='kokuriko' else (0.3,0.4)
    for k in range(n):
        g=k/FPS; u=k/max(n-1,1); kk=int((g-REVEAL)*FPS)
        if g<REVEAL:
            im=zoomed(Bb,u,PAN).convert('RGBA')
        elif kk<len(POP):
            # 元写真の上に、キャラを塊ごとにポンッと出す
            base=zoomed(Bb,u,PAN).convert('RGBA'); s=POP[kk]; L=layer()
            for p,cx,cy in P:
                c=p.resize((max(1,int(p.width*s)),max(1,int(p.height*s))),Image.BICUBIC); L.alpha_composite(c,(int(cx-c.width/2),int(cy-c.height/2)))
            # レイヤーにも同じズームをかける
            z=1.0+0.08*u; sw,sh=W*1.08/z,H*1.08/z; x=(W*1.08-sw)*(PAN[0]+PAN[1]*u); y=(H*1.08-sh)/2
            L=L.resize((int(W*1.08),int(H*1.08)),Image.BILINEAR).resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh))
            base.alpha_composite(L); im=base
            if kk==0: im=Image.blend(im,Image.new('RGBA',im.size,(255,255,255,255)),0.35)
        else:
            im=zoomed(Ba,u,PAN).convert('RGBA')
        im.alpha_composite(LB); im.alpha_composite(CR)
        if 0.2<=g<0.2+wdur(kind)+0.4: im.alpha_composite(ST)
        yield im.convert('RGB')

if len(sys.argv)>4 and sys.argv[4]=='stills':
    for i,(kind,t0,d_) in enumerate(tl):
        if kind=='fol': continue
        n=int(d_*FPS); fr=list(frames(kind,n)); fr[min(n-1,int(4.5*FPS))].save(S+f'../tv/still{i:02d}.jpg',quality=85)
        if kind=='hook': fr[0].save(HERE+'thumbnail.png')
        if kind=='drawers': fr[int(0.6*FPS)].save(S+'../tv/still_before.jpg',quality=85); fr[int((REVEAL+0.07)*FPS)].save(S+'../tv/still_pop.jpg',quality=85)
    sys.exit()
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',NR+'../v.mp4'],stdin=subprocess.PIPE)
for kind,t0,d_ in tl:
    n=int(round((t0+d_)*FPS))-int(round(t0*FPS))
    for f in frames(kind,n): enc.stdin.write(np.asarray(f).tobytes())
enc.stdin.close(); enc.wait()
N=int(TOT*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
for kind,t0,d_ in tl:
    if kind=='hook': add(rd(NR+'hook.wav'),t0+0.15,1.0); add(rd(S+'labsfx/kira1.wav'),t0,0.45)
    elif kind=='end': add(rd(NR+'cta.wav'),t0+0.15,1.0); add(rd(NR+'q.wav'),t0+0.15+wdur('cta')+0.25,1.0); add(rd(S+'labsfx/shine2.wav'),t0,0.4); add(rd(S+'labsfx/pa1.wav'),t0+0.15+wdur('cta')+0.25,0.4)
    elif kind=='fol': add(rd(NR+'fol.wav'),t0+0.1,1.0)
    else: add(rd(NR+kind+'.wav'),t0+0.2,1.0); add(rd(S+'labsfx/sceneswitch1.wav'),t0,0.35); add(rd(S+'labsfx/pa1.wav'),t0+REVEAL,0.5)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
