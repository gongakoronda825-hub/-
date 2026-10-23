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
def text(L,t,sz,cx,cy,fill,w=900,stw=0,stc=WHITE):
    d=ImageDraw.Draw(L); x=cx-tlen(t,sz,w)/2
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
def pill(L,cx,cy,t,sz,bg,fg=WHITE,pad=30,h=None):
    tw=tlen(t,sz); h=h or sz*1.55
    ImageDraw.Draw(L).rounded_rectangle((cx-tw/2-pad,cy-h/2,cx+tw/2+pad,cy+h/2),h/2,fill=bg,outline=WHITE,width=5)
    text(L,t,sz,cx,cy,fg)
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))

# ---------- 素材 ----------
def big(img): return img.convert('RGB').resize((int(W*1.08),int(H*1.08)),Image.LANCZOS)
def zoomed(B,u):
    # ゆっくりズーム（約8%）＋少し横パン。切り取りは小数座標
    z=1.0+0.08*u; sw,sh=min(W*1.08/z,B.width),min(H*1.08/z,B.height); x=(B.width-sw)*(0.3+0.4*u); y=(B.height-sh)/2
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
SCENES=[('drawers','武居三省堂（文具店）'),('izakaya','鍵屋（居酒屋）'),('sento','子宝湯（銭湯）'),('engawa','縁側'),('bus','ボンネットバス'),('garden','縁側から見た庭'),('doma','農家の土間'),('gate','木の門')]
SUB={'hook':'東京に、ジブリの世界\nそのままの場所があるって\n知ってた？','drawers':'壁一面の引き出しは\n釜爺のボイラー室にそっくり！','izakaya':'千尋のお父さんとお母さんが\n夢中で食べてそう','sento':'まるで油屋の大浴場！',
'engawa':'サツキとメイが走り回った\nあの家みたい','bus':'となりでトトロが\n雨宿りしてそう','garden':'カオナシもひと休み','doma':'もののけ姫の世界','gate':'門の奥には\nこだまやトトロが…？',
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
REVEAL=1.4; MIN=5.5
tl=[]; t=0
d_=0.15+wdur('hook')+0.6; tl.append(('hook',t,d_)); t+=d_
for n,_ in SCENES:
    d_=max(0.2+wdur(n)+0.6,MIN); tl.append((n,t,d_)); t+=d_
d_=0.15+wdur('q')+0.25+wdur('cta')+0.6; tl.append(('end',t,d_)); t+=d_
d_=0.1+wdur('fol')+0.5; tl.append(('fol',t,d_)); t+=d_
TOT=t; print('total',round(TOT,2))

HOOK=big(Image.open(UP+'eaca8b03-image.jpg'))
ENDBG=big(Image.open(UP+'eaca8b03-image.jpg').crop((0,900,1206,2144))).filter(ImageFilter.GaussianBlur(6))
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
POP=[0.6,0.9,1.08,1.03]
def frames(kind,n):
    if kind=='fol':
        for _ in range(n): yield FOLLOW
        return
    if kind in ('hook','end'):
        B=HOOK if kind=='hook' else ENDBG
        q0=0.15; qd=wdur('q')+0.25
        for k in range(n):
            g=k/FPS; im=zoomed(B,k/max(n-1,1)).convert('RGBA')
            if kind=='end':
                im=Image.blend(im,Image.new('RGBA',im.size,(0,0,0,255)),0.25)
                key='q' if g<q0+qd else 'cta'; T=sub_layer(SUB[key]); kk=int((g-(q0 if key=='q' else q0+qd))*FPS)
                if kk<len(POP):
                    s=POP[kk]; bb=T.getbbox(); c=T.crop(bb).resize((int((bb[2]-bb[0])*s),int((bb[3]-bb[1])*s)),Image.BICUBIC); T=layer(); T.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2)))
                im.alpha_composite(T)
            yield im.convert('RGB')
        return
    Bb=big(Image.open(AL+kind+'_before.jpg')); Ba=big(Image.open(AL+kind+'_after.jpg')); P=pieces(kind)
    LB=label_layer(dict(SCENES)[kind]); ST=sub_layer(SUB[kind])
    for k in range(n):
        g=k/FPS; u=k/max(n-1,1); kk=int((g-REVEAL)*FPS)
        if g<REVEAL:
            im=zoomed(Bb,u).convert('RGBA')
        elif kk<len(POP):
            # 元写真の上に、キャラを塊ごとにポンッと出す
            base=zoomed(Bb,u).convert('RGBA'); s=POP[kk]; L=layer()
            for p,cx,cy in P:
                c=p.resize((max(1,int(p.width*s)),max(1,int(p.height*s))),Image.BICUBIC); L.alpha_composite(c,(int(cx-c.width/2),int(cy-c.height/2)))
            # レイヤーにも同じズームをかける
            z=1.0+0.08*u; sw,sh=W*1.08/z,H*1.08/z; x=(W*1.08-sw)*(0.3+0.4*u); y=(H*1.08-sh)/2
            L=L.resize((int(W*1.08),int(H*1.08)),Image.BILINEAR).resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh))
            base.alpha_composite(L); im=base
            if kk==0: im=Image.blend(im,Image.new('RGBA',im.size,(255,255,255,255)),0.35)
        else:
            im=zoomed(Ba,u).convert('RGBA')
        im.alpha_composite(LB); im.alpha_composite(CR)
        if 0.2<=g<0.2+wdur(kind)+0.4: im.alpha_composite(ST)
        yield im.convert('RGB')

if len(sys.argv)>4 and sys.argv[4]=='stills':
    for i,(kind,t0,d_) in enumerate(tl):
        if kind=='fol': continue
        n=int(d_*FPS); fr=list(frames(kind,n)); fr[min(n-1,int(4.5*FPS))].save(S+f'../tv/still{i:02d}.jpg',quality=85)
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
    elif kind=='end': add(rd(NR+'q.wav'),t0+0.15,1.0); add(rd(NR+'cta.wav'),t0+0.15+wdur('q')+0.25,1.0); add(rd(S+'labsfx/shine2.wav'),t0,0.4)
    elif kind=='fol': add(rd(NR+'fol.wav'),t0+0.1,1.0)
    else: add(rd(NR+kind+'.wav'),t0+0.2,1.0); add(rd(S+'labsfx/sceneswitch1.wav'),t0,0.35); add(rd(S+'labsfx/pa1.wav'),t0+REVEAL,0.5)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
