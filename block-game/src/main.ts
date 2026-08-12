import * as THREE from 'three';
import { Renderer } from './core/Renderer';
import { EYE_HEIGHT, MAX_DELTA, SPAWN, WORLD_HEIGHT } from './core/config';
import { EntityManager } from './entities/EntityManager';
import { SpawnManager } from './entities/SpawnManager';
import { ActionButtons } from './input/ActionButtons';
import { FlightControls } from './input/FlightControls';
import { Joystick } from './input/Joystick';
import { LookControls } from './input/LookControls';
import { BlockInteraction } from './interaction/BlockInteraction';
import { FirstPersonCamera } from './player/FirstPersonCamera';
import { Player } from './player/Player';
import { ChunkManager } from './world/ChunkManager';
import { World } from './world/World';
import { DebugHud } from './ui/DebugHud';
import { Inventory } from './ui/Inventory';
import { createCrosshair } from './ui/Crosshair';
import { Tutorial } from './ui/Tutorial';

const element = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`要素が見つかりません: #${id}`);
  return el as T;
};

const canvas = element<HTMLCanvasElement>('scene');
const ui = element('ui');

const renderer = new Renderer(canvas);
const world = new World(renderer.scene);
const chunks = new ChunkManager(world);

// 操作説明を読んでいる間に、近いところは作り終えておく
chunks.primeAround(SPAWN.x, SPAWN.z);

// 地形は決定論なので、湧き位置にたまたま木が生えていると毎回そこに埋まる。
// 近くの開けた列を探してから立たせる。
const start = world.findOpenColumn(SPAWN.x, SPAWN.z, 20, 4, 3) ?? {
  x: SPAWN.x,
  z: SPAWN.z,
  y: world.standingHeight(SPAWN.x, SPAWN.z) ?? WORLD_HEIGHT / 2,
};

const player = new Player(world);
player.placeOnGround(start.x, start.z, start.y);

const view = new FirstPersonCamera(renderer.camera);
const inventory = new Inventory(element('hotbar'));
const interaction = new BlockInteraction(
  world,
  player,
  renderer.camera,
  renderer.scene,
  () => inventory.current,
);

const entities = new EntityManager(renderer.scene);
const spawner = new SpawnManager(world, entities);

const joystick = new Joystick(element('joystick-zone'));
new LookControls(element('look-zone'), view);
new ActionButtons(element('break-button'), element('place-button'), {
  onBreak: () => interaction.breakBlock(),
  onPlace: () => interaction.placeBlock(),
});
new FlightControls(player, {
  jump: element('jump-button'),
  up: element('up-button'),
  down: element('down-button'),
});

createCrosshair(ui);
const hud = new DebugHud(ui);

const forward = new THREE.Vector3();
const right = new THREE.Vector3();
const move = new THREE.Vector3();

let running = false;
let lastTime = performance.now();

function frame(now: number): void {
  requestAnimationFrame(frame);

  // デルタタイムで動かす（フレームレート非依存）。タブ復帰の巨大な dt は切り捨てる。
  const dt = Math.min((now - lastTime) / 1000, MAX_DELTA);
  lastTime = now;

  if (!running) {
    renderer.render();
    return;
  }

  // 移動方向 = 前方 × スティックY + 右 × スティックX
  const input = joystick.read();
  view.getHorizontalForward(forward);
  view.getHorizontalRight(right);
  move.copy(forward).multiplyScalar(input.y).addScaledVector(right, input.x);
  if (move.lengthSq() > 1) move.normalize();

  player.update(dt, move);

  // 万一ワールドの外へ落ちたら地表へ戻す
  if (player.position.y < -20) {
    const ground = world.standingHeight(player.position.x, player.position.z);
    player.placeOnGround(player.position.x, player.position.z, ground ?? WORLD_HEIGHT / 2);
  }

  chunks.update(player.position.x, player.position.z);
  entities.update(dt, player.position.x, player.position.z);
  spawner.update(dt, player.position.x, player.position.z);

  view.apply(player.position.x, player.position.y + EYE_HEIGHT, player.position.z);
  interaction.update();
  hud.update(dt, {
    player,
    world,
    hold: inventory.currentName,
    chunks: world.chunkCount,
    mobs: entities.count,
    nearestMob: entities.nearestDistance(player.position.x, player.position.z),
  });

  renderer.render();
}

new Tutorial(ui, () => {
  running = true;
  lastTime = performance.now();
});

// 説明を出している間もワールドは見えているほうがよいので、先に一度だけ組み立てておく
view.apply(player.position.x, player.position.y + EYE_HEIGHT, player.position.z);
requestAnimationFrame(frame);
