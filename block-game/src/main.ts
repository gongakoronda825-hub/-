import * as THREE from 'three';
import { Renderer } from './core/Renderer';
import { EYE_HEIGHT, MAX_DELTA, SPAWN } from './core/config';
import { ActionButtons } from './input/ActionButtons';
import { FlightControls } from './input/FlightControls';
import { Joystick } from './input/Joystick';
import { LookControls } from './input/LookControls';
import { BlockInteraction } from './interaction/BlockInteraction';
import { FirstPersonCamera } from './player/FirstPersonCamera';
import { Player } from './player/Player';
import { DebugHud } from './ui/DebugHud';
import { Inventory } from './ui/Inventory';
import { createCrosshair } from './ui/Crosshair';
import { Tutorial } from './ui/Tutorial';
import { World, buildInitialWorld } from './world/World';

const element = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`要素が見つかりません: #${id}`);
  return el as T;
};

const canvas = element<HTMLCanvasElement>('scene');
const ui = element('ui');

const renderer = new Renderer(canvas);
const world = new World(renderer.scene);
buildInitialWorld(world);

const player = new Player(world);
const view = new FirstPersonCamera(renderer.camera);
const inventory = new Inventory(element('hotbar'));
const interaction = new BlockInteraction(
  world,
  player,
  renderer.camera,
  renderer.scene,
  () => inventory.current,
);

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

  // 移動方向 = 前方 × スティックY + 右 × スティックX（計画書 §3.4）
  const input = joystick.read();
  view.getHorizontalForward(forward);
  view.getHorizontalRight(right);
  move.copy(forward).multiplyScalar(input.y).addScaledVector(right, input.x);
  if (move.lengthSq() > 1) move.normalize();

  player.update(dt, move);

  // 万一ワールドの外へ落ちたら初期位置へ戻す
  if (player.position.y < -30) {
    player.position.set(SPAWN.x, SPAWN.y, SPAWN.z);
    player.velocity.set(0, 0, 0);
  }

  view.apply(player.position.x, player.position.y + EYE_HEIGHT, player.position.z);
  interaction.update();
  hud.update(dt, player, world, inventory.current);

  renderer.render();
}

new Tutorial(ui, () => {
  running = true;
  lastTime = performance.now();
});

// 説明を出している間もワールドは見えているほうがよいので、先に一度だけ組み立てておく
view.apply(player.position.x, player.position.y + EYE_HEIGHT, player.position.z);
requestAnimationFrame(frame);
