import { bindTap } from '../input/ActionButtons';
import { BLOCK_LABELS, BLOCK_TYPES, blockIcon, type BlockType } from '../world/blocks';

/**
 * 画面下中央のインベントリ（ホットバー）。「おく」で使うブロックを選ぶ。
 *
 * 持ち物の増減や個数は扱わない。並んでいる種類から1つ選ぶだけ。
 */
export class Inventory {
  private selected: BlockType = 'stone';
  private readonly slots = new Map<BlockType, HTMLElement>();

  constructor(container: HTMLElement) {
    for (const type of BLOCK_TYPES) {
      const slot = document.createElement('button');
      slot.type = 'button';
      slot.className = 'slot';
      slot.dataset.type = type;
      slot.innerHTML =
        `<span class="icon" style="background-image:url(${blockIcon(type)})"></span>` +
        `<span class="name">${BLOCK_LABELS[type]}</span>`;

      bindTap(slot, () => this.select(type));

      container.appendChild(slot);
      this.slots.set(type, slot);
    }

    // 数字キーでも選べるようにしておく（PC での確認用）
    window.addEventListener('keydown', (e) => {
      const index = Number(e.key) - 1;
      const type = BLOCK_TYPES[index];
      if (type) this.select(type);
    });

    this.refresh();
  }

  /** 「おく」で設置されるブロック。 */
  get current(): BlockType {
    return this.selected;
  }

  select(type: BlockType): void {
    this.selected = type;
    this.refresh();
  }

  private refresh(): void {
    for (const [type, slot] of this.slots) {
      slot.classList.toggle('selected', type === this.selected);
    }
  }
}
