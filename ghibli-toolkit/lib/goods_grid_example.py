import sys
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
src=open(S+'kh2.py').read().split("if len(sys.argv)>1")[0].replace('/ghibli-keyholder/vol2/','/ghibli-kinro-saga/').replace("f'kh/big/{n}.jpg'","S+f'kinro/img/{n}.jpg'")
exec(src)
U='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/'
O='フライデーおじさん'; G='幻燈楼'; N='なんだろう'
ITEMS=[('img_catalog','公式グッズ','改訂版 公式図録','3,000'),('kyoto1',O,'ミニトートバッグ','3,850'),('10',O,'マスコットぬいぐるみ','3,300'),('09a',O,'Tシャツ（オレンジ）','3,300〜'),
('09b',O,'Tシャツ（白）','3,300〜'),('01',O,'クリアファイル','495'),('04',O,'ポストカード','330'),('02',O,'スケッチブック','1,320'),
('03a',O,'耐水ステッカー（全3種）','各660'),('21b',O,'フレークシール','990'),('21a',G,'フレークシール','990'),('18a',G+'・ラピュタ','クリアファイル パズーとシータ','495'),
('18e',G+'・ラピュタ','クリアファイル ロボット兵','495'),('18b',G+'・トトロ','クリアファイル トトロ','495'),('18h',G+'・トトロ','クリアファイル メイ','495'),('18c',G+'・もののけ姫','クリアファイル アシタカ','495'),
('18f',G+'・もののけ姫','クリアファイル サン','495'),('18d',G+'・千と千尋','クリアファイル 千と千尋','495'),('18g',G+'・千と千尋','クリアファイル 油屋','495'),
('11',N,'クリアファイル','440'),('12',N,'ステッカー','440'),('16',N,'付箋メモ','660')]
PAGES=[ITEMS[0:4],ITEMS[4:8],ITEMS[8:12],ITEMS[12:16],ITEMS[16:19],ITEMS[19:22]]
def head_layer(p):
    L=layer(); pill(L,W/2,330,f'金曜ロードショーとジブリ展 佐賀展グッズ　{p+1}/{len(PAGES)}',32,GREEN,WHITE,36)
    text(L,'※会場特設ショップは本展入場者のみ利用可',24,800,1515,(110,100,92),6); return L
def photo_card(path,w,rot,r=30,pad=14):
    im=Image.open(path).convert('RGB'); s=w/im.width; im=im.resize((w,int(im.height*s)),Image.LANCZOS).convert('RGBA'); h=im.height
    im.putalpha(rmask(w,h,r)); card=Image.new('RGBA',(w+2*pad+40,h+2*pad+40),(0,0,0,0))
    sh=Image.new('L',card.size,0); ImageDraw.Draw(sh).rounded_rectangle((20,28,20+w+2*pad,28+h+2*pad),r+pad,fill=90)
    card.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(10)))
    wb=Image.new('RGBA',(w+2*pad,h+2*pad),WHITE); wb.putalpha(rmask(w+2*pad,h+2*pad,r+pad)); card.alpha_composite(wb,(20,20)); card.alpha_composite(im,(20+pad,20+pad))
    return card.rotate(rot,resample=Image.BICUBIC,expand=True)
# thumbnail
fig=Image.open(S+'kinro/fig.png').convert('RGBA'); fig=fig.crop((0,0,fig.width,int(fig.height*0.83)))
al=fig.getchannel('A').point(lambda v:0 if v<90 else v); fig.putalpha(al)
def sticker(im,h,rot=0,ow=12):
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS); pad=ow*3
    big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>100 else 0).filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(A.filter(ImageFilter.GaussianBlur(12)).point(lambda v:int(v*0.35)))
    out.alpha_composite(sh,(6,10)); w=Image.new('RGBA',big.size,WHITE); w.putalpha(A); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
YEL=(246,176,40); RED=(214,58,52)
def gs(n,h,rot): 
    im=Image.open(S+f'kinro/cut/{n}.png').convert('RGBA'); return sticker(im,h,rot,ow=10)
