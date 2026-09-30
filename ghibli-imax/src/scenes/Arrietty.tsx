import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { KenBurns, Telop } from "../components";

// 切手が拡大し始めるフレームと、全画面になるまでの長さ（約0.8秒）
const EXPAND_AT = 22;
const EXPAND_LEN = 24;

// 切手サイズの位置（右下。ただし右端150pxのUI帯には掛けない）
const STAMP = { x: 690, y: 1290, w: 210, h: 272 };

// 6〜10秒：借りぐらしのアリエッティ
export const Arrietty: React.FC = () => {
  const frame = useCurrentFrame();

  const pop = interpolate(frame, [3, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(1.6)),
  });
  const t = interpolate(frame, [EXPAND_AT, EXPAND_AT + EXPAND_LEN], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.85, 0, 0.15, 1),
  });
  const lerp = (a: number, b: number) => a + (b - a) * t;

  const left = lerp(STAMP.x, 0);
  const top = lerp(STAMP.y, 0);
  const width = lerp(STAMP.w, 1080);
  const height = lerp(STAMP.h, 1920);
  const pad = 12 * (1 - t);
  const hole = 4.5 * (1 - t);
  const tilt = 4 * (1 - t);

  // 全画面になった後は Ken Burns に引き継ぐ
  const kb = interpolate(frame, [EXPAND_AT + EXPAND_LEN, 129], [1, 1.07], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const second = interpolate(frame, [86, 98], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const perforation =
    hole > 0.2
      ? {
          WebkitMaskImage: `radial-gradient(circle, transparent ${hole}px, #000 ${hole + 0.5}px), linear-gradient(#000, #000)`,
          WebkitMaskSize: `16px 16px, calc(100% - 16px) calc(100% - 16px)`,
          WebkitMaskPosition: `-8px -8px, center`,
          WebkitMaskRepeat: "repeat, no-repeat",
        }
      : {};

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 60% 65%, #3A3526 0%, #1F1C15 60%, #12100C 100%)",
      }}
    >
      <div
        style={{
          position: "absolute",
          left,
          top,
          width,
          height,
          padding: pad,
          backgroundColor: `rgba(250,246,236,${1 - t})`,
          transform: `scale(${pop}) rotate(${tilt}deg)`,
          transformOrigin: "50% 50%",
          boxShadow: `0 ${14 * (1 - t)}px ${30 * (1 - t)}px rgba(0,0,0,${0.5 * (1 - t)})`,
          ...perforation,
        }}
      >
        <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
          {/* 翔の肩に乗るアリエッティ。小ささが一目で分かる */}
          <Img
            src={staticFile("stills/arrietty/karigurashi037.jpg")}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "58% 50%",
              transform: `scale(${kb})`,
              transformOrigin: "50% 45%",
            }}
          />
        </div>
      </div>

      {/* 庭の草むらに立つアリエッティ */}
      <KenBurns
        src="stills/arrietty/karigurashi022.jpg"
        from={86}
        to={129}
        scale={[1.05, 1.1]}
        x={[76, 84]}
        opacity={second}
      />

      <Telop
        lines={["小さな世界が、", "いちばん大きなスクリーンに。"]}
        top={330}
        appearAt={EXPAND_AT + EXPAND_LEN + 4}
        fontSize={56}
      />
    </AbsoluteFill>
  );
};
