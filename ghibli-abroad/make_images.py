import json,re,html
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
exec(open(S+'loc/make.py').read())
db=json.load(open(S+'loc/ov_db.json'))
def P(q,k): return S+f"loc/ov/{q.replace(' ','_')}_{k}.jpg"
def cred(q,k):
    r=db[q][k]; lic=('CC0' if r['license']=='cc0' else 'CC '+r['license'].upper()+' '+r['license_version'])
    return re.sub(r'\s+',' ',html.unescape(r['creator'] or 'unknown')).strip(),lic,r['foreign_landing_url']
X0,X1,Y0,Y1,G=0,1080,0,1920,6
CW=(X1-X0-G)//2; CH=(Y1-Y0-G)//2
def cell(img,w,h,fx=.5,fy=.5,r=0):
    c=cover(img,w,h,fx,fy).convert('RGBA'); m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255); c.putalpha(m); return c
def pin(col,s=30):
    o=Image.new('RGBA',(s,int(s*1.35)),(0,0,0,0)); d=ImageDraw.Draw(o)
    d.ellipse((0,0,s,s),fill=col); d.polygon([(s*0.14,s*0.68),(s*0.86,s*0.68),(s/2,s*1.33)],fill=col); d.ellipse((s*0.32,s*0.32,s*0.68,s*0.68),fill=(255,253,249)); return o
def grid(imgs,center,acc,credit):
    L=paper()
    pos=[(X0,Y0),(X0+CW+G,Y0),(X0,Y0+CH+G),(X0+CW+G,Y0+CH+G)]
    for (p,fx,fy),(x,y) in zip(imgs,pos):
        c=cover(Image.open(p).convert('RGB'),CW,CH,fx,fy).convert('RGBA'); L.alpha_composite(c,(x,y))
    center(L)
    d=ImageDraw.Draw(L)
    band=Image.new('RGBA',(W,70),(0,0,0,0)); bd=ImageDraw.Draw(band)
    for yy in range(70): bd.line((0,yy,W,yy),fill=(0,0,0,int(140*yy/70)))
    L.alpha_composite(band,(0,H-70)); d=ImageDraw.Draw(L)
    l='　'.join(credit); sz=19
    while fi(sz).getlength(l)>1020: sz-=1
    ctext(d,(W/2,H-24),l,fi(sz,600),(240,236,230))
    return L
def label(en,jp,film,sub,acc):
    def f(L):
        cx,cy=(X0+X1)/2,(Y0+Y1)/2; fp=ImageFont.truetype(F+'NotoSerifJP.ttf',29); fp.set_variation_by_axes([700]); ff=fm(35)
        w=max(fp.getlength(jp)+46,ff.getlength('「'+film+'」'),fm(20,False).getlength(sub))+64; h=188
        box=Image.new('RGBA',(int(w),h),(0,0,0,0)); ImageDraw.Draw(box).rounded_rectangle((0,0,w-1,h-1),20,fill=(252,249,244,248),outline=acc+(255,),width=3)
        shadow(L,box,(int(cx-w/2),int(cy-h/2)),blur=16,off=(0,10),alpha=80); L.alpha_composite(box,(int(cx-w/2),int(cy-h/2)))
        d=ImageDraw.Draw(L); ctext(d,(cx,cy-66),en,fi(23,600),SUB,sp=3)
        tw=fp.getlength(jp); pn=pin(acc+(255,),23); L.alpha_composite(pn,(int(cx-(tw+32)/2),int(cy-28-pn.height/2-2)))
        d.text((cx-(tw+32)/2+32,cy-28),jp,font=fp,fill=INK,anchor='lm')
        ctext(d,(cx,cy+22),'「'+film+'」',ff,acc)
        ctext(d,(cx,cy+67),sub,fm(20,False),SUB)
    return f
