import json,sys,textwrap
from PIL import Image,ImageDraw,ImageFont
W=sys.argv[1]
items=json.load(open(W+'/shop/items.json'))
F=lambda s:ImageFont.truetype(W+'/fonts/jp800.woff',s)
C,cw,ch=6,300,400
R=(len(items)+C-1)//C
im=Image.new('RGB',(C*cw,R*ch),'white');d=ImageDraw.Draw(im)
for n,i in enumerate(items):
    x,y=n%C*cw,n//C*ch
    p=Image.open(f'{W}/shopimg/{n+1:02d}.jpg').convert('RGB');p.thumbnail((280,280));im.paste(p,(x+10+(280-p.width)//2,y+10))
    d.rounded_rectangle((x+8,y+8,x+64,y+52),10,fill=(40,140,60));d.text((x+36,y+30),str(n+1),font=F(30),fill='white',anchor='mm')
    nm=i['name'].replace('耳をすませば','').replace('【Donguri Closet】','').strip()
    d.multiline_text((x+10,y+295),'\n'.join(textwrap.wrap(nm,14)[:3]),font=F(18),fill='black',spacing=2)
    d.text((x+10,y+368),i['price'],font=F(22),fill=(220,90,0))
im.save(W+'/candidates.jpg',quality=88)
