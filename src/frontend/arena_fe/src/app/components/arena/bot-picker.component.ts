import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, HostListener, computed, inject, input, output, signal } from '@angular/core';
import type { BotOption } from '@main/arena.constants';
import { resolveBotLogo } from '@main/arena.utils';

type PickerRow = { id: string; label: string; logo: string | null; icon: string; elo: number | null; disabled: boolean };

type SortMode = 'elo' | 'name';

/** Sort order shared by every bot picker on the page. */
const sortMode = signal<SortMode>('elo');

const HUMAN_LABEL = 'Human Controlled';

const BUILTIN_ICONS: Record<string, string> = {
  human: 'fa-user',
  random: 'fa-dice',
  first: 'fa-backward-step',
  last: 'fa-forward-step'
};

/** Bot dropdown: provider logos, bots sorted by Elo, and the "show all bots" toggle inside the popup. */
@Component({
  selector: 'arena-bot-picker',
  standalone: true,
  templateUrl: './bot-picker.component.html',
  styleUrl: './bot-picker.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class BotPickerComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly label = input.required<string>();
  readonly bots = input.required<BotOption[]>();
  readonly selectedId = input<string | null>(null);
  readonly elo = input<Record<string, number> | null>(null);
  readonly disabled = input(false);
  readonly isOptionDisabled = input<(botId: string) => boolean>(() => false);
  readonly showAll = input(false);
  readonly showAllEnabled = input(true);
  readonly showAllTooltip = input('');

  readonly selectedChange = output<string>();
  readonly showAllChange = output<boolean>();

  readonly open = signal(false);
  readonly sortMode = sortMode;
  /** Fixed (viewport) placement so the popup is not clipped by the scrolling setup panel. */
  readonly popupStyle = signal<Record<string, string>>({});

  readonly rows = computed<PickerRow[]>(() => {
    const elo = this.elo();
    const isDisabled = this.isOptionDisabled();
    const rows = this.bots().map((bot) => ({
      id: bot.id,
      label: bot.id === 'human' ? HUMAN_LABEL : bot.label,
      logo: resolveBotLogo(bot.id),
      icon: BUILTIN_ICONS[bot.id] ?? 'fa-robot',
      elo: elo?.[bot.id] ?? null,
      disabled: isDisabled(bot.id)
    }));
    const byName = (a: PickerRow, b: PickerRow) => a.label.localeCompare(b.label, undefined, { numeric: true });
    // by Elo: rated bots highest first, then the unrated ones by name
    const byElo = (a: PickerRow, b: PickerRow) => (b.elo ?? -Infinity) - (a.elo ?? -Infinity) || byName(a, b);
    const human = rows.filter((row) => row.id === 'human');
    const others = rows.filter((row) => row.id !== 'human').sort(this.sortMode() === 'elo' ? byElo : byName);
    return [...human, ...others];
  });

  readonly selected = computed<PickerRow | null>(() => this.rows().find((row) => row.id === this.selectedId()) ?? null);

  readonly hasRatings = computed(() => this.rows().some((row) => row.elo !== null));

  constructor() {
    // scroll events do not bubble: listen in the capture phase to follow any scrolling ancestor
    const onScroll = (event: Event) => {
      const popup = this.host.nativeElement.querySelector('.bp-popup');
      if (this.open() && !(popup && popup.contains(event.target as Node))) {
        this.place();
      }
    };
    window.addEventListener('scroll', onScroll, true);
    inject(DestroyRef).onDestroy(() => window.removeEventListener('scroll', onScroll, true));
  }

  toggle(): void {
    if (this.disabled()) {
      return;
    }
    if (!this.open()) {
      this.place();
    }
    this.open.update((value) => !value);
  }

  @HostListener('window:resize')
  place(): void {
    const trigger = this.host.nativeElement.querySelector<HTMLElement>('.bp-trigger');
    if (!trigger) {
      return;
    }
    const rect = trigger.getBoundingClientRect();
    const gap = 6;
    const margin = 12;
    const width = Math.max(rect.width, 300);
    const left = Math.max(margin, Math.min(rect.left, window.innerWidth - width - margin));
    const below = window.innerHeight - rect.bottom - gap - margin;
    const above = rect.top - gap - margin;
    const style: Record<string, string> = { left: `${left}px`, width: `${width}px` };
    if (below >= 260 || below >= above) {
      style['top'] = `${rect.bottom + gap}px`;
      style['max-height'] = `${Math.min(420, below)}px`;
    } else {
      style['bottom'] = `${window.innerHeight - rect.top + gap}px`;
      style['max-height'] = `${Math.min(420, above)}px`;
    }
    this.popupStyle.set(style);
  }

  choose(row: PickerRow): void {
    if (row.disabled) {
      return;
    }
    this.open.set(false);
    if (row.id !== this.selectedId()) {
      this.selectedChange.emit(row.id);
    }
  }

  setSort(mode: SortMode): void {
    this.sortMode.set(mode);
  }

  onShowAll(event: Event): void {
    this.showAllChange.emit((event.target as HTMLInputElement).checked);
  }

  eloText(row: PickerRow): string {
    if (row.elo !== null) {
      return String(Math.round(row.elo));
    }
    return row.id === 'human' || !this.hasRatings() ? '' : 'DNQ';
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
