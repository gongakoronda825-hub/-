/* ============================================================
   FACE CHASE
   3D空間を逃げ回り、宙に浮かぶ「顔」に捕まったら終わり。
   Three.js（lib/ に同梱）だけで動く。ビルド不要。
   ============================================================ */
import * as THREE from 'three';

// ------------------------------------------------------------
// 設定（難易度調整はここ）
// ------------------------------------------------------------
const CONFIG = {
  FACE_URL: 'assets/face.png',

  FIELD_HALF: 30,          // フィールドは 60 x 60 の正方形
  PLAYER_START: { x: 0, z: 10 },

  PLAYER_RADIUS: 0.45,
  PLAYER_SPEED: 5.0,
  DASH_SPEED: 8.2,
  STAMINA_MAX: 100,
  STAMINA_DRAIN: 45,       // /秒
  STAMINA_REGEN: 20,       // /秒
  STAMINA_UNLOCK: 30,      // 使い切ったら、ここまで回復するまでダッシュ不可

  ENEMY_RADIUS: 0.6,
  ENEMY_FLOAT: 1.75,       // 顔が浮いている高さ
  FACE_HEIGHT: 2.2,        // 顔の表示の高さ（幅は画像の縦横比から決まる）
  FACE_MAX_WIDTH: 3.2,
  ENEMY_BASE_SPEED: 2.9,
  ENEMY_SPEED_GAIN: 0.03,  // 1秒ごとの加速（ゆるやかに）
  ENEMY_MAX_SPEED: 5.0,
  SPAWN_INTERVAL: 10,      // 10秒ごとに1体追加
  MAX_ENEMIES: 8,          // スマホの処理落ち対策の上限
  SPAWN_MIN_DIST: 18,
  SPAWN_RISE_TIME: 1.2,

  CATCH_DISTANCE: 0.95,
  DANGER_DISTANCE: 10,     // この距離から緊張演出が始まる
};

const H = CONFIG.FIELD_HALF;
const isTouch = window.matchMedia('(pointer: coarse)').matches || 'ontouchstart' in window;
const DEBUG = new URLSearchParams(location.search).has('debug');
document.body.classList.toggle('is-touch', isTouch);

// ------------------------------------------------------------
// 小物
// ------------------------------------------------------------
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const damp = (k, dt) => 1 - Math.exp(-k * dt);
function lerpAngle(a, b, t) {
  let d = ((b - a + Math.PI) % (Math.PI * 2)) - Math.PI;
  if (d < -Math.PI) d += Math.PI * 2;
  return a + d * t;
}
// 固定シードの乱数（障害物の配置を毎回同じにする）
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const $ = (id) => document.getElementById(id);

const ui = {
  hud: $('hud'), time: $('timeValue'), faces: $('facesValue'), stamina: $('staminaFill'),
  vignette: $('vignette'), danger: $('danger'), flash: $('flash'), dim: $('caughtDim'),
  warning: $('warning'), toast: $('toast'), indicators: $('indicators'),
  title: $('titleScreen'), titleFace: $('titleFace'), startBtn: $('startBtn'), faceNote: $('faceNote'),
  countdown: $('countdown'),
  end: $('endLayer'), caughtText: $('caughtText'), overPanel: $('overPanel'),
  overTime: $('overTime'), overBest: $('overBest'), newBest: $('newBest'), retry: $('retryBtn'),
  touch: $('touchControls'), joyZone: $('joyZone'), joyBase: $('joyBase'), joyKnob: $('joyKnob'),
  dash: $('dashBtn'), mute: $('muteBtn'),
};

function restartAnim(el, cls) {
  el.classList.remove(cls);
  void el.offsetWidth; // リフローでアニメーションを最初から
  el.classList.add(cls);
}

const store = {
  get(key, def) { try { const v = localStorage.getItem(key); return v === null ? def : v; } catch (e) { return def; } },
  set(key, v) { try { localStorage.setItem(key, String(v)); } catch (e) { /* 保存できなくても続行 */ } },
};

// ------------------------------------------------------------
// サウンド（Web Audio で全部生成。音源ファイル不要）
// ------------------------------------------------------------
const Sound = (() => {
  let ctx = null, master = null, noiseBuf = null, drone = null;
  let muted = store.get('faceChase.muted', '0') === '1';

  function init() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = muted ? 0 : 0.8;
      master.connect(ctx.destination);
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    if (ctx.state === 'suspended') ctx.resume();
  }

  function tone({ freq, freqEnd = 0, type = 'sine', dur = 0.15, vol = 0.25, delay = 0, attack = 0.005 }) {
    if (!ctx) return;
    const t0 = ctx.currentTime + delay;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t0);
    if (freqEnd) o.frequency.exponentialRampToValueAtTime(freqEnd, t0 + dur);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(vol, t0 + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(master);
    o.start(t0); o.stop(t0 + dur + 0.05);
  }

  function noise({ dur = 0.4, vol = 0.3, delay = 0, freq = 1200, freqEnd = 0, q = 1, type = 'bandpass' }) {
    if (!ctx) return;
    const t0 = ctx.currentTime + delay;
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf; src.loop = true;
    const f = ctx.createBiquadFilter();
    f.type = type; f.Q.value = q;
    f.frequency.setValueAtTime(freq, t0);
    if (freqEnd) f.frequency.exponentialRampToValueAtTime(freqEnd, t0 + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(f); f.connect(g); g.connect(master);
    src.start(t0); src.stop(t0 + dur + 0.05);
  }

  return {
    init,
    get muted() { return muted; },
    toggleMute() {
      muted = !muted;
      store.set('faceChase.muted', muted ? '1' : '0');
      if (master) master.gain.setTargetAtTime(muted ? 0 : 0.8, ctx.currentTime, 0.02);
      return muted;
    },
    suspend() { if (ctx && ctx.state === 'running') ctx.suspend(); },
    resume() { if (ctx && ctx.state === 'suspended') ctx.resume(); },

    countBeep() { tone({ freq: 523, type: 'square', dur: 0.16, vol: 0.12 }); },
    go() {
      tone({ freq: 1046, type: 'square', dur: 0.35, vol: 0.12 });
      tone({ freq: 523, type: 'sawtooth', dur: 0.5, vol: 0.06 });
      tone({ freq: 784, type: 'triangle', dur: 0.5, vol: 0.1, delay: 0.05 });
    },
    spawn() {
      tone({ freq: 900, freqEnd: 260, type: 'sine', dur: 0.9, vol: 0.12 });
      tone({ freq: 910, freqEnd: 250, type: 'triangle', dur: 0.9, vol: 0.06, delay: 0.03 });
    },
    heartbeat(intensity) {
      const v = 0.18 + intensity * 0.35;
      tone({ freq: 75, freqEnd: 40, dur: 0.14, vol: v });
      tone({ freq: 70, freqEnd: 38, dur: 0.12, vol: v * 0.7, delay: 0.16 });
      if (intensity > 0.65) tone({ freq: 1480, type: 'square', dur: 0.07, vol: 0.05 + intensity * 0.05 });
    },
    startDrone() {
      if (!ctx || drone) return;
      const t = ctx.currentTime;
      const g = ctx.createGain(); g.gain.value = 0.0001;
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 150; f.Q.value = 6;
      const oscs = [55, 55.6, 82.5].map((fr, i) => {
        const o = ctx.createOscillator();
        o.type = i === 2 ? 'triangle' : 'sawtooth';
        o.frequency.value = fr;
        o.connect(f); o.start(t);
        return o;
      });
      f.connect(g); g.connect(master);
      g.gain.setTargetAtTime(0.03, t, 0.5);
      drone = { g, f, oscs };
    },
    setDrone(intensity) {
      if (!drone) return;
      const t = ctx.currentTime;
      drone.g.gain.setTargetAtTime(0.03 + intensity * 0.12, t, 0.15);
      drone.f.frequency.setTargetAtTime(150 + intensity * 1100, t, 0.15);
    },
    stopDrone() {
      if (!drone) return;
      const d = drone; drone = null;
      const t = ctx.currentTime;
      d.g.gain.cancelScheduledValues(t);
      d.g.gain.setTargetAtTime(0.0001, t, 0.08);
      d.oscs.forEach((o) => o.stop(t + 0.6));
    },
    caught() {
      noise({ dur: 0.7, vol: 0.5, freq: 3000, freqEnd: 300, q: 0.8 });
      tone({ freq: 700, freqEnd: 70, type: 'sawtooth', dur: 0.7, vol: 0.22 });
      tone({ freq: 1040, freqEnd: 90, type: 'square', dur: 0.6, vol: 0.08 });
    },
    boom() {
      tone({ freq: 90, freqEnd: 30, dur: 0.8, vol: 0.5 });
      noise({ dur: 0.5, vol: 0.35, freq: 400, freqEnd: 60, type: 'lowpass' });
    },
    // 「そこそこバっチリ」用の、妙に明るいジングル
    jingle() {
      const notes = [[784, 0], [988, 0.09], [1175, 0.18], [1568, 0.3]];
      notes.forEach(([f, d], i) => tone({ freq: f, type: 'square', dur: i === 3 ? 0.5 : 0.1, vol: 0.09, delay: d }));
      tone({ freq: 392, type: 'triangle', dur: 0.6, vol: 0.12, delay: 0.3 });
    },
  };
})();

