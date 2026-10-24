# ジブリの秋冬グッズ vol.2（画像スライド：サムネ＋4商品×2ページ＋フォロー）
# 使い方: python3 make_images_vol2.py <作業フォルダ(setup.shのW)> <素材フォルダ(akf2：big/ と cut/)>
import sys,os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S,A=[a.rstrip('/')+'/' for a in sys.argv[1:3]]
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUT=HERE+'vol2/'; os.makedirs(OUT,exist_ok=True)
W,H=1080,1920; DX=40
WHITE=(255,255,255); GREEN=(46,125,62); ORANGE=(236,128,60); RED=(206,72,80); DARK=(40,36,32); GRAY=(110,100,92); AKI=(214,78,24)

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
    d=ImageDraw.Draw(L); x=cx-tlen(t,sz,w)/2; x0=x
    for k,s in segs(t):
        d.text((x,cy),s,font=font(w,sz,k),fill=fill,anchor='lm',stroke_width=stw,stroke_fill=stc); x+=font(w,sz,k).getlength(s)
    return x0,x-x0
def pill(L,cx,cy,t,sz,bg,fg=WHITE,pad=34,h=None,outline=WHITE):
    tw=tlen(t,sz); h=h or sz*1.6
    ImageDraw.Draw(L).rounded_rectangle((cx-tw/2-pad,cy-h/2,cx+tw/2+pad,cy+h/2),h/2,fill=bg,outline=outline,width=5 if outline else 0)
    text(L,t,sz,cx,cy,fg)
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
def rmask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); return m
def paste(L,img,cx,cy): L.alpha_composite(img,(int(cx-img.width/2),int(cy-img.height/2)))
def shifted(L): o=layer(); o.alpha_composite(L.crop((DX,0,W,H)),(0,0)); return o
def sticker(path,bw,bh,rot=0,ow=10):
    im=Image.open(path).convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v:0 if v<40 else v))
    s=min(bw/im.width,bh/im.height); im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
    if not ow: return im.rotate(rot,Image.BICUBIC,expand=True) if rot else im
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    Aa=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=Aa.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(4,8)); w_=Image.new('RGBA',big.size,(255,255,255,0)); w_.putalpha(o); out.alpha_composite(w_); out.alpha_composite(big)
    return out.rotate(rot,Image.BICUBIC,expand=True) if rot else out
def photo(n,s,rot):
    im=Image.open(A+f'big/{n}.jpg').convert('RGB').resize((s,s),Image.LANCZOS).convert('RGBA'); im.putalpha(rmask(s,s,24)); pad=14
    card=Image.new('RGBA',(s+2*pad+40,s+2*pad+40),(0,0,0,0))
    sh=Image.new('L',card.size,0); ImageDraw.Draw(sh).rounded_rectangle((20,28,20+s+2*pad,28+s+2*pad),34,fill=90); card.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(10)))
    wb=Image.new('RGBA',(s+2*pad,s+2*pad),WHITE+(255,)); wb.putalpha(rmask(s+2*pad,s+2*pad,34)); card.alpha_composite(wb,(20,20)); card.alpha_composite(im,(20+pad,20+pad))
    return card.rotate(rot,Image.BICUBIC,expand=True)

# 並び：1番ハウル、2番毛布（カーディガンは1番にしない）
#   (写真, 作品名, 商品名, 価格, ひとこと)
ITEMS=[('howl','ハウルの動く城','ボタン付ストール ハウルのマント','5,280','留めるとカルシファーが現れる'),
('moufu','となりのトトロ','シルエット ハーフ毛布','各5,500','肩掛けにも冬キャンプにも'),
('jiji','魔女の宅急便','もこもこジジ フリーマット','2,750','もこもこ触感がくせになる'),
('slipper','となりのトトロ','どんぐりスリッパ','各2,750','丸洗いOK＆すべりにくい'),
('cardigan','となりのトトロ','カーディガン 夜空','13,200','背中にコマで飛ぶトトロ'),
('dekoboko','となりのトトロ','デコボコ大トトロ ブランケット','3,300','裏はシープボアでぬくぬく'),
('urakimo','となりのトトロ','裏起毛ソックス','1,540','マシュマロ裏起毛で冷えない'),
('room','となりのトトロ','あったかルームソックス','1,320','すべり止め付きで安心')]
PAGES=[ITEMS[0:4],ITEMS[4:8]]
CREDIT='画像出典：どんぐり共和国 そらのうえ店　© Studio Ghibli'
PAGE_CHARS=[('howl035','majo018'),('totoro004','totoro018')]
CELL=[(285,690),(775,690),(285,1270),(775,1270)]
def item_layer(k,it,base):
    n,work,name,price,hito=it; L=layer(); cx,cy=CELL[k]
    paste(L,photo(n,360,[-3,3,3,-3][k]),cx,cy-90)
    pill(L,cx,cy+92,hito,26,RED,pad=20,h=50)
    d=ImageDraw.Draw(L); top=cy+125; lw=470
    d.rounded_rectangle((cx-lw/2,top,cx+lw/2,top+160),30,fill=(255,255,255,245),outline=GREEN,width=4)
    text(L,f'{base+k+1:02d}｜'+work,24,cx,top+32,GRAY,w=800)
    text(L,name,34,cx,top+80,GREEN,maxw=lw-30)
    text(L,(price[0]+'¥'+price[1:] if price[0]=='各' else '¥'+price)+'（税込）',32,cx,top+128,DARK)
    return L
