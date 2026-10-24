# 公式ポスターからタイトルロゴ・IMAXロゴを色で切り抜く（parts/*.png を作る）
# 使い方: python3 cut_logo.py <ポスター画像>   ※ opencv-python-headless が必要
# 切り取り範囲・色の条件はポスターごとに調整する（アリエッティIMAXポスター 1040×1471 用）
import sys,os,numpy as np,cv2
from PIL import Image,ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; P=Image.open(sys.argv[1]).convert('RGB')
K=lambda r:cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
def comps(m,keep):
    # 小さいゴミ（花びら・葉っぱ）を消す：連結成分ごとに残すか決める
    n,lab,st,_=cv2.connectedComponentsWithStats(m.astype(np.uint8),8); out=np.zeros(m.shape,bool)
    for j in range(1,n):
        if keep(*st[j]): out|=lab==j
    return out
def smallholes(m,maxa):
    # 小さい穴（ちょうちょの模様など）だけ埋める。Aの三角のような大きい穴は残す
    n,lab,st,_=cv2.connectedComponentsWithStats((~m).astype(np.uint8),4)
    for j in range(1,n):
        x,y,w,h,a=st[j]
        if a<maxa and x>0 and y>0 and x+w<m.shape[1] and y+h<m.shape[0]: m=m|(lab==j)
    return m
def save(img,m,name):
    a=img.convert('RGBA'); M=Image.fromarray((m*255).astype(np.uint8)); a.putalpha(M.filter(ImageFilter.GaussianBlur(0.7)))
    os.makedirs(HERE+'parts',exist_ok=True); a.crop(M.getbbox()).save(HERE+f'parts/{name}.png')
# タイトル（ピンクの文字）
t=P.crop((150,1040,880,1340)); a=np.asarray(t).astype(int); R,G,B=a[...,0],a[...,1],a[...,2]
m=((R-G)>60)&(B>90)&(R>150)&((R-B)>-10); m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,K(1))>0
save(t,comps(m,lambda x,y,w,h,a:a>=70 and not (y<30 and a<400)),'title_cut')
# IMAXロゴ（白い文字＋ちょうちょ）
t=P.crop((90,90,950,400)); a=np.asarray(t).astype(int); R,G,B=a[...,0],a[...,1],a[...,2]; mx=a.max(2); mn=a.min(2)
m=((mn>155)&((mx-mn)<45))|((R>190)&(G>165)&(B>130)&(R-B<80)&(R>=G)); m[:,:18]=False
m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_OPEN,K(1))>0; m=comps(m,lambda x,y,w,h,a:(y<60 and a>60 and h<40) or a>3000)
m=cv2.dilate(m.astype(np.uint8),K(2))>0; m=smallholes(m,900); m[:,:18]=False; save(t,m,'imax_cut')
