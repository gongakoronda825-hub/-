# ghibli-imax

『耳をすませば』『借りぐらしのアリエッティ』4Kデジタルリマスター IMAX上映の TikTok 告知動画（Remotion）。

- 完成物：`out/ghibli_imax.mp4`（1080×1920、30fps、15秒、**音声なし**。BGM は TikTok アプリ内で付ける）
- 場面写真：スタジオジブリ公式サイトの公開画像のみ。選定理由は `public/stills/SELECTED.md`

## 使い方

```sh
npm i
npm run dev                          # Remotion Studio で確認
npx remotion still scene-hook out/hook.png --frame=21   # シーン単体の静止画
npm run render                       # out/ghibli_imax.mp4 を書き出す
```

コンポジション：`GhibliImax`（本編）と、確認用の `scene-hook` / `scene-mimi` / `scene-arrietty` / `scene-info` / `scene-cta`。

## 構成

| 秒 | シーン | ファイル |
|---|---|---|
| 0〜2 | 図書カードに「IMAX 10.23」のスタンプ | `src/scenes/Hook.tsx` |
| 2〜6 | 耳をすませば（Ken Burns ＋ クロスフェード） | `src/scenes/Mimi.tsx` |
| 6〜10 | アリエッティ（切手サイズ → 0.8秒で全画面） | `src/scenes/Arrietty.tsx` |
| 10〜14 | 上映情報 | `src/scenes/Info.tsx` |
| 14〜15 | 「どっち観る？」＋クレジット | `src/scenes/Cta.tsx` |

シーン間は 0.3 秒のクロスフェード（`src/Root.tsx`）。重要な文字は上下200px・右150pxに置かない（`SAFE`、`src/theme.ts`）。

## フォント

`@remotion/google-fonts` で Zen Old Mincho（見出し）、Zen Kaku Gothic New（情報）、Yomogi（図書カードの手書き欄）を読む。
日本語フォントは約120個のチャンクに分かれているので、`src/theme.ts` の `TEXT_*` に並べた文字を含むチャンクだけを読んでいる。
**画面の文言を変えたら `TEXT_*` にもその文字を足すこと**（足さないとその字だけ別書体になる）。

## プロキシ環境で書き出すとき

HTTPS プロキシ越しの環境（クラウドのサンドボックスなど）では Remotion の headless Chrome が Google Fonts を取れない。
`scripts/chrome-with-proxy.sh` を使うとプロキシを渡せる（プロキシの CA は `~/.pki/nssdb` に登録しておく）。

```sh
npx remotion render GhibliImax out/ghibli_imax.mp4 --browser-executable=scripts/chrome-with-proxy.sh
```

通常の環境では不要。

## 投稿時のメモ

- キャプション例：「耳すまとアリエッティがIMAXに…！10/23から期間限定🎬 どっち観る？」
- ハッシュタグ例：#ジブリ #耳をすませば #借りぐらしのアリエッティ #IMAX
