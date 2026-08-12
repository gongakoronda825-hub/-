import { bindTap } from '../input/ActionButtons';
import { PLACEABLE, STONE, blockIcon, blockKey, type BlockId } from '../world/blocks';

/**
 * 画面下中央のインベントリ（ホットバー）。「おく」で使うブロックを選ぶ。
 *
 * 持ち物の増減や個数は扱わない。並んでいる種類から1つ選ぶだけ。
 */
export class Inventory {
  private selected: BlockId = STONE;
  private readonly slots = new Map<BlockId, HTMLElement>();

  constructor(container: HTMLElement) {
    for (const block of PLACEABLE) {
      const slot = document.createElement('button');
      slot.type = 'button';
      slot.className = 'slot';
      slot.dataset.type = block.key;
      slot.innerHTML =
        `<span class="icon" style="background-image:url(${blockIcon(block.id)})"></span>` +
        `<span class="name">${block.label}</span>`;

      bindTap(slot, () => this.select(block.id));

      container.appendChild(slot);
      this.slots.set(block.id, slot);
    }

    // 数字キーでも選べるようにしておく（PC での確認用）
    window.addEventListener('keydown', (e) => {
      const index = Number(e.key) - 1;
      const block = PLACEABLE[index];
      if (block) this.select(block.id);
    });

    this.refresh();
  }

  /** 「おく」で設置されるブロック。 */
  get current(): BlockId {
    return this.selected;
  }

  /** デバッグ表示用の名前。 */
  get currentName(): string {
    return blockKey(this.selected);
  }

  select(id: BlockId): void {
    this.selected = id;
    this.refresh();
  }

  private refresh(): void {
    for (const [id, slot] of this.slots) {
      slot.classList.toggle('selected', id === this.selected);
    }
  }
}
