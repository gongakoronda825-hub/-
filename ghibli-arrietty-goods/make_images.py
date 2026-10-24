# 借りぐらしのアリエッティ グッズまとめ（画像スライド：サムネ＋4商品×2ページ＋フォロー）
# 使い方: python3 make_images_vol2.py <作業フォルダ(setup.shのW)> <素材フォルダ(akf2：big/ と cut/)>
import sys,os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S,A=[a.rstrip('/')+'/' for a in sys.argv[1:3]]
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; TK=HERE+'../ghibli-toolkit/assets/'
OUT=HERE; os.makedirs(OUT,exist_ok=True)
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

# 並び：ユーザー指定（1ページ目 1・2・7・8／2ページ目 6・11・12・4）
#   (写真, 作品名, 商品名, 価格, ひとこと)
ITEMS=[(1,'借りぐらしのアリエッティ','アリエッティの洗濯ばさみ','1,540','劇中の髪どめを人間サイズに'),
(2,'借りぐらしのアリエッティ','25作品木製クリップ','715','メモをはさめるスタンド'),
(7,'借りぐらしのアリエッティ','クリアファイル レトロフレーム','495','金箔押しのレトロデザイン'),
(8,'借りぐらしのアリエッティ','ピアス 借りへ出発','6,050','角砂糖のビーズがポイント'),
(6,'借りぐらしのアリエッティ','フラワーベース はじめての借り','2,750','服を選ぶアリエッティのガラス'),
(11,'借りぐらしのアリエッティ','みにちゅあーとキット ホミリー','3,740','手のひらサイズのジオラマ'),
(12,'借りぐらしのアリエッティ','みにちゅあーとキット 翔','3,740','お別れのシーンを再現'),
(4,'借りぐらしのアリエッティ','DVD','5,170','おうちで何度でも')]
PAGES=[ITEMS[0:4],ITEMS[4:8]]
CREDIT='画像出典：どんぐり共和国 そらのうえ店　© Studio Ghibli'
PAGE_CHARS=[('karigurashi033','karigurashi024'),('karigurashi024','karigurashi050')]
CELL=[(285,690),(775,690),(285,1270),(775,1270)]
def item_layer(k,it,base):
    n,work,name,price,hito=it; L=layer(); cx,cy=CELL[k]
    paste(L,photo(n,360,[-3,3,3,-3][k]),cx,cy-90)
    pill(L,cx,cy+92,hito,26,RED,pad=20,h=50)
    d=ImageDraw.Draw(L); top=cy+125; lw=470
    d.rounded_rectangle((cx-lw/2,top,cx+lw/2,top+160),30,fill=(255,255,255,245),outline=GREEN,width=4)
    text(L,f'{base+k+1:02d}｜'+work,24,cx,top+32,GRAY,w=800,maxw=lw-30)
    text(L,name,34,cx,top+80,GREEN,maxw=lw-30)
    text(L,(price[0]+'¥'+price[1:] if price[0]=='各' else '¥'+price)+'（税込）',32,cx,top+128,DARK)
    return L
def head_layer(p):
    L=layer(); pill(L,W/2,330,f'アリエッティ グッズまとめ　{p+1}/{len(PAGES)}',36,GREEN,pad=40,h=70)
    text(L,CREDIT,24,W/2,1590,GRAY,w=800,stw=6); return L
def chars_layer(p):
    L=layer()
    for n,cx in zip(PAGE_CHARS[p],(215,905)):
        st=sticker(S+f'cut/{n}.png',260,200); L.alpha_composite(st,(int(cx-st.width/2),1885-st.height))
    return L

# ---------- サムネ ----------
def thumbnail():
    f=Image.open(TK+'bg_grid.jpg').convert('RGBA').resize((W,H))
    CH=Image.new('RGBA',(W,H),(0,0,0,0))   # グッズの後ろに大きくアリエッティと翔
    a_=sticker(S+'cut/karigurashi033.png',560,640); paste(CH,a_,190,245+a_.height/2)   # 顔がグッズに隠れないよう上の段の上に
    s_=sticker(S+'cut/karigurashi048.png',520,470); paste(CH,s_,840,960+s_.height/2)    # 顔が帯と下の段のあいだに出るよう右寄せ
    f.alpha_composite(CH)
    P=Image.new('RGBA',(W,H),(0,0,0,0)); xs=[200,435,670,900]
    def st(n,r):
        if n==11:   # 切り抜きにくいジオラマは写真のまま角丸で
            im=Image.open(A+f'big/{n}.jpg').convert('RGBA').resize((250,250),Image.LANCZOS); im.putalpha(rmask(250,250,24))
            o=Image.new('RGBA',(274,274),(0,0,0,0)); wb=Image.new('RGBA',o.size,WHITE+(255,)); wb.putalpha(rmask(274,274,30)); o.alpha_composite(wb); o.alpha_composite(im,(12,12)); return o.rotate(r,Image.BICUBIC,expand=True)
        return sticker(A+f'cut/{n}.png',250,330,r)
    for k,(n,r) in enumerate([(8,-7),(1,5),(7,-5),(2,7)]): paste(P,st(n,r),[230,455,680,905][k],(640 if k==0 else 590)+(25 if k%2 else 0))
    for k,(n,r) in enumerate([(12,6),(6,-5),(11,5),(4,-7)]): paste(P,st(n,r),xs[k],1420-(25 if k%2 else 0))
    f.alpha_composite(P)
    T=Image.new('RGBA',(W,H),(0,0,0,0)); x,tw=text(T,'どんぐり共和国で買える！',60,W/2,795,DARK,stw=12)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-58,x-28),(x+tw+58,x+tw+28)): d.line((sx,762,ex,828),fill=DARK,width=8)
    text(T,'アリエッティ',120,W/2,925,GREEN,stw=18)
    pill(T,W/2,1065,'グッズまとめ',58,ORANGE,pad=60,h=100)
    f.alpha_composite(T); text(f,'画像出典：どんぐり共和国 そらのうえ店　© Studio Ghibli',24,W/2,1640,GRAY,w=800,stw=6); return f.convert('RGB')

if __name__=='__main__':
    thumbnail().save(OUT+'00_thumbnail.png')
    BG=Image.open(TK+'bg_grid.jpg').convert('RGBA').resize((W,H))
    for p,pg in enumerate(PAGES):
        f=BG.copy()
        for L in (head_layer(p),chars_layer(p),*[item_layer(k,it,p*4) for k,it in enumerate(pg)]): f.alpha_composite(shifted(L))
        f.convert('RGB').save(OUT+f'{p+1:02d}_page.png')
    Image.open(TK+'follow.jpg').convert('RGB').save(OUT+f'{len(PAGES)+1:02d}_follow.png')
    print('ok')
