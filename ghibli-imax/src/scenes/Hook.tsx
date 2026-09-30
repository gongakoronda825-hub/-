import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { STAMP_RED, gothic } from "../theme";

// スタンプが紙に当たるフレーム
export const STAMP_HIT = 18;

// 劇中の図書カードの画像（735×392）
const CARD_SRC = "stills/card/library_cards.jpg";
const SRC_W = 735;
const SRC_H = 392;

// 真ん中のカードの「月島 雫」の下の空いた行（元画像の座標）
const EMPTY_ROW = { x: 410, y: 224 };
// スタンプの横幅（元画像の px。行の幅に合わせる）
const STAMP_SRC_W = 136;

// カメラ：真ん中のカードに寄っていく
const FOCUS = { x: 415, y: 190 };
const FOCUS_ON_SCREEN = { x: 495, y: 930 };

const W = 440;
const H = 124;

type StampProps = {
  frame: number;
  // 画面上の中心位置と、画面上での横幅（px）
  x: number;
  y: number;
  width: number;
};

const Stamp: React.FC<StampProps> = ({ frame, x, y, width }) => {
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
  const scale = (frame < STAMP_HIT ? 1.4 - 0.4 * t : squash) * (width / W);
  const opacity =
    frame < STAMP_HIT - 7 ? 0 : frame < STAMP_HIT ? 0.35 + 0.5 * t : 0.9;
  const rotate = interpolate(t, [0, 1], [-10, -3]);
  const lift = frame < STAMP_HIT ? 1 - t : 0;

  return (
    <div
      style={{
        position: "absolute",
        left: x - W / 2,
        top: y - H / 2,
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
            strokeWidth="9"
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

  // 画面上の拡大率（元画像 1px → S px）。押すまでに寄り、その後もゆっくり寄る
  const approach = interpolate(frame, [0, STAMP_HIT - 2], [2.7, 3.5], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const S =
    approach *
    interpolate(frame, [STAMP_HIT, 69], [1, 1.05], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const left = FOCUS_ON_SCREEN.x - FOCUS.x * S;
  const top = FOCUS_ON_SCREEN.y - FOCUS.y * S;

  return (
    <AbsoluteFill style={{ backgroundColor: "#15110D" }}>
      {/* 背景：同じ画像をぼかして暗く敷く */}
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img
          src={staticFile(CARD_SRC)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "blur(28px) brightness(0.4)",
            transform: "scale(1.15)",
          }}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{ transform: `translate(${shakeX}px, ${shakeY}px)` }}
      >
        <Img
          src={staticFile(CARD_SRC)}
          style={{
            position: "absolute",
            left,
            top,
            width: SRC_W * S,
            height: SRC_H * S,
            WebkitMaskImage:
              "linear-gradient(180deg, transparent 0%, #000 9%, #000 91%, transparent 100%)",
          }}
        />
        <Stamp
          frame={frame}
          x={left + EMPTY_ROW.x * S}
          y={top + EMPTY_ROW.y * S}
          width={STAMP_SRC_W * S}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
