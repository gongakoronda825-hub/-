# クレジット

TikTok の投稿文（キャプション）に次のクレジットを入れてください。

```
VOICEVOX:春日部つむぎ
```

| 素材 | 提供元 | 条件 |
|---|---|---|
| 場面写真 | スタジオジブリ公式サイト（場面写真） | 常識の範囲で自由に使用可 |
| ナレーション | VOICEVOX:春日部つむぎ | 動画内または説明文にクレジット表記が必要 |
| 効果音（ジャン！／和太鼓でドドン／キラッ） | 効果音ラボ https://soundeffect-lab.info/ | 商用利用可・クレジット不要。音源ファイルそのものの再配布は禁止のため、リポジトリには含めない（render.py が自動でダウンロード） |
| 絵文字 👇 | Twemoji | CC-BY 4.0 |
| フォント | Noto Sans JP | SIL Open Font License |

## 作り直し方

1. VOICEVOX Engine を `127.0.0.1:50021` で起動する
2. `python3 ghibli-video/narration.py` … `audio/narration.mp3` を作る
3. `python3 ghibli-video/render.py` … `output/ghibli_minor3.mp4` を作る
