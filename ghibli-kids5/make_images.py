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
from PIL import ImageFont
FD=S+'fonts/'
def styled(parts,font,size,inner,si,so=14,maxw=860,shadow_col=(0,0,0,90)):
    f=ImageFont.truetype(FD+font,size)
    while sum(f.getlength(t) for t,_ in parts)>maxw: size-=4; f=ImageFont.truetype(FD+font,size)
    tw=int(sum(f.getlength(t) for t,_ in parts)); pad=so+si+20; th=int(size*1.5)+2*pad
    T=Image.new('RGBA',(tw+2*pad,th),(0,0,0,0)); y=th/2
    def lay(col,sw,dx=0,dy=0):
        m=Image.new('L',T.size,0); d=ImageDraw.Draw(m); x=pad+dx
        for t,_ in parts: d.text((x,y+dy),t,font=f,fill=255,anchor='lm',stroke_width=sw,stroke_fill=255); x+=f.getlength(t)
        m=m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)) if sw else m
        c=Image.new('RGBA',T.size,col[:3]+(255,)); c.putalpha(m.point(lambda v:int(v*(col[3] if len(col)>3 else 255)/255))); T.alpha_composite(c)
    lay(shadow_col,si+so,6,8); lay((255,255,255),si+so); 
    if si: lay(inner,si)
    d=ImageDraw.Draw(T); x=pad
    for t,c in parts: d.text((x,y),t,font=f,fill=c,anchor='lm'); x+=f.getlength(t)
    return T.crop(T.getbbox())
def logo(i):
    if i==1: return styled([('となりのトトロ',(232,80,122))],'mochiy-japanese.woff',104,(232,80,122),0)
    if i==2:
        O,L_,P=(236,168,72),(200,190,225),(228,80,130)
        return styled([('崖',O),('の',L_),('上',O),('の',L_),('ポニョ',P)],'keifont.ttf',112,(70,45,35),7)
    if i==3: return styled([('魔女の宅急便',(222,96,150))],'ZenOldMincho-Bold.ttf',100,(222,96,150),0,so=12)
    if i==4:
        a=styled([('天空の城',(46,158,120))],'dela-gothic-one.woff',50,(20,60,50),0,so=10)
        b=styled([('ラピュタ',(46,158,120))],'dela-gothic-one.woff',88,(20,60,50),6,so=12)
        o=Image.new('RGBA',(max(a.width,b.width),a.height+b.height-34),(0,0,0,0)); o.alpha_composite(a,(0,0)); o.alpha_composite(b,(int((o.width-b.width)*0.3),a.height-34)); return o
    if i==5: return styled([('千と千尋の神隠し',(255,255,255))],'reggae-one.woff',96,(90,45,130),8,so=10)
FILMS=[('となりのトトロ','1988年','自然の中で遊ぶ楽しさを',['森や田んぼで駆け回る姉妹の姿に','外で遊びたくなる気持ちが芽生える。','どんぐり拾いや虫探しが','いつもの何倍も楽しくなるはず'],'totoro018',.3,GREEN,'3歳ごろ〜','86分'),
('崖の上のポニョ','2008年','純粋な心が育てられる',['5歳にしてお母さんにもポニョにも','気遣いができる宗介。','メロい男になる未来しか見えない。','「好き」をまっすぐ伝える大切さも'],'ponyo049',.5,RED,'3歳ごろ〜','101分'),
('魔女の宅急便','1989年','「ありがとう」が人をつなぐ',['町の人に支えられて成長するキキから','感謝の気持ちの大切さが伝わる。','落ち込んでもまた飛べるようになる姿は','大人が見ても背中を押される'],'majo038',.75,(70,110,170),'5歳ごろ〜','102分'),
('天空の城ラピュタ','1986年','ワクワクが止まらない大冒険',['見たあと「バルス！」を叫ぶ子が続出。','目玉焼きトーストを作ってと','せがまれるのは確定。','友だちを信じる強さも自然と伝わる'],'laputa036',.5,(40,130,150),'6歳ごろ〜','124分'),
('千と千尋の神隠し','2001年','弱虫だった子が強くなる物語',['怖がりの千尋が家族を救うため','頑張る姿に、子どもも勇気をもらえる。','「挨拶」と「お礼」の大切さも','千尋の姿から学べる'],'chihiro045',.5,RED,'6歳ごろ〜','125分')]
CH=[('majo013',200,-6,170,1560),('mimi032',190,6,830,1570),('karigurashi033',190,5,830,1570)]
for i,(jp,yr,catch,lines,st,fx,col,age,mins) in enumerate(FILMS,1):
    L=layer(); d=ImageDraw.Draw(L)
    pill(L,W/2,300,f'将来子どもに見せたいジブリ　{i}/5',34,GREEN,WHITE,40)
    paste(L,logo(i),W/2,{4:412}.get(i,410)); text(L,f'（{yr}公開）',28,800,{4:518}.get(i,495),(110,100,92),6)
    paste(L,still(st,820,480,fx,rot=[-2,2][i%2]),W/2,800)
    top=1080; d.rounded_rectangle((90,top,990,top+400),36,fill=(255,255,255,245),outline=GREEN,width=5)
    pill(L,W/2,top,catch,40,ORANGE,WHITE,36)
    for k,l in enumerate(lines): text(L,l,36,800,top+82+k*56,DARK,cx=W/2,maxw=840)
    d.rounded_rectangle((W/2-190,top+300,W/2+190,top+360),30,fill=(236,244,236))
    text(L,'上映時間　'+mins,30,900,top+330,GREEN,cx=W/2)
    text(L,'© Studio Ghibli',22,800,1500,(110,100,92),6)
    C=layer(); a,b=[('totoro008','totoro044'),('ponyo021','ponyo033'),('majo013','majo010'),('laputa006','laputa048'),('chihiro019','chihiro022')][i-1]
    paste(C,chara(a,170,-6),190,1610); paste(C,chara(b,160,6),830,1615)
    compose(C,L).convert('RGB').save(OUT+f'{i:02d}.png')
# thumbnail
P=layer()
for (n,fx,cx,cy,r) in [('totoro018',.3,320,500,-5),('ponyo049',.5,760,520,5),('majo038',.75,320,1310,4),('chihiro045',.5,760,1330,-4),('laputa036',.5,540,1560,0)]:
    paste(P,still(n,380,250,fx,rot=r),cx,cy)
C=layer()
for nm,h,r,x,y in [('totoro044',150,-6,170,220),('ponyo021',150,6,540,190),('majo013',170,5,890,230),
('ponyo033',150,-5,170,1720),('chihiro019',170,5,540,1780),('totoro008',160,-6,880,1730)]:
    paste(C,chara(nm,h,r),x,y)
T=layer()
x,tw=text(T,'将来子どもに見せたい',58,900,800,DARK,10); d=ImageDraw.Draw(T)
for sx,ex in ((x-54,x-26),(x+tw+54,x+tw+26)): d.line((sx,770,ex,830),fill=DARK,width=8)
text(T,'ジブリ映画',120,900,930,GREEN,16,maxw=980)
pill(T,W/2,1080,'5選',64,ORANGE,WHITE,60)
compose(C,P,T).convert('RGB').save(OUT+'00_thumbnail.png')
print('ok')
