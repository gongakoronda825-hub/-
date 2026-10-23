# 今決まっているジブリイベントまとめ（2026/10/23時点）ナレーション動画
# 使い方: python3 make_video.py <作業フォルダ(setup.shのW)> <ナレーションwavのフォルダ>
import sys,os,math,wave,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S=sys.argv[1].rstrip('/')+'/'; NR=sys.argv[2].rstrip('/')+'/'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
UP='/root/.claude/uploads/e8d6fde2-cc10-5a5b-97f9-6bcb99a3b93e/'; POSTER=UP+'43b67aa6-image.jpg'
MIMI_POSTER=None  # 『耳をすませば』IMAXポスター（まだ受け取っていない）
OUTV=HERE+'ghibli_events_1023.mp4'
W,H=1080,1920; FPS=30; SR=44100; DX=40; CX=W/2-DX
WHITE=(255,255,255); INK=(45,40,36); GREEN=(46,125,62); ORANGE=(236,128,60); RED=(206,72,80); NAVY=(30,58,110); GRAY=(110,100,92)

# ---------- 文字（日本語=jp、英数字=lat を混ぜて描く） ----------
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
def text(L,t,sz,cx,cy,fill,w=900,stw=0,stc=WHITE,anchor='m',maxw=None):
    while maxw and tlen(t,sz,w)>maxw: sz-=2
    d=ImageDraw.Draw(L); x=cx-tlen(t,sz,w)/2 if anchor=='m' else cx
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
def pill(L,cx,cy,t,sz,bg,fg=WHITE,pad=30,h=None,maxw=800):
    while tlen(t,sz)>maxw: sz-=2
    tw=tlen(t,sz); h=h or sz*1.55
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

# ---------- イベントカード ----------
CARD=(CX-440,260,CX+440,1320)
def card_base(num,area,title):
    L=layer(); d=ImageDraw.Draw(L)
    sh=layer(); ImageDraw.Draw(sh).rounded_rectangle((CARD[0]+4,CARD[1]+16,CARD[2]+4,CARD[3]+16),44,fill=(0,0,0,120)); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle(CARD,44,fill=(255,252,246,255),outline=WHITE,width=10)
    d.ellipse((CARD[0]+30,CARD[1]+28,CARD[0]+130,CARD[1]+128),fill=ORANGE,outline=WHITE,width=5); text(L,str(num),62,CARD[0]+80,CARD[1]+80,WHITE)
    pill(L,CARD[0]+150+tlen(area,34)/2+28,CARD[1]+78,area,34,NAVY,pad=28)
    ls=title.split('\n')
    for j,l in enumerate(ls): text(L,l,62 if len(ls)==1 else 56,CX,CARD[1]+190+j*74,GREEN,stw=0,maxw=820)
    return L,CARD[1]+190+(len(ls)-1)*74
def info(L,y0,date,lines,src,cr=True):
    pill(L,CX,y0,date,44,ORANGE,pad=34,h=78)
    for j,(t,sz,col) in enumerate(lines): text(L,t,sz,CX,y0+86+j*58,col,maxw=820)
    text(L,src,22,CX,CARD[3]-58,GRAY,w=800,maxw=820)
    if cr: text(L,'© Studio Ghibli',22,CX,CARD[3]-28,GRAY,w=800)

def poster_side(L,y,f,rows,pw=330):
    # 左に公式ポスター、右に情報の行（見出し＝オレンジ、中身＝黒。中身は\nで2行）
    P=Image.open(UP+f).convert('RGB'); po=photo(P,pw,int(pw*P.height/P.width),r=16); framed(L,po,CX-215,y+60+po.height/2)
    d=ImageDraw.Draw(L); X=CX-20; yy=y+60
    for lab,val in rows:
        ls=val.split('\n'); h=40+46*len(ls); d.rounded_rectangle((X,yy,X+460,yy+h),20,fill=(240,233,222,255))
        text(L,lab,28,X+18,yy+26,ORANGE,anchor='l')
        for k,l in enumerate(ls): text(L,l,32,X+18,yy+66+k*46,INK,anchor='l',maxw=424)
        yy+=h+16
    return y+60+po.height
