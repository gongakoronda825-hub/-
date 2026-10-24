# アリエッティをIMAXで観た人の感想（2026/10/25）ナレーション動画　約61秒
# 使い方: python3 make_narration.py <出力先>/ → python3 make_video.py <作業フォルダ(setup.shのW)> <出力先>/narr [stills]
import json,sys,os,math,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S=sys.argv[1].rstrip('/')+'/'; NR=sys.argv[2].rstrip('/')+'/'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUTV=HERE+'arrietty_imax.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
WHITE=(255,255,255); INK=(45,40,36); GREEN=(46,125,62); ORANGE=(236,128,60); RED=(206,72,80); NAVY=(30,58,110); GRAY=(110,100,92); CREAM=(240,233,222)
TOTAL=61.5   # 収益化の「1分以上」を超えるよう、最後のフォロー画像で尺を合わせる
CREDIT='© 2010 Mary Norton/Keiko Niwa/Studio Ghibli, NDHDMTW'

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
BOX={}   # 話している部分を目立たせる枠の位置（カード座標）
def addbox(key,bb):
    if key: o=BOX.get(key); BOX[key]=bb if not o else (min(o[0],bb[0]),min(o[1],bb[1]),max(o[2],bb[2]),max(o[3],bb[3]))
def text(L,t,sz,cx,cy,fill,w=900,stw=0,stc=WHITE,anchor='m',maxw=None,key=None):
    while maxw and tlen(t,sz,w)>maxw: sz-=2
    d=ImageDraw.Draw(L); x=cx-tlen(t,sz,w)/2 if anchor=='m' else cx
    addbox(key,(x-14,cy-sz*0.75,x+tlen(t,sz,w)+14,cy+sz*0.75))
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
def pill(L,cx,cy,t,sz,bg,fg=WHITE,pad=30,h=None,maxw=800,key=None):
    while tlen(t,sz)>maxw: sz-=2
    tw=tlen(t,sz); h=h or sz*1.55; addbox(key,(cx-tw/2-pad,cy-h/2,cx+tw/2+pad,cy+h/2))
    ImageDraw.Draw(L).rounded_rectangle((cx-tw/2-pad,cy-h/2,cx+tw/2+pad,cy+h/2),h/2,fill=bg)
    text(L,t,sz,cx,cy,fg)
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def photo(img,w,h,fx=0.5,fy=0.5,r=22):
    s=max(w/img.width,h/img.height); im=img.resize((int(img.width*s)+1,int(img.height*s)+1),Image.LANCZOS)
    x=int((im.width-w)*fx); y=int((im.height-h)*fy); c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,r)); return c
def gb(n):
    w=n.rstrip('0123456789'); return Image.open(S+f'gb/{w}{int(n[len(w):]):03d}.jpg').convert('RGB')
def framed(L,img,cx,cy,pad=10,rot=0):
    o=Image.new('RGBA',(img.width+2*pad,img.height+2*pad),(0,0,0,0))
    if pad: wb=Image.new('RGBA',o.size,WHITE+(255,)); wb.putalpha(rmask(*o.size,28)); o.alpha_composite(wb)
    o.alpha_composite(img,(pad,pad))
    if rot: o=o.rotate(rot,Image.BICUBIC,expand=True)
    sh=Image.new('RGBA',(o.width+60,o.height+60),(0,0,0,0)); m=Image.new('L',sh.size,0); m.paste(o.getchannel('A'),(30,38)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(12)).point(lambda v:int(v*0.35)))
    L.alpha_composite(sh,(int(cx-sh.width/2),int(cy-sh.height/2))); L.alpha_composite(o,(int(cx-o.width/2),int(cy-o.height/2)))

# ---------- 背景 ----------
def cover(img,w,h):
    s=max(w/img.width,h/img.height); im=img.resize((int(img.width*s)+1,int(img.height*s)+1),Image.LANCZOS)
    x=(im.width-w)//2; y=(im.height-h)//2; return im.crop((x,y,x+w,y+h))
NAVYBG=Image.open(TK+'bg_grid_navy.jpg').convert('RGB').resize((W,H))
def scene_bg(n,fx=0.5):
    im=gb(n); ch=im.height; cw=int(ch*W/H); x=int((im.width-cw)*fx)
    b=cover(im.crop((x,0,x+cw,ch)),int(W*1.12),int(H*1.12)).filter(ImageFilter.GaussianBlur(2))
    return Image.blend(b,Image.new('RGB',b.size,(0,0,0)),0.18)