// ------------------------------------------------------------
// Three.js 基本セット
// ------------------------------------------------------------
const canvas = $('scene');
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: window.devicePixelRatio < 2,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, isTouch ? 1.75 : 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color(0x120d14);
const FOG_NEAR = 14, FOG_FAR = 60;
scene.background = FOG_COLOR.clone();
scene.fog = new THREE.Fog(FOG_COLOR, FOG_NEAR, FOG_FAR);

const BASE_FOV = 55;
const camera = new THREE.PerspectiveCamera(BASE_FOV, window.innerWidth / window.innerHeight, 0.1, 260);

const HEMI_BASE = 1.35, DIR_BASE = 1.4;
const hemi = new THREE.HemisphereLight(0x9aa0c8, 0x1a1720, HEMI_BASE);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xc8ccff, DIR_BASE);
sun.position.set(12, 24, 6);
scene.add(sun);

// 空：上は黒、地平線は霧の色へ。霧と境目が出ないように合わせている
const sky = new THREE.Mesh(
  new THREE.SphereGeometry(200, 24, 12),
  new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: {
      top: { value: new THREE.Color(0x020104) },
      horizon: { value: FOG_COLOR.clone() },
    },
    vertexShader: /* glsl */`
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 top;
      uniform vec3 horizon;
      varying vec3 vDir;
      void main() {
        float h = clamp(vDir.y * 2.2, 0.0, 1.0);
        gl_FragColor = vec4(mix(horizon, top, pow(h, 0.5)), 1.0);
        #include <colorspace_fragment>
      }`,
  })
);
sky.renderOrder = -10;
scene.add(sky);

// ------------------------------------------------------------
// テクスチャ（すべて Canvas で生成）
// ------------------------------------------------------------
const maxAniso = Math.min(4, renderer.capabilities.getMaxAnisotropy());

function makeGroundTexture() {
  const s = 256;
  const c = document.createElement('canvas');
  c.width = c.height = s;
  const g = c.getContext('2d');
  g.fillStyle = '#34363b';
  g.fillRect(0, 0, s, s);
  const rnd = mulberry32(7);
  for (let i = 0; i < 1400; i++) {
    const v = 40 + Math.floor(rnd() * 30);
    g.fillStyle = `rgba(${v},${v},${v + 4},${0.25 + rnd() * 0.3})`;
    g.fillRect(rnd() * s, rnd() * s, 1 + rnd() * 2, 1 + rnd() * 2);
  }
  // 汚れのムラ
  for (let i = 0; i < 6; i++) {
    const gr = g.createRadialGradient(rnd() * s, rnd() * s, 0, rnd() * s, rnd() * s, 40 + rnd() * 60);
    gr.addColorStop(0, 'rgba(10,8,12,0.18)');
    gr.addColorStop(1, 'rgba(10,8,12,0)');
    g.fillStyle = gr;
    g.fillRect(0, 0, s, s);
  }
  g.strokeStyle = '#1d1e22';
  g.lineWidth = 4;
  g.strokeRect(0, 0, s, s);
  g.strokeStyle = 'rgba(255,255,255,0.05)';
  g.lineWidth = 1;
  g.strokeRect(3, 3, s - 6, s - 6);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = maxAniso;
  return t;
}

