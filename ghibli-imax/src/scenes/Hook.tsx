import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { PAPER, STAMP_RED, gothic, hand, mincho } from "../theme";

// スタンプが紙に当たるフレーム
export const STAMP_HIT = 18;

const CARD_W = 780;
const CARD_H = 1060;
const ROW_H = 86;
const DATE_COL = 170;

// 手書き欄（名前は架空）
const ENTRIES = [
  { out: "6.14", name: "佐伯 ゆう", back: "6.28", rot: -1.5 },
  { out: "7.2", name: "森川 透", back: "7.16", rot: 1 },
  { out: "8.20", name: "高梨 みつ", back: "9.3", rot: -0.5 },
  { out: "9.9", name: "小野寺 薫", back: "9.23", rot: 1.8 },
];
const STAMP_ROW = ENTRIES.length;
const ROWS = 9;

const Paper: React.FC = () => (
  <svg
    width={CARD_W}
    height={CARD_H}
    style={{ position: "absolute", inset: 0, borderRadius: 22 }}
  >
    <defs>
      <filter id="paper-noise">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.85"
          numOctaves="3"
          seed="7"
        />
        <feColorMatrix
          type="matrix"
          values="0 0 0 0 0.35  0 0 0 0 0.27  0 0 0 0 0.15  0 0 0 0.55 0"
        />
      </filter>
      <filter id="paper-fiber">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.012 0.08"
          numOctaves="2"
          seed="3"
        />
        <feColorMatrix
          type="matrix"
          values="0 0 0 0 0.45  0 0 0 0 0.36  0 0 0 0 0.2  0 0 0 0.35 0"
        />
      </filter>
      <radialGradient id="age" cx="50%" cy="45%" r="75%">
        <stop offset="55%" stopColor="#000" stopOpacity="0" />
        <stop offset="100%" stopColor="#8A6A2E" stopOpacity="0.32" />
      </radialGradient>
      <radialGradient id="stain" cx="80%" cy="88%" r="22%">
        <stop offset="0%" stopColor="#B8914A" stopOpacity="0.16" />
        <stop offset="100%" stopColor="#B8914A" stopOpacity="0" />
      </radialGradient>
    </defs>
    <rect width="100%" height="100%" fill={PAPER} />
    <rect width="100%" height="100%" filter="url(#paper-fiber)" opacity="0.5" />
    <rect
      width="100%"
      height="100%"
      filter="url(#paper-noise)"
      opacity="0.35"
    />
    <rect width="100%" height="100%" fill="url(#stain)" />
    <rect width="100%" height="100%" fill="url(#age)" />
  </svg>
);

