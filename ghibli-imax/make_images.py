import sys; sys.argv=['x']
exec(open('kh.py').read())
from PIL import ImageFont
OUT='/home/user/-/ghibli-imax/'
RED=(206,72,80); NAVY=(30,50,100); GRAY=(110,100,92); YEL=(255,226,0); PINK=(226,50,110)
KF='fonts/keifont.ttf'; U='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/'
def kf(L,t,size,cy,fill,inner=(20,20,20),outer=WHITE,si=14,so=26,cx=540,maxw=None):
    f=ImageFont.truetype(KF,size)
    while maxw and f.getlength(t)>maxw: size-=4; f=ImageFont.truetype(KF,size)
    tw=int(f.getlength(t))+so*2+40; th=int(size*1.5)+so*2
    T=Image.new('RGBA',(tw,th),(0,0,0,0)); d=ImageDraw.Draw(T); x=so+20; y=th/2
    def solid(ox,oy,sw,col):
        m=Image.new('L',T.size,0); ImageDraw.Draw(m).text((x+ox,y+oy),t,font=f,fill=255,anchor='lm',stroke_width=sw,stroke_fill=255)
        m=m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
        c=Image.new('RGBA',T.size,col[:3]+(255,)); c.putalpha(m.point(lambda v:int(v*(col[3] if len(col)>3 else 255)/255))); T.alpha_composite(c)
    solid(8,10,so,(0,0,0,140)); solid(0,0,so,outer); solid(0,0,si,inner)
    d.text((x,y),t,font=f,fill=fill,anchor='lm')
    L.alpha_composite(T,(int(cx-T.width/2),int(cy-T.height/2)))
