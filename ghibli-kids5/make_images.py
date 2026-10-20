S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
exec(open(S+'loc/make.py').read())
OUT='/home/user/-/ghibli-kids5/'
def rcard(img,w,h,fx=.5,fy=.5,r=36,b=12):
    ph=cover(img,w,h,fx,fy).convert('RGBA'); m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); ph.putalpha(m)
    o=Image.new('RGBA',(w+2*b,h+2*b),(0,0,0,0)); wb=Image.new('RGBA',o.size,(255,253,249,255)); mm=Image.new('L',o.size,0); ImageDraw.Draw(mm).rounded_rectangle((0,0,o.width-1,o.height-1),r+b,fill=255); wb.putalpha(mm); o.alpha_composite(wb); o.alpha_composite(ph,(b,b)); return o
def wrap(t,f,maxw):
    out=[];cur=''
    for c in t:
        if f.getlength(cur+c)>maxw and c not in '、。」！': out.append(cur);cur=c
        else: cur+=c
    out.append(cur); return out
X=500
FILMS=[('となりのトトロ','My Neighbor Totoro','1988年・86分','自然の中で遊ぶ楽しさを','森や田んぼで駆け回る姉妹の姿に、外で遊びたくなる気持ちが芽生える','totoro018',.3,(110,150,100)),
('崖の上のポニョ','Ponyo','2008年・101分','純粋な心が育てられる','5歳にしてお母さんにもポニョにも気遣いができる宗介。メロい男になる未来しか見えない','ponyo049',.5,(220,110,100)),
('魔女の宅急便',"Kiki's Delivery Service",'1989年・102分','「ありがとう」が人をつなぐ','町の人に支えられて成長するキキから、感謝の気持ちの大切さが伝わる','majo038',.75,(122,150,190)),
('天空の城ラピュタ','Castle in the Sky','1986年・124分','ワクワクが止まらない大冒険','空飛ぶ城を目指すハラハラの展開に、子どもも最後まで夢中になれる','laputa036',.5,(90,150,165)),
('千と千尋の神隠し','Spirited Away','2001年・125分','弱虫だった子が強くなる物語','怖がりの千尋が家族を救うため頑張る姿に、子どもも勇気をもらえる','chihiro045',.5,(190,90,80))]
for i,(jp,en,meta,catch,reason,st,fx,acc) in enumerate(FILMS,1):
    L=paper(); d=ImageDraw.Draw(L)
    ctext(d,(X,250),f'No.{i}',fi(64,600),acc)
    ctext(d,(X,330),'『'+jp+'』',fm(62),INK)
    ctext(d,(X,395),en+'　|　'+meta,fi(28,500),SUB,sp=1)
    c=rcard(Image.open(S+f'gb/{st}.jpg').convert('RGB'),860,560,fx); shadow(L,c,(int(X-c.width/2),450)); L.alpha_composite(c,(int(X-c.width/2),450))
    d=ImageDraw.Draw(L)
    f1=fm(58); tw=f1.getlength(catch); y=1140
    d.rounded_rectangle((X-tw/2-30,y-52,X+tw/2+30,y+52),52,fill=acc)
    ctext(d,(X,y),catch,f1,(255,253,249))
    f2=fm(36,False); ls=wrap(reason,f2,780)
    for k,l in enumerate(ls): ctext(d,(X,1260+k*62),l,f2,INK)
    ctext(d,(X,1560),'© Studio Ghibli',fi(24,500),SUB)
    L.convert('RGB').save(OUT+f'{i:02d}.png')
# thumbnail
L=paper(); d=ImageDraw.Draw(L)
ctext(d,(X,240),'for kids',fs(110),ACC)
ctext(d,(X,370),'子どもに見せたい',fm(64),INK,sp=4)
ctext(d,(X,470),'ジブリ映画',fm(96),INK,sp=4)
d.rounded_rectangle((X-150,540,X+150,640),50,fill=ACC); ctext(d,(X,590),'5選',fm(64),(255,253,249))
pos=[(270,850,-4),(730,850,4),(270,1170,3),(730,1170,-3),(500,1450,0)]
for (cx,cy,r),(jp,en,meta,catch,reason,st,fx,acc) in zip(pos,FILMS):
    c=rcard(Image.open(S+f'gb/{st}.jpg').convert('RGB'),400,260,fx,r=26,b=10).rotate(r,resample=Image.BICUBIC,expand=True)
    shadow(L,c,(int(cx-c.width/2),int(cy-c.height/2))); paste_c(L,c,cx,cy)
ctext(ImageDraw.Draw(L),(X,1640),'© Studio Ghibli',fi(24,500),SUB)
L.convert('RGB').save(OUT+'00_thumbnail.png')
Image.open('/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/6a98b9bb-image.jpg').convert('RGB').resize((W,H)).save(OUT+'06_follow.png')
print('ok')
