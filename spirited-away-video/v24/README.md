# 24秒版

親フォルダの18秒版とは別に、24秒版の構成で作り直したもの。

- 冒頭：一礼するカーテンコール（元の音あり、3.3秒）
- 「累計動員90万人突破／千と千尋の神隠しの／舞台が帰ってきた！」の場面：背景は座って並ぶカーテンコールの映像（等速）＋拍手の効果音
- 中盤（元は舞台映像だった場所）：ポスター。日程とハクが見える画から千尋へ寄り、次の場面の最初の画につなげる。風鈴とそよ風
- 冒頭の文字の場面の「ドン」と、国内4都市の「トン×4」は消している

```
python3 sfx.py sfx.wav
python3 render.py poster.jpg intro.jpg clip1x <フォントのフォルダ> sfx.wav main.mp4   # clip1x は舞台映像を等速で書き出したコマ
python3 opening.py open open.wav main.mp4 spirited_away_tiktok_24s.mp4
```
