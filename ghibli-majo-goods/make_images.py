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
P,T=thumb_layers(); compose(P,T).convert('RGB').save(OUT+'00_thumbnail.png')
for p,pg in enumerate(PAGES):
    compose(head_layer(p),*[item_layer(k,it) for k,it in enumerate(pg)]).convert('RGB').save(OUT+f'{p+1:02d}_page.png')
print('ok')
