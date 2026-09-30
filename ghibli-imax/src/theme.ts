import * as ZenOldMincho from "@remotion/google-fonts/ZenOldMincho";
import * as ZenKakuGothicNew from "@remotion/google-fonts/ZenKakuGothicNew";
import * as Yomogi from "@remotion/google-fonts/Yomogi";

// 画面に出る文字をすべて並べたもの。日本語の Google Fonts は約120個の
// unicode-range チャンクに分かれていて、全部読むと1書体で数百リクエストになる。
// ここに含まれる文字のチャンクだけを読む（文言を足したらここにも足す）。
const TEXT_MINCHO =
  "貸出カード日氏　名返却あの夜道を、IMAXで。小さな世界が、いちばん大きなスクリーンに。" +
  "『耳をすませば』『借りぐらしのアリエッティ』期間限定上映どっち観る？";
const TEXT_GOTHIC =
  "IMAX 10.23 4Kデジタルリマスター2026年10月23日（金）〜11月2日（月）全国のIMAX劇場" +
  "入場者プレゼント：IMAX劇場公開用ビジュアルポスター（A3）" +
  "10月30日（金）〜11月12日：全国47都道府県＋Dolby Cinemaにも拡大" +
  "コメントで教えて画像：スタジオジブリ公式サイトより";
const TEXT_HAND =
  "6.14佐伯ゆう6.287.2森川透7.168.20高梨みつ9.39.9小野寺薫9.23 ";

type FontModule = {
  getInfo: () => { unicodeRanges: Record<string, string> };
  loadFont: (
    style: "normal",
    options: {
      weights: string[];
      subsets: string[];
      ignoreTooManyRequestsWarning: boolean;
    },
  ) => { fontFamily: string };
};

const inRange = (cp: number, range: string) =>
  range.split(",").some((part) => {
    const [a, b] = part.trim().replace(/^U\+/i, "").split("-");
    if (a.includes("?")) {
      const lo = parseInt(a.replace(/\?/g, "0"), 16);
      const hi = parseInt(a.replace(/\?/g, "F"), 16);
      return cp >= lo && cp <= hi;
    }
    const lo = parseInt(a, 16);
    const hi = b ? parseInt(b, 16) : lo;
    return cp >= lo && cp <= hi;
  });

// チャンク名（"[12]" など）は型定義に無いので緩い型で受ける
const load = (font: unknown, weights: string[], text: string) => {
  const mod = font as FontModule;
  const ranges = mod.getInfo().unicodeRanges;
  const cps = [...new Set([...text].map((c) => c.codePointAt(0)!))];
  const subsets = Object.keys(ranges).filter((key) =>
    cps.some((cp) => inRange(cp, ranges[key])),
  );
  return mod.loadFont("normal", {
    weights,
    subsets,
    ignoreTooManyRequestsWarning: true,
  }).fontFamily;
};

// 見出し：Zen Old Mincho／情報：Zen Kaku Gothic New
// 図書カードの手書き欄だけ Yomogi を使う
export const mincho = load(ZenOldMincho, ["500", "700", "900"], TEXT_MINCHO);
export const gothic = load(
  ZenKakuGothicNew,
  ["400", "500", "700"],
  TEXT_GOTHIC,
);
export const hand = load(Yomogi, ["400"], TEXT_HAND);

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// TikTok の UI を避ける範囲。重要な文字はこの内側にだけ置く
export const SAFE = { top: 200, bottom: 200, left: 60, right: 150 };

export const STAMP_RED = "#C0302A";
export const PAPER = "#F3EAD3";

// テロップ共通の「白文字＋薄い影」
export const textShadow =
  "0 2px 6px rgba(0,0,0,0.45), 0 0 18px rgba(0,0,0,0.25)";
