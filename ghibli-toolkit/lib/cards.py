import re,sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
F=S+'fonts/'
C='/home/user/-/notebook-crops/'
OUT='/home/user/-/notebook-cards/'
import os; os.makedirs(OUT,exist_ok=True)
names={1:('もののけ姫',''),2:('天空の城ラピュタ',''),3:('魔女の宅急便','(ホワイト)'),
4:('となりのトトロ','(ブルー)'),5:('魔女の宅急便',''),6:('となりのトトロ','(ベージュ)'),
7:('ゲド戦記',''),8:('紅の豚',''),9:('魔女の宅急便','(ピンク)'),10:('となりのトトロ',''),
11:('平成狸合戦ぽんぽこ',''),12:('耳をすませば','')}
groups=[[1,2,3,4],[5,6,7,8],[9,10,11,12]]
W,H=1080,1920
DARK=(60,52,45); GREEN=(46,125,62)
def fonts(w,size): return ImageFont.truetype(F+f'jp{w}.woff',size),ImageFont.truetype(F+f'lat{w}.woff',size)
def segs(text):
    return re.findall(r'[\x00-\x7f]+|[^\x00-\x7f]+',text)
def tlen(text,fp):
    return sum(fp[1 if s.isascii() else 0].getlength(s) for s in segs(text))
def tdraw(d,cx,cy,text,fp,fill):
    x=cx-tlen(text,fp)/2
    for s in segs(text):
        f=fp[1 if s.isascii() else 0]; d.text((x,cy),s,font=f,fill=fill,anchor='lm'); x+=f.getlength(s)
def sticker(img,h,angle):
    im=img.convert('RGBA'); im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
    pad=16
    base=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0))
    ImageDraw.Draw(base).rounded_rectangle((0,0,base.width-1,base.height-1),22,fill=(255,255,255,255))
    base.alpha_composite(im,(pad,pad))
    sh=Image.new('RGBA',(base.width+50,base.height+50),(0,0,0,0))
    m=Image.new('L',sh.size,0); ImageDraw.Draw(m).rounded_rectangle((25,31,25+base.width,31+base.height),22,fill=90)
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(10))); sh.alpha_composite(base,(25,25))
    return sh.rotate(angle,resample=Image.BICUBIC,expand=True)
bg0=Image.open('/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/5a0f7bc1-image.jpg').convert('RGBA')
big=fonts(900,40); small=fonts(800,22)
cx=[282,798]; cy=[540,1300]; angs=[-2,2,2,-2]
for gi,g in enumerate(groups,1):
    bg=bg0.copy()
    fr=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(fr).rectangle((34,34,W-34,H-34),outline=(255,255,255,255),width=7)
    bg.alpha_composite(fr)
    for k,i in enumerate(g):
        x=cx[k%2]; y=cy[k//2]
        st=sticker(Image.open(C+f'{i:02d}.png'),480,angs[k])
        bg.alpha_composite(st,(int(x-st.width/2),int(y-st.height/2)))
        title,sub=names[i]
        line2=('ロルバーン ポケット付メモ L '+sub).strip()
        lw=max(tlen(title,big),tlen(line2,small))+44
        top=y+st.height/2-10
        lab=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lab)
        d.rounded_rectangle((x-lw/2,top,x+lw/2,top+108),30,fill=(255,255,255,240),outline=GREEN,width=4)
        tdraw(d,x,top+38,title,big,GREEN); tdraw(d,x,top+80,line2,small,DARK)
        bg.alpha_composite(lab)
    bg.convert('RGB').save(OUT+f'card_{gi}.png')
