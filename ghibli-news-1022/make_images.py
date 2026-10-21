import sys
S='/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/'
src=open(S+'kh2.py').read().split("if len(sys.argv)>1")[0].replace('/ghibli-keyholder/vol2/','/ghibli-news-1022/')
exec(src)
cs=open(S+'imax.py').read(); exec(cs[cs.index('def chara('):cs.index('from PIL import ImageOps')]); from PIL import ImageOps
RED=(206,72,80); GRAY=(110,100,92)
def block(L,y,title,rows,k_=1.0):
    # rows: list of (kind,text) kind: 'b' bold dark, 'n' normal, 's' small gray, 'o' orange accent
    sz={k:(int(v[0]*k_),v[1],v[2]) for k,v in {'b':(34,900,DARK),'n':(29,800,DARK),'s':(24,800,GRAY),'o':(32,900,ORANGE),'g':(30,900,GREEN)}.items()}
    hs=[sz[k][0]*1.5 for k,_ in rows]; h=int(70+sum(hs)+30)
    d=ImageDraw.Draw(L); d.rounded_rectangle((90,y,990,y+h),32,fill=(255,255,255,245),outline=GREEN,width=5)
    pill(L,W/2,y,title,int(34*min(k_,1.25)),GREEN,WHITE,32)
    yy=y+60
    for (k,t),hh in zip(rows,hs):
        f,w,c=sz[k]; text(L,t,f,w,yy+hh/2,c,cx=W/2,maxw=840); yy+=hh
    return y+h+50
def head(L,no,t):
    pill(L,W/2,250,f'10/22 最新ジブリニュース　{no}/5',30,ORANGE,WHITE,30)
    text(L,t,74,900,345,GREEN,12,maxw=900)
def st(C,items):
    for nm,h,r,x,y in items: paste(C,chara(nm,h,r),x,y)
def still(n,w,h,fx=.5,rot=0,r=26,pad=12):
    im=Image.open(S+f'gb/{n}.jpg').convert('RGB'); s=max(w/im.width,h/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS)
    x=int((im.width-w)*fx); y=(im.height-h)//2; c=im.crop((x,y,x+w,y+h)).convert('RGBA'); c.putalpha(rmask(w,h,r))
    o=Image.new('RGBA',(w+2*pad+40,h+2*pad+40),(0,0,0,0)); sh=Image.new('L',o.size,0); ImageDraw.Draw(sh).rounded_rectangle((20,28,20+w+2*pad,28+h+2*pad),r+pad,fill=90)
    o.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(10))); wb=Image.new('RGBA',(w+2*pad,h+2*pad),WHITE); wb.putalpha(rmask(w+2*pad,h+2*pad,r+pad)); o.alpha_composite(wb,(20,20)); o.alpha_composite(c,(20+pad,20+pad))
    return o.rotate(rot,resample=Image.BICUBIC,expand=True)
