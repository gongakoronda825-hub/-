/**
 * タイトルとゲームオーバーの全画面パネル（指示書 §16）。
 *
 * どちらも「押すまでゲームループを進めない」という同じ約束で動く。
 */

/** 共通の下ごしらえ。overlay を作って parent にぶら下げる。 */
function createOverlay(parent: HTMLElement, id: string, html: string): HTMLElement {
  const overlay = document.createElement('div');
  overlay.id = id;
  overlay.className = 'overlay';
  overlay.innerHTML = html;
  parent.appendChild(overlay);
  return overlay;
}

/** 開始前の操作説明。 */
export class TitleScreen {
  private readonly overlay: HTMLElement;

  constructor(parent: HTMLElement, private readonly onStart: () => void) {
    this.overlay = createOverlay(
      parent,
      'title',
      `
      <div class="panel">
        <h1>ピンポンダッシュ</h1>
        <p class="sub">押すほど儲かる。押すほど危ない。</p>
        <ul>
          <li><b>移動</b><span>左下のスティックを倒す</span></li>
          <li><b>見まわす</b><span>画面の右半分をなぞる</span></li>
          <li><b>ダッシュ</b><span>右下のボタンを押しっぱなし</span></li>
          <li><b>ピンポン</b><span>門に近づくと出るボタンを押す</span></li>
        </ul>
        <p class="note">
          鳴らすほどポイントは増えますが、危険度も上がって住民が出てきます。<br>
          塀は越えられません。逃げ道は道と路地と物陰だけ。<br>
          見つかっても即アウトではありません。<b>3秒</b>見られ続けるか、捕まると終わりです。<br>
          角を曲がって視線を切れば、相手はあなたを見失います。
        </p>
        <button type="button" id="start-button">はじめる</button>
      </div>
    `,
    );

    this.bind('#start-button', () => {
      this.overlay.remove();
      this.onStart();
      requestFullscreen();
    });
  }

  private bind(selector: string, action: () => void): void {
    const button = this.overlay.querySelector<HTMLButtonElement>(selector);
    button?.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      action();
    });
  }
}

export interface Result {
  readonly score: number;
  readonly pings: number;
  readonly highscore: number;
  readonly newRecord: boolean;
  /** 何にやられたか（テキストで出すだけ）。 */
  readonly cause: string;
}

/** ゲームオーバー画面。show() で出し、リトライで消える。 */
export class ResultScreen {
  private overlay: HTMLElement | null = null;

  constructor(
    private readonly parent: HTMLElement,
    private readonly onRetry: () => void,
  ) {}

  show(result: Result): void {
    this.overlay = createOverlay(
      this.parent,
      'result',
      `
      <div class="panel">
        <h1>${result.cause}</h1>
        <p class="sub">ピンポンダッシュ、失敗</p>
        <div class="final">${result.score}<span style="font-size:16px"> pt</span></div>
        <ul class="lines">
          <li><b>ピンポン回数</b><span>${result.pings} 回</span></li>
          <li><b>ハイスコア</b><span class="best">${result.highscore} pt</span></li>
        </ul>
        ${result.newRecord ? '<p class="sub">自己ベスト更新</p>' : ''}
        <button type="button" id="retry-button">もう一回</button>
      </div>
    `,
    );

    const button = this.overlay.querySelector<HTMLButtonElement>('#retry-button');
    button?.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      this.hide();
      this.onRetry();
    });
  }

  hide(): void {
    this.overlay?.remove();
    this.overlay = null;
  }
}

/**
 * 全画面にできない環境（iOS Safari など）でもそのまま遊べるので、
 * 失敗しても握りつぶす。必ずユーザー操作のあとに呼ぶこと。
 */
function requestFullscreen(): void {
  try {
    void document.documentElement.requestFullscreen?.()?.catch(() => {});
  } catch {
    /* 全画面なしで続行 */
  }
}