def head_layer(p):
    L=layer(); pill(L,W/2,330,f'ジブリの秋冬グッズ vol.2　{p+1}/{len(PAGES)}',36,GREEN,pad=40,h=70)
    text(L,CREDIT,24,W/2,1590,GRAY,w=800,stw=6); return L
def chars_layer(p):
    L=layer()
    for n,cx in zip(PAGE_CHARS[p],(215,905)):
        st=sticker(S+f'cut/{n}.png',260,200); L.alpha_composite(st,(int(cx-st.width/2),1885-st.height))
    return L

# ---------- サムネ ----------
def thumbnail():
    bg=Image.open(TK+'bg_autumn_leaves2.jpg').convert('RGB'); s=max(W/bg.width,H/bg.height); bg=bg.resize((int(bg.width*s+0.5),int(bg.height*s+0.5)),Image.LANCZOS)
    bg=bg.crop(((bg.width-W)//2,(bg.height-H)//2,(bg.width-W)//2+W,(bg.height-H)//2+H)); f=Image.blend(bg,Image.new('RGB',(W,H),(0,0,0)),0.22).convert('RGBA')
    CH=layer(); paste(CH,sticker(S+'cut/howl035.png',600,470,ow=0),190,290); paste(CH,sticker(S+'cut/totoro004.png',600,470,ow=0),860,1640)   # キャラは商品の後ろ
    f.alpha_composite(CH)
    P=layer(); xs=[200,435,670,900]
    top=[('src_003',-7),('src_017',5),('src_058',-5),('src_019',7)]; bot=[('src_039',6),('src_052',-5),('src_064',5),('src_054',-7)]
    for k,(n,r) in enumerate(top): paste(P,sticker(A+f'cut/{n}.png',250,330,r),xs[k],520+(30 if k%2 else 0))
    for k,(n,r) in enumerate(bot): paste(P,sticker(A+f'cut/{n}.png',250,330,r),xs[k],1350-(30 if k%2 else 0))
    f.alpha_composite(P)
    T=layer(); x,tw=text(T,'どんぐり共和国で買える！',66,W/2,790,DARK,stw=12)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-62,x-30),(x+tw+62,x+tw+30)): d.line((sx,755,ex,825),fill=WHITE,width=21); d.line((sx,755,ex,825),fill=DARK,width=9)
    parts=[('ジブリの',86,GREEN),('あったか',102,AKI),('グッズ',86,GREEN)]   # 「あったか」だけ紅葉色で少し大きく
    x=W/2-sum(tlen(t,z) for t,z,_ in parts)/2
    for t,z,c in parts: text(T,t,z,x+tlen(t,z)/2,915,c,stw=18); x+=tlen(t,z)
    pw=tlen('1,320円から！',60)+100; px=W/2-70
    pill(T,px,1062,'1,320円から！',60,ORANGE,pad=50,h=104)
    pill(T,px+pw/2+95,1062,'vol.2',40,GREEN,pad=26,h=72)
    f.alpha_composite(T); return f.convert('RGB')

if __name__=='__main__':
    thumbnail().save(OUT+'00_thumbnail.png')
    BG=Image.open(TK+'bg_grid_brown.jpg').convert('RGBA').resize((W,H))
    for p,pg in enumerate(PAGES):
        f=BG.copy()
        for L in (head_layer(p),chars_layer(p),*[item_layer(k,it,p*4) for k,it in enumerate(pg)]): f.alpha_composite(shifted(L))
        f.convert('RGB').save(OUT+f'{p+1:02d}_page.png')
    Image.open(TK+'follow.jpg').convert('RGB').save(OUT+f'{len(PAGES)+1:02d}_follow.png')
    print('ok')
