# 秋冬グッズの候補表（番号つき・画像1枚）を作る
# 使い方: python3 make_candidates.py <作業フォルダ(setup.shのW)> <fetch_candidates.pyの保存フォルダ>
import sys,json,os,textwrap,time,urllib.request
from PIL import Image,ImageDraw,ImageFont
W=sys.argv[1].rstrip('/')+'/'; O=sys.argv[2].rstrip('/')+'/'
PICK=[ # 秋冬らしい商品だけ手で選んだもの（ジャンル順）
'32645','32646','32647',                                   # 新作ボタン付ストール（10/24発売）
'21902773','21902138','21902139','21902656','21902659','21902504','21902505','21902506','21902415','21902418','21902660',  # ひざ掛け
'21902314','21902248','21902416','21902417','21902419','21902767',  # ロングブランケット・毛布
'21902058','21902753','21901793','21902199','21900441','21901918',  # お昼寝ケット・シュラフ
'21902421','21902422','21702085','21702087','21901889',            # スリーパー
'23485','23486',                                                   # 腹巻き
'22000562','22000584','22000608','22000645','22000646','22000643','22000644','22000650','22000661',  # スリッパ
'26110587','26110588','26110504','26110589','26110590','26110522','26110389','26110202','26110203','26110200','26110201','26110585',  # あったか靴下
'22301426','22301085','22000732','22000734','22000733','21902356','21902360','21902553',  # もこもこ雑貨
'43307','V47348',                                                  # カーディガン
'44396','44397','44399',                                           # 加湿器
'21902729','21902728','21902727','21902725','21902726','21902677','12300039','12300040','21902523',  # 秋・冬柄
'20100215','20100221','20100234','20100078','21902021',            # きのこ・10月
'22301708','22301709','22301686','22301687','22301688','22301689'] # 2027年カレンダー・手帳
items={i['id']:i for i in json.load(open(O+'items_all.json'))}
L=[items[k] for k in PICK]; os.makedirs(O+'img',exist_ok=True)
for n,i in enumerate(L,1):
    p=O+f'img/{n:03d}.jpg'
    if not os.path.exists(p):
        urllib.request.urlretrieve(urllib.request.Request('https://www.donguri-sora.com'+i['img'],headers={'User-Agent':'Mozilla/5.0'}).full_url,p) if False else open(p,'wb').write(urllib.request.urlopen(urllib.request.Request('https://www.donguri-sora.com'+i['img'],headers={'User-Agent':'Mozilla/5.0'})).read()); time.sleep(0.3)
json.dump(L,open(O+'items.json','w'),ensure_ascii=False,indent=1)
F=lambda s:ImageFont.truetype(W+'fonts/jp800.woff',s)
C,cw,ch=8,300,400; R=(len(L)+C-1)//C
im=Image.new('RGB',(C*cw,R*ch),'white'); d=ImageDraw.Draw(im)
for n,i in enumerate(L):
    x,y=n%C*cw,n//C*ch
    p=Image.open(O+f'img/{n+1:03d}.jpg').convert('RGB'); p.thumbnail((280,280)); im.paste(p,(x+10+(280-p.width)//2,y+10))
    d.rounded_rectangle((x+8,y+8,x+70,y+52),10,fill=(40,140,60)); d.text((x+39,y+30),str(n+1),font=F(28),fill='white',anchor='mm')
    nm=i['name'].replace('《10/24(土)午前10時発売予定》','【10/24発売】').replace('【Donguri Closet】','')
    d.multiline_text((x+10,y+295),'\n'.join(textwrap.wrap(nm,15)[:3]),font=F(17),fill='black',spacing=2)
    d.text((x+10,y+370),i['price'],font=F(22),fill=(220,90,0))
im.save(O+'candidates.jpg',quality=85); print(len(L),im.size)
