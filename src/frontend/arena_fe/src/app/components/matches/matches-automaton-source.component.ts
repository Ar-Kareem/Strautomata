import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  effect,
  inject,
  input,
  model,
  signal,
  untracked,
  viewChild
} from '@angular/core';
import type { HistoryIndexGame } from '@main/history.types';
import { ArenaCodeEditorComponent } from '../create/code-editor.component';
import { HistoryService } from './history.service';
import { modelOf } from './history-format';

const escapeHtml = (text: string): string =>
  text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** The model's own write-up, with its **bold**, *italic* and `code` spans; line breaks are kept by CSS. */
const renderStrategy = (text: string): string =>
  escapeHtml(text)
    .replace(/^#+\s*(.+)$/gm, '<strong>$1</strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
    .replace(/`([^`\n]+)`/g, '<code>$1</code>');

/**
 * An automaton's strategy (the model's explanation) and its code side by side. In a list it can be
 * closed to the write-up's first few lines.
 */
@Component({
  selector: 'matches-automaton-source',
  standalone: true,
  imports: [ArenaCodeEditorComponent],
  templateUrl: './matches-automaton-source.component.html',
  styleUrl: './matches-automaton-source.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesAutomatonSourceComponent {
  private readonly history = inject(HistoryService);
  private readonly injector = inject(Injector);
  private readonly fullDialog = viewChild.required<ElementRef<HTMLDialogElement>>('fullDialog');
  private readonly fullCode = viewChild<ElementRef<HTMLElement>>('fullCode');

  readonly game = input.required<HistoryIndexGame>();
  readonly bot = input.required<string>();
  /** lines of the write-up shown while closed */
  readonly lines = input(2);
  readonly open = model(false);
  /** always show strategy and code, with no way to fold them */
  readonly fixed = input(false);
  readonly shown = computed(() => this.fixed() || this.open());
  readonly strategy = signal<string | null | undefined>(undefined);
  readonly code = signal<string | null>(null);
  readonly codeError = signal<string | null>(null);
  /** strategy above code, over the whole page */
  readonly full = signal(false);

  /** the write-up's opening, as plain text for the collapsed line */
  readonly preview = computed(() => {
    const text = this.strategy();
    return text ? text.replace(/[*`#]/g, '').replace(/\s+/g, ' ').trim() : null;
  });

  readonly strategyHtml = computed(() => {
    const text = this.strategy();
    return text ? renderStrategy(text) : null;
  });

  constructor() {
    effect(() => {
      if (this.shown()) {
        untracked(() => this.loadCode());
      }
    });
    effect(() => {
      const game = this.game();
      const bot = this.bot();
      // the parent can hand over null for a moment while its view is torn down
      if (!game || !bot) {
        return;
      }
      untracked(() => {
        if (this.open()) {
          this.open.set(false);
        }
        this.strategy.set(undefined);
        this.code.set(null);
        this.codeError.set(null);
        this.history
          .loadStrategies(game.id, modelOf(bot))
          .then((map) => bot === this.bot() && this.strategy.set(map[bot] ?? null))
          .catch(() => bot === this.bot() && this.strategy.set(null));
      });
    });
  }

  setOpen(open: boolean): void {
    this.open.set(open);
  }

  openFull(focus: 'strategy' | 'code'): void {
    this.full.set(true);
    this.fullDialog().nativeElement.showModal();
    afterNextRender(
      () => {
        const dialog = this.fullDialog().nativeElement;
        if (focus === 'code') {
          this.fullCode()?.nativeElement.scrollIntoView({ block: 'start' });
        } else {
          dialog.scrollTop = 0;
        }
      },
      { injector: this.injector }
    );
  }

  private loadCode(): void {
    if (this.code() !== null || !this.game()) {
      return;
    }
    const { game, world } = this.game();
    const bot = this.bot();
    this.history
      .loadBotCode(game, world, bot)
      .then((code) => {
        if (bot !== this.bot()) {
          return;
        }
        // a dev server answers a missing file with the app's index.html
        if (/^\s*<!doctype html/i.test(code)) {
          this.codeError.set('The code of this automaton is not published.');
        } else {
          this.code.set(code);
        }
      })
      .catch(() => bot === this.bot() && this.codeError.set('The code of this automaton is not published.'));
  }
}
