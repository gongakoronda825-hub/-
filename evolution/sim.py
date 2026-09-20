"""Headless genetic simulation: natural selection on a single trait `speed`.

The whole evolutionary history is computed up-front (fast, no drawing), then the
renderer replays it.  That way the video length is a pure layout problem and the
run never falls apart half way through.

Model
-----
Every creature owns one gene: ``speed`` in [0, 1].

* movement per tick: ``v = v_min + speed * (v_max - v_min)``  -> faster creatures
  reach food sooner and cover more ground.
* energy cost per tick: ``c0 + c2 * speed**2``  -> quadratic, so "just go max
  speed" is a losing strategy.
* food is a fixed budget per generation and is *removed* when eaten, so the
  creatures genuinely compete with each other.

End of generation: energy < 0 -> death, energy >= repro_energy -> one child that
inherits the parent's speed plus a small mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

HIST_BINS = 26


@dataclass
class Params:
    # --- population -------------------------------------------------------
    generations: int = 60
    n_init: int = 42
    max_pop: int = 64
    min_pop: int = 14

    # --- world ------------------------------------------------------------
    n_food: int = 170
    steps: int = 130
    eat_radius: float = 0.018
    wander: float = 0.22          # heading jitter (radians, 1 sigma)
    body_r: float = 0.0155        # bodies push apart instead of stacking
    tail_steps: int = 5           # beats to keep after the last crumb goes
    food_keep: float = 0.30       # stop showing a generation while the field still looks rich
    min_active: int = 20          # never record a window shorter than this

    # --- trait -> movement ------------------------------------------------
    v_min: float = 0.0030
    v_max: float = 0.0185

    # --- trait -> cost ----------------------------------------------------
    # totals across one whole generation, expressed in "food units"
    cost_base_total: float = 0.65
    cost_quad_total: float = 2.60

    # --- selection --------------------------------------------------------
    survive_energy: float = 0.0
    repro_energy: float = 2.30

    # --- inheritance ------------------------------------------------------
    mut_sigma: float = 0.017
    init_beta_a: float = 2.0
    init_beta_b: float = 5.2

    def as_dict(self) -> dict:
        return asdict(self)


class Generation:
    """Everything the renderer needs to replay one generation."""

    __slots__ = (
        "index", "speeds", "pos", "food", "food_eaten_step", "food_eater",
        "energy", "survived", "children", "mean", "std", "hist", "n_eaten",
        "active_steps", "feast_steps",
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _colour_hist(speeds: np.ndarray) -> np.ndarray:
    h, _ = np.histogram(speeds, bins=HIST_BINS, range=(0.0, 1.0))
    return h.astype(np.int32)


def run(params: Params, seed: int) -> tuple[list[Generation], Params]:
    rng = np.random.default_rng(seed)
    p = params

    c0 = p.cost_base_total / p.steps
    c2 = p.cost_quad_total / p.steps

    speeds = np.clip(rng.beta(p.init_beta_a, p.init_beta_b, p.n_init), 0.0, 1.0)
    history: list[Generation] = []

    for g in range(p.generations):
        n = len(speeds)
        v = p.v_min + speeds * (p.v_max - p.v_min)
        cost = c0 + c2 * speeds ** 2

        pos = rng.random((n, 2)).astype(np.float32)
        food = rng.random((p.n_food, 2)).astype(np.float32)
        food_alive = np.ones(p.n_food, dtype=bool)
        food_eaten_step = np.full(p.n_food, -1, dtype=np.int32)
        food_eater = np.full(p.n_food, -1, dtype=np.int32)
        energy = np.zeros(n, dtype=np.float64)

        track = np.empty((p.steps + 1, n, 2), dtype=np.float32)
        track[0] = pos
        heading = rng.uniform(0.0, 2 * np.pi, n)

        for t in range(p.steps):
            idx = np.flatnonzero(food_alive)
            if idx.size:
                d = np.linalg.norm(pos[:, None, :] - food[None, idx, :], axis=2)
                nearest = np.argmin(d, axis=1)
                delta = food[idx[nearest]] - pos
                ang = np.arctan2(delta[:, 1], delta[:, 0])
            else:
                ang = heading
            ang = ang + rng.normal(0.0, p.wander, n)
            heading = ang

            step = np.stack([np.cos(ang), np.sin(ang)], axis=1) * v[:, None]
            pos = np.clip(pos + step, 0.0, 1.0)

            # Soft-body separation: creatures crowd around food but never stack.
            diff = pos[:, None, :] - pos[None, :, :]
            dist = np.linalg.norm(diff, axis=2)
            np.fill_diagonal(dist, np.inf)
            overlap = np.where(np.isfinite(dist), (2 * p.body_r) - dist, 0.0)
            np.maximum(overlap, 0.0, out=overlap)
            if overlap.any():
                unit = diff / np.maximum(dist, 1e-6)[..., None]
                pos = np.clip(pos + (unit * (overlap * 0.35)[..., None]).sum(axis=1), 0.0, 1.0)

            energy -= cost
            track[t + 1] = pos

            idx = np.flatnonzero(food_alive)
            if idx.size:
                d = np.linalg.norm(pos[:, None, :] - food[None, idx, :], axis=2)
                dm = np.where(d <= p.eat_radius, d, np.inf)
                best = np.argmin(dm, axis=0)
                hit = np.isfinite(dm[best, np.arange(idx.size)])
                if hit.any():
                    taken = idx[hit]
                    eaters = best[hit]
                    np.add.at(energy, eaters, 1.0)
                    food_alive[taken] = False
                    food_eaten_step[taken] = t + 1
                    food_eater[taken] = eaters

        # The season always lasts `steps` ticks (that is what the energy cost
        # pays for) but the feeding frenzy is over long before that.  Record the
        # window that is worth watching; how much of it actually gets shown is
        # the renderer's call, since that depends on the frame budget.
        last_bite = int(food_eaten_step.max()) if (food_eaten_step >= 0).any() else 0
        active = int(np.clip(last_bite + p.tail_steps, p.min_active, p.steps))

        # The swarm strips the field bare every single time, and the last few
        # steps are one straggler chasing one crumb.  Note the moment the field
        # still holds `food_keep` of its crumbs: that is where the frame looks
        # busiest, and the renderer cuts there when it has the frames to spare.
        bites = np.sort(food_eaten_step[food_eaten_step >= 0])
        k = int(p.n_food * (1.0 - p.food_keep))
        feast = int(bites[k]) if bites.size > k else active
        feast = int(np.clip(feast, 8, active))

        survived = energy >= p.survive_energy
        children = np.where(energy >= p.repro_energy, 1, 0).astype(np.int32)

        history.append(Generation(
            index=g,
            speeds=speeds.copy(),
            pos=track[: active + 1].copy(),
            active_steps=active,
            feast_steps=feast,
            food=food,
            food_eaten_step=food_eaten_step,
            food_eater=food_eater,
            energy=energy.copy(),
            survived=survived.copy(),
            children=children.copy(),
            mean=float(speeds.mean()),
            std=float(speeds.std()),
            hist=_colour_hist(speeds),
            n_eaten=int((~food_alive).sum()),
        ))

        # ---- build the next generation ------------------------------------
        parents = speeds[survived]
        kids_from = np.repeat(speeds, children)
        kids = np.clip(kids_from + rng.normal(0.0, p.mut_sigma, kids_from.size), 0.0, 1.0)
        nxt = np.concatenate([parents, kids])

        if nxt.size > p.max_pop:                       # crowding
            nxt = rng.permutation(nxt)[: p.max_pop]
        if nxt.size < p.min_pop:                       # rescue from extinction
            src = nxt if nxt.size else speeds
            extra = rng.choice(src, p.min_pop - nxt.size)
            extra = np.clip(extra + rng.normal(0.0, p.mut_sigma, extra.size), 0.0, 1.0)
            nxt = np.concatenate([nxt, extra])
        speeds = nxt

    return history, p
