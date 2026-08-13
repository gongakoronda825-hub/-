/**
 * 街の色。
 *
 * 狙いは「昔のテレビアニメの背景美術のような住宅街」（指示書 §12, §14）。
 * 彩度は低め、明度は高め。影は付けず、面の向きで付く陰影だけで立体に見せる。
 * 特定の作品の色をそのまま持ってきたものは無い。
 */

export const ROAD = 0x8f949b;
export const ROAD_LINE = 0xd8d4c8;
export const ALLEY = 0x9d968c;
export const SIDEWALK = 0xb4b0a6;
export const DIRT = 0xc0a97f;
export const GRASS = 0x7fb45c;
export const SAND = 0xd9c48d;

/** 家の壁。1軒ごとにこの中から1つ選ぶ。 */
export const HOUSE_WALLS: readonly number[] = [0xf3e8d6, 0xe9dcc6, 0xdfe6ec, 0xf1dcc4, 0xe4e7dd];

/** 屋根。瓦・スレート・トタンのつもり。 */
export const HOUSE_ROOFS: readonly number[] = [0x59708c, 0x8b5a48, 0x4f6b53, 0x6a6470, 0x9c7a4f];

export const BLOCK_WALL = 0xd0cabb;
export const BLOCK_WALL_CAP = 0xb9b3a4;
export const DOOR = 0x6d4a34;
export const WINDOW = 0xaad6ef;
export const GATE_POST = 0xcfc9ba;
export const DOORBELL_PLATE = 0xf4f2ec;
export const DOORBELL_BUTTON = 0xff7a6a;

export const POLE = 0x9b9a94;
export const WIRE = 0x3a3a3e;
export const VENDING = 0xd2453c;
export const VENDING_PANEL = 0xf3f6f8;
export const POST_BOX = 0xd2453c;
export const HEDGE = 0x4f8f45;
export const TREE_TRUNK = 0x7a5638;
export const TREE_LEAF = 0x4f9c47;
export const BENCH = 0x8a6a45;
export const PIPE = 0xc8c3b6;
export const FENCE = 0xb0b6bb;

/** 車。1台ごとにこの中から1つ選ぶ。 */
export const CAR_BODIES: readonly number[] = [0xe2e2e2, 0x3f6fa8, 0xc44f4f, 0x35353c, 0xf0d27a];
export const CAR_GLASS = 0x9fc4d8;
export const CAR_TIRE = 0x2a2a2e;