def ev1():
    L,y=card_base(1,'神奈川','ジブリパーク展\n横須賀展')
    b=poster_side(L,y,'18d69da3-image.jpg',[('会場','横須賀美術館'),('休館日','3/1（月）・4/5（月）')])
    pill(L,CX,b+80,'2027.2.11（木・祝）〜5.14（金）',44,ORANGE,pad=34,h=78)
    text(L,'出典：横須賀美術館・スタジオジブリ公式',22,CX,CARD[3]-58,GRAY,w=800); text(L,'画像：公式ポスター　© Studio Ghibli',22,CX,CARD[3]-28,GRAY,w=800); return L
def ev2():
    L,y=card_base(2,'全国ツアー','舞台『千と千尋の神隠し』'); P=Image.open(POSTER).convert('RGB')
    po=photo(P,330,int(330*P.height/P.width),r=16); framed(L,po,CX-215,y+290)
    d=ImageDraw.Draw(L); X=CX-20; rows=[('2027.3〜5','東京・明治座'),('6','愛知・御園座'),('6〜7','大阪・梅田芸術劇場'),('7〜8','福岡・博多座'),('8','北海道・hitaru')]
    for j,(m,p) in enumerate(rows):
        yy=y+80+j*92; d.rounded_rectangle((X,yy,X+460,yy+76),20,fill=(240,233,222,255))
        text(L,m+'月',28,X+18,yy+24,ORANGE,anchor='l'); text(L,p,30,X+18,yy+56,INK,anchor='l',maxw=420)
    pill(L,CX,y+590,'千尋役は7人！',44,RED,pad=34,h=78)
    text(L,'橋本環奈・上白石萌音・福地桃子・森莉那',28,CX,y+676,INK)
    text(L,'井上和・豊嶋花・平澤宏々路',28,CX,y+720,INK)
    text(L,'※公演日の詳細は今後発表',24,CX,y+766,GRAY)
    text(L,'出典：東宝『千と千尋』公式・ぴあ　画像：東宝',22,CX,CARD[3]-36,GRAY,w=800); return L
def ev3():
    L,y=card_base(3,'全国の映画館','『耳をすませば』\n『借りぐらしのアリエッティ』')
    for k,(src,rot) in enumerate([(MIMI_POSTER,3),('ac81aad3-image.webp',-3)]):
        if src: P=Image.open(UP+src).convert('RGB'); po=photo(P,290,int(290*P.height/P.width),r=14)
        else: po=photo(gb('mimi47'),290,410,0.5,0.4,r=14)
        framed(L,po,CX+(-170 if k==0 else 170),y+250,pad=0,rot=rot)
    pill(L,CX,y+520,'4K・IMAX上映　10.23（金）〜11.2（月）',36,ORANGE,pad=30,h=72)
    pill(L,CX,y+604,'全国拡大上映　10.30（金）〜11.12（木）',36,NAVY,pad=30,h=72)
    text(L,'IMAX劇場では入場者プレゼント（A3ポスター）',30,CX,y+680,INK)
    text(L,'出典：MOVIE WALKER PRESS',22,CX,CARD[3]-58,GRAY,w=800); text(L,'画像：公式ポスター　© Studio Ghibli',22,CX,CARD[3]-28,GRAY,w=800); return L
def ev4():
    L,y=card_base(4,'愛知・長久手','ジブリパーク\n秋のどんどこ祭り')
    framed(L,photo(gb('majo11'),380,280,0.5,0.5),CX-200,y+210,rot=3); framed(L,photo(gb('mononoke24'),380,280,0.5,0.5),CX+200,y+225,rot=-3)
    info(L,y+430,'2026.10.30（金）〜11.22（日）',[('10/30〜 魔女の谷・もののけの里',34,INK),('夜7時まで営業＆イルミネーション開始',32,INK),('※日程はイベントごとに異なります',26,GRAY),('※チケット・事前申込が必要なものあり',26,GRAY)],'出典：ジブリパーク公式'); return L
