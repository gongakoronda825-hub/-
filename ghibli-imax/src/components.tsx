import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { SAFE, mincho, textShadow } from "./theme";

type KenBurnsProps = {
  src: string;
  // 表示区間（シーン内フレーム）。この区間でズーム・パンが進む
  from: number;
  to: number;
  scale: [number, number];
  // 横長の場面写真を縦で切り出すので、左右位置（%）をゆっくり動かす
  x: [number, number];
  y?: number;
  opacity?: number;
  style?: React.CSSProperties;
};

// 場面写真をゆっくり寄せながら横に流す（Ken Burns）
export const KenBurns: React.FC<KenBurnsProps> = ({
  src,
  from,
  to,
  scale,
  x,
  y = 50,
  opacity = 1,
  style,
}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.sin),
  });
  const s = scale[0] + (scale[1] - scale[0]) * t;
  const px = x[0] + (x[1] - x[0]) * t;
  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity, ...style }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: `${px}% ${y}%`,
          transform: `scale(${s})`,
          transformOrigin: `${px}% ${y}%`,
        }}
      />
    </AbsoluteFill>
  );
};

// 0→1 のフェード（クランプ済み）
export const fade = (frame: number, start: number, length: number) =>
  interpolate(frame, [start, start + length], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

type TelopProps = {
  lines: string[];
  // 文字の縦位置（上端からの px）
  top: number;
  appearAt: number;
  fontSize?: number;
  // 明るい場面では下に半透明の黒帯を敷く
  band?: boolean;
};

// 白文字＋薄い影のテロップ。右側 150px と上下 200px を避けて置く
export const Telop: React.FC<TelopProps> = ({
  lines,
  top,
  appearAt,
  fontSize = 76,
  band = true,
}) => {
  const frame = useCurrentFrame();
  const o = fade(frame, appearAt, 14);
  const rise = interpolate(o, [0, 1], [18, 0]);
  const lineHeight = 1.55;
  const bandHeight = lines.length * fontSize * lineHeight + fontSize * 1.1;
  return (
    <AbsoluteFill>
      {band ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: top - fontSize * 0.55,
            height: bandHeight,
            background:
              "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.42) 22%, rgba(0,0,0,0.42) 78%, rgba(0,0,0,0) 100%)",
            opacity: o,
          }}
        />
      ) : null}
      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: SAFE.right,
          top,
          textAlign: "center",
          fontFamily: mincho,
          fontWeight: 700,
          fontSize,
          lineHeight,
          letterSpacing: "0.06em",
          color: "#FFFFFF",
          textShadow,
          opacity: o,
          transform: `translateY(${rise}px)`,
        }}
      >
        {lines.map((l) => (
          <div key={l}>{l}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
