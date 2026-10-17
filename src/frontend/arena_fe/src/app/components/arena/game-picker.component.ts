import { ChangeDetectionStrategy, Component, ElementRef, HostListener, computed, inject, input, output, signal } from '@angular/core';
import type { GameWorldOption } from '@main/arena.constants';

export type GamePickerOption = Pick<GameWorldOption, 'id' | 'gameId' | 'worldId' | 'label'>;
import { GamePreviewComponent } from '../previews/game-preview.component';

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

  toggle(): void {
    if (!this.open()) {
      this.place();
    }
    this.open.update((value) => !value);
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
