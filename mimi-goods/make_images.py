import sys,math,subprocess,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
exec(open('cards.py').read().split("bg0=")[0].replace("import os; os.makedirs(OUT,exist_ok=True)",""))
exec(open('chars.py').read())
S_='/tmp/claude-0/-home-user--/b8f917d6-5155-5900-b9a6-72f48256ef3a/scratchpad/work/'
OUT='/home/user/-/mimi-goods/'; import os; os.makedirs(OUT,exist_ok=True)
FPS=30; DX=40; WHITE=(255,255,255); ORANGE=(236,128,60)
BG=Image.open('/home/user/-/ghibli-toolkit/assets/bg_grid.jpg').convert('RGBA')
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def photo(n,s,rot):
    im=Image.open(f'mimi/big/{n}.jpg').convert('RGB'); m=min(im.size); im=im.crop(((im.width-m)//2,(im.height-m)//2,(im.width+m)//2,(im.height+m)//2)).resize((s,s),Image.LANCZOS).convert('RGBA')
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

ITEMS=[(2,'「地球屋」ミニタオル','880'),(44,'ガラスミニ皿 鍋焼きうどん','1,100'),
(26,'ロルバーン ポケット付メモL','1,430'),(34,'刺繍キーホルダー 地球屋の看板','1,760'),
(13,'アートマグカップ','2,530'),(42,'こもれび ムーン','3,960'),
(11,'ディフューザー 地球屋での思い出','5,500'),(67,'オルゴール バロンドール／ルイーゼ','各14,300')]
PAGES=[ITEMS[i:i+4] for i in range(0,len(ITEMS),4)]
CREDIT='画像出典：どんぐり共和国 そらのうえ店'
PAGE_CREDIT=CREDIT+'　© Studio Ghibli'
# 各ページの左下・右下に貼るキャラ（場面写真の切り抜き）
PAGE_CHARS=[('mimi049','mimi005'),('mimi013','mimi026')]
# 6と7を左右に並べた1枚
a,b=[Image.open(f'mimi/big/{n}.jpg').convert('RGB') for n in (6,7)]
def half(im,cx): s=min(im.size); w=s//2; x=int(im.width*cx)-w//2; return im.crop((x,(im.height-s)//2,x+w,(im.height+s)//2))
pa,pb=half(a,0.5),half(b,0.52); c=Image.new('RGB',(pa.width*2,pa.height)); c.paste(pa,(0,0)); c.paste(pb.resize(pa.size),(pa.width,0)); c.save('mimi/big/67.jpg')
# 切り抜きに残った背景を消す（割合で指定）
TRIM={42:[(0,0,0.27,1)],34:[(0.4,0,1,0.3)],'mimi026':[(0.4,0,1,1)]}
def cut_sticker(n,bw,bh,rot,ow=10):
    im=Image.open(f'cut/{n}.png' if isinstance(n,str) else f'mimi/cut/{n}.png').convert('RGBA')
    al=im.getchannel('A').point(lambda v:0 if v<30 else v)
    for (x0,y0,x1,y1) in TRIM.get(n,()): al.paste(0,(int(x0*im.width),int(y0*im.height),int(x1*im.width),int(y1*im.height)))
    im.putalpha(al); im=im.crop(al.getbbox())
    s=min(bw/im.width,bh/im.height); im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0)
    o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
def thumb_layers():
    P=layer(); xs=[200,435,670,900]
    top=[(6,-6,230,430),(13,5,250,330),(42,-5,250,330),(7,6,230,430)]
    bot=[(26,6,230,330),(44,-5,250,300),(2,5,250,300),(11,-6,230,400)]
    for k,(n,r,bw,bh) in enumerate(top): paste(P,cut_sticker(n,bw,bh,r),xs[k],505+(30 if k%2 else 0))
    for k,(n,r,bw,bh) in enumerate(bot): paste(P,cut_sticker(n,bw,bh,r),xs[k],1345-(30 if k%2 else 0))
    T=layer()
    x,tw=text(T,'どんぐり共和国で買える',54,900,800,DARK,10)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,770,ex,830),fill=DARK,width=8)
    text(T,'耳をすませば',118,900,925,GREEN,16,maxw=980)
    pill(T,W/2,1065,'グッズまとめ',58,ORANGE,WHITE,60)
    return P,T
CELL=[(285,690),(775,690),(285,1270),(775,1270)]
def item_layer(k,item,cells=None):
    n,name,price=item; L=layer(); cx,cy=(cells or CELL)[k]
    paste(L,photo(n,360,[-3,3,3,-3][k]),cx,cy-90)
    d=ImageDraw.Draw(L); top=cy+125; lw=470
    d.rounded_rectangle((cx-lw/2,top,cx+lw/2,top+160),30,fill=(255,255,255,245),outline=GREEN,width=4)
    text(L,'耳をすませば',24,800,top+30,(110,100,92),cx=cx)
    text(L,name,34,900,top+78,GREEN,cx=cx,maxw=lw-30)
    text(L,(price[0]+'¥'+price[1:] if price[0]=='各' else '¥'+price)+'（税込）',32,900,top+126,DARK,cx=cx)
    return L
def head_layer(p):
    L=layer(); pill(L,W/2,330,f'耳をすませば グッズまとめ　{p+1}/{len(PAGES)}',36,GREEN,WHITE,40)
    text(L,PAGE_CREDIT,24,800,1590,(110,100,92),6); return L
def chars_layer(p):
    L=layer()
    for n,cx in zip(PAGE_CHARS[p],(215,905)):
        st=cut_sticker(n,260,190,0); L.alpha_composite(st,(int(cx-st.width/2),1885-st.height))
    return L
def compose(*Ls):
    f=BG.copy()
    for L in Ls: f.alpha_composite(shifted(L))
    return f
if __name__=='__main__':
    P,T=thumb_layers(); f=BG.copy(); f.alpha_composite(P); f.alpha_composite(T)
    text(f,CREDIT,24,800,1515,(110,100,92),6); f.convert('RGB').save(OUT+'00_thumbnail.png')
    for p,pg in enumerate(PAGES):
        compose(head_layer(p),chars_layer(p),*[item_layer(k,it) for k,it in enumerate(pg)]).convert('RGB').save(OUT+f'{p+1:02d}_page.png')
    Image.open('/home/user/-/ghibli-toolkit/assets/follow.jpg').convert('RGB').save(OUT+'03_follow.png')
    print('ok')
