import * as THREE from 'three';
import { Sfx } from './audio/Sfx';
import { GameState } from './core/GameState';
import { Renderer } from './core/Renderer';
import { ESCAPE_BONUS_BASE, MAX_DELTA, WATCH_GAUGE_MAX } from './core/config';
import { DoorbellSystem } from './doorbell/DoorbellSystem';
import { DashButton, bindTap } from './input/ActionButtons';
import { Joystick } from './input/Joystick';
import { LookControls } from './input/LookControls';
import { FirstPersonCamera } from './player/FirstPersonCamera';
import { Player } from './player/Player';
import { ResidentManager } from './residents/ResidentManager';
import { Town } from './town/Town';
import { DebugHud } from './ui/DebugHud';
import { Hud } from './ui/Hud';
import { ResultScreen, TitleScreen } from './ui/Screens';

const element = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`要素が見つかりません: #${id}`);
  return el as T;
};

const canvas = element<HTMLCanvasElement>('scene');
const ui = element('ui');

const renderer = new Renderer(canvas);
const town = new Town();
renderer.scene.add(town.group);

const state = new GameState();
const sfx = new Sfx();
const hud = new Hud(ui);
const debug = new DebugHud(ui);

const player = new Player(town.colliders);
player.place(town.spawn.x, town.spawn.z);

const view = new FirstPersonCamera(renderer.camera);

const residents = new ResidentManager(renderer.scene, town.colliders, town, {
  onAppear: (resident) => {
    hud.toast(resident.type.shout, 'bad');
    sfx.door();
  },
  onChase: (resident) => {
    hud.toast(`${resident.type.name}が追ってきた！`, 'bad');
    sfx.alert();
  },
  onEscape: (resident) => {
    // 追ってきた相手をまいた。危険な住民ほど見返りが大きい（指示書 §8）。
    // ただし相手は消えず、このあとも街を歩き続ける（追加仕様 §12）。
    const bonus = Math.round(ESCAPE_BONUS_BASE * resident.type.escapeMultiplier);
    state.addScore(bonus);
    hud.toast(`まいた！ +${bonus}`, 'good');
    sfx.escape();
  },
  onCaught: () => {
    /* 実際の処理はゲームループ側（gameOver）でまとめて行う */
  },
});

const doorbells = new DoorbellSystem(town, state, residents);

// ── 入力 ──────────────────────────────────────────

const joystick = new Joystick(element('joystick-zone'));
new LookControls(element('look-zone'), view);

const pingButton = element<HTMLButtonElement>('ping-button');
const dash = new DashButton(element('dash-button'));
bindTap(pingButton, () => doPing());

// ── ゲームの進行 ──────────────────────────────────

type Phase = 'title' | 'playing' | 'over';
let phase: Phase = 'title';

let highscore = GameState.loadHighscore();

const forward = new THREE.Vector3();
const right = new THREE.Vector3();
const move = new THREE.Vector3();

/**
 * ピンポン（指示書 §5）。押した瞬間に鳴る。確認も溜めも無い。
 */
function doPing(): void {
  if (phase !== 'playing') return;

  const result = doorbells.ping();
  if (!result) return;

  sfx.ping();
  hud.gain(result.points);
  if (result.extra) hud.toast('近所もざわついた…', 'bad');
}

function start(): void {
  sfx.unlock();
  phase = 'playing';
  lastTime = performance.now();
}

function retry(): void {
  state.reset();
  residents.clear();
  doorbells.reset();
  hud.reset();
  player.place(town.spawn.x, town.spawn.z);
  view.yaw = 0;
  view.pitch = 0;
  phase = 'playing';
  lastTime = performance.now();
}

function gameOver(cause: string): void {
  if (phase !== 'playing') return;
  phase = 'over';
  sfx.caught();

  const newRecord = state.score > highscore;
  if (newRecord) {
    highscore = state.score;
    GameState.saveHighscore(highscore);
  }

  pingButton.classList.add('hidden');
  result.show({
    score: state.score,
    pings: state.pings,
    bestCombo: state.bestCombo,
    highscore,
    newRecord,
    cause,
  });
}

const result = new ResultScreen(ui, retry);
new TitleScreen(ui, start);

// ── ループ ────────────────────────────────────────

let lastTime = performance.now();

function frame(now: number): void {
  requestAnimationFrame(frame);

  // デルタタイムで動かす（フレームレート非依存）。タブ復帰の巨大な dt は切り捨てる。
  const dt = Math.min((now - lastTime) / 1000, MAX_DELTA);
  lastTime = now;

  if (phase === 'playing') {
    step(dt);
  }

  renderer.render();
}

function step(dt: number): void {
  // 移動方向 = 前方 × スティックY + 右 × スティックX
  const input = joystick.read();
  view.getHorizontalForward(forward);
  view.getHorizontalRight(right);
  move.copy(forward).multiplyScalar(input.y).addScaledVector(right, input.x);
  if (move.lengthSq() > 1) move.normalize();

  const wantDash = dash.held || joystick.shiftHeld;
  player.update(dt, move, wantDash);
  view.updateFov(dt, player.dashing);
  view.apply(player.position.x, player.eyeY, player.position.z);

  // 住民 → 危険度 → インターホン の順。住民の状態を見てから危険度を更新する
  const caught = residents.update(dt, player.position);
  state.update(dt, residents.anyChasing, doorbells.distanceToCombo(player.position));
  doorbells.update(dt, player.position, forward);

  // PC で確認するとき用のキー操作
  if (joystick.consumeActionKey()) doPing();

  const available = doorbells.available !== null;
  pingButton.classList.toggle('hidden', !available);
  dash.setEmpty(!player.canDash);

  const gauge = residents.maxGauge;
  hud.update(state, player.staminaRatio, gauge, residents.count);
  debug.update(dt, state, player, residents, gauge, view.yaw);

  if (caught) {
    gameOver('つかまった！');
  } else if (gauge >= WATCH_GAUGE_MAX) {
    gameOver('顔を覚えられた！');
  }
}

// タイトルを出している間も街は見えていてほしいので、先に1回だけ組み立てる
view.apply(player.position.x, player.eyeY, player.position.z);
requestAnimationFrame(frame);
