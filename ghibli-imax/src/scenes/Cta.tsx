import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { KenBurns, fade } from "../components";
import { SAFE, gothic, mincho, textShadow } from "../theme";

// 14〜15秒：問いかけとクレジット
export const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const o = fade(frame, 2, 9);
  const s = interpolate(frame, [2, 14], [0.94, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const sub = fade(frame, 8, 9);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0D0B09" }}>
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
          src="stills/mimi/mimi029.jpg"
          from={0}
          to={39}
          scale={[1.1, 1.13]}
          x={[40, 44]}
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
          src="stills/arrietty/karigurashi037.jpg"
          from={0}
          to={39}
          scale={[1.1, 1.13]}
          x={[52, 56]}
        />
      </div>
      <AbsoluteFill style={{ backgroundColor: "rgba(12,10,8,0.68)" }} />

      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: SAFE.right,
          top: 720,
          textAlign: "center",
          color: "#FFFFFF",
          textShadow,
        }}
      >
        <div
          style={{
            fontFamily: mincho,
            fontWeight: 900,
            fontSize: 128,
            letterSpacing: "0.04em",
            opacity: o,
            transform: `scale(${s})`,
          }}
        >
          どっち観る？
        </div>
        <div
          style={{
            marginTop: 30,
            fontFamily: gothic,
            fontWeight: 700,
            fontSize: 60,
            letterSpacing: "0.08em",
            opacity: sub,
          }}
        >
          コメントで教えて
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: SAFE.right,
          bottom: SAFE.bottom + 40,
          textAlign: "center",
          fontFamily: gothic,
          fontWeight: 400,
          fontSize: 26,
          letterSpacing: "0.06em",
          color: "rgba(255,255,255,0.85)",
          textShadow,
        }}
      >
        画像：スタジオジブリ公式サイトより
      </div>
    </AbsoluteFill>
  );
};