P=layer()
pc=Image.open(U+'0fa04ca6-image.jpg').convert('RGB').crop((40,330,1614,1740)); pc.save(S+'kinro/pc.jpg')
paste(P,photo_card(S+'kinro/pc.jpg',780,-2,r=40,pad=16),W/2,620)
tl=sticker(Image.open(S+'kinro/title_cut.png').convert('RGBA'),190,-3,ow=12)
tl=tl.resize((1060,int(tl.height*1060/tl.width)),Image.LANCZOS)
T=layer(); d=ImageDraw.Draw(T); paste(T,tl,W/2,250)
# saga stamp
st=Image.new('RGBA',(330,330),(0,0,0,0)); sd=ImageDraw.Draw(st); sd.ellipse((10,10,320,320),fill=RED,outline=WHITE,width=10)
T2=layer(); text(T2,'佐賀',96,900,0,WHITE,0,cx=0)
from PIL import ImageFont
f=ImageFont.truetype(S+'fonts/jp900.woff',100); sd.text((165,140),'佐賀',font=f,fill=WHITE,anchor='mm'); f2=ImageFont.truetype(S+'fonts/jp900.woff',44); sd.text((165,232),'で開催！',font=f2,fill=WHITE,anchor='mm')
st=st.rotate(12,resample=Image.BICUBIC,expand=True); paste(T,st.resize((int(st.width*1.2),int(st.height*1.2))),860,760)
text(T,'11/3(火・祝)〜 佐賀県立美術館',42,900,935,DARK,10)
text(T,'会場限定グッズ',136,900,1075,RED,20,maxw=1000)
pill(T,W/2,1220,'全22点 まとめました！',54,GREEN,WHITE,52)
C=layer()
for n,h,r,cx,cy in [('10',250,-6,150,900),('09a',230,6,200,1560),('21b',230,-5,540,1610),('kyoto1',230,5,880,1570)]:
    paste(C,gs(n,h,r),cx,cy)
_f=BG.copy()
for _L in (P,T):
    _s=Image.new('RGBA',(W,H),(0,0,0,0)); _s.alpha_composite(_L.crop((0,0,W,H-120)),(0,120)); _f.alpha_composite(_s) if _L is P else None
_f.alpha_composite(C)
_s=Image.new('RGBA',(W,H),(0,0,0,0)); _s.alpha_composite(T.crop((0,0,W,H-120)),(0,120)); _f.alpha_composite(_s)
_f.convert('RGB').save(OUT+'00_thumbnail.png')
# info slide
L=layer(); d=ImageDraw.Draw(L)
pill(L,W/2,330,'開催概要',40,GREEN,WHITE,44)
text(L,'金曜ロードショーとジブリ展',60,900,450,GREEN,12,maxw=900); text(L,'佐賀展',76,900,550,GREEN,12)
d.rounded_rectangle((110,640,990,1330),40,fill=(255,255,255,245),outline=GREEN,width=5)
rows=[('会期','2026年11月3日(火・祝)','〜2027年2月14日(日)'),('会場','佐賀県立美術館','・佐賀県立博物館'),('時間','9:30〜18:00（最終入場17:00）','金・土・祝前日は20:00まで'),('休館','月曜日','（祝日は開館・年末年始休館あり）')]
for k,(a,b,c) in enumerate(rows):
    y=720+k*155; pill(L,230,y+20,a,32,ORANGE,WHITE,28); text(L,b,36,900,y,DARK,cx=640,maxw=560); text(L,c,28,800,y+52,(110,100,92),cx=640,maxw=560)
text(L,'※グッズショップは本展入場者のみ利用可',28,800,1390,(110,100,92),6)
compose(L).convert('RGB').save(OUT+'01_info.png')
for p,pg in enumerate(PAGES):
    cells=CELL if len(pg)>2 else [(290,900),(760,900)]
    compose(head_layer(p),*[item_layer(k,it,cells) for k,it in enumerate(pg)]).convert('RGB').save(OUT+f'{p+2:02d}_page.png')
Image.open(U+'6a98b9bb-image.jpg').convert('RGB').resize((W,H)).save(OUT+f'{len(PAGES)+2:02d}_follow.png')
print('ok')
