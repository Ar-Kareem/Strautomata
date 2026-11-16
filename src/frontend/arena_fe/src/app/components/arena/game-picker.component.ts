import { ChangeDetectionStrategy, Component, ElementRef, HostListener, computed, inject, input, output, signal } from '@angular/core';
import type { GameWorldOption } from '@main/arena.constants';

export type GamePickerOption = Pick<GameWorldOption, 'id' | 'gameId' | 'worldId' | 'label'>;
import { GamePreviewComponent } from '../previews/game-preview.component';

let nextPickerId = 0;

/** Game switcher: the current game as a live mini board and title; opens a grid of every game. */
@Component({
  selector: 'arena-game-picker',
  standalone: true,
  imports: [GamePreviewComponent],
  templateUrl: './game-picker.component.html',
  styleUrl: './game-picker.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '[class.is-compact]': 'compact()' }
})
export class GamePickerComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly games = input.required<GamePickerOption[]>();
  readonly selectedId = input<string | null>(null);
  /** label of an extra first option that selects no game (emitted as null); omitted when unset */
  readonly allLabel = input<string | null>(null);
  readonly compact = input(false);
  readonly selectedChange = output<string | null>();

  readonly open = signal(false);
  /** Fixed (viewport) placement so the popup is not clipped by the scrolling setup panel. */
  readonly popupStyle = signal<Record<string, string>>({});

  readonly selected = computed(() => this.games().find((game) => game.id === this.selectedId()) ?? null);

  readonly listboxId = `gpk-listbox-${nextPickerId++}`;
  /** option highlighted by the arrow keys (focus stays on the trigger: aria-activedescendant) */
  readonly activeIndex = signal(-1);
  /** the "all" option, when present, is option 0 */
  readonly offset = computed(() => (this.allLabel() ? 1 : 0));
  private readonly optionIds = computed(() => [...(this.allLabel() ? [null] : []), ...this.games().map((game) => game.id)]);

  optionId(index: number): string {
    return `${this.listboxId}-${index}`;
  }

  toggle(): void {
    if (this.open()) {
      this.open.set(false);
    } else {
      this.openPopup();
    }
  }

  private openPopup(): void {
    this.place();
    this.activeIndex.set(Math.max(0, this.optionIds().indexOf(this.selectedId())));
    this.open.set(true);
    this.scrollActiveIntoView();
  }

  onKeydown(event: KeyboardEvent): void {
    const count = this.optionIds().length;
    if (!this.open()) {
      if (['Enter', ' ', 'ArrowDown', 'ArrowUp'].includes(event.key)) {
        event.preventDefault();
        this.openPopup();
      }
      return;
    }
    const moves: Record<string, (i: number) => number> = {
      ArrowDown: (i) => Math.min(count - 1, i + 1),
      ArrowRight: (i) => Math.min(count - 1, i + 1),
      ArrowUp: (i) => Math.max(0, i - 1),
      ArrowLeft: (i) => Math.max(0, i - 1),
      Home: () => 0,
      End: () => count - 1
    };
    if (moves[event.key]) {
      event.preventDefault();
      this.activeIndex.update(moves[event.key]);
      this.scrollActiveIntoView();
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      const index = this.activeIndex();
      if (index >= 0 && index < count) {
        this.choose(this.optionIds()[index]);
      }
    } else if (event.key === 'Tab') {
      this.open.set(false);
    }
  }

  private scrollActiveIntoView(): void {
    setTimeout(() => document.getElementById(this.optionId(this.activeIndex()))?.scrollIntoView({ block: "nearest" }));
  }

  @HostListener('window:resize')
  place(): void {
    const trigger = this.host.nativeElement.querySelector<HTMLElement>('.gpk-trigger');
    if (!trigger) {
      return;
    }
    const rect = trigger.getBoundingClientRect();
    const gap = 8;
    const margin = 12;
    const width = Math.min(760, window.innerWidth - 2 * margin);
    const left = Math.max(margin, Math.min(rect.left, window.innerWidth - width - margin));
    const top = rect.bottom + gap;
    this.popupStyle.set({
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      'max-height': `${Math.max(240, window.innerHeight - top - margin)}px`
    });
  }

  choose(id: string | null): void {
    this.open.set(false);
    this.host.nativeElement.querySelector<HTMLElement>('.gpk-trigger')?.focus();
    if (id !== this.selectedId()) {
      this.selectedChange.emit(id);
    }
  }

  @HostListener('document:pointerdown', ['$event'])
  onDocumentPointerDown(event: PointerEvent): void {
    if (this.open() && !this.host.nativeElement.contains(event.target as Node)) {
      this.open.set(false);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.open.set(false);
  }
}
