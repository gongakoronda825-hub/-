import React from "react";
import { Composition } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { Hook } from "./scenes/Hook";
import { Mimi } from "./scenes/Mimi";
import { Arrietty } from "./scenes/Arrietty";
import { Info } from "./scenes/Info";
import { Cta } from "./scenes/Cta";
import { FPS, HEIGHT, WIDTH } from "./theme";

// シーン間のクロスフェード（0.3秒）
const XF = 9;

// 各シーンは次のシーンとの重なり分（XF）だけ長く持たせる。
// 開始位置：0秒／2秒／6秒／10秒／14秒、全体で15秒（450フレーム）
const SCENES = [
  { id: "hook", C: Hook, frames: 2 * FPS + XF },
  { id: "mimi", C: Mimi, frames: 4 * FPS + XF },
  { id: "arrietty", C: Arrietty, frames: 4 * FPS + XF },
  { id: "info", C: Info, frames: 4 * FPS + XF },
  { id: "cta", C: Cta, frames: 1 * FPS },
];

const TOTAL =
  SCENES.reduce((s, x) => s + x.frames, 0) - XF * (SCENES.length - 1);

export const GhibliImax: React.FC = () => (
  <TransitionSeries>
    {SCENES.map(({ id, C, frames }, i) => (
      <React.Fragment key={id}>
        {i > 0 ? (
          <TransitionSeries.Transition
            presentation={fade()}
            timing={linearTiming({ durationInFrames: XF })}
          />
        ) : null}
        <TransitionSeries.Sequence durationInFrames={frames}>
          <C />
        </TransitionSeries.Sequence>
      </React.Fragment>
    ))}
  </TransitionSeries>
);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="GhibliImax"
      component={GhibliImax}
      durationInFrames={TOTAL}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
    {/* シーン単体の確認用 */}
    {SCENES.map(({ id, C, frames }) => (
      <Composition
        key={id}
        id={`scene-${id}`}
        component={C}
        durationInFrames={frames}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
    ))}
  </>
);
