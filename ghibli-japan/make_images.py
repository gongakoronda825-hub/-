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
        im=Image.open(p).convert('RGB')
        if fx=='fit':
            bg=cover(im,CW,CH).filter(ImageFilter.GaussianBlur(28)); bg=Image.blend(bg,Image.new('RGB',bg.size,(250,246,240)),0.25)
            s_=CW/im.width; fg=im.resize((CW,int(im.height*s_)),Image.LANCZOS); bg.paste(fg,(0,int(CH*fy-fg.height/2))); c=bg.convert('RGBA')
        else: c=cover(im,CW,CH,fx,fy).convert('RGBA')
        L.alpha_composite(c,(x,y))
    center(L)
    d=ImageDraw.Draw(L)
    band=Image.new('RGBA',(W,70),(0,0,0,0)); bd=ImageDraw.Draw(band)
    for yy in range(70): bd.line((0,yy,W,yy),fill=(0,0,0,int(140*yy/70)))
    L.alpha_composite(band,(0,H-70)); d=ImageDraw.Draw(L)
    l='　'.join(credit); sz=17
    def nf(z):
        f=ImageFont.truetype(F+'NotoSerifJP.ttf',z); f.set_variation_by_axes([500]); return f
    while nf(sz).getlength(l)>1020: sz-=1
    ctext(d,(W/2,H-26),l,nf(sz),(240,236,230))
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
    ctext(d,(cx,cy+118),'—  日本編  —',fm(30,False),INK,sp=6)
G_=lambda n,fx=.5,fy=.5:(S+f'gb/{n}.jpg',fx,fy)
J=lambda i:S+f'loc/jp/{i:02d}.jpg'
J2=lambda i:S+f'loc/jp2/{i:02d}.jpg'
OUT='/home/user/-/ghibli-japan/'; os.makedirs(OUT,exist_ok=True)
SL=[('Sayama Hills, Saitama','狭山丘陵（埼玉・所沢）','となりのトトロ','トトロの森と呼ばれる、宮崎監督ゆかりの雑木林',[(J(3),.5,.5,'Asanagi','CC0'),(J(0),.5,.5,'Asanagi','CC0')],[G_('totoro019',.57),G_('totoro018',.28)],(110,150,100)),
('Dogo Onsen, Ehime','道後温泉本館（愛媛・松山）','千と千尋の神隠し','油屋のモデルのひとつと言われる老舗の湯',[(J(5),.5,.5,'Maarten Heerlien','CC BY 2.0'),(J(4),.55,.5,'松山市役所','CC BY 4.0')],[G_('chihiro011',.72),G_('chihiro048',.79)],(190,90,80)),
('Yakushima, Kagoshima','屋久島・白谷雲水峡（鹿児島）','もののけ姫','スタッフが森を取材したと言われる苔むす森',[(J(8),.5,.5,'MaedaAkihiko','CC0'),(J(11),.5,.5,'lumoplank','CC0')],[G_('mononoke010',.62),G_('mononoke023',.68)],(90,140,110)),
('Tomonoura, Hiroshima','鞆の浦（広島・福山）','崖の上のポニョ','宮崎監督が滞在し、構想のヒントになったと言われる港町',[(J(12),.55,.5,'Saigen Jiro','CC0'),(J2(2),.5,.5,'663highland','CC BY 2.5')],[G_('ponyo006',.35),G_('ponyo012',.5)],(90,150,180)),
('Seiseki-Sakuragaoka, Tokyo','聖蹟桜ヶ丘（東京・多摩）','耳をすませば','雫の住む町のモデルと言われる坂の町',[(J2(1),.5,.5,'多摩に暇人','CC BY 3.0'),(J(16),.5,.5,'多摩に暇人','CC BY 3.0')],[G_('mimi017',.5),G_('mimi047',.58)],(200,128,128)),
('Yamate, Yokohama','横浜・山手（神奈川）','コクリコ坂から','作中の舞台は横浜。港を見下ろす丘の町',[(J(18),.4,.5,'Yoshio Kohara','CC BY 3.0'),(J(22),.5,.5,'Fumihiko Ueno','CC BY 3.0')],[G_('kokurikozaka002',.5),G_('kokurikozaka003',.57)],(200,150,90))]
allcred=[]
for i,(en,jp,film,sub,reals,ghib,acc) in enumerate(SL,1):
    r1,r2=reals; imgs=[r1[:3],ghib[0],ghib[1],r2[:3]]
    allcred+=[f'{jp} {r[3]} ({r[4]})' for r in reals if r[3]]
    names=' , '.join(f'{r[3]} ({r[4]})' for r in reals if r[3])
    L=grid(imgs,label(en,jp,film,sub,acc),acc,([f'Photos: {names} / Wikimedia Commons'] if names else [])+['© Studio Ghibli'])
    L.convert('RGB').save(OUT+f'{i:02d}_{en.split(",")[0].split()[0].lower().replace('-','')}.png')
T=grid([(J(5),.5,.5),G_('chihiro011',.72),G_('ponyo012',.5),(J(12),.55,.5)],thumb_label,ACC,['Photos: Maarten Heerlien (CC BY 2.0) , Saigen Jiro (CC0) / Wikimedia Commons','© Studio Ghibli'])
T.convert('RGB').save(OUT+'00_thumbnail.png')
open(OUT+'credits.txt','w').write('\n'.join(dict.fromkeys(allcred))+'\n')
print('ok')