def bg_frames(B,n):
    # 背景だけゆっくりズーム(8%)＋横パン。切り取りは小数座標
    for k in range(n):
        u=k/max(n-1,1); z=1.0+0.08*u
        sw,sh=min(W*1.12/z,B.width),min(H*1.12/z,B.height); x=(B.width-sw)*(0.25+0.5*u); y=(B.height-sh)/2
        yield B.resize((W,H),Image.BILINEAR,box=(x,y,x+sw,y+sh)).convert('RGBA')

# ---------- キャラ（場面写真の切り抜き＝cutout.py の cut/） ----------
def chara(name,h,ow=10):
    im=Image.open(S+f'cut/{name}.png').convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<50 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big); return out
def safe(L,s=0.9,x0=10,y0=410):
    # 右のいいね・コメントのボタンを避ける：前景を0.9倍にして左へ寄せる（上端 y0 は固定）
    o=layer(); o.alpha_composite(L.resize((int(W*s),int(H*s)),Image.LANCZOS),(x0,int(y0-y0*s))); return o

def K(n): return f'karigurashi{n}'
# ---------- カード ----------
CARD=(CX-440,410,CX+440,1470)
def card_base(label,title):
    L=layer(); d=ImageDraw.Draw(L)
    sh=layer(); ImageDraw.Draw(sh).rounded_rectangle((CARD[0]+4,CARD[1]+16,CARD[2]+4,CARD[3]+16),44,fill=(0,0,0,120)); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle(CARD,44,fill=(255,252,246,255),outline=WHITE,width=10)
    pill(L,CARD[0]+40+tlen(label,32)/2+26,CARD[1]+72,label,32,ORANGE,pad=26)
    text(L,title,64,CX,CARD[1]+170,GREEN,maxw=820)
    text(L,'観た人の感想をもとに再構成',22,CX,CARD[3]-58,GRAY,w=800); text(L,CREDIT,22,CX,CARD[3]-28,GRAY,w=800)
    return L
def voice(L,cy,t,sz=36):
    # 観た人の声：吹き出し＋「観た人の声」タグ
    ls=t.split('\n'); w=max(tlen(l,sz) for l in ls)+90; h=len(ls)*sz*1.45+56; d=ImageDraw.Draw(L)
    x0,y0=CX-w/2,cy-h/2
    d.rounded_rectangle((x0,y0,x0+w,y0+h),30,fill=CREAM+(255,)); d.polygon([(x0+70,y0+h-2),(x0+110,y0+h-2),(x0+62,y0+h+34)],fill=CREAM+(255,))
    pill(L,x0+110,y0,'観た人の声',24,NAVY,pad=18,h=42)
    for j,l in enumerate(ls): text(L,l,sz,CX,y0+42+sz*0.55+j*sz*1.45,INK)
def body(label,title,ph,rows,fx=0.5,fy=0.5,phh=430):
    L=card_base(label,title); y=CARD[1]+240
    if ph: framed(L,photo(gb(K(ph)),780,phh,fx,fy),CX,y+phh/2,pad=8); y+=phh+40
    for r in rows:
        k=r[0]
        if k=='t': text(L,r[1],r[2],CX,y+r[2]*0.6,r[3] if len(r)>3 else INK,maxw=820); y+=r[2]*1.5
        elif k=='p': pill(L,CX,y+40,r[1],r[3] if len(r)>3 else 40,r[2],pad=32,h=78); y+=100
        elif k=='v': n=r[1].count('\n')+1; hh=n*36*1.45+56; voice(L,y+hh/2+8,r[1]); y+=hh+50
    return L
def c1(): return body('観た人の声','迷ってた人ほど',21,[('t','「わざわざIMAXじゃなくても…」',38),('t','って思ってた人も',34,GRAY),('p','没入感がすごくて',ORANGE),('t','ちゃんと小人になってたらしい',38,GREEN)],fx=0.55)
def c2():
    L=card_base('そもそも','なんでアリエッティなのか'); y=CARD[1]+250
    for j,(n,lab,fx) in enumerate([(18,'小さい音',0.55),(7,'細かい画',0.5)]):
        x=CX+(-200 if j==0 else 200); framed(L,photo(gb(K(n)),370,420,fx),x,y+210,pad=8); pill(L,x,y+460,lab,40,GREEN,pad=30,h=76)
    text(L,'この2つが主役の映画',40,CX,y+575,INK)
    pill(L,CX,y+665,'IMAXで変わるのが、ちょうどその2つ',38,ORANGE,pad=30,h=76); return L