def ev5():
    L,y=card_base(5,'京都','「禅とジブリ」京都展'); pill(L,CX+300,CARD[1]+78,'開催中！',34,RED,pad=24)
    b=poster_side(L,y,'064c96c3-image.webp',[('会場','京都市京セラ美術館\n新館 東山キューブ'),('料金','一般・大学生 1,900円')])
    pill(L,CX,b+70,'〜2026.12.6（日）',44,ORANGE,pad=34,h=78)
    text(L,'『君たちはどう生きるか』の世界観が中心',28,CX,b+150,GRAY)
    text(L,'出典：スタジオジブリ公式',22,CX,CARD[3]-58,GRAY,w=800); text(L,'画像：公式ポスター　© Studio Ghibli',22,CX,CARD[3]-28,GRAY,w=800); return L
def ev6():
    L,y=card_base(6,'佐賀','金曜ロードショーとジブリ展')
    for j,(n,fx) in enumerate([('totoro29',0.5),('majo40',0.5),('chihiro20',0.5),('mimi32',0.5)]):
        framed(L,photo(gb(n),370,210,fx),CX+(-195 if j%2==0 else 195),y+150+(j//2)*240,pad=8)
    pill(L,CX+300,CARD[1]+78,'佐賀初！',34,RED,pad=24)
    info(L,y+570,'2026.11.3（火・祝）〜2027.2.14（日）',[('佐賀県立美術館・博物館',38,INK),('一般 1,900円',36,INK)],'出典：佐賀展実行委員会・ローチケ'); return L
def ev7():
    L,y=card_base(7,'京都','スタジオジブリ企画制作\n『白隠さんの禅』')
    d=ImageDraw.Draw(L); d.rounded_rectangle((CX-390,y+90,CX+390,y+430),30,fill=(240,233,222,255))
    text(L,'禅とジブリの後期展',40,CX,y+160,GREEN); text(L,'禅僧・白隠の作品を',36,CX,y+240,INK); text(L,'映像とともに展示する美術展',36,CX,y+296,INK)
    text(L,'※ジブリ作品の展示ではありません',28,CX,y+376,RED)
    info(L,y+530,'2026.12.17（木）〜2027.1.11（月・祝）',[('京都市京セラ美術館 新館 東山キューブ',34,INK)],'出典：スタジオジブリ公式',cr=False); return L

# ---------- キャラ（場面写真の切り抜き＝cutout.py の cut/） ----------
def chara(name,h,ow=10):
    im=Image.open(S+f'cut/{name}.png').convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<50 else v))
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big); return out
# カードの四すみ（左上・右上・左下・右下）。カードの後ろに置いて、すみからのぞかせる
CORN=[(CARD[0]+20,CARD[1]-95,0),(CARD[2]-20,CARD[1]-95,0),(CARD[0]+20,CARD[3]+85,1),(CARD[2]-20,CARD[3]+85,1)]
def corner_set(names,h=230):
    out=[]
    for j,(n,(x,y,_)) in enumerate(zip(names,CORN)):
        c=chara(n,h); out.append((c,x,y,j))
    return out
def chars_layer(cs,g):
    L=layer()
    for c,x,y,j in cs:
        L.alpha_composite(c,(int(x-c.width/2),int(y-c.height/2)))
    return L
CHS=[[('totoro018',260,100,900),('chihiro019',260,980,900)],
['totoro018','totoro044','totoro004','majo018'],['chihiro019','chihiro022','chihiro016','chihiro045'],['mimi032','mimi015','karigurashi033','mimi002'],
['majo011','majo018','mononoke015','mononoke029'],['kimitachi027','kimitachi018','kimitachi047','kimitachi031'],['totoro004','chihiro019','majo018','mimi032'],[],[],[]]
CHS=[[(chara(n,h),x,y,j) for j,(n,h,x,y) in enumerate(c)] if i==0 else corner_set(c) for i,c in enumerate(CHS)]

