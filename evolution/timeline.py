"""Shot list.

A generation only contains 10-25 ticks of real action (the swarm strips the
field that fast), so the duration of each shot is derived from its own feast
window rather than picked in advance.  A playback-pace ramp gives the opening
generations a deliberate, readable speed and squeezes the later ones into a
montage; one global scale factor on that ramp makes the whole thing land
exactly on the frame budget.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Slot:
    gen: int
    start: int
    frames: int
    forage: int
    steps: int          # sim ticks replayed during `forage`

    @property
    def end(self) -> int:
        return self.start + self.frames

    @property
    def verdict(self) -> int:
        return self.frames - self.forage


@dataclass
class Schedule:
    slots: list[Slot]
    frame_to_slot: np.ndarray
    gens_end: int
    total: int
    fps: int

    def slot_at(self, f: int) -> Slot:
        return self.slots[int(self.frame_to_slot[min(f, self.gens_end - 1)])]


def build(feast: np.ndarray, fps: int, total_frames: int, outro_frames: int,
          pace_hi: float = 5.0, pace_lo: float = 2.4, tau: float = 10.0,
          verdict_frac: float = 0.62, min_slot: int = 30) -> Schedule:
    """`feast[g]` = ticks worth watching in generation g."""
    feast = np.asarray(feast, dtype=np.float64)
    n = len(feast)
    budget = total_frames - outro_frames

    pace = pace_lo + (pace_hi - pace_lo) * np.exp(-np.arange(n) / tau)

    def lay_out(k: float):
        forage = np.maximum(10, np.round(feast * pace * k)).astype(int)
        verdict = np.maximum(8, np.round(forage * verdict_frac)).astype(int)
        slot = np.maximum(min_slot, forage + verdict)
        verdict = slot - forage
        return forage, verdict, slot

    lo, hi = 0.05, 40.0
    for _ in range(70):
        mid = (lo + hi) / 2
        if lay_out(mid)[2].sum() < budget:
            lo = mid
        else:
            hi = mid
    forage, verdict, slot = lay_out((lo + hi) / 2)

    # Absorb the rounding residue in the longest shots so the pace ramp holds.
    drift = budget - int(slot.sum())
    order = np.argsort(-slot)
    i = 0
    while drift != 0:
        g = order[i % n]
        step = 1 if drift > 0 else -1
        if slot[g] + step >= min_slot:
            slot[g] += step
            verdict[g] += step
            drift -= step
        i += 1
        if i > 40 * n:
            break

    slots, cursor = [], 0
    for g in range(n):
        slots.append(Slot(gen=g, start=cursor, frames=int(slot[g]),
                          forage=int(forage[g]), steps=int(feast[g])))
        cursor += int(slot[g])

    f2s = np.zeros(cursor, dtype=np.int32)
    for s in slots:
        f2s[s.start:s.end] = s.gen

    return Schedule(slots=slots, frame_to_slot=f2s, gens_end=cursor,
                    total=total_frames, fps=fps)
