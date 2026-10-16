import math, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
F='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/fonts/'
OUT='/home/user/-/ghibli-otona/'
W,H,FPS,DUR=1080,1920,30,30
DARK=(60,52,45); WHITE=(255,255,255)
def fonts(w,s): return ImageFont.truetype(F+f'jp{w}.woff',s),ImageFont.truetype(F+f'lat{w}.woff',s)
def segs(t): return re.findall(r'[\x00-\x7f]+|[^\x00-\x7f]+',t)
def tlen(t,fp): return sum(fp[1 if s.isascii() else 0].getlength(s) for s in segs(t))
def tdraw(d,cx,cy,t,fp,fill,stroke=0,sfill=WHITE):
    x=cx-tlen(t,fp)/2
    for s in segs(t):
        f=fp[1 if s.isascii() else 0]
        d.text((x,cy),s,font=f,fill=fill,anchor='lm',stroke_width=stroke,stroke_fill=sfill); x+=f.getlength(s)

# palettes: (bg, line, accent)
PAL={'hook':((244,242,236),(46,125,62),(46,125,62)),
'kiki':((250,240,240),(214,92,92),(206,72,80)),
'chihiro':((250,242,232),(196,110,60),(184,84,52)),
'totoro':((240,246,236),(70,140,80),(52,120,64)),
'howl':((236,242,250),(80,120,190),(64,100,176)),
'cta':((244,242,236),(46,125,62),(46,125,62))}

def background(t,key,key2=None,mix=0.0):
    bg,ln,_=PAL[key]
    if key2:
        b2,l2,_=PAL[key2]
        bg=tuple(int(a+(b-a)*mix) for a,b in zip(bg,b2)); ln=tuple(int(a+(b-a)*mix) for a,b in zip(ln,l2))
    ln=tuple(int(a*0.55+b*0.45) for a,b in zip(ln,bg))
    im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
    ph=t*0.6
    for i in range(-1,11):
        x0=i*118+20
        pts=[(x0+28*math.sin(y/260+i*1.7+ph)+14*math.sin(y/97+i),y) for y in range(-20,H+40,40)]
        d.line(pts,fill=ln,width=4,joint='curve')
    for j in range(-1,18):
        y0=j*118+30
        pts=[(x,y0+26*math.sin(x/230+j*1.3+ph*0.8)+10*math.sin(x/83+j)) for x in range(-20,W+40,40)]
        d.line(pts,fill=ln,width=4,joint='curve')
    return im

def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))

def card(y0,y1,fill,outline):
    L=layer(); d=ImageDraw.Draw(L)
    d.rounded_rectangle((100,y0+10,W-100,y1+10),48,fill=(0,0,0,40))
    d.rounded_rectangle((90,y0,W-90,y1),48,fill=fill,outline=outline,width=6)
    return L

def pill(L,cx,cy,text,size,bg,fg,pad=34):
    d=ImageDraw.Draw(L); fp=fonts(900,size); w=tlen(text,fp)+pad*2
    d.rounded_rectangle((cx-w/2,cy-size*0.85,cx+w/2,cy+size*0.85),size,fill=bg)
    tdraw(d,cx,cy,text,fp,fg)

def lines(L,cy,ls,size,fill,w=900,gap=1.35,stroke=0):
    d=ImageDraw.Draw(L); fp=fonts(w,size)
    top=cy-(len(ls)-1)*size*gap/2
    for k,t in enumerate(ls): tdraw(d,W/2,top+k*size*gap,t,fp,fill,stroke)

# ---- build static layers ----
hook=layer()
lines(hook,860,['大人になって','ジブリ見たら、'],96,DARK,stroke=14)
hook2=layer()
d=ImageDraw.Draw(hook2)
lines(hook2,1110,['泣く場所が','変わってた'],120,PAL['hook'][2],stroke=16)

