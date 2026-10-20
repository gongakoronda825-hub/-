import sys
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
src=open(S+'kh2.py').read().split("if len(sys.argv)>1")[0].replace('/ghibli-keyholder/vol2/','/ghibli-kids5/')
exec(src)
cs=open(S+'imax.py').read(); exec(cs[cs.index('def chara('):cs.index('from PIL import ImageOps')]); from PIL import ImageOps
RED=(206,72,80)
def still(n,w,h,fx=.5,r=26,pad=12,rot=0):
    im=Image.open(f'gb/{n}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-w)*fx); y=(im.height-h)//2; c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,r))
    o=Image.new('RGBA',(w+2*pad+40,h+2*pad+40),(0,0,0,0)); sh=Image.new('L',o.size,0); ImageDraw.Draw(sh).rounded_rectangle((20,28,20+w+2*pad,28+h+2*pad),r+pad,fill=90)
    o.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(10))); wb=Image.new('RGBA',(w+2*pad,h+2*pad),WHITE); wb.putalpha(rmask(w+2*pad,h+2*pad,r+pad)); o.alpha_composite(wb,(20,20)); o.alpha_composite(c,(20+pad,20+pad))
    return o.rotate(rot,resample=Image.BICUBIC,expand=True)
FILMS=[('となりのトトロ','1988年','自然の中で遊ぶ楽しさを',['森や田んぼで駆け回る姉妹の姿に','外で遊びたくなる気持ちが芽生える'],'totoro018',.3,GREEN),
('崖の上のポニョ','2008年','純粋な心が育てられる',['5歳にしてお母さんにもポニョにも','気遣いができる宗介。','メロい男になる未来しか見えない'],'ponyo049',.5,RED),
('魔女の宅急便','1989年','「ありがとう」が人をつなぐ',['町の人に支えられて成長するキキから','感謝の気持ちの大切さが伝わる'],'majo038',.75,(70,110,170)),
('天空の城ラピュタ','1986年','ワクワクが止まらない大冒険',['見たあと「バルス！」を叫ぶ子が続出。','目玉焼きトーストを作ってと','せがまれるのは確定'],'laputa036',.5,(40,130,150)),
('千と千尋の神隠し','2001年','弱虫だった子が強くなる物語',['怖がりの千尋が家族を救うため','頑張る姿に、子どもも勇気をもらえる'],'chihiro045',.5,RED)]
CH=[('majo013',200,-6,170,1560),('mimi032',190,6,830,1570),('karigurashi033',190,5,830,1570)]
for i,(jp,yr,catch,lines,st,fx,col) in enumerate(FILMS,1):
    L=layer(); d=ImageDraw.Draw(L)
    pill(L,W/2,300,f'子どもに見せたいジブリ　{i}/5',34,GREEN,WHITE,40)
    text(L,jp,76,900,410,col,12,maxw=900); text(L,f'（{yr}公開）',28,800,475,(110,100,92),6)
    paste(L,still(st,820,500,fx,rot=[-2,2][i%2]),W/2,790)
    top=1080; d.rounded_rectangle((90,top,990,top+330),36,fill=(255,255,255,245),outline=GREEN,width=5)
    pill(L,W/2,top,catch,40,ORANGE,WHITE,36)
    for k,l in enumerate(lines): text(L,l,38,800,top+105+k*62-(31 if len(lines)==2 else 0)+ (20 if len(lines)==2 else 0),DARK,cx=W/2,maxw=840)
    text(L,'© Studio Ghibli',22,800,1450,(110,100,92),6)
    C=layer(); a,b=[('majo013','mimi032'),('karigurashi033','majo010'),('mimi049','karigurashi012'),('majo010','mimi013'),('karigurashi024','majo013')][i-1]
    paste(C,chara(a,190,-6),200,1560); paste(C,chara(b,180,6),820,1565)
    compose(C,L).convert('RGB').save(OUT+f'{i:02d}.png')
# thumbnail
P=layer()
for (n,fx,cx,cy,r) in [('totoro018',.3,320,500,-5),('ponyo049',.5,760,520,5),('majo038',.75,320,1310,4),('chihiro045',.5,760,1330,-4),('laputa036',.5,540,1560,0)]:
    paste(P,still(n,380,250,fx,rot=r),cx,cy)
T=layer()
x,tw=text(T,'子どもに見せたい',58,900,800,DARK,10); d=ImageDraw.Draw(T)
for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,770,ex,830),fill=DARK,width=8)
text(T,'ジブリ映画',120,900,930,GREEN,16,maxw=980)
pill(T,W/2,1080,'5選',64,ORANGE,WHITE,60)
compose(P,T).convert('RGB').save(OUT+'00_thumbnail.png')
print('ok')
