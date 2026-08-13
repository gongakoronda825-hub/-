import { WATCH_SHOW_THRESHOLD } from '../core/config';
import type { GameState } from '../core/GameState';

/**
 * 常時表示の HUD（指示書 §15）。
 *
 * スコア・危険度・スタミナ・視認ゲージ。DOM で作る。3D の上に文字を置くだけなら
 * Canvas やスプライトより DOM のほうが軽いし、解像度も端末に合う。
 *
 * 数字は毎フレーム書き換えず、変わったときだけ触る（モバイルでは
 * textContent の代入がそのままレイアウト再計算になる）。
 */
export class Hud {
  private readonly scoreEl: HTMLElement;
  private readonly pingsEl: HTMLElement;
  private readonly comboEl: HTMLElement;
  private readonly comboCount: HTMLElement;
  private readonly townEl: HTMLElement;
  private readonly dangerFill: HTMLElement;
  private readonly dangerLabel: HTMLElement;
  private readonly staminaFill: HTMLElement;
  private readonly watch: HTMLElement;
  private readonly watchFill: HTMLElement;
  private readonly vignette: HTMLElement;
  private readonly toasts: HTMLElement;
  private readonly gains: HTMLElement;

  private lastScore = -1;
  private lastPings = -1;
  private lastTier = '';
  private lastCombo = -1;
  private lastTown = -1;

  constructor(parent: HTMLElement) {
    const root = document.createElement('div');
    root.innerHTML = `
      <div id="hud">
        <div class="score">0<span class="unit">pt</span></div>
        <div class="pings">ピンポン 0回</div>
        <div class="town">街の住民 0人</div>
        <div class="meter danger">
          <div class="label"><span>危険度</span><span class="tier">しずか</span></div>
          <div class="bar"><div class="fill"></div></div>
        </div>
        <div class="meter stamina">
          <div class="label"><span>スタミナ</span></div>
          <div class="bar"><div class="fill"></div></div>
        </div>
      </div>
      <div id="combo"><b class="count">2</b><span class="label">COMBO</span></div>
      <div id="watch">
        <div class="eye">みられている</div>
        <div class="bar"><div class="fill"></div></div>
      </div>
      <div id="vignette"></div>
      <div id="toasts"></div>
      <div id="gains"></div>
    `;
    while (root.firstElementChild) parent.appendChild(root.firstElementChild);

    const find = <T extends HTMLElement>(selector: string): T => {
      const el = parent.querySelector<T>(selector);
      if (!el) throw new Error(`HUD の要素が見つかりません: ${selector}`);
      return el;
    };

    this.scoreEl = find('#hud .score');
    this.pingsEl = find('#hud .pings');
    this.townEl = find('#hud .town');
    this.comboEl = find('#combo');
    this.comboCount = find('#combo .count');
    this.dangerFill = find('#hud .danger .fill');
    this.dangerLabel = find('#hud .danger .tier');
    this.staminaFill = find('#hud .stamina .fill');
    this.watch = find('#watch');
    this.watchFill = find('#watch .fill');
    this.vignette = find('#vignette');
    this.toasts = find('#toasts');
    this.gains = find('#gains');
  }

  update(state: GameState, stamina: number, gauge: number, townResidents: number): void {
    if (state.score !== this.lastScore) {
      this.scoreEl.innerHTML = `${state.score}<span class="unit">pt</span>`;
      this.lastScore = state.score;
      // 一度クラスを外してから付け直さないと、続けて加点したときに再生されない
      this.scoreEl.classList.remove('bump');
      void this.scoreEl.offsetWidth;
      this.scoreEl.classList.add('bump');
    }

    if (state.pings !== this.lastPings) {
      this.pingsEl.textContent = `ピンポン ${state.pings}回`;
      this.lastPings = state.pings;
    }

    // 街を何人が歩いているか。増えていくのが見えるだけで緊張感が変わる
    if (townResidents !== this.lastTown) {
      this.townEl.textContent = `街の住民 ${townResidents}人`;
      this.townEl.classList.toggle('busy', townResidents >= 3);
      this.lastTown = townResidents;
    }

    // コンボは2連続目から出す。1回目から出ていると「連続」だと伝わらない
    if (state.combo !== this.lastCombo) {
      const showing = state.combo >= 2;
      this.comboEl.classList.toggle('on', showing);
      if (showing) {
        this.comboCount.textContent = String(state.combo);
        this.comboEl.classList.remove('bump');
        void this.comboEl.offsetWidth;
        this.comboEl.classList.add('bump');
      }
      this.lastCombo = state.combo;
    }

    const tier = state.tier;
    if (tier.label !== this.lastTier) {
      this.dangerLabel.textContent = tier.label;
      this.lastTier = tier.label;
    }

    this.dangerFill.style.width = `${Math.round(state.dangerRatio * 100)}%`;
    // 危険度が上がるほど黄 → 赤へ。数字を読まなくても色で分かるように
    this.dangerFill.style.background = `hsl(${48 - state.dangerRatio * 48}, 92%, 60%)`;

    this.staminaFill.style.width = `${Math.round(stamina * 100)}%`;

    const showing = gauge > WATCH_SHOW_THRESHOLD;
    this.watch.classList.toggle('on', showing);
    this.watchFill.style.width = `${Math.round(gauge * 100)}%`;
    this.vignette.style.opacity = String(Math.max(0, gauge - 0.25) * 1.1);
  }

  /** 画面中央のテロップ。 */
  toast(text: string, kind: 'normal' | 'good' | 'bad' = 'normal'): void {
    const el = document.createElement('div');
    el.className = `toast ${kind}`;
    el.textContent = text;
    this.toasts.appendChild(el);
    setTimeout(() => el.remove(), 950);
  }

  /** 獲得ポイントの飛び出し。 */
  gain(points: number): void {
    const el = document.createElement('div');
    el.className = 'gain';
    el.textContent = `+${points}`;
    this.gains.appendChild(el);
    setTimeout(() => el.remove(), 900);
  }

  reset(): void {
    this.lastScore = -1;
    this.lastPings = -1;
    this.lastTier = '';
    this.lastCombo = -1;
    this.lastTown = -1;
    this.comboEl.classList.remove('on');
    this.toasts.replaceChildren();
    this.gains.replaceChildren();
    this.vignette.style.opacity = '0';
    this.watch.classList.remove('on');
  }
}
