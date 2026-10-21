# Instagram用フォーマット（4:5 = 1080×1350）サムネ＋商品紹介
import sys
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
exec(open(S+'kh2.py').read().split("if len(sys.argv)>1")[0].replace('/ghibli-keyholder/vol2/','/ig-format/'))
cs=open(S+'imax.py').read(); exec(cs[cs.index('def chara('):cs.index('from PIL import ImageOps')].replace("f'cut/","S+f'cut/")); from PIL import ImageOps
W,H=1080,1350
g=Image.open('/home/user/-/ghibli-toolkit/assets/bg_grid.jpg').convert('RGBA'); BG=g.crop((0,(g.height-H)//2,W,(g.height-H)//2+H))
def layer(): return Image.new('RGBA',(W,H),(0,0,0,0))
YEL=(255,214,0); RED=(214,64,72); GRAY=(110,100,92)
def frame(L):  # 内側の白い枠線
    ImageDraw.Draw(L).rounded_rectangle((26,26,W-27,H-27),40,outline=(255,255,255,235),width=10)
def sticker(path,bw,bh,rot,ow=10):
    im=Image.open(path).convert('RGBA'); al=im.getchannel('A').point(lambda v:0 if v<40 else v); im.putalpha(al); im=im.crop(al.getbbox())
    s=min(bw/im.width,bh/im.height); im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0).filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(A.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(4,8)); w=Image.new('RGBA',big.size,WHITE); w.putalpha(A); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
def sparkle(L,x,y,s,col=YEL):
    d=ImageDraw.Draw(L); pts=[]
    import math
    for k in range(8):
        r=s if k%2==0 else s*0.38; a=math.pi/4*k-math.pi/2; pts.append((x+r*math.cos(a),y+r*math.sin(a)))
    d.polygon(pts,fill=col)
def next_mark(L):
    text(L,'NEXT',30,900,H-70,GREEN,0,cx=W-185)
    d=ImageDraw.Draw(L)
    for k in range(2): x=W-135+k*26; d.polygon([(x,H-86),(x+22,H-70),(x,H-54)],fill=GREEN)
# ---------- サムネ ----------
def thumbnail(top,bottom,small,title,sub,out,credit):
    L=layer(); frame(L); C=layer()
    for (p,bw,bh,r),cx in zip(top,[180,420,660,900]): paste(C,sticker(p,int(bw*1.15),int(bh*1.15),r),cx,270)
    for (p,bw,bh,r),cx in zip(bottom,[190,430,670,900]): paste(C,sticker(p,int(bw*1.15),int(bh*1.15),r),cx,1090)
    for x,y,s in [(80,520,22),(1000,470,18),(110,860,16),(985,880,24),(540,140,14)]: sparkle(C,x,y,s)
    T=layer(); d=ImageDraw.Draw(T)
    x,tw=text(T,small,46,900,580,DARK,10)
    for sx,ex in ((x-48,x-24),(x+tw+48,x+tw+24)): d.line((sx,555,ex,605),fill=DARK,width=7)
    text(T,title,128,900,705,GREEN,18,maxw=980)
    pill(T,W/2,845,sub,60,ORANGE,WHITE,60)
    text(T,credit,20,800,H-50,GRAY,6)
    next_mark(T)
    f=BG.copy(); f.alpha_composite(L); f.alpha_composite(C); f.alpha_composite(T); f.convert('RGB').save(out)
# ---------- 商品紹介（1ページ1商品） ----------
def product_card(path,s,rot):
    im=Image.open(path).convert('RGB'); m=max(im.size); sq=Image.new('RGB',(m,m),WHITE); sq.paste(im,((m-im.width)//2,(m-im.height)//2)); im=sq.resize((s,s),Image.LANCZOS).convert('RGBA'); im.putalpha(rmask(s,s,30))
    pad=16; card=Image.new('RGBA',(s+2*pad+40,s+2*pad+40),(0,0,0,0)); sh=Image.new('L',card.size,0); ImageDraw.Draw(sh).rounded_rectangle((20,30,20+s+2*pad,30+s+2*pad),44,fill=90)
    card.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(12))); wb=Image.new('RGBA',(s+2*pad,s+2*pad),WHITE); wb.putalpha(rmask(s+2*pad,s+2*pad,46)); card.alpha_composite(wb,(20,20)); card.alpha_composite(im,(20+pad,20+pad))
    return card.rotate(rot,resample=Image.BICUBIC,expand=True)
def item_page(no,series,name,price,photo_path,chars,out,credit,tag=None):
    L=layer(); frame(L); d=ImageDraw.Draw(L)
    # 見出し帯（番号＋商品名）
    d.rounded_rectangle((60,70,W-60,230),36,fill=(255,255,255,245))
    nf=fonts(900,96); d.text((110,150),f'{no:02d}',font=nf[1],fill=WHITE,anchor='lm',stroke_width=9,stroke_fill=GREEN)
    text(L,series,30,800,118,GRAY,0,cx=620,maxw=600)
    text(L,name,46,900,178,GREEN,0,cx=620,maxw=600)
    paste(L,product_card(photo_path,700,[-2,2][no%2]),W/2,670)
    if tag: pill(L,W-210,310,tag,32,RED,WHITE,30)
    pill(L,W/2,1090,price,56,ORANGE,WHITE,56)
    text(L,credit,20,800,H-50,GRAY,6)
    C=layer()
    for (n,h,r),cx in zip(chars,(140,940)): paste(C,chara(n,int(h*0.85),r),cx,1170)
    for x,y,s in [(95,330,18),(990,980,20)]: sparkle(L,x,y,s)
    next_mark(L)
    f=BG.copy(); f.alpha_composite(C); f.alpha_composite(L); f.convert('RGB').save(out)
if __name__=='__main__':
    P=S+'ig/'; OUT='/home/user/-/ig-format/'
    CR='画像出典：どんぐり共和国 そらのうえ店　© Studio Ghibli'
    thumbnail([(P+'cut/46940.png',190,300,-6),(P+'cut/38478.png',210,270,5),(P+'cut/21502640.png',230,260,-4),(P+'cut/46890.png',200,300,6)],
              [(P+'cut/21702551.png',200,290,6),(P+'cut/38863.png',250,250,-5),(P+'cut/21902596.png',240,240,5),(P+'cut/21902558.png',260,240,-6)],
              'どんぐり共和国で買える','耳をすませば','グッズまとめ',OUT+'ig_00_thumbnail.png',CR)
    items=[('21702551','箔押し ミニリングノート','¥495（税込）'),('21902596','「地球屋」ミニタオル','¥880（税込）'),('38863','ガラスミニ皿 鍋焼きうどん','¥1,100（税込）'),('21902558','ミニタオル カントリーロード','¥1,100（税込）')]
    ch=[(('mimi049',190,-6),('mimi026',180,6)),(('mimi013',190,-6),('mimi026',180,6)),(('mimi032',200,-6),('mimi049',180,6)),(('mimi049',190,-6),('mimi013',180,6))]
    for k,(i,nm,pr) in enumerate(items,1):
        item_page(k,'耳をすませば',nm,pr,P+f'raw/{i}.jpg',ch[k-1],OUT+f'ig_{k:02d}_item.png',CR,tag='人気' if k==1 else None)
    print('ok')