def thumb_label(L):
    cx,cy=(X0+X1)/2,(Y0+Y1)/2; w,h=540,350
    box=Image.new('RGBA',(w,h),(0,0,0,0)); ImageDraw.Draw(box).rounded_rectangle((0,0,w-1,h-1),30,fill=(252,249,244,250),outline=ACC+(255,),width=3)
    shadow(L,box,(int(cx-w/2),int(cy-h/2)),blur=18,off=(0,12),alpha=90); L.alpha_composite(box,(int(cx-w/2),int(cy-h/2)))
    d=ImageDraw.Draw(L)
    ctext(d,(cx,cy-100),'Ghibli Trip',fs(80),ACC)
    ctext(d,(cx,cy-22),'実在する',fm(28,False),SUB,sp=10)
    ctext(d,(cx,cy+42),'ジブリの舞台',fm(66),INK,sp=3)
    ctext(d,(cx,cy+118),'—  海外編  —',fm(30,False),INK,sp=6)
G_=lambda n,fx=.5,fy=.5:(S+f'gb/{n}.jpg',fx,fy)
Q=lambda i:S+f'loc/q/{i:02d}.jpg'
def O(q,k):
    c,l,u=cred(q,k); return (P(q,k),c,l)
SL=[('Visby, Sweden','ヴィスビー（スウェーデン）','魔女の宅急便','コリコの町のモデルと言われる城壁の町',[(Q(1),.5,.5,'VisbyStar','CC0'),(Q(0),.42,.5,'Alexandru Baboş','CC BY 3.0')],[G_('majo024'),G_('majo038')],(122,150,190)),
('Stockholm, Sweden','ストックホルム（スウェーデン）','魔女の宅急便','ロケハンで訪れたと言われる旧市街',[(Q(2),.5,.5,'Julian Herzog','CC BY 4.0'),(Q(3),.5,.5,'OleNeitzel','CC BY 4.0')],[G_('majo014'),G_('majo036',.85)],(122,150,190)),
('Colmar, France','コルマール（フランス）','ハウルの動く城','町並みの参考にしたと言われる',[(Q(6),.4,.5,'DimiTalen','CC0'),(P('Colmar Petite Venise',7),.5,.5)+O('Colmar Petite Venise',7)[1:]],[G_('howl006'),G_('howl004')],(200,128,128)),
('Wales, UK','ウェールズ（イギリス）','天空の城ラピュタ','宮崎監督が訪れた炭鉱の町がヒントと言われる',[(Q(11),.5,.5,'Rosser1954','CC BY 4.0'),(P('Blaenavon',4),.5,.5)+O('Blaenavon',4)[1:]],[G_('laputa004'),G_('laputa002')],(120,150,110)),
('Adriatic Sea, Croatia','アドリア海（クロアチア）','紅の豚','作中の舞台はアドリア海',[(Q(9),.5,.5,'László Szalai','Public domain'),(P('Dubrovnik old town',5),.5,.5)+O('Dubrovnik old town',5)[1:]],[G_('porco002'),G_('porco001')],(90,150,165)),
('Jiufen, Taiwan','九份（台湾）','千と千尋の神隠し','モデルと噂されるが、ジブリは公式に明言していない',[(Q(15),.5,.5,'lumoplank','CC0'),(S+'loc/q/user_jiufen.jpg',.62,.5,None,None)],[G_('chihiro008'),G_('chihiro011')],(190,90,80))]
allcred=[]
for i,(en,jp,film,sub,reals,ghib,acc) in enumerate(SL,1):
    r1,r2=reals; imgs=[r1[:3],ghib[0],ghib[1],r2[:3]]
    allcred+=[f'{jp} {r[3]} ({r[4]})' for r in reals if r[3]]
    names=' , '.join(f'{r[3]} ({r[4]})' for r in reals if r[3])
    L=grid(imgs,label(en,jp,film,sub,acc),acc,[f'Photos: {names} / Wikimedia Commons','© Studio Ghibli'])
    L.convert('RGB').save(OUT+f'{i:02d}_{en.split(",")[0].split()[0].lower()}.png')
T=grid([(Q(2),.5,.5),G_('majo024'),G_('chihiro008'),(Q(15),.5,.5)],thumb_label,ACC,['Photos: Julian Herzog (CC BY 4.0) , lumoplank (CC0) / Wikimedia Commons','© Studio Ghibli'])
T.convert('RGB').save(OUT+'00_thumbnail.png')
open(OUT+'credits.txt','w').write('\n'.join(dict.fromkeys(allcred))+'\n')
print('ok')
