# たてもの園「大和屋本店」×コクリコ坂から（1枚画像・元写真の解像度で作り直し）
# 使い方: python3 make_kokuriko.py <作業フォルダ(setup.shのW)>
import sys
from PIL import Image,ImageFilter,ImageDraw,ImageFont,ImageChops
S=sys.argv[1].rstrip('/')+'/'; U='/root/.claude/uploads/e8d6fde2-cc10-5a5b-97f9-6bcb99a3b93e/'
OUT='/home/user/-/ghibli-tatemono/kokuriko_yamatoya.png'
P=Image.open(U+'084e440f-image.jpg').convert('RGBA')            # 元写真 1206x1608
# 右上：場面写真（俊がコロッケをくわえる）
sc=Image.open(U+'1b01c394-image.jpg').convert('RGB'); w=586; sc=sc.resize((w,int(sc.height*w/sc.width)),Image.LANCZOS)
P.alpha_composite(sc.convert('RGBA'),(566,171))
# 左：縦書きタイトル（白地を抜いて赤い文字だけ）
T=Image.open(U+'99bcb5ae-image.png').convert('RGB'); r,g,b=T.split()
A=ImageChops.subtract(r,g).point(lambda v:min(255,int(v*2.2))); T=T.convert('RGBA'); T.putalpha(A)
T=T.crop(A.point(lambda v:255 if v>40 else 0).getbbox()); h=610; T=T.resize((int(T.width*h/T.height),h),Image.LANCZOS)
P.alpha_composite(T,(int(128-T.width/2),319))
# 下：俊（自転車）と海の切り抜き
C=Image.open(S+'cut/kok_shunumi.png').convert('RGBA'); s=1.5
C=C.resize((int(C.width*s),int(C.height*s)),Image.LANCZOS); C=C.filter(ImageFilter.UnsharpMask(2,60,2))
P.alpha_composite(C,(67,904))
d=ImageDraw.Draw(P); f=ImageFont.truetype(S+'fonts/lat800.woff',24)
d.text((1180,1585),'© Studio Ghibli',font=f,fill=(255,255,255),anchor='rs',stroke_width=3,stroke_fill=(0,0,0))
P.convert('RGB').save(OUT); print(OUT,P.size)
