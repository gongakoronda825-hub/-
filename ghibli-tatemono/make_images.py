import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
U='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/'
OUT=os.path.dirname(os.path.abspath(__file__))+'/'
W,H=1080,1920; WHITE=(255,255,255)
KF=ImageFont.truetype(S+'fonts/keifont.ttf',124)

def sticker(im,h,rot=0,ow=10):
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS); pad=ow*3
    big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    A=big.getchannel('A').point(lambda v:255 if v>90 else 0).filter(ImageFilter.MaxFilter(ow*2+1)).filter(ImageFilter.GaussianBlur(1.2))
    out=Image.new('RGBA',big.size,(0,0,0,0)); sh=Image.new('RGBA',big.size,(0,0,0,0)); sh.putalpha(A.filter(ImageFilter.GaussianBlur(12)).point(lambda v:int(v*0.4)))
    out.alpha_composite(sh,(6,10)); w=Image.new('RGBA',big.size,WHITE); w.putalpha(A); out.alpha_composite(w); out.alpha_composite(big)
    return out.rotate(rot,resample=Image.BICUBIC,expand=True)
def cut(n): return Image.open(S+f'cut/{n}.png').convert('RGBA')
def paste(L,img,cx,cy): L.alpha_composite(img,(int(cx-img.width/2),int(cy-img.height/2)))

PRE={'4dc98609':OUT+'src/06_nopole.png'}  # ポールを消した写真（9:16済み）
def photo(f,fx,faces):
    if f in PRE: return Image.open(PRE[f]).convert('RGBA')
    im=Image.open(U+f+'-image.jpg').convert('RGBA')
    for x,y,h in faces: paste(im,sticker(cut('c_susu2'),h,0,ow=6),x,y)  # 人の顔はススワタリで隠す
    im=im.resize((int(im.width*H/im.height),H),Image.LANCZOS); x0=int((im.width-W)*fx)
    return im.crop((x0,0,x0+W,H))

def logo(L,t,y=330):
    global KF
    sz=124
    while ImageFont.truetype(S+'fonts/keifont.ttf',sz).getlength(t)>880: sz-=4
    KF=ImageFont.truetype(S+'fonts/keifont.ttf',sz)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((W/2-40,y+8),t,font=KF,fill=(0,0,0,170),anchor='mm',stroke_width=8,stroke_fill=(0,0,0,170))
    L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(L).text((W/2-40,y),t,font=KF,fill=WHITE,anchor='mm',stroke_width=5,stroke_fill=(70,70,70))

def inset(L,g,cx,cy,w=540,rot=3,box=None):
    im=Image.open(S+f'gb/{g}.jpg').convert('RGB')
    if box: im=im.crop(box)
    im=im.resize((w,int(im.height*w/im.width)),Image.LANCZOS)
    m=Image.new('L',im.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,im.width-1,im.height-1),22,fill=255)
    c=Image.new('RGBA',(im.width+24,im.height+24),(0,0,0,0)); ImageDraw.Draw(c).rounded_rectangle((0,0,c.width-1,c.height-1),30,fill=WHITE); c.paste(im,(12,12),m)
    s=Image.new('RGBA',(c.width+80,c.height+80),(0,0,0,0)); s.alpha_composite(Image.new('RGBA',c.size,(0,0,0,110)),(46,52)); s=s.filter(ImageFilter.GaussianBlur(14)); s.alpha_composite(c,(40,40))
    paste(L,s.rotate(rot,resample=Image.BICUBIC,expand=True),cx,cy)

def credit(L,t='© Studio Ghibli'):
    ImageDraw.Draw(L).text((W-150,1700),t,font=ImageFont.truetype(S+'fonts/jp800.woff',24),fill=WHITE,anchor='rs',stroke_width=3,stroke_fill=(0,0,0))

