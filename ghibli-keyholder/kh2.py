import sys,math,subprocess,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
exec(open('cards.py').read().split("bg0=")[0].replace("import os; os.makedirs(OUT,exist_ok=True)",""))
exec(open('chars.py').read())
S_='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
OUT='/home/user/-/ghibli-keyholder/vol2/'; import os; os.makedirs(OUT,exist_ok=True)
VOL='2'; FPS=30; DX=40; WHITE=(255,255,255); ORANGE=(236,128,60)
ITEMS=[(17,'ハウルの動く城','刺繍キーホルダー 色円盤','1,760'),(18,'天空の城ラピュタ','【GBL】ランタンキーチェーン 飛行石','2,420'),
(19,'となりのトトロ','【GBL】ランタンキーチェーン 小トトロ','2,420'),(27,'魔女の宅急便','キーホルダー パンリース','1,320'),
(28,'紅の豚','キーホルダー サボイアとポルコ','1,320'),(29,'天空の城ラピュタ','キーホルダー 園庭のロボット兵','1,320'),
(30,'となりのトトロ','キーホルダー コマトトロ','1,540'),(32,'もののけ姫','キーホルダー お面とコダマ','1,320'),
(33,'もののけ姫','キーホルダー カタカタコダマ','1,540'),(34,'千と千尋の神隠し','キーホルダー かさなりカシラ','1,540')]
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
def cut_sticker(n,bw,bh,rot,ow=10):
    im=Image.open(f'khcut/{n}.png').convert('RGBA')
    al=im.getchannel('A').point(lambda v:0 if v<30 else v); im.putalpha(al)
    s=min(bw/im.width,bh/im.height); im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0)
    o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
def thumb_layers():
    P=layer(); xs=[200,435,670,900]
    top=[(18,-7),(28,5),(32,-5),(19,7)]; bot=[(29,6),(30,-5),(34,5),(33,-7)]
    for k,(n,r) in enumerate(top): paste(P,cut_sticker(n,250,400,r),xs[k],505+(30 if k%2 else 0))
    for k,(n,r) in enumerate(bot): paste(P,cut_sticker(n,260,400,r),xs[k],1345-(30 if k%2 else 0))
    T=layer()
    x,tw=text(T,'どんぐり共和国で買える',54,900,800,DARK,10)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,770,ex,830),fill=DARK,width=8)
    text(T,'キーホルダーまとめ',108,900,925,GREEN,16,maxw=980)
    pill(T,W/2,1065,f'vol.{VOL}',58,ORANGE,WHITE,60)
    return P,T
# ---------- page ----------
CELL=[(290,640),(760,640),(290,1180),(760,1180)]
def item_layer(k,item,cells=None):
    n,work,name,price=item; L=layer(); cx,cy=(cells or CELL)[k]
    paste(L,photo(n,270,[-3,3,3,-3][k]),cx,cy-60)
    d=ImageDraw.Draw(L); top=cy+110; lw=430
    d.rounded_rectangle((cx-lw/2,top,cx+lw/2,top+150),30,fill=(255,255,255,245),outline=GREEN,width=4)
    text(L,work,24,800,top+30,(110,100,92),cx=cx)
    text(L,name,32,900,top+74,GREEN,cx=cx,maxw=lw-30)
    text(L,f'¥{price}（税込）',30,900,top+118,DARK,cx=cx)
    return L
def head_layer(p):
    L=layer(); pill(L,W/2,330,f'キーホルダーまとめ vol.{VOL}　{p+1}/{len(PAGES)}',36,GREEN,WHITE,40)
    text(L,'どんぐり共和国 そらのうえ店',24,800,1515,(110,100,92),6); return L
def compose(*Ls):
    f=BG.copy()
    for L in Ls: f.alpha_composite(shifted(L))
    return f
if len(sys.argv)>1 and sys.argv[1]=='images':
    P,T=thumb_layers(); compose(P,T).convert('RGB').save(OUT+'00_thumbnail.png')
    for p,pg in enumerate(PAGES):
        cells=CELL if len(pg)>2 else [(290,900),(760,900)]
        compose(head_layer(p),*[item_layer(k,it,cells) for k,it in enumerate(pg)]).convert('RGB').save(OUT+f'{p+1:02d}_page.png')
    print('ok')