def chara(name,h,rot=0,ow=10,flip=False):
    im=Image.open(f'cut/{name}.png').convert('RGBA')
    al=im.getchannel('A').point(lambda v:0 if v<50 else v); im.putalpha(al)
    if flip: im=ImageOps.mirror(im)
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(0,0)); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
from PIL import ImageOps
def still(name,w,h,fx=0.5,fy=0.5,r=24):
    im=Image.open(f'gb/{name}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-w)*fx); y=int((im.height-h)*fy); c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,r)); return c
def framed(img,rot=0,pad=12):
    o=Image.new('RGBA',(img.width+2*pad,img.height+2*pad),(0,0,0,0)); wb=Image.new('RGBA',o.size,WHITE); wb.putalpha(rmask(o.width,o.height,30)); o.alpha_composite(wb); o.alpha_composite(img,(pad,pad))
    return o.rotate(rot,resample=Image.BICUBIC,expand=True) if rot else o
def title(L,t,num=None,col=GREEN):
    d=ImageDraw.Draw(L); 
    if num: pill(L,540,250,num,30,col,WHITE,30)
    kf(L,t,92,350,col,inner=WHITE,outer=col,si=0,so=0) if False else kf(L,t,92,345,WHITE,inner=col,outer=WHITE,si=14,so=24)
def card(L,box,outline=GREEN,fill=(255,255,255,245)):
    ImageDraw.Draw(L).rounded_rectangle(box,32,fill=fill,outline=outline,width=5)
def save(name,*Ls): compose(*Ls).convert('RGB').save(OUT+name)
CR=layer(); text(CR,'© Studio Ghibli',20,800,1560,GRAY)
# ---------- 00 thumbnail ----------
P=layer()
for f,rot,cx in [(U+'0c729ed3-image.webp',-6,385),(U+'ae693571-image.webp',6,695)]:
    im=Image.open(f).convert('RGBA'); h=370; im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    paste(P,framed(im,rot,10),cx,480)
T=layer(); d=ImageDraw.Draw(T)
pill(T,540,700,'保存版',40,RED,WHITE,40)
kf(T,'ジブリIMAX上映',100,820,WHITE,inner=NAVY)
kf(T,'まとめ',200,990,YEL,si=18,so=32)
text(T,'耳をすませば ＆ 借りぐらしのアリエッティ',38,900,1140,NAVY,10)
items=['日程','特典','チケット','おすすめ席','魅力']
x0=540-(len(items)*170+(len(items)-1)*12)/2
for k,it in enumerate(items):
    x=x0+k*182; d.rounded_rectangle((x,1195,x+170,1255),30,fill=(255,255,255,240),outline=GREEN,width=3)
    text(T,'✓ '+it if False else it,26,900,1225,GREEN,cx=x+85)
d.rounded_rectangle((410,232,670,298),33,fill=PINK,outline=WHITE,width=5); text(T,'ポスター配布あり',28,900,265,WHITE,cx=540)
C=layer()
for nm,h,r,x,y in [('mimi032',320,-6,230,1430),('majo013',300,5,540,1470),('karigurashi033',330,6,880,1440)]: paste(C,chara(nm,h,r),x,y)
CT=layer(); text(CT,'© Studio Ghibli',20,800,1650,GRAY)
save('00_thumbnail.png',P,C,T,CT)
# ---------- 01 dates ----------
L=layer(); d=ImageDraw.Draw(L); title(L,'いつから？','1｜日程')
card(L,(80,440,1000,760),NAVY)
pill(L,240,500,'IMAX上映',34,NAVY,WHITE,30)
kf(L,'10/23(金)〜11/2(月)',74,600,WHITE,inner=NAVY,si=10,so=18,maxw=880)
text(L,'たった11日間の期間限定！',38,900,700,RED)
card(L,(80,800,1000,1120),GREEN)
pill(L,320,860,'拡大上映＋Dolby Cinema',32,GREEN,WHITE,30)
kf(L,'10/30(金)〜11/12(木)',74,960,WHITE,inner=GREEN,si=10,so=18,maxw=880)
text(L,'全国47都道府県で上映',38,900,1060,DARK)
pill(L,540,1190,'IMAXで観るなら 11/2まで！',44,RED,WHITE,40)
C=layer()
for nm,h,r,x,y in [('mimi049',260,-5,200,1380),('karigurashi048',240,6,880,1390)]: paste(C,chara(nm,h,r),x,y)
save('01_dates.png',L,C,CR)
# ---------- 02 present ----------
L=layer(); d=ImageDraw.Draw(L); title(L,'入場者プレゼント','2｜特典',PINK)
for k,(f,rot,cx) in enumerate([(U+'0c729ed3-image.webp',-4,300),(U+'ae693571-image.webp',4,780)]):
    im=Image.open(f).convert('RGBA'); h=600; im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    paste(L,framed(im,rot,10),cx,750)
pill(L,540,1110,'IMAX限定 A3ポスター',50,PINK,WHITE,44)
text(L,'10/23(金)〜　数量限定・なくなり次第終了',36,900,1200,DARK,8)
pill(L,540,1290,'狙うなら初日がおすすめ！',38,RED,WHITE,36)
text(L,'※拡大上映・Dolby Cinemaの特典は未発表',24,800,1370,GRAY,6)
C=layer(); paste(C,chara('majo013',230,6),900,1450)
save('02_present.png',L,C,CR)
# ---------- 03 ticket ----------
L=layer(); d=ImageDraw.Draw(L); title(L,'チケットはいつから？','3｜チケット')
card(L,(80,450,1000,760),GREEN)
text(L,'多くの劇場で',40,900,520,DARK)
kf(L,'上映日の2日前 0時〜',78,620,WHITE,inner=GREEN,si=10,so=18,maxw=880)
text(L,'会員なら先行で買える劇場も',36,900,710,GRAY)
card(L,(80,800,1000,1080),RED)
pill(L,540,850,'例：初日に観るなら',34,RED,WHITE,30)
text(L,'10/23(金)の回',44,900,930,DARK)
d.polygon([(510,965),(570,965),(540,995)],fill=RED)
kf(L,'10/21(水) 0:00〜',70,1030,WHITE,inner=RED,si=10,so=18)
text(L,'※劇場によって異なります。各劇場の公式サイトで確認を',26,800,1130,GRAY,6)
C=layer()
for nm,h,r,x,y in [('karigurashi012',280,-6,220,1360),('mimi007',250,5,860,1370)]: paste(C,chara(nm,h,r),x,y)
save('03_ticket.png',L,C,CR)
# ---------- 04 seat ----------
L=layer(); d=ImageDraw.Draw(L); title(L,'どこの席がいい？','4｜おすすめ席')
card(L,(80,440,1000,1180),NAVY)
d.rounded_rectangle((160,480,920,520),20,fill=(60,70,100)); text(L,'SCREEN',28,900,500,WHITE,cx=540)
rows=12; cols=14; sx=170; sy=570; cw=52; ch=40
for r in range(rows):
    for c in range(cols):
        x=sx+c*cw+(18 if c>=7 else 0); y=sy+r*ch
        good=(5<=r<=8) and (4<=c<=9)
        d.rounded_rectangle((x,y,x+40,y+30),7,fill=RED if good else (215,212,205))
d.rounded_rectangle((sx+4*cw-8,sy+5*ch-8,sx+9*cw+18+48,sy+8*ch+38),14,outline=YEL,width=6)
text(L,'縦：真ん中より少し後ろ',40,900,1090,NAVY,cx=540)
text(L,'横：ど真ん中',40,900,1140,NAVY,cx=540)
pill(L,540,1240,'画面全体が見えて、音のバランスも◎',34,GREEN,WHITE,30)
text(L,'※一般的によく言われる目安です',24,800,1310,GRAY,6)
C=layer(); paste(C,chara('mimi032',300,-6),190,1420); paste(C,chara('karigurashi024',260,5),880,1430)
save('04_seat.png',L,C,CR)
# ---------- 05 appeal ----------
L=layer(); d=ImageDraw.Draw(L); title(L,'IMAXで観る魅力','5｜魅力')
pill(L,540,440,'ジブリ監修の4Kデジタルリマスター',38,NAVY,WHITE,36)
for k,(img,ttl,ln) in enumerate([('mimi047','耳をすませば',['夜の街・地球屋の空気感','「カントリー・ロード」の名場面も']),('karigurashi033','借りぐらしのアリエッティ',['小人目線で見る大きな世界','草花や水滴の色が鮮やかに'])]):
    y=500+k*420; card(L,(80,y,1000,y+390),GREEN)
    L.alpha_composite(still(img,400,330),(100,y+30))
    text(L,ttl,38,900,y+90,PINK,cx=760,maxw=440)
    for j,l in enumerate(ln): text(L,l,30,800,y+170+j*60,DARK,cx=760,maxw=440)
pill(L,540,1370,'大画面で没入感MAX！',46,RED,WHITE,40)
C=layer(); paste(C,chara('majo010',200,-6),160,1470); paste(C,chara('mimi049',220,6),920,1470)
save('05_appeal.png',L,C,CR)
# ---------- 06 follow ----------
Image.open(U+'6a98b9bb-image.jpg').convert('RGB').resize((W,H)).save(OUT+'06_follow.png')
print('ok')
