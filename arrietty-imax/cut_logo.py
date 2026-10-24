# 公式ポスターからタイトルロゴ・IMAXロゴを切り抜く（parts/*.png を作る）。部品は ghibli-toolkit/lib/logo_cut.py
# 使い方: python3 cut_logo.py <ポスター画像>   ※ opencv-python-headless が必要
# 切り取り範囲・色の条件はアリエッティIMAXポスター（1040×1471）用
import sys,os
HERE=os.path.dirname(os.path.abspath(__file__))+'/'; sys.path.insert(0,HERE+'../ghibli-toolkit/lib')
from PIL import Image
from logo_cut import cut,by_color,bright,either
P=Image.open(sys.argv[1])
# タイトル：ピンクの文字（上のほうの小さい花びらは捨てる）
cut(P,(150,1040,880,1340),by_color(lambda R,G,B:((R-G)>60)&(B>90)&(R>150)&((R-B)>-10)),HERE+'parts/title_cut.png',
    keep=lambda x,y,w,h,a:a>=70 and not (y<30 and a<400))
# IMAX：白い文字＋クリーム色のちょうちょ。黒いふち線まで含め、ちょうちょの模様の穴は埋める
cut(P,(90,90,950,400),either(bright(155,45),by_color(lambda R,G,B:(R>190)&(G>165)&(B>130)&(R-B<80)&(R>=G))),HERE+'parts/imax_cut.png',
    open_r=1,close_r=0,keep=lambda x,y,w,h,a:(y<60 and a>60 and h<40) or a>3000,grow=2,holes=900,left=18)