function makeConcreteTexture() {
  const s = 128;
  const c = document.createElement('canvas');
  c.width = c.height = s;
  const g = c.getContext('2d');
  g.fillStyle = '#c8c8c8';
  g.fillRect(0, 0, s, s);
  const rnd = mulberry32(11);
  for (let i = 0; i < 900; i++) {
    const v = 150 + Math.floor(rnd() * 90);
    g.fillStyle = `rgba(${v},${v},${v},0.5)`;
    g.fillRect(rnd() * s, rnd() * s, 1 + rnd() * 3, 1 + rnd() * 3);
  }
  // 雨だれの筋
  for (let i = 0; i < 14; i++) {
    g.fillStyle = `rgba(60,55,60,${0.05 + rnd() * 0.1})`;
    g.fillRect(rnd() * s, 0, 1 + rnd() * 3, s * (0.4 + rnd() * 0.6));
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = maxAniso;
  return t;
}

function makeRadialTexture(stops) {
  const s = 128;
  const c = document.createElement('canvas');
  c.width = c.height = s;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  stops.forEach(([o, col]) => gr.addColorStop(o, col));
  g.fillStyle = gr;
  g.fillRect(0, 0, s, s);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const shadowTex = makeRadialTexture([[0, 'rgba(0,0,0,0.75)'], [0.6, 'rgba(0,0,0,0.35)'], [1, 'rgba(0,0,0,0)']]);
const auraTex = makeRadialTexture([[0, 'rgba(255,40,50,0.5)'], [0.45, 'rgba(160,0,20,0.22)'], [1, 'rgba(80,0,10,0)']]);

// ------------------------------------------------------------
// 顔画像の読み込み
//  - 周囲の透明/白い余白は自動でトリミング（縦横比は変えない）
//  - 読めなかったときは仮の顔を描いて続行
// ------------------------------------------------------------
function drawPlaceholderFace() {
  const c = document.createElement('canvas');
  c.width = 400; c.height = 500;
  const g = c.getContext('2d');
  const skin = g.createRadialGradient(200, 230, 30, 200, 260, 250);
  skin.addColorStop(0, '#efd9c6');
  skin.addColorStop(0.75, '#cfae96');
  skin.addColorStop(1, '#8e6d5c');
  g.fillStyle = skin;
  g.beginPath(); g.ellipse(200, 260, 180, 235, 0, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#16110f';
  g.beginPath(); g.ellipse(200, 120, 185, 110, 0, Math.PI, 0); g.fill();
  g.fillRect(15, 110, 370, 40);
  for (const x of [130, 270]) {
    g.fillStyle = '#fff';
    g.beginPath(); g.ellipse(x, 240, 44, 34, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#000';
    g.beginPath(); g.arc(x, 242, 13, 0, Math.PI * 2); g.fill();
    g.strokeStyle = 'rgba(80,40,40,0.5)'; g.lineWidth = 3;
    g.beginPath(); g.arc(x, 250, 46, 0.2 * Math.PI, 0.8 * Math.PI); g.stroke();
  }
  g.fillStyle = '#4a1216';
  g.beginPath();
  g.moveTo(90, 350); g.quadraticCurveTo(200, 470, 310, 350); g.quadraticCurveTo(200, 400, 90, 350);
  g.fill();
  g.fillStyle = '#f4efe6';
  g.beginPath(); g.moveTo(110, 362); g.quadraticCurveTo(200, 405, 290, 362); g.quadraticCurveTo(200, 385, 110, 362); g.fill();
  return c;
}

function prepareFace(img) {
  // 大きすぎる画像はスマホのために 1024px に縮める
  const scale = Math.min(1, 1024 / Math.max(img.naturalWidth, img.naturalHeight));
  const w = Math.max(1, Math.round(img.naturalWidth * scale));
  const h = Math.max(1, Math.round(img.naturalHeight * scale));
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(img, 0, 0, w, h);
  let data;
  try { data = g.getImageData(0, 0, w, h); } catch (e) { return c; }
  const px = data.data;

  // 四隅が白っぽく不透明なら「白背景の画像」とみなし、外周から塗りつぶして透明にする
  const whiteAt = (i) => px[i + 3] > 200 && px[i] > 230 && px[i + 1] > 230 && px[i + 2] > 230;
  const corners = [0, (w - 1) * 4, (h - 1) * w * 4, ((h - 1) * w + w - 1) * 4];
  if (corners.filter(whiteAt).length >= 3) {
    const seen = new Uint8Array(w * h);
    const stack = [];
    for (let x = 0; x < w; x++) { stack.push(x, (h - 1) * w + x); }
    for (let y = 0; y < h; y++) { stack.push(y * w, y * w + w - 1); }
    while (stack.length) {
      const p = stack.pop();
      if (seen[p]) continue;
      seen[p] = 1;
      if (!whiteAt(p * 4)) continue;
      px[p * 4 + 3] = 0;
      const x = p % w;
      if (x > 0) stack.push(p - 1);
      if (x < w - 1) stack.push(p + 1);
      if (p >= w) stack.push(p - w);
      if (p < w * (h - 1)) stack.push(p + w);
    }
    g.putImageData(data, 0, 0);
  }

  // 不透明部分の外接矩形でトリミング
  let minX = w, minY = h, maxX = -1, maxY = -1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (px[(y * w + x) * 4 + 3] > 16) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  if (maxX < 0) return c;
  const pad = Math.round(Math.max(maxX - minX, maxY - minY) * 0.02);
  minX = Math.max(0, minX - pad); minY = Math.max(0, minY - pad);
  maxX = Math.min(w - 1, maxX + pad); maxY = Math.min(h - 1, maxY + pad);
  const cw = maxX - minX + 1, ch = maxY - minY + 1;
  if (cw === w && ch === h) return c;
  const out = document.createElement('canvas');
  out.width = cw; out.height = ch;
  out.getContext('2d').drawImage(c, minX, minY, cw, ch, 0, 0, cw, ch);
  return out;
}

function loadFace() {
  return new Promise((resolve) => {
    const img = new Image();
    let done = false;
    const finish = (faceCanvas, isPlaceholder) => {
      if (done) return;
      done = true;
      resolve({ canvas: faceCanvas, isPlaceholder });
    };
    img.onload = () => {
      try { finish(prepareFace(img), false); } catch (e) { console.warn(e); finish(drawPlaceholderFace(), true); }
    };
    img.onerror = () => {
      console.warn(`[FACE CHASE] ${CONFIG.FACE_URL} を読み込めなかったので、仮の顔を使います。`);
      finish(drawPlaceholderFace(), true);
    };
    setTimeout(() => finish(drawPlaceholderFace(), true), 8000);
    // 差し替えた画像がキャッシュで古いままにならないよう、クエリを付ける
    img.src = `${CONFIG.FACE_URL}?v=${Date.now()}`;
  });
}

let faceTex = null;
let faceAspect = 1;        // 幅 / 高さ（画像そのままの比率）
let faceW = 1, faceH = 1;  // ワールド単位の表示サイズ
let faceDataURL = '';

function setFace({ canvas: fc, isPlaceholder }) {
  faceTex = new THREE.CanvasTexture(fc);
  faceTex.colorSpace = THREE.SRGBColorSpace;
  faceTex.anisotropy = maxAniso;
  faceAspect = fc.width / fc.height;
  faceH = CONFIG.FACE_HEIGHT;
  faceW = faceH * faceAspect;
  if (faceW > CONFIG.FACE_MAX_WIDTH) {
    faceW = CONFIG.FACE_MAX_WIDTH;
    faceH = faceW / faceAspect;
  }
  faceDataURL = fc.toDataURL('image/png');
  ui.titleFace.src = faceDataURL;
  for (const el of indicatorPool) el.face.style.backgroundImage = `url(${faceDataURL})`;
  if (isPlaceholder) {
    ui.faceNote.textContent = 'assets/face.png が見つからないため、仮の顔で動いています';
    ui.faceNote.classList.remove('hidden');
  }
}

// ------------------------------------------------------------
// フィールドと障害物
// ------------------------------------------------------------
const boxes = [];    // { x, z, w, d, h, kind }  … 軸平行の直方体（壁・箱）
const pillars = [];  // { x, z, r, h }            … 円柱

function rectRectGap(a, b) {
  const gx = Math.max(0, Math.abs(a.x - b.x) - (a.w + b.w) / 2);
  const gz = Math.max(0, Math.abs(a.z - b.z) - (a.d + b.d) / 2);
  return Math.hypot(gx, gz);
}
function pointRectDist(x, z, b) {
  const gx = Math.max(0, Math.abs(x - b.x) - b.w / 2);
  const gz = Math.max(0, Math.abs(z - b.z) - b.d / 2);
  return Math.hypot(gx, gz);
}

function buildLayout() {
  // 固定の壁（L字や囲いを作らず、どこも行き止まりにならない配置）
  const walls = [
    [-15, -16, 14, 0.8], [16, -12, 0.8, 14], [14, 16, 12, 0.8], [-17, 12, 0.8, 12],
    [0, -24, 10, 0.8], [24, 22, 0.8, 8], [-25, -25, 8, 0.8], [-2, -5, 0.8, 5],
  ];
  for (const [x, z, w, d] of walls) boxes.push({ x, z, w, d, h: 2.8, kind: 'wall' });

  const fixedPillars = [
    [-7, 3], [7, 2], [7, -9], [-9, -8], [0, -14], [-26, 3], [26, 1],
    [10, 25], [-8, 24], [23, -25], [-24, -14], [21, 8],
  ];
  for (const [x, z] of fixedPillars) pillars.push({ x, z, r: 0.7, h: 5.5 });

  // 箱はシード付き乱数で散らす。通路が狭くならないよう間隔を確保
  const rnd = mulberry32(20240925);
  const GAP = 2.6;
  let tries = 0;
  while (boxes.filter((b) => b.kind === 'box').length < 18 && tries++ < 800) {
    const w = 1.2 + rnd() * 1.4;
    const d = rnd() < 0.5 ? w : 1.2 + rnd() * 1.4;
    const cand = { x: (rnd() * 2 - 1) * 26, z: (rnd() * 2 - 1) * 26, w, d, h: 1 + rnd() * 1.2, kind: 'box' };
    if (Math.hypot(cand.x - CONFIG.PLAYER_START.x, cand.z - CONFIG.PLAYER_START.z) < 6) continue;
    if (boxes.some((b) => rectRectGap(b, cand) < GAP)) continue;
    if (pillars.some((p) => pointRectDist(p.x, p.z, cand) - p.r < GAP)) continue;
    boxes.push(cand);
  }
}
buildLayout();

const groundTex = makeGroundTexture();
groundTex.repeat.set(H, H);
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(H * 2, H * 2),
  new THREE.MeshLambertMaterial({ map: groundTex })
);
ground.rotation.x = -Math.PI / 2;
scene.add(ground);

// フィールド外（壁の向こう）の地面
const outer = new THREE.Mesh(
  new THREE.PlaneGeometry(400, 400),
  new THREE.MeshLambertMaterial({ color: 0x141318 })
);
outer.rotation.x = -Math.PI / 2;
outer.position.y = -0.02;
scene.add(outer);

const concreteTex = makeConcreteTexture();
const wallMat = new THREE.MeshLambertMaterial({ color: 0x6a6d74, map: concreteTex });
const boxMat = new THREE.MeshLambertMaterial({ color: 0x77705f, map: concreteTex });
const pillarMat = new THREE.MeshLambertMaterial({ color: 0x8a8d96, map: concreteTex });
const borderMat = new THREE.MeshLambertMaterial({ color: 0x3b3c42, map: concreteTex });

{
  const unitBox = new THREE.BoxGeometry(1, 1, 1);
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  const p = new THREE.Vector3();

  const wallList = boxes.filter((b) => b.kind === 'wall');
  const boxList = boxes.filter((b) => b.kind === 'box');
  const walls = new THREE.InstancedMesh(unitBox, wallMat, wallList.length);
  wallList.forEach((b, i) => walls.setMatrixAt(i, m.compose(p.set(b.x, b.h / 2, b.z), q, s.set(b.w, b.h, b.d))));
  scene.add(walls);

  const crates = new THREE.InstancedMesh(unitBox, boxMat, boxList.length);
  boxList.forEach((b, i) => crates.setMatrixAt(i, m.compose(p.set(b.x, b.h / 2, b.z), q, s.set(b.w, b.h, b.d))));
  scene.add(crates);

  const cyl = new THREE.CylinderGeometry(1, 1, 1, 14);
  const cols = new THREE.InstancedMesh(cyl, pillarMat, pillars.length);
  pillars.forEach((c, i) => cols.setMatrixAt(i, m.compose(p.set(c.x, c.h / 2, c.z), q, s.set(c.r, c.h, c.r))));
  scene.add(cols);

  // 外周の壁（見た目用。当たり判定はフィールド範囲のクランプで行う）
  const bh = 3.2;
  const border = new THREE.InstancedMesh(unitBox, borderMat, 4);
  [[0, -H - 0.5, H * 2 + 2, 1], [0, H + 0.5, H * 2 + 2, 1], [-H - 0.5, 0, 1, H * 2 + 2], [H + 0.5, 0, 1, H * 2 + 2]]
    .forEach(([x, z, w, d], i) => border.setMatrixAt(i, m.compose(p.set(x, bh / 2, z), q, s.set(w, bh, d))));
  scene.add(border);
}

// 円（xz平面）を障害物とフィールド外から押し出す
function resolveCollisions(pos, r) {
  for (let pass = 0; pass < 2; pass++) {
    for (const b of boxes) {
      const minX = b.x - b.w / 2, maxX = b.x + b.w / 2;
      const minZ = b.z - b.d / 2, maxZ = b.z + b.d / 2;
      const cx = clamp(pos.x, minX, maxX);
      const cz = clamp(pos.z, minZ, maxZ);
      const dx = pos.x - cx, dz = pos.z - cz;
      const d2 = dx * dx + dz * dz;
      if (d2 >= r * r) continue;
      if (d2 > 1e-8) {
        const d = Math.sqrt(d2);
        pos.x = cx + (dx / d) * r;
        pos.z = cz + (dz / d) * r;
      } else {
        // 中心が箱の中：最も浅い面から外へ
        const l = pos.x - minX, rr = maxX - pos.x, t = pos.z - minZ, bt = maxZ - pos.z;
        const mn = Math.min(l, rr, t, bt);
        if (mn === l) pos.x = minX - r;
        else if (mn === rr) pos.x = maxX + r;
        else if (mn === t) pos.z = minZ - r;
        else pos.z = maxZ + r;
      }
    }
    for (const c of pillars) {
      const dx = pos.x - c.x, dz = pos.z - c.z;
      const rr = c.r + r;
      const d2 = dx * dx + dz * dz;
      if (d2 >= rr * rr) continue;
      const d = Math.sqrt(d2) || 1e-4;
      pos.x = c.x + (dx / d) * rr;
      pos.z = c.z + (dz / d) * rr;
    }
    pos.x = clamp(pos.x, -H + r, H - r);
    pos.z = clamp(pos.z, -H + r, H - r);
  }
}

// ------------------------------------------------------------
// 経路探索用グリッド（プレイヤーからの距離場 = フローフィールド）
//  敵は「距離が減る方向」をたどるので、障害物の裏にいても回り込んでくる
// ------------------------------------------------------------
const GN = H * 2;                  // 1マス = 1m
const blocked = new Uint8Array(GN * GN);
const flow = new Float32Array(GN * GN);
const cellOf = (v) => clamp(Math.floor(v + H), 0, GN - 1);
const cellCenter = (i) => -H + i + 0.5;
{
  const inflate = CONFIG.ENEMY_RADIUS - 0.05;
  for (let j = 0; j < GN; j++) {
    for (let i = 0; i < GN; i++) {
      const x = cellCenter(i), z = cellCenter(j);
      let bad = boxes.some((b) => pointRectDist(x, z, b) < inflate);
      if (!bad) bad = pillars.some((c) => Math.hypot(x - c.x, z - c.z) < c.r + inflate);
      blocked[j * GN + i] = bad ? 1 : 0;
    }
  }
}
const isBlockedAt = (x, z) => blocked[cellOf(z) * GN + cellOf(x)] === 1;

// 小さな二分ヒープ付きダイクストラ（3600マス。数ミリ秒もかからない）
const heapIdx = new Int32Array(GN * GN * 8);
const heapKey = new Float32Array(GN * GN * 8);
const NB = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2]];
function computeFlow(px, pz) {
  flow.fill(Infinity);
  let si = cellOf(px), sj = cellOf(pz);
  if (blocked[sj * GN + si]) {
    // プレイヤーが壁際にいる：近くの空きマスを起点にする
    let found = false;
    for (let r = 1; r < 4 && !found; r++) {
      for (let dj = -r; dj <= r && !found; dj++) {
        for (let di = -r; di <= r && !found; di++) {
          const i = si + di, j = sj + dj;
          if (i < 0 || j < 0 || i >= GN || j >= GN) continue;
          if (!blocked[j * GN + i]) { si = i; sj = j; found = true; }
        }
      }
    }
  }
  let n = 0;
  const push = (idx, key) => {
    let k = n++;
    while (k > 0) {
      const p = (k - 1) >> 1;
      if (heapKey[p] <= key) break;
      heapIdx[k] = heapIdx[p]; heapKey[k] = heapKey[p]; k = p;
    }
    heapIdx[k] = idx; heapKey[k] = key;
  };
  const pop = () => {
    const top = heapIdx[0];
    const lastI = heapIdx[--n], lastK = heapKey[n];
    let k = 0;
    for (;;) {
      let c = 2 * k + 1;
      if (c >= n) break;
      if (c + 1 < n && heapKey[c + 1] < heapKey[c]) c++;
      if (heapKey[c] >= lastK) break;
      heapIdx[k] = heapIdx[c]; heapKey[k] = heapKey[c]; k = c;
    }
    heapIdx[k] = lastI; heapKey[k] = lastK;
    return top;
  };
  const start = sj * GN + si;
  flow[start] = 0;
  push(start, 0);
  while (n > 0) {
    const cur = pop();
    const d = flow[cur];
    const ci = cur % GN, cj = (cur / GN) | 0;
    for (const [di, dj, cost] of NB) {
      const i = ci + di, j = cj + dj;
      if (i < 0 || j < 0 || i >= GN || j >= GN) continue;
      const ni = j * GN + i;
      if (blocked[ni]) continue;
      // 斜め移動は角をすり抜けないときだけ
      if (di && dj && (blocked[cj * GN + i] || blocked[j * GN + ci])) continue;
      const nd = d + cost;
      if (nd < flow[ni]) { flow[ni] = nd; push(ni, nd); }
    }
  }
}

// 2点間に障害物（膨張済み）がないか
function lineClear(x0, z0, x1, z1) {
  const dx = x1 - x0, dz = z1 - z0;
  const len = Math.hypot(dx, dz);
  const steps = Math.ceil(len / 0.4);
  for (let s = 1; s < steps; s++) {
    const t = s / steps;
    if (len * t < 0.7 || len * (1 - t) < 0.7) continue;
    if (isBlockedAt(x0 + dx * t, z0 + dz * t)) return false;
  }
  return true;
}

const _target = { x: 0, z: 0 };
function steerTarget(e) {
  const px = player.pos.x, pz = player.pos.z;
  const ex = e.pos.x, ez = e.pos.z;
  _target.x = px; _target.z = pz;
  if (Math.hypot(px - ex, pz - ez) < 2.5 || lineClear(ex, ez, px, pz)) return _target;

  // 距離場を下っていき、見通せる一番先のマスを目標にする（経路のショートカット）
  let ci = cellOf(ex), cj = cellOf(ez);
  let found = false;
  for (let step = 0; step < 10; step++) {
    const here = flow[cj * GN + ci];
    let best = -1, bestD = step === 0 && blocked[cj * GN + ci] ? Infinity : here;
    for (const [di, dj] of NB) {
      const i = ci + di, j = cj + dj;
      if (i < 0 || j < 0 || i >= GN || j >= GN) continue;
      if (di && dj && (blocked[cj * GN + i] || blocked[j * GN + ci])) continue;
      const v = flow[j * GN + i];
      if (v < bestD) { bestD = v; best = j * GN + i; }
    }
    if (best < 0) break;
    ci = best % GN; cj = (best / GN) | 0;
    const tx = cellCenter(ci), tz = cellCenter(cj);
    if (step === 0 || lineClear(ex, ez, tx, tz)) {
      _target.x = tx; _target.z = tz; found = true;
    } else break;
    if (bestD === 0) break;
  }
  if (!found) { _target.x = px; _target.z = pz; }
  return _target;
}

// ------------------------------------------------------------
// プレイヤー
// ------------------------------------------------------------
const player = {
  pos: new THREE.Vector3(CONFIG.PLAYER_START.x, 0, CONFIG.PLAYER_START.z),
  vel: new THREE.Vector3(),
  facing: Math.PI,
  stamina: CONFIG.STAMINA_MAX,
  staminaLock: false,
  dashing: false,
  runPhase: 0,
};

const playerGroup = new THREE.Group();
const playerBody = new THREE.Group();
{
  const bodyMat = new THREE.MeshLambertMaterial({ color: 0xdfe5ec, emissive: 0x1a2430 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.34, 0.62, 4, 10), bodyMat);
  body.position.y = 0.68;
  playerBody.add(body);
  const visor = new THREE.Mesh(
    new THREE.BoxGeometry(0.44, 0.14, 0.2),
    new THREE.MeshBasicMaterial({ color: 0x52e3ff })
  );
  visor.position.set(0, 1.02, 0.25);
  playerBody.add(visor);
  playerGroup.add(playerBody);

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.55, 0.68, 32),
    new THREE.MeshBasicMaterial({ color: 0x52e3ff, transparent: true, opacity: 0.55, depthWrite: false })
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.03;
  playerGroup.add(ring);

  const sh = new THREE.Mesh(
    new THREE.PlaneGeometry(1.4, 1.4),
    new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false })
  );
  sh.rotation.x = -Math.PI / 2;
  sh.position.y = 0.02;
  playerGroup.add(sh);
}
scene.add(playerGroup);