def c3(): return body('変わること 1','画面',36,[('t','大きくて、ゆるく湾曲したスクリーン',36),('p','小人から見た部屋の広さが伝わる',ORANGE,38),('v','部屋がとにかく広く感じた')],fx=0.45)
def c4(): return body('変わること 2','音',40,[('p','横と上にもスピーカー',ORANGE),('t','雨、風、虫の声がまわりから',36),('v','普段は気にしない音がずっと聞こえてた\nニーヤのゴロゴロまで')],fx=0.7,phh=340)
def c5(): return body('変わること 3','画質',32,[('p','ジブリ監修の4Kリマスター版',NAVY,38),('t','昔の映像を、今の高画質で作り直したもの',30,GRAY),('p','レーザー映写で明るく、色が深い',ORANGE,38),('v','水のつぶや花の色まで見えた')],fx=0.4,phh=300)
def c6(): return body('歌','セシル・コルベルの歌声',24,[('p','IMAXの音で聴ける',ORANGE,44),('t','これ目当てでもいいと思う',40,GREEN)],fx=0.6,phh=470)
def c7(): return body('観たあと','ちょっとしんどい',37,[('v','アリエッティの側で観てたはずが\n「自分は翔の側なんだよな」って'),('t','でも、小さい世界って',38),('t','きれいなんだなって思い出させてくれる',36,GREEN)],fx=0.4,phh=320)
def c8():
    L=card_base('上映期間','観に行くなら'); y=CARD[1]+250
    framed(L,photo(gb(K(47)),780,240,0.5,0.5),CX,y+120,pad=8); y+=280
    d=ImageDraw.Draw(L)
    for j,(lab,dt,col) in enumerate([('IMAX','〜11/2（月）',ORANGE),('全国の拡大上映','10/30（金）〜11/12（木）',NAVY)]):
        yy=y+j*120; d.rounded_rectangle((CX-390,yy,CX+390,yy+104),26,fill=CREAM+(255,))
        pill(L,CX-250,yy+52,lab,30,col,pad=20,h=58,maxw=230); text(L,dt,40,CX+110,yy+52,INK,maxw=470)
    pill(L,CX,y+290,'迷ってる人に送ってあげて',44,GREEN,pad=36,h=86)
    text(L,'※劇場によって設備が違います',26,CX,y+370,GRAY); text(L,'（レーザーでない劇場、2K上映の劇場あり）',26,CX,y+406,GRAY); return L

# ---------- つかみ（最初のフレーム＝サムネ。y=240〜1680に収める） ----------
def hook_layer():
    L=layer()
    for n,(x,y,r,fx) in zip([33,37,45,24],[(285,470,-3,0.5),(795,470,3,0.4),(285,1440,3,0.6),(795,1440,-3,0.6)]):
        framed(L,photo(gb(K(n)),460,300,fx),x,y,pad=10,rot=r)
    text(L,'アリエッティ',62,540,780,INK,stw=12); d=ImageDraw.Draw(L); hw=tlen('アリエッティ',62)/2
    for x0,x1 in ((540-hw-70,540-hw-30),(540+hw+70,540+hw+30)):
        d.line((x0,745,x1,815),fill=WHITE,width=20); d.line((x0,745,x1,815),fill=INK,width=8)
    text(L,'IMAXで観る',124,540,920,GREEN,stw=16)
    pill(L,540,1075,'意味ある？',84,ORANGE,pad=50,h=128)
    pill(L,540,1215,'何が変わるのか、観た人の声と一緒に',34,NAVY,pad=30,h=66)
    text(L,CREDIT,22,540,1650,WHITE,w=800,stw=3,stc=(0,0,0)); return L

# ---------- キャラ（紹介作品から4体まで：アリエッティ×2・翔・スピラー） ----------
CH={n:chara(K(n),240) for n in ['033','048','029','012']}
def chars_layer(a,b):
    L=layer()
    for n,x in ((a,CARD[0]+90),(b,CARD[2]-90)):
        c=CH[n]; L.alpha_composite(c,(int(x-c.width/2),int(CARD[1]-60-c.height/2)))
    return safe(L)