const Stamp: React.FC<{ frame: number }> = ({ frame }) => {
  // 1.4 → 1.0 に加速しながら押し下ろす
  const t = interpolate(frame, [STAMP_HIT - 7, STAMP_HIT], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.quad),
  });
  // 当たった直後にわずかに沈み込んで戻る
  const squash = interpolate(
    frame,
    [STAMP_HIT, STAMP_HIT + 2, STAMP_HIT + 6],
    [0.96, 0.985, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const scale = frame < STAMP_HIT ? 1.4 - 0.4 * t : squash;
  const opacity =
    frame < STAMP_HIT - 7 ? 0 : frame < STAMP_HIT ? 0.35 + 0.5 * t : 0.9;
  const rotate = interpolate(t, [0, 1], [-14, -7]);
  const lift = frame < STAMP_HIT ? 1 - t : 0;

  const W = 440;
  const H = 140;
  return (
    <div
      style={{
        position: "absolute",
        left: 120,
        top: 0,
        width: W,
        height: H,
        transform: `scale(${scale}) rotate(${rotate}deg)`,
        opacity,
        filter: `drop-shadow(0 ${24 * lift}px ${30 * lift}px rgba(0,0,0,${0.35 * lift}))`,
        mixBlendMode: frame < STAMP_HIT ? "normal" : "multiply",
      }}
    >
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.7"
              numOctaves="2"
              seed="11"
              result="n"
            />
            <feColorMatrix
              in="n"
              type="matrix"
              values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -5 3.4"
              result="holes"
            />
            <feComposite in="SourceGraphic" in2="holes" operator="in" />
          </filter>
        </defs>
        <g filter="url(#ink)" fill="none" stroke={STAMP_RED}>
          <rect
            x="6"
            y="6"
            width={W - 12}
            height={H - 12}
            rx="14"
            strokeWidth="7"
          />
          <rect
            x="18"
            y="18"
            width={W - 36}
            height={H - 36}
            rx="8"
            strokeWidth="2.5"
          />
          <text
            x={W / 2}
            y={H / 2 + 27}
            textLength={W - 70}
            lengthAdjust="spacingAndGlyphs"
            textAnchor="middle"
            fill={STAMP_RED}
            stroke="none"
            style={{
              fontFamily: gothic,
              fontWeight: 700,
              fontSize: 78,
              letterSpacing: "0.04em",
            }}
          >
            IMAX 10.23
          </text>
        </g>
      </svg>
    </div>
  );
};

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();

  // 押した瞬間の揺れ（減衰）
  const since = frame - STAMP_HIT;
  const decay = since >= 0 ? Math.exp(-since / 4) : 0;
  const shakeX = since >= 0 ? Math.sin(since * 2.3) * 13 * decay : 0;
  const shakeY = since >= 0 ? Math.cos(since * 3.1) * 9 * decay : 0;

  // カードは最初からあり、ゆっくり寄っていく
  const settle = interpolate(frame, [0, 14], [1.03, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const push = interpolate(frame, [STAMP_HIT, 69], [1, 1.05], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const tableTop = 250;

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 50% 45%, #4A3A2A 0%, #2A2019 55%, #16110D 100%)",
      }}
    >
      <AbsoluteFill
        style={{
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${settle * push})`,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: (1080 - CARD_W) / 2 - 45,
            top: (1920 - CARD_H) / 2 - 20,
            width: CARD_W,
            height: CARD_H,
            borderRadius: 22,
            overflow: "hidden",
            transform: "rotate(-1.2deg)",
            boxShadow:
              "0 30px 60px rgba(0,0,0,0.45), 0 6px 14px rgba(0,0,0,0.3)",
          }}
        >
          <Paper />

          <div
            style={{
              position: "absolute",
              top: 70,
              left: 0,
              right: 0,
              textAlign: "center",
              fontFamily: mincho,
              fontWeight: 700,
              fontSize: 64,
              letterSpacing: "0.5em",
              color: "#3B3024",
              paddingLeft: "0.5em",
            }}
          >
            貸出カード
          </div>
          <div
            style={{
              position: "absolute",
              top: 172,
              left: 60,
              right: 60,
              borderTop: "3px double #7A6448",
            }}
          />

          {/* 表 */}
          <div
            style={{
              position: "absolute",
              top: tableTop,
              left: 50,
              right: 50,
              height: ROW_H * (ROWS + 0.7),
              border: "2px solid #8C7556",
            }}
          >
            {/* 見出し行 */}
            <div
              style={{
                height: ROW_H * 0.7,
                display: "flex",
                alignItems: "center",
                borderBottom: "2px solid #8C7556",
                fontFamily: mincho,
                fontWeight: 500,
                fontSize: 30,
                color: "#5A4834",
                letterSpacing: "0.2em",
              }}
            >
              <div style={{ width: DATE_COL, textAlign: "center" }}>貸出日</div>
              <div style={{ flex: 1, textAlign: "center" }}>{"氏\u3000名"}</div>
              <div style={{ width: DATE_COL, textAlign: "center" }}>返却日</div>
            </div>
            {Array.from({ length: ROWS }).map((_, i) => {
              const e = ENTRIES[i];
              return (
                <div
                  key={i}
                  style={{
                    height: ROW_H,
                    display: "flex",
                    alignItems: "center",
                    borderBottom:
                      i === ROWS - 1
                        ? "none"
                        : "1.5px solid rgba(122,100,72,0.55)",
                    fontFamily: hand,
                    fontSize: 42,
                    color: i % 2 ? "#2C3A63" : "#2E2A26",
                  }}
                >
                  <div
                    style={{
                      width: DATE_COL,
                      textAlign: "center",
                      transform: `rotate(${e?.rot ?? 0}deg)`,
                    }}
                  >
                    {e?.out}
                  </div>
                  <div
                    style={{
                      flex: 1,
                      textAlign: "center",
                      transform: `rotate(${-(e?.rot ?? 0)}deg)`,
                    }}
                  >
                    {e?.name}
                  </div>
                  <div
                    style={{
                      width: DATE_COL,
                      textAlign: "center",
                      transform: `rotate(${(e?.rot ?? 0) * 0.6}deg)`,
                    }}
                  >
                    {e?.back}
                  </div>
                </div>
              );
            })}
            {/* 縦罫 */}
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                left: DATE_COL,
                borderLeft: "1.5px solid rgba(122,100,72,0.7)",
              }}
            />
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                right: DATE_COL,
                borderLeft: "1.5px solid rgba(122,100,72,0.7)",
              }}
            />

            {/* 空いた行に押すスタンプ */}
            <div
              style={{
                position: "absolute",
                left: 0,
                top: ROW_H * 0.7 + ROW_H * STAMP_ROW + ROW_H / 2 - 70,
              }}
            >
              <Stamp frame={frame} />
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
