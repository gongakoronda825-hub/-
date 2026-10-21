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
P=layer(); paste(P,photo_card(U+'97812fdd-image.jpg',640,-3),W/2+20,520)
T=layer(); x,tw=text(T,'金曜ロードショーとジブリ展',50,900,950,DARK,10); d=ImageDraw.Draw(T)
for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,920,ex,980),fill=DARK,width=8)
text(T,'佐賀展',90,900,1070,GREEN,16); text(T,'グッズまとめ',110,900,1200,GREEN,16,maxw=980)
pill(T,W/2,1335,'2026.11.3(火・祝)〜 佐賀県立美術館',40,ORANGE,WHITE,44)
C=layer()
for k,(n,r,cx,cy) in enumerate([('10',-6,280,1560),('18b',5,560,1600),('09a',6,830,1560)]):
    paste(C,photo(n,230,r),cx,cy)
compose(P,C,T).convert('RGB').save(OUT+'00_thumbnail.png')
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