pages=[]
# 1 上映
L=layer(); head(L,1,'上映')
y=block(L,440,'IMAX上映（目玉！）',[('g','『耳をすませば』『借りぐらしのアリエッティ』'),('s','4Kデジタルリマスター'),('o','10/23(金)〜11/2(月)'),('n','全国のIMAX劇場で2作品同日公開'),('b','入場者プレゼント'),('n','IMAX限定ビジュアルポスター（A3）'),('s','※10/23からIMAX上映のみ・数量限定'),('b','拡大上映 10/30(金)〜11/12(木)'),('s','全国47都道府県＋Dolby Cinema')],1.3)
y=block(L,y,'上映延長',[('g','短編『魔女の谷の夜』'),('n','ジブリパーク ジブリの大倉庫「オリヲン座」'),('o','2027年6月まで延長！')],1.3)
C=layer(); st(C,[('mimi032',200,-6,150,1600),('karigurashi033',200,6,860,1600)]); pages.append((L,C))
# 2 舞台
L=layer(); head(L,2,'舞台『千と千尋の神隠し』')
y=block(L,440,'ワールドツアー2026-2028 千尋役7人',[('b','橋本環奈／上白石萌音／福地桃子'),('b','森莉那／井上和（乃木坂46）'),('b','豊嶋花／平澤宏々路'),('s','10/15発表')],1.25)
rows=[('o','台北　国家戯劇院　2026年12月〜2027年1月'),('n','東京　明治座　2027年3〜5月'),('n','愛知　御園座　2027年6月'),('n','大阪　梅田芸術劇場　2027年6〜7月'),('n','福岡　博多座　2027年7〜8月'),('n','札幌　hitaru　2027年8月'),('g','トロント 2027年5〜8月／LA 2027年9〜10月'),('g','ロンドン 2028年3〜7月')]
block(L,y,'日程',rows,1.2)
C=layer(); st(C,[('chihiro019',190,-6,150,1640),('chihiro022',190,6,860,1640)]); pages.append((L,C))
# 3 イベント
L=layer(); head(L,3,'イベント')
y=block(L,440,'ジブリパーク',[('g','秋のどんどこ祭り'),('o','10/30(金)〜11/22(日)')],1.45)
y=block(L,y,'『巨神兵東京に現わる』上映＆トーク',[('n','特撮美術監督・三池敏夫さん登壇／事前申込制'),('b','① 10/31(土) 16:00〜'),('n','福島・須賀川特撮アーカイブセンター'),('s','定員30名'),('b','② 11/8(日) 13:00〜14:15'),('n','高知県立美術館ホール'),('s','無料・先着順')],1.35)
C=layer(); st(C,[('totoro008',190,-6,150,1620),('totoro044',170,6,860,1630)]); pages.append((L,C))
# 4 展覧会
L=layer(); head(L,4,'展覧会')
y=block(L,440,'「禅とジブリ」京都展',[('o','開催中〜12/6(日)'),('n','京都市京セラ美術館 新館 東山キューブ'),('s','休館日：月曜')],1.4)
y=block(L,y,'「金曜ロードショーとジブリ展」佐賀展',[('o','11/3(火・祝)〜2027/2/14(日)'),('n','佐賀県立美術館・博物館'),('b','JR九州とコラボ'),('n','佐賀駅で島本須美さんの案内アナウンス放送中'),('n','JRで来場した先着15,000人に'),('n','オリジナルクリアファイルをプレゼント')],1.35)
C=layer(); st(C,[('majo013',180,-6,150,1640),('mimi049',180,6,860,1640)]); pages.append((L,C))
# 5 テレビ
L=layer(); head(L,5,'テレビ')
y=block(L,440,'東海テレビ',[('g','「また、会えたね！ジブリパーク」'),('n','毎週月曜 21:54〜'),('o','次回 10/26(月)')],1.5)
y=block(L,y,'補足',[('n','金曜ロードショーの10/23・10/30は'),('n','ジブリ作品の放送ではありません'),('s','10/23 ALWAYS 三丁目の夕日／10/30 ゴジラ-1.0')],1.4)
paste(L,still('totoro001',640,340,.5,-2),W/2,y+200)
C=layer(); st(C,[('totoro044',190,-6,170,1640),('ponyo021',170,6,860,1640)]); pages.append((L,C))
for i,(L,C) in enumerate(pages,1):
    text(L,'© Studio Ghibli',22,800,1545,GRAY,6)
    compose(C,L).convert('RGB').save(OUT+f'{i:02d}.png')
# thumbnail
cs2=open(S+'imax.py').read(); exec(cs2[cs2.index('def kf('):cs2.index('def chara(')].replace("KF,","S+'fonts/keifont.ttf',"))
YEL=(255,214,0); NAVY=(30,50,100)
P=layer()
for n,fx,cx,cy,r in [('mimi048',.5,280,300,-5),('chihiro011',.72,800,320,5),('totoro019',.57,280,1620,4),('karigurashi033',.5,800,1640,-4)]:
    paste(P,still(n,400,260,fx,r),cx,cy)
T=layer(); d=ImageDraw.Draw(T)
pill(T,W/2,640,'10/22',64,RED,WHITE,56)
st_=Image.new('RGBA',(190,190),(0,0,0,0)); ImageDraw.Draw(st_).ellipse((5,5,185,185),fill=YEL,outline=WHITE,width=9)
from PIL import ImageFont; ImageDraw.Draw(st_).text((95,95),'NEW',font=ImageFont.truetype(S+'fonts/lat900.woff',56),fill=RED,anchor='mm')
paste(T,st_.rotate(14,resample=Image.BICUBIC,expand=True),820,625)
kf(T,'最新ジブリニュース',112,780,YEL,inner=(20,20,20),si=16,so=28,maxw=1010)
chips=[('IMAX上映',GREEN),('千と千尋 舞台',RED),('どんどこ祭り',ORANGE),('展覧会',(70,110,170)),('テレビ',(140,90,160))]
rows=[chips[:2],chips[2:4],chips[4:]]
for r_,row in enumerate(rows):
    fp=fonts(900,58); ws=[tlen(t,fp)+80 for t,_ in row]; tot=sum(ws)+26*(len(row)-1); x=W/2-tot/2
    for (t,c),w in zip(row,ws): pill(T,x+w/2,975+r_*125,t,58,c,WHITE,40); x+=w+26
C=layer()
f=BG.copy()
for Lx in (P,C,T): f.alpha_composite(Lx)
f.convert('RGB').save(OUT+'00_thumbnail.png')
Image.open('/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/6a98b9bb-image.jpg').convert('RGB').resize((W,H)).save(OUT+'06_follow.png')
print('ok')
