import sys,math,subprocess,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
exec(open('cards.py').read().split("bg0=")[0].replace("import os; os.makedirs(OUT,exist_ok=True)",""))
exec(open('chars.py').read())
S_='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
OUT='/home/user/-/ghibli-keyholder/vol1/'; import os; os.makedirs(OUT,exist_ok=True)
VOL='1'; FPS=30; DX=40; WHITE=(255,255,255); ORANGE=(236,128,60)
ITEMS=[(1,'天空の城ラピュタ','飛行石ホルダー 王の飛行石','880'),(5,'天空の城ラピュタ','ころ鈴根付 ロボット兵','1,100'),
(6,'千と千尋の神隠し','ころ鈴根付 カオナシ','1,100'),(7,'ハウルの動く城','【GBL】ランタンキーチェーン カルシファー','2,420'),
(9,'となりのトトロ','キーホルダー 中トトロと小トトロ','1,540'),(10,'千と千尋の神隠し','キーホルダー 砂金とカオナシ','1,540'),
(14,'千と千尋の神隠し','キーホルダー 坊ネズミとハエドリ','1,320'),(15,'崖の上のポニョ','キーホルダー クラゲポニョ','1,320')]
PAGES=[ITEMS[i:i+4] for i in range(0,len(ITEMS),4)]
BG=Image.open('/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/5a0f7bc1-image.jpg').convert('RGBA')
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def photo(n,s,rot):
    im=Image.open(f'kh/big/{n}.jpg').convert('RGB'); m=min(im.size); im=im.crop(((im.width-m)//2,(im.height-m)//2,(im.width+m)//2,(im.height+m)//2)).resize((s,s),Image.LANCZOS).convert('RGBA')
    im.putalpha(rmask(s,s,24)); pad=14
    card=Image.new('RGBA',(s+2*pad+40,s+2*pad+40),(0,0,0,0))
    sh=Image.new('L',card.size,0); ImageDraw.Draw(sh).rounded_rectangle((20,28,20+s+2*pad,28+s+2*pad),34,fill=90)
    card.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(10)))
    wb=Image.new('RGBA',(s+2*pad,s+2*pad),WHITE); wb.putalpha(rmask(s+2*pad,s+2*pad,34)); card.alpha_composite(wb,(20,20)); card.alpha_composite(im,(20+pad,20+pad))
    return card.rotate(rot,resample=Image.BICUBIC,expand=True)
def paste(L,img,cx,cy): L.alpha_composite(img,(int(cx-img.width/2),int(cy-img.height/2)))
def text(L,t,size,w,cy,col,stw=0,cx=W/2,maxw=None):
    fp=fonts(w,size)
    while maxw and tlen(t,fp)>maxw: size-=2; fp=fonts(w,size)
    d=ImageDraw.Draw(L); x=cx-tlen(t,fp)/2
    for p in ('st','f'):
        if p=='st' and not stw: continue
        xx=x
        for s_ in segs(t):
            f=fp[1 if s_.isascii() else 0]
            d.text((xx,cy),s_,font=f,anchor='lm',fill=WHITE if p=='st' else col,stroke_width=stw if p=='st' else 0,stroke_fill=WHITE); xx+=f.getlength(s_)
    return x,tlen(t,fp)
def pill(L,cx,cy,t,size,bg,fg,pad=34):
    d=ImageDraw.Draw(L); fp=fonts(900,size); w=tlen(t,fp)+pad*2
    d.rounded_rectangle((cx-w/2,cy-size*0.85,cx+w/2,cy+size*0.85),size,fill=bg); text(L,t,size,900,cy,fg,cx=cx)
def shifted(L): o=layer(); o.alpha_composite(L.crop((DX,0,W,H)),(0,0)); return o
# ---------- thumbnail ----------
def thumb_layers():
    P=layer(); xs=[215,445,675,905]; angs=[-6,4,-4,6]
    for k,(n,*_) in enumerate(ITEMS[:4]): paste(P,photo(n,200,angs[k]),xs[k],470+(25 if k%2 else 0))
    for k,(n,*_) in enumerate(ITEMS[4:8]): paste(P,photo(n,200,-angs[k]),xs[k],1330-(25 if k%2 else 0))
    T=layer()
    x,tw=text(T,'どんぐり共和国で買える',54,900,790,DARK,10)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,760,ex,820),fill=DARK,width=8)
    text(T,'キーホルダーまとめ',108,900,915,GREEN,16,maxw=980)
    pill(T,W/2,1065,f'vol.{VOL}',58,ORANGE,WHITE,60)
    return P,T
# ---------- page ----------
CELL=[(285,600),(795,600),(285,1180),(795,1180)]
def item_layer(k,item):
    n,work,name,price=item; L=layer(); cx,cy=CELL[k]
    paste(L,photo(n,300,[-3,3,3,-3][k]),cx,cy-55)
    d=ImageDraw.Draw(L); top=cy+135; lw=470
    d.rounded_rectangle((cx-lw/2,top,cx+lw/2,top+150),30,fill=(255,255,255,245),outline=GREEN,width=4)
    text(L,work,24,800,top+30,(110,100,92),cx=cx)
    text(L,name,32,900,top+74,GREEN,cx=cx,maxw=lw-30)
    text(L,f'¥{price}（税込）',30,900,top+118,DARK,cx=cx)
    return L
def head_layer(p):
    L=layer(); pill(L,W/2,290,f'キーホルダーまとめ vol.{VOL}　{p+1}/{len(PAGES)}',36,GREEN,WHITE,40)
    text(L,'どんぐり共和国 そらのうえ店',24,800,1515,(110,100,92),6); return L
def compose(*Ls):
    f=BG.copy()
    for L in Ls: f.alpha_composite(shifted(L))
    return f
if len(sys.argv)>1 and sys.argv[1]=='images':
    P,T=thumb_layers(); compose(P,T).convert('RGB').save(OUT+'00_thumbnail.png')
    for p,pg in enumerate(PAGES):
        compose(head_layer(p),*[item_layer(k,it) for k,it in enumerate(pg)]).convert('RGB').save(OUT+f'{p+1:02d}_page.png')
    print('ok')
