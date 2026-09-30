import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { KenBurns, fade } from "../components";
import { SAFE, gothic, mincho, textShadow } from "../theme";

const GOLD = "#E8CF96";

type Item = {
  at: number;
  node: React.ReactNode;
  gap?: number;
};

// 10〜14秒：上映情報。文言は指示書どおり（改行位置だけ調整）
const ITEMS: Item[] = [
  {
    at: 10,
    node: (
      <div
        style={{
          fontFamily: mincho,
          fontWeight: 700,
          fontSize: 40,
          letterSpacing: "0.02em",
        }}
      >
        <div>『耳をすませば』</div>
        <div>『借りぐらしのアリエッティ』</div>
      </div>
    ),
  },
  {
    at: 18,
    gap: 44,
    node: (
      <div
        style={{
          fontFamily: gothic,
          fontWeight: 500,
          fontSize: 52,
          letterSpacing: "0.12em",
        }}
      >
        4Kデジタルリマスター
      </div>
    ),
  },
  {
    at: 26,
    gap: 14,
    node: (
      <div
        style={{
          fontFamily: mincho,
          fontWeight: 900,
          fontSize: 88,
          letterSpacing: "0.04em",
          color: GOLD,
        }}
      >
        IMAX 期間限定上映
      </div>
    ),
  },
  {
    at: 38,
    gap: 48,
    node: (
      <div style={{ fontFamily: gothic, fontWeight: 700, fontSize: 48 }}>
        2026年10月23日（金）〜11月2日（月）
      </div>
    ),
  },
  {
    at: 46,
    gap: 16,
    node: (
      <div
        style={{
          fontFamily: gothic,
          fontWeight: 500,
          fontSize: 44,
          letterSpacing: "0.08em",
        }}
      >
        全国のIMAX劇場
      </div>
    ),
  },
  {
    at: 58,
    gap: 80,
    node: (
      <div style={{ fontFamily: gothic, fontWeight: 500 }}>
        <div style={{ fontSize: 34, color: GOLD, letterSpacing: "0.1em" }}>
          入場者プレゼント：
        </div>
        <div style={{ fontSize: 42, marginTop: 8 }}>
          IMAX劇場公開用ビジュアルポスター（A3）
        </div>
      </div>
    ),
  },
  {
    at: 70,
    gap: 48,
    node: (
      <div style={{ fontFamily: gothic, fontWeight: 500 }}>
        <div style={{ fontSize: 34, color: GOLD, letterSpacing: "0.04em" }}>
          10月30日（金）〜11月12日：
        </div>
        <div style={{ fontSize: 42, marginTop: 8 }}>
          全国47都道府県＋Dolby Cinemaにも拡大
        </div>
      </div>
    ),
  },
];

export const Info: React.FC = () => {
  const frame = useCurrentFrame();
  const rule = fade(frame, 34, 14);
  return (
    <AbsoluteFill style={{ backgroundColor: "#0D0B09" }}>
      {/* 背景：上に耳すま、下にアリエッティを暗めに敷く */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 1080,
          height: 960,
        }}
      >
        <KenBurns
          src="stills/mimi/mimi020.jpg"
          from={0}
          to={129}
          scale={[1.02, 1.08]}
          x={[70, 78]}
        />
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 960,
          width: 1080,
          height: 960,
        }}
      >
        <KenBurns
          src="stills/arrietty/karigurashi002.jpg"
          from={0}
          to={129}
          scale={[1.08, 1.02]}
          x={[40, 50]}
        />
      </div>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(12,10,8,0.72) 0%, rgba(12,10,8,0.78) 45%, rgba(12,10,8,0.9) 50%, rgba(12,10,8,0.78) 55%, rgba(12,10,8,0.72) 100%)",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: SAFE.right,
          top: 360,
          textAlign: "center",
          color: "#FFFFFF",
          textShadow,
          lineHeight: 1.45,
        }}
      >
        {ITEMS.map((item, i) => {
          const o = fade(frame, item.at, 12);
          const y = interpolate(o, [0, 1], [14, 0]);
          return (
            <React.Fragment key={i}>
              {i === 3 ? (
                <div
                  style={{
                    margin: "44px auto 0",
                    width: 520 * rule,
                    height: 2,
                    background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
                  }}
                />
              ) : null}
              <div
                style={{
                  marginTop: item.gap ?? 0,
                  opacity: o,
                  transform: `translateY(${y}px)`,
                }}
              >
                {item.node}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