films=[('kiki','魔女の宅急便',['ほうきで','飛びたかった'],['13歳で知らない街に','一人で住んだキキ、','強すぎる']),
('chihiro','千と千尋の神隠し',['湯屋が','こわかった'],['10歳で働いて、','名前を守り抜いた','千尋']),
('totoro','となりのトトロ',['ネコバスに','乗りたかった'],['お母さんの入院中、','妹を守ってた','サツキ']),
('howl','ハウルの動く城',['ハウル','かっこいい'],['自分に自信がない','ソフィーの気持ち、','わかる'])]
FL=[]
for n,(key,title,kid,adult) in enumerate(films):
    acc=PAL[key][2]
    T=layer(); pill(T,W/2,400,title,52,acc,WHITE,44)
    pd=ImageDraw.Draw(T)
    for k in range(4):
        cx=W/2+(k-1.5)*44
        pd.ellipse((cx-11,1540-11,cx+11,1540+11),fill=acc if k==n else (200,200,200))
    A=card(500,800,(255,255,255,245),(210,205,195))
    pill(A,W/2,500,'子どもの頃',36,(150,140,130),WHITE)
    lines(A,665,kid,62,DARK,w=800,gap=1.3)
    AR=layer(); ad=ImageDraw.Draw(AR)
    ad.polygon([(W/2-40,845),(W/2+40,845),(W/2,895)],fill=acc)
    B=card(950,1420,acc+(255,),WHITE)
    pill(B,W/2,950,'大人になって',40,WHITE,acc)
    lines(B,1200,adult,70,WHITE,w=900,gap=1.32)
    FL.append((key,T,A,AR,B))
cta1=layer(); lines(cta1,800,['あなたが','大人になって','変わった作品は？'],92,DARK,stroke=14,gap=1.3)
cta2=layer(); d=ImageDraw.Draw(cta2)
# speech bubble icon drawn by code
cx,cy=W/2,1150; acc=PAL['cta'][2]
d.rounded_rectangle((cx-110,cy-80,cx+110,cy+70),50,fill=acc)
d.polygon([(cx-40,cy+60),(cx-70,cy+120),(cx+5,cy+66)],fill=acc)
for k in (-55,0,55): d.ellipse((cx+k-16,cy-16,cx+k+16,cy+16),fill=WHITE)
pill(cta2,W/2,1340,'コメントで教えてね',54,acc,WHITE,50)

def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def put(frame,L,t0,t,dur=0.45,dy=40,out=None):
    a=ease((t-t0)/dur)
    if out is not None: a*=1-ease((t-out)/0.3)
    if a<=0: return
    l=L if a>=1 else L.copy()
    if a<1:
        al=l.getchannel('A').point(lambda v:int(v*a)); l.putalpha(al)
    frame.alpha_composite(l,(0,int(dy*(1-a))))

def render(t):
    # determine segment
    if t<2: key,k2,mix=('hook',None,0)
    elif t<26:
        i=int((t-2)//6); key=films[i][0]; ts=(t-2)-i*6
        prev='hook' if i==0 else films[i-1][0]
        k2,mix=(None,0) if ts>0.4 else (key,ease(ts/0.4)); 
        if ts<=0.4: key=prev
    else:
        ts=t-26; key,k2,mix=(films[-1][0],'cta',ease(ts/0.4)) if ts<0.4 else ('cta',None,0)
    fr=background(t,key,k2,mix).convert('RGBA')
    if t<2:
        put(fr,hook,0.0,t,dur=0.3,out=1.75); put(fr,hook2,0.4,t,dur=0.35,out=1.75)
        if t<1.75: pass
    elif t<26:
        i=int((t-2)//6); ts=(t-2)-i*6; _,T,A,AR,B=FL[i]
        o=5.7
        put(fr,T,0.1,ts,out=o); put(fr,A,0.25,ts,out=o)
        put(fr,AR,2.0,ts,out=o,dy=-20); put(fr,B,2.2,ts,dy=60,out=o)
    else:
        ts=t-26; put(fr,cta1,0.2,ts); put(fr,cta2,0.9,ts)
    return fr.convert('RGB')

if len(sys.argv)>1 and sys.argv[1]=='stills':
    for t in [1.5,3.5,6.5,13,19,25,29]:
        render(t).save(OUT+f'still_{t:05.1f}.png')
    sys.exit()
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart',OUT+'ghibli_otona.mp4'],stdin=subprocess.PIPE)
for n in range(FPS*DUR):
    p.stdin.write(render(n/FPS).tobytes())
p.stdin.close(); p.wait(); print('done',p.returncode)
