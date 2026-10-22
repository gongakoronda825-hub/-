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

def photo(f,fx,faces):
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

# (写真, 横位置, 顔[(x,y,高さ)], ロゴ, 場面写真, 場面位置(cx,cy,回転), キャラ[(名前,高さ,回転,cx,cy)])
SLIDES=[
 ('e1197088',0.5,[],'となりのトトロ','totoro029',(720,820,4),[('totoro044',300,-4,330,1480)]),
 ('9e55a828',0.3,[(348,1140,96),(434,1222,96),(516,1148,96),(608,1230,88),(670,1248,88),(762,1272,88),(366,1300,80),(888,1174,96)],'千と千尋の神隠し','chihiro027',(700,800,-3),[('chihiro019',520,4,250,1430)]),
 ('7531cbc0',0.5,[],'千と千尋の神隠し','chihiro004',(680,820,3),[('tt_pig',360,-5,320,1460)]),
 ('77f2ed49',0.4,[(783,1087,160),(1092,1077,160)],'となりのトトロ','totoro014',(700,1350,-3),[('c_susu',200,-8,260,980),('c_susu2',150,10,880,560)]),
 ('dd2fa721',0.15,[(296,1435,240)],'もののけ姫','mononoke011',(640,820,3),[('mononoke009',380,-4,820,1460)]),
 ('4dc98609',0.45,[],'となりのトトロ','totoro004',(640,820,-3),[('totoro018',540,0,280,1400),('c_chibitotoro',230,6,820,1520)]),
 ('17a17976',0.5,[],'風立ちぬ','kazetachinu042',(660,1360,3),[('tt_nahoko',560,0,250,820)]),
 ('ec8b4c93',0.5,[],'ハウルの動く城','howl016',(660,780,-3),[('c_calcifer',300,6,280,1500)]),
]
if __name__=='__main__':
    for i,(f,fx,faces,lg,g,(icx,icy,ir),ch) in enumerate(SLIDES):
        L=photo(f,fx,faces); inset(L,g,icx,icy,rot=ir)
        for n,h,r,cx,cy in ch: paste(L,sticker(cut(n),h,r),cx,cy)
        logo(L,lg); credit(L); L.convert('RGB').save(OUT+f'{i+1:02d}_slide.png')
    Image.open(OUT+'../ghibli-toolkit/assets/follow.jpg').convert('RGB').resize((W,H)).save(OUT+f'{len(SLIDES)+1:02d}_follow.png')
    print('ok')