def place(L,n,h,cx,by,rot=0,keep=1.0,flip=False):
    """キャラだけを縁なしで置く（by=足元のy）。keep<1 で下側を切る"""
    im=cut(n); im.putalpha(im.getchannel('A').point(lambda v:0 if v<110 else v))
    if keep<1: im=im.crop((0,0,im.width,int(im.height*keep)))
    if flip: im=im.transpose(Image.FLIP_LEFT_RIGHT)
    im=im.resize((int(im.width*h/im.height),h),Image.LANCZOS).rotate(rot,resample=Image.BICUBIC,expand=True)
    sh=Image.new('RGBA',(im.width+60,im.height+60),(0,0,0,0)); a_=im.getchannel('A').point(lambda v:int(v*0.35))
    sh.paste((0,0,0,255),(36,40),a_); sh=sh.filter(ImageFilter.GaussianBlur(10))
    L.alpha_composite(sh,(int(cx-im.width/2-30),int(by-im.height-30))); L.alpha_composite(im,(int(cx-im.width/2),int(by-im.height)))

def scene(L,g,cx,cy,w):
    """風景の場面写真を縁なしで置く"""
    im=Image.open(S+f'gb/{g}.jpg').convert('RGBA'); im=im.resize((w,int(im.height*w/im.width)),Image.LANCZOS)
    sh=Image.new('RGBA',(im.width+80,im.height+80),(0,0,0,0)); sh.paste((0,0,0,120),(46,52,46+im.width,52+im.height)); sh=sh.filter(ImageFilter.GaussianBlur(14))
    L.alpha_composite(sh,(int(cx-im.width/2-40),int(cy-im.height/2-40))); L.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

# (写真, 横位置, 顔[(x,y,高さ)], ロゴ, [('c',キャラ,高さ,cx,足元y,回転,残す割合,反転) / ('s',場面,cx,cy,幅)])
SLIDES=[
 ('e1197088',0.5,[],'となりのトトロ',[('c','totoro044',330,330,1720,0,1.0,False)]),
 ('9e55a828',0.3,[(348,1140,96),(434,1222,96),(516,1148,96),(608,1230,88),(670,1248,88),(762,1272,88),(366,1300,80),(888,1174,96)],'千と千尋の神隠し',[('c','tc_chihiro027',300,560,1262,0,0.82,False)]),
 ('7531cbc0',0.5,[],'千と千尋の神隠し',[('c','tc_chihiro004',360,650,1000,0,1.0,False)]),
 ('77f2ed49',0.4,[(783,1087,160),(1092,1077,160)],'となりのトトロ',[('c','tc_satsuki',400,220,1160,0,1.0,False),('c','c_susu2',80,420,1100,0,1.0,False),('c','c_susu2',70,630,1095,0,1.0,True),('c','c_susu',90,520,860,-10,1.0,False)]),
 ('dd2fa721',0.15,[(296,1435,240)],'もののけ姫',[('c','mononoke009',640,820,1920,0,1.0,False)]),
 ('4dc98609',0.45,[],'となりのトトロ',[('c','c_chibitotoro',130,700,1210,0,1.0,False),('c','totoro018',480,800,1700,0,1.0,False)]),
 ('17a17976',0.5,[],'風立ちぬ',[('s','kazetachinu042',520,1530,760),('c','tt_nahoko',300,330,1105,0,1.0,False)]),
 ('ec8b4c93',0.5,[],'ハウルの動く城',[('c','tc_pan',420,440,930,0,1.0,False)]),
]
if __name__=='__main__':
    for i,(f,fx,faces,lg,items) in enumerate(SLIDES):
        L=photo(f,fx,faces)
        for it in items:
            if it[0]=='s': scene(L,*it[1:])
            else: place(L,*it[1:])
        credit(L); L.convert('RGB').save(OUT+f'{i+1:02d}_slide.png')
    Image.open(OUT+'../ghibli-toolkit/assets/follow.jpg').convert('RGB').resize((W,H)).save(OUT+f'{len(SLIDES)+1:02d}_follow.png')
    print('ok')