# ---------- 字幕（ナレーション。改行は手動） ----------
SUB={'c1':'迷ってた人も、没入感がすごくて\nちゃんと小人になってたらしい','c2':'小さい音と細かい画が主役\nIMAXで変わるのが、ちょうどその2つ',
'c3':'大きくて湾曲したスクリーンだから\n小人から見た部屋の広さがそのまま伝わる','c4':'雨、風、虫の声がまわりから聞こえる\nニーヤのゴロゴロまで、って声も',
'c5':'ジブリ監修の4Kリマスター版を\nレーザー映写機で映すから、明るくて色が深い','c6':'セシル・コルベルの歌も\nIMAXの音で',
'c7':'アリエッティの側で観てたはずが\n自分は翔の側だって気づく','c8':'IMAXは11月2日まで\n迷ってる人に送ってあげて'}
_sl={}
def sub_layer(t):
    if t in _sl: return _sl[t]
    L=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): text(L,l,42,CX,1600+(j-(len(ls)-1)/2)*60,WHITE,stw=8,stc=(20,20,20),maxw=860)
    _sl[t]=safe(L); return _sl[t]

# ---------- タイムライン ----------
def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
#   (キー, 背景の場面, 前景, キャラ, 効果音)
GRIDBG=Image.open(TK+'bg_grid.jpg').convert('RGB').resize((W,H))
SEG=[('hook','grid',hook_layer(),None,'kira1'),
('c1',scene_bg(K(22)),safe(c1()),('033','048'),'sceneswitch1'),('c2',scene_bg(K(6)),safe(c2()),('012','029'),'sceneswitch1'),
('c3',scene_bg(K(28)),safe(c3()),('033','048'),'sceneswitch1'),('c4',scene_bg(K(18)),safe(c4()),('012','029'),'sceneswitch1'),
('c5',scene_bg(K(3)),safe(c5()),('033','048'),'sceneswitch1'),('c6',scene_bg(K(1)),safe(c6()),('012','029'),'sceneswitch1'),
('c7',scene_bg(K(48)),safe(c7()),('033','048'),'sceneswitch1'),('c8',scene_bg(K(2)),safe(c8()),('012','029'),'shine2'),('fol',None,None,None,None)]
DUR={'hook':2.9}
tl=[]; t=0
for s in SEG:
    d_=max(DUR.get(s[0],0),0.15+wdur(s[0])+0.45); tl.append([t,d_]+list(s)); t+=d_
tl[-1][1]+=max(0,TOTAL-t); TOT=sum(x[1] for x in tl); print('total',round(TOT,2))
if len(sys.argv)>3 and sys.argv[3]=='stills':
    os.makedirs(S+'../stills',exist_ok=True)
    for i,(t0,d_,k,B,F,ch,sfx) in enumerate(tl):
        if F is None: continue
        b=(GRIDBG.convert('RGBA') if B=='grid' else next(bg_frames(B,1)))
        if ch: b.alpha_composite(chars_layer(*ch))
        b.alpha_composite(F)
        if k in SUB: b.alpha_composite(sub_layer(SUB[k]))
        b.convert('RGB').save(S+f'../stills/{i:02d}_{k}.jpg',quality=85)
    sys.exit()
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
POP=[0.6,0.9,1.08,1.03]
def popped(F,k):
    if k>=len(POP): return F
    s=POP[k]; bb=F.getbbox(); c=F.crop(bb); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',NR+'../v.mp4'],stdin=subprocess.PIPE)
for t0,d_,k,B,F,ch,sfx in tl:
    n=int(round((t0+d_)*FPS))-int(round(t0*FPS))
    if F is None:
        for _ in range(n): enc.stdin.write(np.asarray(FOLLOW).tobytes())
        continue
    BG=(GRIDBG.convert('RGBA') for _ in range(n)) if B=='grid' else bg_frames(B,n)
    CL=chars_layer(*ch) if ch else None
    for j in range(n):
        im=next(BG)
        if CL: im.alpha_composite(popped(CL,j))
        im.alpha_composite(popped(F,j))
        if k in SUB and 0.1<=j/FPS<0.15+wdur(k)+0.3: im.alpha_composite(sub_layer(SUB[k]))
        enc.stdin.write(np.asarray(im.convert('RGB')).tobytes())
enc.stdin.close(); enc.wait()
# ---------- 音 ----------
N=int(TOT*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
for t0,d_,k,B,F,ch,sfx in tl:
    add(rd(NR+k+'.wav'),t0+0.15,1.0)
    if sfx: add(rd(S+f'labsfx/{sfx}.wav'),t0,0.4)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
