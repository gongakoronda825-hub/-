/**
 * 開始時の操作説明オーバーレイ（仕様書 §9, §11）。
 *
 * 「はじめる」を押すまでゲームループは回さない。最初のタップを受けてから
 * 全画面にするので、モバイルの「ユーザー操作が必要」な API とも噛み合う。
 */
export class Tutorial {
  private readonly overlay: HTMLElement;

  constructor(parent: HTMLElement, private readonly onStart: () => void) {
    this.overlay = document.createElement('div');
    this.overlay.id = 'tutorial';
    this.overlay.innerHTML = `
      <div class="panel">
        <h1>ブロックの世界</h1>
        <ul>
          <li><b>移動</b><span>左下のスティックを倒す</span></li>
          <li><b>見まわす</b><span>画面の右半分をなぞる</span></li>
          <li><b>こわす</b><span>中央の ＋ を合わせて「こわす」</span></li>
          <li><b>おく</b><span>面を狙って「おく」。となりに積まれる</span></li>
        </ul>
        <p class="note">とどく範囲は5ブロックまで。遠すぎると何も起きません。</p>
        <button type="button" id="start-button">はじめる</button>
      </div>
    `;
    parent.appendChild(this.overlay);

    const button = this.overlay.querySelector<HTMLButtonElement>('#start-button')!;
    button.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      this.start();
    });
  }

  private start(): void {
    this.overlay.remove();
    this.onStart();

    // 全画面にできない環境（iOS Safari など）でもそのまま遊べるので、
    // 失敗しても握りつぶす。ゲーム開始のあとに試すこと。
    try {
      void document.documentElement.requestFullscreen?.()?.catch(() => {});
    } catch {
      /* 全画面なしで続行 */
    }
  }
}
