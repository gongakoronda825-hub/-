import sys
src=open('kh2.py').read().split("if len(sys.argv)>1")[0]
src=src.replace("/ghibli-keyholder/vol2/","/ghibli-majo-goods/").replace("kh/big/","mg/big/").replace("khcut/","mg/cut/")
exec(src)
ITEMS=[(43,'フィギュア','ポーズがいっぱい ジジセット(6個入り)','7,920'),
(51,'バッグチャーム','ジジのスイーツぶらりん ビスケット','1,650'),
(53,'小物入れ','キキへのチョコレートケーキ','3,850'),
(11,'Donguri Closet 限定','ゴブラントート ジジとオキノ邸','5,500'),
(9,'壁かけ飾り','グーチョキパン店のパンリース','6,600'),
(31,'ぬいぐるみ','黒猫 ジジ M','4,400'),
(3,'食器','カップ&ソーサー(ピンク)','4,400'),
(19,'オルゴール','キキへの伝言','12,100')]
PAGES=[ITEMS[i:i+4] for i in range(0,len(ITEMS),4)]
def head_layer(p):
    L=layer(); pill(L,W/2,330,f'魔女の宅急便シリーズ　{p+1}/{len(PAGES)}',36,GREEN,WHITE,40)
    text(L,'どんぐり共和国 そらのうえ店',24,800,1515,(110,100,92),6); return L
def thumb_layers():
    P=layer(); xs=[200,435,670,900]
    top=[(51,-6),(31,5),(9,-5),(19,6)]; bot=[(3,6),(53,-5),(11,5),(43,-6)]
    for k,(n,r) in enumerate(top): paste(P,cut_sticker(n,240,330,r),xs[k],540+(30 if k%2 else 0))
    for k,(n,r) in enumerate(bot): paste(P,cut_sticker(n,240,280,r),xs[k],1365-(25 if k%2 else 0))
    T=layer()
    x,tw=text(T,'どんぐり共和国で買える',54,900,850,DARK,10)
    d=ImageDraw.Draw(T)
    for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,820,ex,880),fill=DARK,width=8)
    text(T,'魔女の宅急便',112,900,975,GREEN,16,maxw=980)
    text(T,'シリーズ紹介',96,900,1095,GREEN,16,maxw=980)
    return P,T
import re as _re
cs=open('imax.py').read(); exec(cs[cs.index('def chara('):cs.index('from PIL import ImageOps')]); from PIL import ImageOps
NOTE={43:'劇中のいろんなポーズのジジが6体セットに',51:'マグとビスケットを抱えたジジがゆらゆら',53:'キキへのチョコレートケーキが小物入れに',
11:'オキノ邸とジジをゴブラン織りで表現',9:'グーチョキパン店に飾られたパンのリース',31:'赤いリボンが目印の定番ジジ',
3:'バラとジジが描かれたピンクのカップ',19:'黒電話とジジのオルゴール'}
DECO=[('majo011',150,0,250,1450,'majo006',300,4,890,470),('majo043o',150,-6,230,1450,'majo018',200,5,880,460),
('majo016',230,-5,220,1440,'majo024',260,6,880,470),('majo040',240,4,250,1440,'majo013',230,-4,880,450),
('majo032o',150,6,230,1450,'majo017',250,5,880,470),('majo006',300,-3,210,1420,'majo011',140,0,820,420),
('majo017',240,-4,230,1440,'majo018',190,5,880,450),('majo013',240,5,230,1440,'majo040',230,-4,870,460)]
def page(i,item):
    n,cat,name,price=item; L=layer(); d=ImageDraw.Draw(L)
    pill(L,W/2,300,f'魔女の宅急便シリーズ　{i+1}/{len(ITEMS)}',36,GREEN,WHITE,40)
    paste(L,photo(n,600,[-2,2][i%2]),W/2,720)
    top=1070; d.rounded_rectangle((110,top,970,top+330),36,fill=(255,255,255,245),outline=GREEN,width=5)
    pill(L,W/2,top,cat,30,ORANGE,WHITE,30)
    text(L,name,54,900,top+100,GREEN,cx=W/2,maxw=800)
    text(L,NOTE[n],32,800,top+180,(110,100,92),cx=W/2,maxw=800)
    text(L,f'¥{price}（税込）',56,900,top+262,DARK,cx=W/2)
    text(L,'どんぐり共和国 そらのうえ店',24,800,1530,(110,100,92),6,cx=620)
    C=layer(); a,ah,ar,ax,ay,b,bh,br,bx,by=DECO[i]
    ah=min(ah,190); paste(C,chara(b,bh,br),bx,by); paste(C,chara(a,ah,ar),ax-20,1425+ah//2)
    return L,C
P,T=thumb_layers(); compose(P,T).convert('RGB').save(OUT+'00_thumbnail.png')
import glob,os
for f in glob.glob(OUT+'0[1-9]_page.png'): os.remove(f)
for i,it in enumerate(ITEMS):
    L,C=page(i,it); compose(L,C).convert('RGB').save(OUT+f'{i+1:02d}_item.png')
Image.open('/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/6a98b9bb-image.jpg').convert('RGB').resize((W,H)).save(OUT+'09_follow.png')
print('ok')