# ---------- つかみ・まとめ ----------
def hook_layer():
    L=layer()
    # 各イベントの公式ポスター（白フチなし・影だけ）
    for f,(x,y,h,r) in zip(['064c96c3-image.webp','18d69da3-image.jpg','f48da2b0-image.jpg','ac81aad3-image.webp'],[(280,440,390,-4),(800,440,390,4),(280,1440,450,3),(800,1440,450,-3)]):
        P=Image.open(UP+f).convert('RGB'); framed(L,photo(P,int(h*P.width/P.height),h,r=12),x,y,pad=0,rot=r)
    pill(L,540,690,'2026年10月〜2027年 決定分',38,NAVY,pad=34,h=70)
    text(L,'これから行ける',84,540,830,INK,stw=12)
    text(L,'ジブリイベント',112,540,965,GREEN,stw=16)
    pill(L,540,1110,'全部まとめた！',72,ORANGE,pad=44,h=118)
    text(L,'画像：各公式ポスター　© Studio Ghibli',22,540,1700,WHITE,w=800,stw=3,stc=(0,0,0)); return L
EVLIST=[('1','ジブリパーク展 横須賀展','2027.2.11〜5.14'),('2','舞台『千と千尋の神隠し』','2027.3〜8 全国5都市'),('3','耳をすませば・アリエッティ IMAX','10.23〜／全国10.30〜'),
('4','ジブリパーク 秋のどんどこ祭り','10.30〜11.22'),('5','「禅とジブリ」京都展','〜12.6'),('6','金曜ロードショーとジブリ展 佐賀','11.3〜2027.2.14'),('7','『白隠さんの禅』京都','12.17〜2027.1.11')]
def list_layer():
    L=layer(); d=ImageDraw.Draw(L)
    d.rounded_rectangle((CX-450,260,CX+450,1380),44,fill=(255,252,246,255),outline=WHITE,width=10)
    text(L,'ジブリイベント予定表',62,CX,350,GREEN); text(L,'2026年10月23日時点',28,CX,415,GRAY)
    for j,(n,t,dt) in enumerate(EVLIST):
        y=470+j*128; d.rounded_rectangle((CX-410,y,CX+410,y+110),26,fill=(240,233,222,255))
        d.ellipse((CX-390,y+25,CX-330,y+85),fill=ORANGE); text(L,n,36,CX-360,y+55,WHITE)
        text(L,t,34,CX-305,y+36,INK,anchor='l',maxw=700); text(L,dt,30,CX-305,y+80,ORANGE,anchor='l')
    return L
QL=layer(); pill(QL,CX,1470,'あなたはどれに行く？',54,ORANGE,pad=40,h=96)
CTAL=layer(); pill(CTAL,CX,1470,'一緒に行く人に送ってね！',54,GREEN,pad=40,h=96)

# ---------- 字幕 ----------
SUB={'e1':'まずは横須賀！\nジブリパーク展が来年開催','e2':'舞台『千と千尋』が\n全国ツアー！','e3':'今日から耳すま＆アリエッティが\nIMAXに！','e4':'ジブリパークは\n秋のどんどこ祭り','e5':'京都の「禅とジブリ」展は\n12月6日まで',
'e6':'佐賀で初めての\n金曜ロードショーとジブリ展','e7':'12月17日からは\n『白隠さんの禅』'}
def sub_layer(t):
    L=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): text(L,l,46,CX,1440+(j-(len(ls)-1)/2)*64,WHITE,stw=8,stc=(20,20,20))
    return L

# ---------- タイムライン ----------
def wdur(k):
    with wave.open(NR+k+'.wav') as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
