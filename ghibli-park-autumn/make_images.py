import sys; sys.argv=['x']
exec(open('kh.py').read())
exec(open('chars.py').read())
OUT='/home/user/-/ghibli-park-autumn/'
RED=(196,72,52); BROWN=(120,80,40); GRAY=(110,100,92)
def still(name,w,h,fx=0.5):
    im=Image.open(f'gb/{name}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    x=int((im.width-w)*fx); y=(im.height-h)//2; c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,22)); return c
def framed(img,rot=0,pad=10):
    o=Image.new('RGBA',(img.width+2*pad,img.height+2*pad),(0,0,0,0)); wb=Image.new('RGBA',o.size,WHITE); wb.putalpha(rmask(o.width,o.height,30)); o.alpha_composite(wb); o.alpha_composite(img,(pad,pad))
    return o.rotate(rot,resample=Image.BICUBIC,expand=True) if rot else o
# ---------- 00 thumbnail ----------
L=layer()
paste(L,framed(still('totoro030',400,240),-5),330,430)
paste(L,framed(still('porco007',400,240),5),770,455)
T=layer(); d=ImageDraw.Draw(T)
pill(T,W/2,660,'ジブリパーク',50,GREEN,WHITE,50)
text(T,'秋のどんどこ祭り',112,900,800,BROWN,18,maxw=900)
pill(T,W/2,950,'開催決定！',70,RED,WHITE,60)
text(T,'2026.10.30(金) 〜 11.22(日)',58,900,1090,DARK,12)
text(T,'野外上映会・トワイライト営業・初企画も！',38,900,1175,GREEN,10)
P=layer()
for nm,r,x,y,h in [('c_chibitotoro',8,250,1370,230),('c_susu',-8,830,1380,170),('c_kodama2',6,560,1400,190)]:
    paste(P,cut_sticker_png(nm,h,r) if False else None,0,0) if False else None
from PIL import ImageOps
def csticker(name,h,rot,ow=9):
    im=Image.open(f'cut/{name}.png').convert('RGBA'); im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=ow*3; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>60 else 0); o=A.filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(8)).point(lambda v:int(v*0.3)))
    out.alpha_composite(sh); w=Image.new('RGBA',big.size,(255,255,255,0)); w.putalpha(o); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
for nm,r,x,y,h in [('c_chibitotoro',8,230,1350,220),('c_kodama2',-6,540,1380,190),('c_susu',-8,850,1360,170)]:
    paste(P,csticker(nm,h,r),x,y)
f=compose(L,P,T)
for j,(nm,side,h) in enumerate([('totoro019','L',300),('totoro044','R',280)]):
    st=sticker(nm,h,side)
    if st.width>460: st=st.resize((460,int(st.height*460/st.width)),Image.LANCZOS)
    f.alpha_composite(st,(0 if j==0 else W-st.width,H-st.height+8))
f.convert('RGB').save(OUT+'00_thumbnail.png')
# ---------- 01 event list ----------
EV=[('10/30','金','ZIP-FM GHIBLI DAY with ジブリパーク',''),
('10/30','金','魔女の谷＆もののけの里 トワイライト営業','チケット必要'),
('10/31','土','子どもたちだけの“夜の”映画鑑賞会【初企画】','申込終了'),
('11/1','日','野外上映会＆コンサート『紅の豚』','申込終了'),
('11/7・8','土日','美術監督に学ぶ『背景美術の描き方』','事前申込'),
('11/8','日','長久手「警固祭り」の鉄砲隊がやってくる','どなたでも'),
('11/14・15','土日','タイルでカフェトレー作り','事前申込'),
('11/21・22','土日','トトロのぬいぐるみを作ろう【初企画】','事前申込')]
TAGC={'チケット必要':GREEN,'申込終了':(150,140,130),'事前申込':ORANGE,'どなたでも':(56,96,180)}
L=layer(); d=ImageDraw.Draw(L)
pill(L,W/2,320,'秋のどんどこ祭り イベント一覧',42,GREEN,WHITE,46)
y=420
for date,dow,title,tag in EV:
    d.rounded_rectangle((70,y,1010,y+118),26,fill=(255,255,255,245),outline=GREEN,width=3)
    d.rounded_rectangle((86,y+14,276,y+104),20,fill=BROWN)
    text(L,date,36 if len(date)<6 else 30,900,y+48,WHITE,cx=181); text(L,f'({dow})',22,800,y+84,WHITE,cx=181)
    tx=300; fp=fonts(900,32); sz=32
    while tlen(title,fp)>(690 if tag else 690): sz-=1; fp=fonts(900,sz)
    x0=tx; 
    for s_ in segs(title):
        f_=fp[1 if s_.isascii() else 0]; d.text((x0,y+(42 if tag else 59)),s_,font=f_,fill=DARK,anchor='lm'); x0+=f_.getlength(s_)
    if tag:
        tw=tlen(tag,fonts(800,22))+30; d.rounded_rectangle((tx,y+68,tx+tw,y+102),17,fill=TAGC[tag]); text(L,tag,22,800,y+85,WHITE,cx=tx+tw/2)
    y+=128
text(L,'※事前申込制のイベントはパークのチケットがなくても申込可',24,800,1462,GRAY,6)
compose(L).convert('RGB').save(OUT+'01_events.png')
# ---------- 02 pickup ----------
L=layer(); d=ImageDraw.Draw(L)
pill(L,W/2,320,'注目イベント',44,RED,WHITE,50)
PK=[('porco007','11/1(日)','野外上映会＆コンサート',['『紅の豚』を野外上映','主題歌の加藤登紀子さんが','コンサートに登場！']),
('majo011','10/30(金)','トワイライト営業',['魔女の谷ともののけの里が','19:00まで営業','夜のジブリパークを楽しめる']),
('totoro019','11/21・22','トトロのぬいぐるみ作り',['初企画のワークショップ','目を付けて綿を詰めて','世界に一つだけのトトロに'])]
y=400
for img,date,title,desc in PK:
    d.rounded_rectangle((70,y,1010,y+330),30,fill=(255,255,255,245),outline=GREEN,width=4)
    L.alpha_composite(still(img,400,290,0.5),(90,y+20))
    text(L,date,30,900,y+55,RED,cx=750)
    text(L,title,36,900,y+110,GREEN,cx=750,maxw=470)
    for k,line in enumerate(desc): text(L,line,27,800,y+170+k*45,DARK,cx=750,maxw=470)
    y+=355
text(L,'詳しくはジブリパーク公式サイトへ　© Studio Ghibli',24,800,1475,GRAY,6)
compose(L).convert('RGB').save(OUT+'02_pickup.png')
print('ok')
