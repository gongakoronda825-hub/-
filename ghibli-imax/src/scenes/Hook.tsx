import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { PAPER, STAMP_RED, gothic, hand, mincho } from "../theme";

// スタンプが紙に当たるフレーム
export const STAMP_HIT = 18;

const CARD_W = 780;
const CARD_H = 1060;
const TABLE_TOP = 222;
const HEAD_H = 60;
const ROW_H = 76;
const ROWS = 10;
const OUT_COL = 132;
const BACK_COL = 168;

const INK = "#2B2622";
const LINE = "rgba(52,44,38,0.78)";
const HAND_INK = "#1F1F26";
const DATE_INK = "#34323D";

// 書名と借りた人（どちらも架空）
const BOOK_TITLE = "月夜の坂道";
const ENTRIES = [
  { out: "6/10", name: "佐伯 ゆう", back: "6.17", rot: -1.2 },
  { out: "6/19", name: "森川 透", back: "6.26", rot: 0.8 },
  { out: "7/2", name: "高梨 みつ", back: "7.09", rot: -0.4 },
  { out: "7/21", name: "小野寺 薫", back: "7.28", rot: 1.4 },
  { out: "8/15", name: "小森 はる", back: "8.22", rot: -0.9 },
];
// 次の空いた行にスタンプを押す
const STAMP_ROW = ENTRIES.length;

// 右上の蔵書印
const Seal: React.FC = () => (
  <div
    style={{
      position: "absolute",
      top: 30,
      right: 50,
      width: 74,
      height: 74,
      border: `4px solid ${STAMP_RED}`,
      borderRadius: 10,
      color: STAMP_RED,
      fontFamily: mincho,
      fontWeight: 900,
      fontSize: 28,
      lineHeight: 1.05,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      transform: "rotate(8deg)",
      opacity: 0.8,
      mixBlendMode: "multiply",
    }}
  >
    <span>図</span>
    <span>書</span>
  </div>
);

const Paper: React.FC = () => (
  <svg
    width={CARD_W}
    height={CARD_H}
    style={{ position: "absolute", inset: 0 }}
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

const STAMP_H = 124;

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
  const H = STAMP_H;
  return (
    <div
      style={{
        position: "absolute",
        left: 100,
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
            y={H / 2 + 24}
            textLength={W - 70}
            lengthAdjust="spacingAndGlyphs"
            textAnchor="middle"
            fill={STAMP_RED}
            stroke="none"
            style={{
              fontFamily: gothic,
              fontWeight: 700,
              fontSize: 70,
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
            borderRadius: 6,
            overflow: "hidden",
            transform: "rotate(-1.2deg)",
            boxShadow:
              "0 30px 60px rgba(0,0,0,0.45), 0 6px 14px rgba(0,0,0,0.3)",
          }}
        >
          <Paper />

          {/* 見出しと蔵書印 */}
          <div
            style={{
              position: "absolute",
              top: 44,
              left: 52,
              fontFamily: mincho,
              fontWeight: 700,
              fontSize: 46,
              letterSpacing: "0.08em",
              color: INK,
            }}
          >
            県立図書館貸出カード
          </div>
          <Seal />

          {/* 書名（手書き） */}
          <div
            style={{
              position: "absolute",
              top: 122,
              left: 52,
              right: 52,
              height: 64,
              borderBottom: `2px solid ${LINE}`,
              fontFamily: hand,
              fontSize: 46,
              color: HAND_INK,
              paddingLeft: 40,
              transform: "rotate(-0.4deg)",
            }}
          >
            {BOOK_TITLE}
          </div>

          {/* 表 */}
          <div
            style={{
              position: "absolute",
              top: TABLE_TOP,
              left: 52,
              right: 52,
              height: HEAD_H + ROW_H * ROWS,
              border: `2.5px solid ${LINE}`,
            }}
          >
            {/* 見出し行 */}
            <div
              style={{
                height: HEAD_H,
                display: "flex",
                alignItems: "center",
                borderBottom: `2px solid ${LINE}`,
                fontFamily: mincho,
                fontWeight: 700,
                fontSize: 28,
                color: INK,
                letterSpacing: "0.1em",
              }}
            >
              <div style={{ width: OUT_COL, textAlign: "center" }}>貸出日</div>
              <div style={{ flex: 1, textAlign: "center" }}>
                {"氏\u3000\u3000名"}
              </div>
              <div style={{ width: BACK_COL, textAlign: "center" }}>返却日</div>
            </div>
            {Array.from({ length: ROWS }).map((_, i) => {
              const e = ENTRIES[i];
              return (
                <div
                  key={i}
                  style={{
                    position: "relative",
                    height: ROW_H,
                    display: "flex",
                    alignItems: "center",
                    borderBottom:
                      i === ROWS - 1 ? "none" : `1.5px solid ${LINE}`,
                  }}
                >
                  {/* 貸出日：空欄は月/日の斜線だけ印刷されている */}
                  <div
                    style={{
                      width: OUT_COL,
                      textAlign: "center",
                      fontFamily: hand,
                      fontSize: 34,
                      color: HAND_INK,
                      transform: `rotate(${e?.rot ?? 0}deg)`,
                    }}
                  >
                    {e ? (
                      e.out
                    ) : (
                      <svg
                        width={40}
                        height={40}
                        style={{ verticalAlign: "middle" }}
                      >
                        <line
                          x1={30}
                          y1={6}
                          x2={10}
                          y2={34}
                          stroke={LINE}
                          strokeWidth={2}
                        />
                      </svg>
                    )}
                  </div>
                  <div
                    style={{
                      flex: 1,
                      paddingLeft: 36,
                      fontFamily: hand,
                      fontSize: 42,
                      letterSpacing: "0.12em",
                      color: HAND_INK,
                      transform: `rotate(${-(e?.rot ?? 0)}deg)`,
                    }}
                  >
                    {e?.name}
                  </div>
                  {/* 返却日は日付印で押した体裁 */}
                  <div
                    style={{
                      width: BACK_COL,
                      textAlign: "center",
                      fontFamily: gothic,
                      fontWeight: 700,
                      fontSize: 38,
                      letterSpacing: "0.02em",
                      color: DATE_INK,
                      opacity: 0.88,
                      transform: `rotate(${(e?.rot ?? 0) * 0.5}deg)`,
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
                left: OUT_COL,
                borderLeft: `2px solid ${LINE}`,
              }}
            />
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                right: BACK_COL,
                borderLeft: `2px solid ${LINE}`,
              }}
            />

            {/* 空いた行に押すスタンプ */}
            <div
              style={{
                position: "absolute",
                left: 0,
                top: HEAD_H + ROW_H * STAMP_ROW + ROW_H / 2 - STAMP_H / 2 + 16,
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
