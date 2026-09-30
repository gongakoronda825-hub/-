import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { KenBurns, Telop } from "../components";

// 2〜6秒：耳をすませば。2枚を Ken Burns でつなぐ
export const Mimi: React.FC = () => {
  const frame = useCurrentFrame();
  // 2枚目へのクロスフェード（約0.4秒）
  const second = interpolate(frame, [62, 74], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* 自転車を押す聖司 → 雫へ流す */}
      <KenBurns
        src="stills/mimi/mimi015.jpg"
        from={0}
        to={74}
        scale={[1.04, 1.12]}
        x={[42, 78]}
      />
      {/* 街を見下ろす二人。逆向きに流す */}
      <KenBurns
        src="stills/mimi/mimi029.jpg"
        from={62}
        to={129}
        scale={[1.06, 1.14]}
        x={[82, 52]}
        opacity={second}
      />
      <Telop
        lines={["あの夜道を、IMAXで。"]}
        top={1380}
        appearAt={12}
        fontSize={68}
      />
    </AbsoluteFill>
  );
};
