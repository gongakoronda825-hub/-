# 公式ポスター・画像からロゴや文字を「色」で切り抜く部品（初出：arrietty-imax/cut_logo.py）
# 使い方: from logo_cut import cut, by_color, bright   ※ opencv-python-headless が必要
#   cut(画像, (左,上,右,下), by_color(lambda R,G,B:(R-G)>60), minarea=70, out='parts/title_cut.png')
# 流れ：色でマスク → 連結成分で小さいゴミ（花びら・葉っぱ）を消す → 小さい穴だけ埋める → 切り抜き保存
# 切り抜いたあとは screen_fx.logo() で白フチ・影をつけて貼る。「〇〇ロゴ：公式ポスターより」と小さく表記
import os,numpy as np,cv2
from PIL import Image,ImageFilter
K=lambda r:cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
def by_color(f):
    # f(R,G,B)→bool配列 の条件でマスク（例：ピンクの文字 lambda R,G,B:((R-G)>60)&(B>90)&(R>150)）
    def m(a): return f(a[...,0],a[...,1],a[...,2])
    return m
def bright(minv=155,sat=45):
    # 白っぽい文字（白い英字ロゴなど）：明るくて色の薄いところ
    def m(a): return (a.min(2)>minv)&((a.max(2)-a.min(2))<sat)
    return m
def either(*ms): return lambda a:np.logical_or.reduce([m(a) for m in ms])
def comps(m,keep):
    n,lab,st,_=cv2.connectedComponentsWithStats(m.astype(np.uint8),8); out=np.zeros(m.shape,bool)
    for j in range(1,n):
        if keep(*st[j]): out|=lab==j
    return out
def smallholes(m,maxa):
    # 面積maxa未満の穴だけ埋める（Aの三角のような大きい穴は残す）
    n,lab,st,_=cv2.connectedComponentsWithStats((~m).astype(np.uint8),4)
    for j in range(1,n):
        x,y,w,h,a=st[j]
        if a<maxa and x>0 and y>0 and x+w<m.shape[1] and y+h<m.shape[0]: m=m|(lab==j)
    return m
def cut(img,box,mask,out,minarea=70,keep=None,open_r=0,close_r=1,grow=0,holes=0,left=0):
    # keep(x,y,w,h,面積)→bool で残す成分を細かく決められる（指定なしは minarea 以上）
    # open_r：細いゴミを消す／close_r：文字の切れ目をつなぐ／grow：黒いふち線まで含める／holes：埋める穴の最大面積／left：左はしを何px捨てるか
    t=img.convert('RGB').crop(box); a=np.asarray(t).astype(int); m=mask(a)
    if left: m[:,:left]=False
    if open_r: m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_OPEN,K(open_r))>0
    if close_r: m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,K(close_r))>0
    m=comps(m,keep or (lambda x,y,w,h,ar:ar>=minarea))
    if grow: m=cv2.dilate(m.astype(np.uint8),K(grow))>0
    if holes: m=smallholes(m,holes)
    if left: m[:,:left]=False
    r=t.convert('RGBA'); M=Image.fromarray((m*255).astype(np.uint8)); r.putalpha(M.filter(ImageFilter.GaussianBlur(0.7)))
    os.makedirs(os.path.dirname(out) or '.',exist_ok=True); r=r.crop(M.getbbox()); r.save(out); return r
