/**
 * 効果音。Web Audio で作る（音声ファイルは持たない＝1ファイル配布のまま）。
 *
 * このゲームでいちばん大事な音は「ピンポーン」。押した手触りの半分は音なので、
 * 2音の下降（ピン → ポーン）をちゃんと鳴らす。
 *
 * AudioContext はユーザー操作のあとでないと動かない端末があるので、
 * 最初の音を鳴らすときに resume() を試みる。失敗しても無音で続行する。
 */
export class Sfx {
  private context: AudioContext | null = null;
  private muted = false;

  /** 「はじめる」を押したときに呼ぶ。ここで作れば自動再生の制限に引っかからない。 */
  unlock(): void {
    if (this.context) {
      void this.context.resume().catch(() => {});
      return;
    }
    try {
      this.context = new AudioContext();
    } catch {
      this.muted = true;
    }
  }

  /** インターホン。2音を続けて鳴らす。 */
  ping(): void {
    this.tone(988, 0.42, 'sine', 0.001);
    this.tone(784, 0.75, 'sine', 0.36);
  }

  /** 玄関が開いた音。低めのノック。 */
  door(): void {
    this.tone(180, 0.14, 'square', 0, 0.16);
    this.tone(140, 0.18, 'square', 0.09, 0.16);
  }

  /** 追跡開始。危機感のある上昇音。 */
  alert(): void {
    this.tone(330, 0.12, 'sawtooth', 0, 0.14);
    this.tone(440, 0.12, 'sawtooth', 0.1, 0.14);
    this.tone(587, 0.3, 'sawtooth', 0.2, 0.14);
  }

  /** 逃げ切り。ほっとする和音。 */
  escape(): void {
    this.tone(523, 0.3, 'triangle', 0, 0.18);
    this.tone(659, 0.3, 'triangle', 0.06, 0.18);
    this.tone(784, 0.45, 'triangle', 0.12, 0.18);
  }

  /** 捕まった。 */
  caught(): void {
    this.tone(220, 0.5, 'sawtooth', 0, 0.2);
    this.tone(155, 0.9, 'sawtooth', 0.12, 0.2);
  }

  /**
   * @param frequency 周波数
   * @param duration  長さ（秒）
   * @param type      波形
   * @param delay     鳴らし始めるまでの待ち（秒）
   * @param volume    音量
   */
  private tone(
    frequency: number,
    duration: number,
    type: OscillatorType,
    delay = 0,
    volume = 0.22,
  ): void {
    if (this.muted || !this.context) return;

    const ctx = this.context;
    const start = ctx.currentTime + delay;

    const osc = ctx.createOscillator();
    osc.type = type;
    osc.frequency.setValueAtTime(frequency, start);

    // 減衰は指数で。線形だと「ブツッ」と切れて安っぽく聞こえる
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(volume, start + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);

    osc.connect(gain).connect(ctx.destination);
    osc.start(start);
    osc.stop(start + duration + 0.02);
  }
}