#   (種類, 背景, 前景, ナレーション, 効果音)
SEG=[('hook','navy',hook_layer(),['hook'],'kira1'),
('ev',scene_bg('totoro40'),ev1(),['e1'],'sceneswitch1'),('ev',scene_bg('chihiro32',0.3),ev2(),['e2'],'sceneswitch1'),('ev',scene_bg('mimi33'),ev3(),['e3'],'sceneswitch1'),
('ev',scene_bg('majo2'),ev4(),['e4'],'sceneswitch1'),('ev',scene_bg('kimitachi46'),ev5(),['e5'],'sceneswitch1'),('ev',scene_bg('totoro1',0.3),ev6(),['e6'],'sceneswitch1'),
('ev','navy',ev7(),['e7'],'sceneswitch1'),('end','navy',list_layer(),['q','cta'],'shine2'),('fol',None,None,['fol'],None)]
GAP=0.25; tl=[]; t=0
for s in SEG:
    d_=0.15+sum(wdur(k)+GAP for k in s[3])+0.45; tl.append((t,d_)+s); t+=d_
TOT=t; print('total',round(TOT,2))
if len(sys.argv)>3 and sys.argv[3]=='stills':
    for i,(t0,d_,kind,B,F,ns,sfx) in enumerate(tl):
        if F is None: continue
        b=(NAVYBG.convert('RGBA') if B=='navy' else next(bg_frames(B,1))); b.alpha_composite(chars_layer(CHS[i],0)); b.alpha_composite(F)
        if ns[0] in SUB: b.alpha_composite(sub_layer(SUB[ns[0]]))
        if kind=='end': b.alpha_composite(QL)
        b.convert('RGB').save(S+f'../ev/still{i:02d}.jpg',quality=85)
    sys.exit()
FOLLOW=Image.open(TK+'follow.jpg').convert('RGB').resize((W,H))
POP=[0.6,0.9,1.08,1.03]
def popped(F,k):
    if k>=len(POP): return F,0,0
    s=POP[k]; bb=F.getbbox(); c=F.crop(bb); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))),Image.BICUBIC)
    o=layer(); o.alpha_composite(c,(int((bb[0]+bb[2])/2-c.width/2),int((bb[1]+bb[3])/2-c.height/2))); return o,0,0
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',NR+'../v.mp4'],stdin=subprocess.PIPE)
for si,(t0,d_,kind,B,F,ns,sfx) in enumerate(tl):
    n=int(round((t0+d_)*FPS))-int(round(t0*FPS))
    if kind=='fol':
        for _ in range(n): enc.stdin.write(np.asarray(FOLLOW).tobytes())
        continue
    subs=[]; tt=0.15
    for k in ns: subs.append((tt,tt+wdur(k)+GAP,k)); tt+=wdur(k)+GAP
    BG=(b for b in iter(lambda:NAVYBG.convert('RGBA'),None)) if B=='navy' else bg_frames(B,n)
    for k in range(n):
        g=k/FPS; im=next(BG)
        if CHS[si]: cl,_,_=popped(chars_layer(CHS[si],g),k); im.alpha_composite(cl)
        fr,_,_=popped(F,k); im.alpha_composite(fr)
        for a,b_,key in subs:
            if a<=g<b_:
                if key in SUB: im.alpha_composite(sub_layer(SUB[key]))
                if key in ('q','cta'):
                    P=QL if key=='q' else CTAL; pp,_,_=popped(P,int((g-a)*FPS)); im.alpha_composite(pp)
        enc.stdin.write(np.asarray(im.convert('RGB')).tobytes())
enc.stdin.close(); enc.wait()
# ---------- 音 ----------
N=int(TOT*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
for t0,d_,kind,B,F,ns,sfx in tl:
    tt=t0+0.15
    for k in ns:
        add(rd(NR+k+'.wav'),tt,1.0)
        if k=='q': add(rd(S+'labsfx/pa1.wav'),tt,0.4)
        tt+=wdur(k)+GAP
    if sfx: add(rd(S+f'labsfx/{sfx}.wav'),t0,0.45)
mix=mix[:int(TOT*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(NR+'../a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',NR+'../v.mp4','-i',NR+'../a.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.8:level=0','-ar','44100','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',OUTV)