// ------------------------------------------------------------
// 敵（顔）
// ------------------------------------------------------------
const enemies = [];
const enemyShadowGeo = new THREE.PlaneGeometry(1.8, 1.8);
const enemyShadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false, opacity: 0.8 });
const GHOST_OPACITY = [0.3, 0.17, 0.08];

function createEnemy(x, z) {
  const faceMat = new THREE.SpriteMaterial({
    map: faceTex, fog: false, transparent: true, alphaTest: 0.02, depthWrite: true, toneMapped: false,
  });
  const sprite = new THREE.Sprite(faceMat);
  sprite.scale.set(faceW, faceH, 1);
  sprite.renderOrder = 3;

  const auraMat = new THREE.SpriteMaterial({
    map: auraTex, fog: false, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  });
  const aura = new THREE.Sprite(auraMat);
  aura.scale.set(faceH * 2, faceH * 2, 1);
  aura.renderOrder = 2;

  // 後ろに尾を引く赤い残像
  const ghosts = GHOST_OPACITY.map((op) => {
    const m = new THREE.SpriteMaterial({
      map: faceTex, fog: false, transparent: true, opacity: op, depthWrite: false,
      blending: THREE.AdditiveBlending, color: 0xff3040,
    });
    const s = new THREE.Sprite(m);
    s.scale.set(faceW, faceH, 1);
    s.renderOrder = 1;
    return s;
  });

  const shadow = new THREE.Mesh(enemyShadowGeo, enemyShadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(x, 0.025, z);

  scene.add(shadow, aura, sprite, ...ghosts);

  const e = {
    pos: new THREE.Vector3(x, 0, z),
    vel: new THREE.Vector3(),
    sprite, aura, ghosts, shadow,
    spawnT: 0,
    phase: Math.random() * Math.PI * 2,
    speedMul: 0.92 + Math.random() * 0.16,
    near: 0,
  };
  const y = CONFIG.ENEMY_FLOAT - 2;
  sprite.position.set(x, y, z);
  aura.position.copy(sprite.position);
  ghosts.forEach((g) => g.position.copy(sprite.position));
  enemies.push(e);
  return e;
}

function removeEnemy(e) {
  scene.remove(e.sprite, e.aura, e.shadow, ...e.ghosts);
  e.sprite.material.dispose();
  e.aura.material.dispose();
  e.ghosts.forEach((g) => g.material.dispose());
}

function clearEnemies() {
  enemies.forEach(removeEnemy);
  enemies.length = 0;
}

function findSpawnPoint() {
  let best = null, bestD = -1;
  for (let i = 0; i < 60; i++) {
    const x = (Math.random() * 2 - 1) * (H - 3);
    const z = (Math.random() * 2 - 1) * (H - 3);
    if (isBlockedAt(x, z)) continue;
    if (!Number.isFinite(flow[cellOf(z) * GN + cellOf(x)])) continue; // 到達できない場所は除外
    if (enemies.some((e) => Math.hypot(e.pos.x - x, e.pos.z - z) < 4)) continue;
    const d = Math.hypot(x - player.pos.x, z - player.pos.z);
    if (d >= CONFIG.SPAWN_MIN_DIST) return { x, z };
    if (d > bestD) { bestD = d; best = { x, z }; }
  }
  return best || { x: -H + 3, z: -H + 3 };
}

function spawnEnemy(announce) {
  const p = findSpawnPoint();
  createEnemy(p.x, p.z);
  if (announce) {
    Sound.spawn();
    ui.toast.textContent = 'FACE +1';
    restartAnim(ui.toast, 'pop');
  }
}

// ------------------------------------------------------------
// 入力（キーボード / 仮想ジョイスティック / ダッシュボタン）
// ------------------------------------------------------------
const keys = Object.create(null);
const joy = { id: null, x: 0, y: 0, cx: 0, cy: 0, active: false };
let dashTouch = false;
const JOY_R = 56;

window.addEventListener('keydown', (e) => {
  keys[e.code] = true;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
  if (e.code === 'Enter' && !e.repeat) {
    if (game.state === 'title' && !ui.startBtn.disabled) ui.startBtn.click();
    else if (game.state === 'over') ui.retry.click();
  }
  if (e.code === 'KeyM' && !e.repeat) toggleMute();
});
window.addEventListener('keyup', (e) => { keys[e.code] = false; });
window.addEventListener('blur', () => {
  for (const k in keys) keys[k] = false;
  resetJoy();
  setDash(false);
});

function joyHome() {
  ui.joyBase.style.left = '';
  ui.joyBase.style.top = '';
  ui.joyBase.style.bottom = '';
}
function resetJoy() {
  joy.id = null; joy.x = 0; joy.y = 0; joy.active = false;
  ui.joyKnob.style.transform = '';
  ui.joyBase.classList.remove('active');
  joyHome();
}
function moveJoy(e) {
  let dx = e.clientX - joy.cx, dy = e.clientY - joy.cy;
  const len = Math.hypot(dx, dy);
  if (len > JOY_R) { dx = (dx / len) * JOY_R; dy = (dy / len) * JOY_R; }
  ui.joyKnob.style.transform = `translate(${dx}px, ${dy}px)`;
  const m = Math.min(len, JOY_R) / JOY_R;
  const dead = 0.12;
  const k = m < dead ? 0 : (m - dead) / (1 - dead) / (m || 1);
  joy.x = (dx / JOY_R) * k;
  joy.y = (dy / JOY_R) * k;
}
ui.joyZone.addEventListener('pointerdown', (e) => {
  if (joy.id !== null) return;
  e.preventDefault();
  joy.id = e.pointerId;
  joy.active = true;
  try { ui.joyZone.setPointerCapture(e.pointerId); } catch (err) { /* 古いブラウザ */ }
  // 指を置いた場所にスティックを移動（どこから触っても操作できる）
  const zr = ui.joyZone.getBoundingClientRect();
  const size = ui.joyBase.offsetWidth;
  const cx = clamp(e.clientX, zr.left + size / 2, zr.right - size / 2);
  const cy = clamp(e.clientY, zr.top + size / 2, zr.bottom - size / 2);
  joy.cx = cx; joy.cy = cy;
  ui.joyBase.style.left = `${cx - zr.left - size / 2}px`;
  ui.joyBase.style.top = `${cy - zr.top - size / 2}px`;
  ui.joyBase.style.bottom = 'auto';
  ui.joyBase.classList.add('active');
  moveJoy(e);
});
ui.joyZone.addEventListener('pointermove', (e) => { if (e.pointerId === joy.id) moveJoy(e); });
const joyEnd = (e) => { if (e.pointerId === joy.id) resetJoy(); };
ui.joyZone.addEventListener('pointerup', joyEnd);
ui.joyZone.addEventListener('pointercancel', joyEnd);
ui.joyZone.addEventListener('lostpointercapture', joyEnd);

function setDash(on) {
  dashTouch = on;
  ui.dash.classList.toggle('pressed', on);
}
ui.dash.addEventListener('pointerdown', (e) => {
  e.preventDefault();
  try { ui.dash.setPointerCapture(e.pointerId); } catch (err) { /* 古いブラウザ */ }
  setDash(true);
});
['pointerup', 'pointercancel', 'lostpointercapture'].forEach((t) => ui.dash.addEventListener(t, () => setDash(false)));

// ページのスクロール・ピンチ・ダブルタップ拡大・長押しメニューを止める
document.addEventListener('touchmove', (e) => { if (e.cancelable) e.preventDefault(); }, { passive: false });
document.addEventListener('gesturestart', (e) => e.preventDefault());
document.addEventListener('dblclick', (e) => e.preventDefault());
document.addEventListener('contextmenu', (e) => e.preventDefault());
window.addEventListener('pointerdown', (e) => {
  if (e.pointerType === 'touch' && !document.body.classList.contains('is-touch')) {
    document.body.classList.add('is-touch');
  }
});

const _input = new THREE.Vector2();
function readInput() {
  let x = 0, z = 0;
  if (keys.KeyA || keys.ArrowLeft) x -= 1;
  if (keys.KeyD || keys.ArrowRight) x += 1;
  if (keys.KeyW || keys.ArrowUp) z -= 1;
  if (keys.KeyS || keys.ArrowDown) z += 1;
  const kl = Math.hypot(x, z);
  if (kl > 0) { x /= kl; z /= kl; }
  // キーとスティックは大きい方を採用
  if (Math.hypot(joy.x, joy.y) > kl) { x = joy.x; z = joy.y; }
  _input.set(x, z);
  if (_input.lengthSq() > 1) _input.normalize();
  return _input;
}
const wantsDash = () => !!(keys.ShiftLeft || keys.ShiftRight || keys.Space || dashTouch);

// ------------------------------------------------------------
// 画面外の敵インジケーター（顔アイコン＋矢印）
// ------------------------------------------------------------
const indicatorPool = [];
for (let i = 0; i < CONFIG.MAX_ENEMIES; i++) {
  const root = document.createElement('div');
  root.className = 'ind';
  const face = document.createElement('div');
  face.className = 'ind-face';
  const arrow = document.createElement('div');
  arrow.className = 'ind-arrow';
  root.append(arrow, face);
  root.style.display = 'none';
  ui.indicators.appendChild(root);
  indicatorPool.push({ root, face, arrow, shown: false });
}
const _proj = new THREE.Vector3();
function updateIndicators() {
  const w = window.innerWidth, h = window.innerHeight;
  const active = game.state === 'playing';
  for (let i = 0; i < indicatorPool.length; i++) {
    const ind = indicatorPool[i];
    const e = enemies[i];
    let show = false;
    if (active && e && e.spawnT >= 1) {
      _proj.copy(e.sprite.position).project(camera);
      const behind = _proj.z > 1;
      let x = _proj.x, y = _proj.y;
      if (behind) { x = -x; y = -y; }
      if (behind || Math.abs(x) > 0.94 || Math.abs(y) > 0.94) {
        show = true;
        const ang = Math.atan2(-y, x);           // 画面座標（下が+）での向き
        const dx = Math.cos(ang), dy = Math.sin(ang);
        const m = 40;
        const hw = w / 2 - m, hh = h / 2 - m - 20;
        const s = Math.min(hw / Math.max(Math.abs(dx), 1e-4), hh / Math.max(Math.abs(dy), 1e-4));
        const px = w / 2 + dx * s, py = h / 2 + 10 + dy * s;
        ind.root.style.transform = `translate(${px.toFixed(1)}px, ${py.toFixed(1)}px)`;
        ind.arrow.style.transform = `rotate(${ang.toFixed(3)}rad) translateX(26px)`;
        const d = Math.hypot(e.pos.x - player.pos.x, e.pos.z - player.pos.z);
        ind.root.style.opacity = (1 - clamp((d - 4) / 30, 0, 0.65)).toFixed(2);
      }
    }
    if (show !== ind.shown) {
      ind.root.style.display = show ? '' : 'none';
      ind.shown = show;
    }
  }
}

// ------------------------------------------------------------
// ゲーム状態
// ------------------------------------------------------------
const game = {
  state: 'loading',  // loading → title → countdown → playing → caught → over
  time: 0,
  cdT: 0, cdStep: -1,
  goHideT: 0,
  caughtT: 0, catcher: null, catchFrom: new THREE.Vector3(), catchScaleFrom: new THREE.Vector2(),
  caughtFlags: { flash: false, text: false, panel: false },
  intensity: 0,
  heartT: 0,
  shake: 0,
  flowCell: -1, flowT: 0,
  best: parseFloat(store.get('faceChase.best', '0')) || 0,
  invincible: false,
  titleAngle: 0,
  lastTimeText: '',
};

function formatClock(t) {
  const s = Math.floor(t);
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

function setTouchVisible(v) {
  ui.touch.classList.toggle('hidden', !v);
  if (!v) { resetJoy(); setDash(false); }
}

function enterTitle() {
  game.state = 'title';
  ui.startBtn.disabled = false;
  ui.startBtn.textContent = 'START';
  // タイトル画面の奥で、顔がじっとこちらを見ている
  clearEnemies();
  const e = createEnemy(0, -2);
  e.spawnT = 1;
  playerGroup.visible = false;
}

function startGame() {
  Sound.init();
  clearEnemies();
  player.pos.set(CONFIG.PLAYER_START.x, 0, CONFIG.PLAYER_START.z);
  player.vel.set(0, 0, 0);
  player.facing = Math.PI;
  player.stamina = CONFIG.STAMINA_MAX;
  player.staminaLock = false;
  player.dashing = false;
  playerGroup.visible = true;
  playerGroup.position.copy(player.pos);
  playerGroup.rotation.y = player.facing;

  game.time = 0;
  game.intensity = 0;
  game.shake = 0;
  game.heartT = 0;
  game.catcher = null;
  game.caughtFlags = { flash: false, text: false, panel: false };
  game.lastTimeText = '';
  computeFlow(player.pos.x, player.pos.z);
  game.flowCell = cellOf(player.pos.z) * GN + cellOf(player.pos.x);
  spawnEnemy(false);

  ui.title.classList.add('hidden');
  ui.end.classList.add('hidden');
  ui.caughtText.classList.remove('show');
  ui.overPanel.classList.remove('show');
  ui.newBest.classList.add('hidden');
  ui.dim.classList.remove('on');
  ui.flash.classList.remove('pop');
  ui.warning.classList.add('hidden');
  ui.hud.classList.remove('hidden');
  ui.time.textContent = '00:00';
  ui.faces.textContent = 'FACE ×1';
  ui.vignette.style.opacity = '0';
  ui.danger.style.opacity = '0';
  setTouchVisible(document.body.classList.contains('is-touch'));

  snapCamera();
  game.state = 'countdown';
  game.cdT = 0;
  game.cdStep = -1;
}

function beginPlay() {
  game.state = 'playing';
  game.goHideT = 0.6;
  Sound.startDrone();
}

function startCatch(e) {
  game.state = 'caught';
  game.caughtT = 0;
  game.catcher = e;
  game.catchFrom.copy(e.sprite.position);
  game.catchScaleFrom.set(e.sprite.scale.x, e.sprite.scale.y);
  e.sprite.renderOrder = 20;
  e.sprite.material.depthTest = false;
  e.ghosts.forEach((g) => { g.visible = false; });
  e.aura.visible = false;
  Sound.stopDrone();
  Sound.caught();
  setTouchVisible(false);
  ui.warning.classList.add('hidden');
  ui.countdown.textContent = '';

  const t = game.time;
  const isBest = t > game.best;
  if (isBest) { game.best = t; store.set('faceChase.best', t.toFixed(2)); }
  ui.overTime.textContent = `生存時間：${t.toFixed(2)}秒`;
  ui.overBest.textContent = `BEST：${game.best.toFixed(2)}秒`;
  ui.newBest.classList.toggle('hidden', !isBest);
}

// ------------------------------------------------------------
// カメラ（プレイヤーの後ろ・上から見る三人称。向きは固定で、画面の上＝前）
// ------------------------------------------------------------
const camBase = new THREE.Vector3();
const camLook = new THREE.Vector3();
const _v = new THREE.Vector3();

function camOffset() {
  const a = camera.aspect;
  if (a < 0.7) return { h: 13, d: 10, ahead: -2.5 };   // スマホ縦
  if (a < 1.2) return { h: 11.5, d: 10, ahead: -1.5 };
  return { h: 9.5, d: 10.5, ahead: -1 };               // PC・横画面
}
function snapCamera() {
  const o = camOffset();
  camBase.set(player.pos.x, o.h, player.pos.z + o.d);
  camLook.set(player.pos.x, 0.8, player.pos.z + o.ahead);
}
function updateCamera(dt) {
  if (game.state === 'title' || game.state === 'loading') {
    game.titleAngle += dt * 0.12;
    camBase.set(Math.sin(game.titleAngle) * 24, 9, Math.cos(game.titleAngle) * 24);
    camLook.set(0, 1.5, 0);
  } else if (game.state === 'countdown' || game.state === 'playing') {
    const o = camOffset();
    _v.set(player.pos.x, o.h, player.pos.z + o.d);
    camBase.lerp(_v, damp(6, dt));
    _v.set(player.pos.x, 0.8, player.pos.z + o.ahead);
    camLook.lerp(_v, damp(8, dt));
  }
  // caught / over ではカメラを止める

  camera.position.copy(camBase);
  camera.lookAt(camLook);
  if (game.shake > 0.001) {
    const s = game.shake;
    camera.position.x += (Math.random() - 0.5) * s;
    camera.position.y += (Math.random() - 0.5) * s;
    camera.rotation.z += (Math.random() - 0.5) * s * 0.08;
  }

  const targetFov = player.dashing && game.state === 'playing' ? BASE_FOV + 6 : BASE_FOV;
  if (Math.abs(camera.fov - targetFov) > 0.01) {
    camera.fov = lerp(camera.fov, targetFov, damp(6, dt));
    camera.updateProjectionMatrix();
  }
  sky.position.copy(camera.position);
}

// ------------------------------------------------------------
// 更新
// ------------------------------------------------------------
function updatePlayer(dt, canMove) {
  const input = canMove ? readInput() : _input.set(0, 0);
  const moving = input.lengthSq() > 0.0025;

  const dashOk = moving && wantsDash() && !player.staminaLock && player.stamina > 0;
  player.dashing = dashOk;
  if (dashOk) {
    player.stamina -= CONFIG.STAMINA_DRAIN * dt;
    if (player.stamina <= 0) { player.stamina = 0; player.staminaLock = true; }
  } else {
    player.stamina = Math.min(CONFIG.STAMINA_MAX, player.stamina + CONFIG.STAMINA_REGEN * dt);
    if (player.staminaLock && player.stamina >= CONFIG.STAMINA_UNLOCK) player.staminaLock = false;
  }

  const speed = dashOk ? CONFIG.DASH_SPEED : CONFIG.PLAYER_SPEED;
  _v.set(input.x * speed, 0, input.y * speed);
  player.vel.lerp(_v, damp(12, dt));
  player.pos.addScaledVector(player.vel, dt);
  resolveCollisions(player.pos, CONFIG.PLAYER_RADIUS);

  const sp = Math.hypot(player.vel.x, player.vel.z);
  if (sp > 0.3) player.facing = lerpAngle(player.facing, Math.atan2(player.vel.x, player.vel.z), damp(12, dt));
  player.runPhase += dt * sp * 2.4;
  const f = clamp(sp / CONFIG.DASH_SPEED, 0, 1);
  playerGroup.position.copy(player.pos);
  playerGroup.rotation.y = player.facing;
  playerBody.position.y = Math.abs(Math.sin(player.runPhase)) * 0.12 * f;
  playerBody.rotation.x = f * 0.22;

  const pct = (player.stamina / CONFIG.STAMINA_MAX) * 100;
  ui.stamina.style.transform = `scaleX(${(pct / 100).toFixed(3)})`;
  ui.stamina.classList.toggle('low', player.staminaLock);
  ui.dash.style.setProperty('--st', `${pct.toFixed(1)}%`);
  ui.dash.classList.toggle('low', player.staminaLock);
}

const _sep = new THREE.Vector3();
function updateEnemies(dt, now, canMove) {
  const speedBase = Math.min(CONFIG.ENEMY_MAX_SPEED, CONFIG.ENEMY_BASE_SPEED + CONFIG.ENEMY_SPEED_GAIN * game.time);
  let nearest = Infinity;

  for (const e of enemies) {
    if (e === game.catcher) continue;
    e.spawnT = Math.min(1, e.spawnT + dt / CONFIG.SPAWN_RISE_TIME);

    if (canMove) {
      const t = steerTarget(e);
      _v.set(t.x - e.pos.x, 0, t.z - e.pos.z);
      const len = _v.length();
      if (len > 1e-4) _v.multiplyScalar(1 / len);
      // 仲間同士で重ならないように少し離れる
      _sep.set(0, 0, 0);
      for (const o of enemies) {
        if (o === e) continue;
        const dx = e.pos.x - o.pos.x, dz = e.pos.z - o.pos.z;
        const d2 = dx * dx + dz * dz;
        if (d2 < 2.6 && d2 > 1e-6) {
          const d = Math.sqrt(d2);
          _sep.x += (dx / d) * (1.6 - d);
          _sep.z += (dz / d) * (1.6 - d);
        }
      }
      _v.addScaledVector(_sep, 0.9);
      const rising = e.spawnT < 1 ? 0.25 : 1;
      _v.normalize().multiplyScalar(speedBase * e.speedMul * rising);
      e.vel.lerp(_v, damp(5, dt));
      e.pos.addScaledVector(e.vel, dt);
      resolveCollisions(e.pos, CONFIG.ENEMY_RADIUS);
    }

    const d = Math.hypot(e.pos.x - player.pos.x, e.pos.z - player.pos.z);
    if (e.spawnT >= 1 && d < nearest) nearest = d;
    e.near = clamp(1 - (d - 1.5) / 6, 0, 1);

    // 見た目：ふわふわ浮いて、近いほど小刻みに震える
    const rise = 1 - Math.pow(1 - e.spawnT, 3);
    const bob = Math.sin(now * 2.1 + e.phase) * 0.14;
    const jit = e.near * e.near;
    e.sprite.position.set(
      e.pos.x + (Math.random() - 0.5) * 0.08 * jit,
      lerp(CONFIG.ENEMY_FLOAT - 2, CONFIG.ENEMY_FLOAT, rise) + bob + (Math.random() - 0.5) * 0.08 * jit,
      e.pos.z
    );
    const pulse = 1 + Math.sin(now * 3 + e.phase) * 0.02 + jit * 0.08;
    e.sprite.scale.set(faceW * pulse * (1 + (Math.random() - 0.5) * 0.08 * jit), faceH * pulse, 1);
    e.sprite.material.rotation = Math.sin(now * 1.3 + e.phase) * 0.07 + (Math.random() - 0.5) * 0.12 * jit;
    e.sprite.material.opacity = clamp(e.spawnT * 1.4, 0, 1);
    const b = 0.78 + 0.22 * e.near;
    e.sprite.material.color.setRGB(b, b, b);

    e.aura.position.copy(e.sprite.position);
    e.aura.material.opacity = (0.55 + Math.sin(now * 5 + e.phase) * 0.15 + e.near * 0.4) * e.spawnT;
    const as = faceH * (2 + e.near * 0.5);
    e.aura.scale.set(as, as, 1);

    let prev = e.sprite.position;
    const moveSp = Math.hypot(e.vel.x, e.vel.z);
    for (let i = 0; i < e.ghosts.length; i++) {
      const g = e.ghosts[i];
      g.position.lerp(prev, damp(9, dt));
      g.scale.copy(e.sprite.scale);
      g.material.opacity = GHOST_OPACITY[i] * clamp(moveSp / 3, 0, 1) * e.spawnT;
      prev = g.position;
    }

    e.shadow.position.set(e.pos.x, 0.025, e.pos.z);
    const ss = 0.6 + 0.6 * rise;
    e.shadow.scale.set(ss, ss, 1);
  }
  return nearest;
}

function updateTension(dt, nearest, now) {
  const raw = clamp(1 - (nearest - 1.5) / (CONFIG.DANGER_DISTANCE - 1.5), 0, 1);
  game.intensity = lerp(game.intensity, raw, damp(6, dt));
  const k = game.intensity;

  ui.vignette.style.opacity = (0.25 + k * 0.75).toFixed(3);
  const pulse = 0.75 + 0.25 * Math.sin(now * (6 + k * 10));
  ui.danger.style.opacity = (k * k * 0.85 * pulse).toFixed(3);
  const showWarn = k > 0.35;
  ui.warning.classList.toggle('hidden', !showWarn);
  if (showWarn) ui.warning.style.opacity = (0.55 + 0.45 * Math.abs(Math.sin(now * (4 + k * 8)))).toFixed(2);

  game.shake = k > 0.4 ? (k - 0.4) * 0.35 : 0;

  // 近いほど暗く、霧が濃くなる
  hemi.intensity = HEMI_BASE * (1 - 0.5 * k);
  sun.intensity = DIR_BASE * (1 - 0.55 * k);
  scene.fog.far = lerp(FOG_FAR, 30, k);
  scene.fog.near = lerp(FOG_NEAR, 6, k);

  Sound.setDrone(k);
  if (k > 0.06) {
    game.heartT -= dt;
    if (game.heartT <= 0) {
      Sound.heartbeat(k);
      game.heartT = lerp(1.1, 0.34, k);
    }
  } else {
    game.heartT = Math.min(game.heartT, 0.25);
  }
}

function resetTensionVisuals() {
  hemi.intensity = HEMI_BASE;
  sun.intensity = DIR_BASE;
  scene.fog.far = FOG_FAR;
  scene.fog.near = FOG_NEAR;
}

const _fwd = new THREE.Vector3();
function updateCaught(dt, now) {
  game.caughtT += dt;
  const e = game.catcher;
  const T = game.caughtT;

  // 1. 顔が画面いっぱいまで急接近
  camera.getWorldDirection(_fwd);
  const dist = 1.0;
  _v.copy(camBase).addScaledVector(_fwd, dist);
  const k = clamp(T / 0.42, 0, 1);
  const ease = k * k * k;
  e.sprite.position.lerpVectors(game.catchFrom, _v, ease);
  const visH = 2 * dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const visW = visH * camera.aspect;
  // 縦は画面の高さいっぱい（縦長画面では左右がはみ出す）
  const fillH = visH * 1.02;
  const breathe = T > 0.42 ? 1 + Math.sin(now * 2.2) * 0.025 : 1;
  const sh = lerp(game.catchScaleFrom.y, fillH, ease) * breathe;
  e.sprite.scale.set(sh * faceAspect, sh, 1);
  e.sprite.material.rotation = T < 0.42 ? (Math.random() - 0.5) * 0.25 * ease : Math.sin(now * 1.5) * 0.03;
  e.sprite.material.opacity = 1;
  e.sprite.material.color.setRGB(1, 1, 1);

  // 2. フラッシュ
  if (!game.caughtFlags.flash && T >= 0.42) {
    game.caughtFlags.flash = true;
    restartAnim(ui.flash, 'pop');
    Sound.boom();
    game.shake = 0.6;
    ui.vignette.style.opacity = '0.9';
    ui.danger.style.opacity = '0.6';
  }
  // 3〜4. 停止して「そこそこバっチリ」
  if (!game.caughtFlags.text && T >= 0.8) {
    game.caughtFlags.text = true;
    ui.end.classList.remove('hidden');
    ui.dim.classList.add('on');
    ui.hud.classList.add('hidden');
    restartAnim(ui.caughtText, 'show');
    Sound.jingle();
    game.shake = 0.35;
  }
  // 少し間を置いて GAME OVER
  if (!game.caughtFlags.panel && T >= 2.3) {
    game.caughtFlags.panel = true;
    ui.overPanel.classList.add('show');
    game.state = 'over';
  }
  game.shake = Math.max(0, game.shake - dt * 0.9);
}

function update(dt, now) {
  switch (game.state) {
    case 'loading':
    case 'title':
      updateEnemies(dt, now, false);
      break;

    case 'countdown': {
      game.cdT += dt;
      const step = Math.floor(game.cdT / 0.8);
      if (step !== game.cdStep) {
        game.cdStep = step;
        if (step <= 2) {
          ui.countdown.textContent = String(3 - step);
          ui.countdown.classList.remove('go');
          restartAnim(ui.countdown, 'tick');
          Sound.countBeep();
        } else {
          ui.countdown.textContent = 'GO!';
          ui.countdown.classList.add('go');
          restartAnim(ui.countdown, 'tick');
          Sound.go();
          beginPlay();
        }
      }
      updatePlayer(dt, false);
      updateEnemies(dt, now, false);
      break;
    }

    case 'playing': {
      if (game.goHideT > 0) {
        game.goHideT -= dt;
        if (game.goHideT <= 0) { ui.countdown.textContent = ''; ui.countdown.classList.remove('tick', 'go'); }
      }
      game.time += dt;
      const txt = formatClock(game.time);
      if (txt !== game.lastTimeText) { ui.time.textContent = txt; game.lastTimeText = txt; }

      // 難易度：10秒ごとに1体（上限あり）
      const want = Math.min(CONFIG.MAX_ENEMIES, 1 + Math.floor(game.time / CONFIG.SPAWN_INTERVAL));
      while (enemies.length < want) {
        spawnEnemy(true);
        ui.faces.textContent = `FACE ×${enemies.length}`;
      }

      updatePlayer(dt, true);

      const pc = cellOf(player.pos.z) * GN + cellOf(player.pos.x);
      game.flowT -= dt;
      if (pc !== game.flowCell || game.flowT <= 0) {
        computeFlow(player.pos.x, player.pos.z);
        game.flowCell = pc;
        game.flowT = 0.5;
      }

      const nearest = updateEnemies(dt, now, true);
      updateTension(dt, nearest, now);

      if (!game.invincible) {
        for (const e of enemies) {
          if (e.spawnT < 1) continue;
          if (Math.hypot(e.pos.x - player.pos.x, e.pos.z - player.pos.z) < CONFIG.CATCH_DISTANCE) {
            startCatch(e);
            break;
          }
        }
      }
      break;
    }

    case 'caught':
    case 'over':
      updateEnemies(dt, now, false);
      updateCaught(dt, now);
      break;
  }

  updateCamera(dt);
  updateIndicators();
}

// ------------------------------------------------------------
// ループとリサイズ
// ------------------------------------------------------------
function onResize() {
  const w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', onResize);
window.addEventListener('orientationchange', () => setTimeout(onResize, 200));
if (window.visualViewport) window.visualViewport.addEventListener('resize', onResize);
onResize();

document.addEventListener('visibilitychange', () => {
  if (document.hidden) Sound.suspend(); else Sound.resume();
});

let lastT = performance.now();
function frame(t) {
  requestAnimationFrame(frame);
  const dt = Math.min((t - lastT) / 1000, 0.05); // タブ復帰時などの大きな飛びを抑える
  lastT = t;
  update(dt, t / 1000);
  renderer.render(scene, camera);
}

// ------------------------------------------------------------
// ボタン
// ------------------------------------------------------------
function toggleMute() {
  const m = Sound.toggleMute();
  ui.mute.textContent = m ? 'SOUND OFF' : 'SOUND ON';
  ui.mute.classList.toggle('off', m);
}
ui.mute.textContent = Sound.muted ? 'SOUND OFF' : 'SOUND ON';
ui.mute.classList.toggle('off', Sound.muted);
ui.mute.addEventListener('click', (e) => { e.stopPropagation(); Sound.init(); toggleMute(); });

ui.startBtn.addEventListener('click', () => {
  if (game.state !== 'title') return;
  startGame();
});
ui.retry.addEventListener('click', () => {
  if (game.state !== 'over') return;
  resetTensionVisuals();
  startGame();
});

// ------------------------------------------------------------
// 起動
// ------------------------------------------------------------
window.__faceChaseReady = true;
requestAnimationFrame(frame);
loadFace().then((f) => {
  setFace(f);
  enterTitle();
});

if (DEBUG) {
  window.__fc = { game, player, enemies, CONFIG, Sound, drawPlaceholderFace, faceInfo: () => ({ faceAspect, faceW, faceH }) };
}
