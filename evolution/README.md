# 自然選択シミュレーション → TikTok縦動画

形質「speed」を持つ生き物が餌を集め、生き残った個体だけが子を残す。
速いほど餌に早く着けるが、速いほど体力を食う ── そのせいで集団は
「最速」ではなく **ちょうどいい速さ** に収束する。その様子を1080x1920/60fps
の縦動画にする。

```
evolution/
  sim.py         遺伝シミュレーション本体（ML不使用）
  timeline.py    どの世代を何フレーム見せるかの尺配分
  render.py      フレーム合成（スプライト + ヒストグラム + 文字）
  sprites.py     4倍解像度で焼いたアンチエイリアス済みスプライト
  colors.py      speed → 色（青=遅い … 赤=速い）
  typography.py  日本語フォント（Noto Sans CJK JP Bold）
  audio.py       効果音・パッドをnumpyで生成
  main.py        CLI
```

## 使い方

```bash
pip install --break-system-packages numpy pillow imageio-ffmpeg

# 1枚だけ確認
python3 -m evolution.main preview --frame 0 1800 3700 --out output/preview.png

# 短縮版（14世代・22秒）で世代進行を確認
python3 -m evolution.main video --gens 14 --seconds 22 --out output/short.mp4

# 本番（60世代・70秒）
python3 -m evolution.main video --out output/evolution.mp4

# シードを変えれば毎回違う進化になる（省略時は毎回ランダム）
python3 -m evolution.main video --seed 12345 --out output/evolution_12345.mp4

# 量産
for i in $(seq 1 10); do
  python3 -m evolution.main video --out "output/evo_$i.mp4"
done
```

`--no-audio` で無音、`--keep-wav` で生成した音声を残す。
書き出しと同時に `<出力名>.json` に seed とパラメータと結果が残るので、
気に入った回は seed から完全に再現できる。

## モデル

各個体は `speed ∈ [0,1]` を1つだけ持つ。

| | |
|---|---|
| 移動量/tick | `v_min + speed * (v_max - v_min)` |
| 消費/tick | `c0 + c2 * speed²` （**2乗**なので速すぎは損） |
| 餌 | 1個 = エネルギー1。食べると消える（個体間で奪い合い） |
| 判定 | `energy < 0` → 死亡、`energy ≥ repro_energy` → 子を1体 |
| 遺伝 | 子は親の speed ± `N(0, mut_sigma)` |

消費が speed の2乗なので、利得（≒移動距離に比例）と釣り合う内点に最適値ができる。
「全員最速」にはならない。

## 現在のパラメータ（`sim.Params`）

```
generations 60   n_init 42   max_pop 64   n_food 170   steps 130
v_min 0.0030     v_max 0.0185      eat_radius 0.018
cost_base_total 0.65   cost_quad_total 2.60   repro_energy 2.30
mut_sigma 0.017   初期分布 Beta(2.0, 5.2) → 平均0.27
```

この設定での典型的な結果（seedを変えても安定）:

```
平均speed  0.27 → 0.60    ばらつき  0.15 → 0.04    収束はだいたい第30〜40世代
```

## 調整するなら

| やりたいこと | 触る場所 |
|---|---|
| 収束先を速く（赤寄り）に | `cost_quad_total` を下げる / `v_max` を上げる |
| 収束先を遅く（青寄り）に | `cost_quad_total` を上げる |
| 変化をもっと長く続かせる | `mut_sigma` を下げる（0.014〜0.017）、`generations` を増やす |
| 最後の色をもっと揃える | `mut_sigma` を下げる |
| 序盤をもっとゆっくり見せる | `timeline.build` の `pace_hi` |
| 終盤をもっと速く畳む | `timeline.build` の `pace_lo` |
| 死亡/出産の間を長く | `timeline.build` の `verdict_frac` |

`cost_quad_total` を極端に下げると「全部最速（赤一色）」になり、オチが壊れる。
中間値に落ち着いているかは書き出し時のログか `.json` の
`mean_speed_last` で確認する（0.5〜0.7 なら狙い通り）。

## 尺の考え方

1世代の「餌の奪い合い」は実は10〜25tickしかない（群れが一瞬で食べ尽くす）。
なので各ショットの長さは *見せ場のtick数 × 再生ペース* から決めて、
ペース全体を1つの係数でスケールして尺ちょうどに着地させている
（`timeline.build`）。ペースは序盤 約5フレーム/tick から終盤 約2.4へ落ちるので、
最初はじっくり、後半はモンタージュになる。

- 0〜8秒 … ルール3枚（速い=有利 / 速い=体力を食う / 集めた個体が子を残す）
- 〜60秒 … 世代が加速しながら進む。世代カウンター・個体数・平均speed・
  ヒストグラム（灰色は第1世代の形）は途切れず動き続ける
- 60〜70秒 … 第1世代 vs 最終世代の対比 → 収束値を大きく表示 → 最後は静止

## 描画について

全画面を2倍で描いて縮小する代わりに、**丸・リング・目などのスプライトを
4倍解像度で焼いてから縮小**して使い回している（`sprites.py`）。
エッジのアンチエイリアスは同じで、1フレーム約70msに収まる。
棒グラフは軸に平行なのでそのまま、文字はPillowが自前でアンチエイリアスする。
