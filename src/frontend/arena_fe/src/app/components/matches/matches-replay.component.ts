import { JsonPipe, NgComponentOutlet } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  HostListener,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
  viewChild,
  type ElementRef,
  type Type
} from '@angular/core';
import type { MatchResultSummary } from '@main/arena.constants';
import type { MatchDetail, ReplayFrame, ReplayResult } from '@main/history.types';
import { GAME_GUI_MAP } from '@game-gui/game-gui-map';
import { HistoryService } from './history.service';
import { REASON_LABEL, RESULT_LABEL, formatSecs, moveToText, resultTone } from './history-format';

type ReplayStatus = 'idle' | 'loading' | 'ready' | 'error' | 'unavailable';

interface MoveLine {
  index: number;
  turn: number;
  player: number;
  text: string;
  think: number | null;
  failed: boolean;
  applied: boolean;
}

@Component({
  selector: 'matches-replay',
  standalone: true,
  imports: [NgComponentOutlet, JsonPipe],
  templateUrl: './matches-replay.component.html',
  styleUrl: './matches-replay.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesReplayComponent {
  private readonly history = inject(HistoryService);
  private readonly destroyRef = inject(DestroyRef);

  readonly gameId = input.required<string>();
  readonly worldId = input.required<string>();
  readonly gameLabel = input<string>('');
  readonly detail = input.required<MatchDetail>();
  readonly labelA = input.required<string>();
  readonly labelB = input.required<string>();
  readonly replayable = input(true);
  readonly close = output<void>();
  private readonly moveList = viewChild<ElementRef<HTMLElement>>('moveList');

  readonly formatSecs = formatSecs;
  readonly reasonLabel = REASON_LABEL;
  readonly resultLabel = RESULT_LABEL;
  readonly resultTone = resultTone;

  readonly status = signal<ReplayStatus>('idle');
  readonly error = signal<string | null>(null);
  readonly replay = signal<ReplayResult | null>(null);
  readonly turn = signal(0);
  readonly playing = signal(false);
  readonly speed = signal(4); // moves per second
  private timer: number | null = null;
  private replayToken = 0;
  private readonly finishedStamp = Date.now();

  readonly guiComponent = computed<Type<unknown> | null>(() => GAME_GUI_MAP[this.gameId()] ?? null);

  readonly frames = computed<ReplayFrame[]>(() => this.replay()?.frames ?? []);
  readonly lastTurn = computed(() => Math.max(0, this.frames().length - 1));
  readonly frame = computed<ReplayFrame | null>(() => this.frames()[this.turn()] ?? null);

  readonly moveLines = computed<MoveLine[]>(() => {
    const d = this.detail();
    const failed = this.replay()?.failed_move ?? null;
    const applied = this.replay()?.applied ?? d.moves.length;
    return d.moves.map(([player, move], index) => ({
      index,
      turn: index + 1,
      player,
      text: moveToText(move),
      think: d.think[index] ?? null,
      failed: failed !== null && failed !== undefined && failed.index === index,
      applied: index < applied
    }));
  });

  /** who actually moved first (seat 0 does not always open, e.g. Backgammon's opening roll) */
  readonly firstMover = computed(() => this.moveLines()[0]?.player ?? this.frames()[0]?.player ?? 0);

  readonly maxThink = computed(() => Math.max(0.001, ...this.moveLines().map((line) => line.think ?? 0)));

  readonly outcomeText = computed(() => {
    const d = this.detail();
    const a = this.labelA();
    const b = this.labelB();
    switch (d.reason) {
      case 'win':
        return d.winner === 0 ? `${a} won` : `${b} won`;
      case 'draw':
        return 'Draw';
      case 'error':
        if (d.winner === null) {
          return 'Both players errored';
        }
        return `${d.winner === 0 ? b : a} lost by illegal move / crash`;
      case 'timeout':
        if (d.winner === null) {
          return 'Timeout';
        }
        return `${d.winner === 0 ? b : a} lost on time`;
      default:
        return 'Unknown outcome';
    }
  });

  readonly guiInputs = computed<Record<string, unknown>>(() => {
    const frame = this.frame();
    const atEnd = this.turn() >= this.lastTurn() && this.status() === 'ready';
    const d = this.detail();
    const matchResult: MatchResultSummary | null = atEnd
      ? { winner: d.winner, illegal: d.reason === 'error', finishedAt: this.finishedStamp }
      : null;
    return {
      observation: frame ? { state: frame.state, player: frame.player } : null,
      botA: this.labelA(),
      botB: this.labelB(),
      statusTone: 'ready',
      statusMessage: '',
      showHumanControls: false,
      awaitingHumanMove: false,
      legalMoves: [],
      submitHumanMove: () => undefined,
      illegalAction: null,
      matchResult
    };
  });

  readonly currentLine = computed<MoveLine | null>(() => {
    const t = this.turn();
    return t > 0 ? this.moveLines()[t - 1] ?? null : null;
  });

  readonly exceptionText = computed(() => {
    const d = this.detail();
    const failed = this.replay()?.failed_move;
    const parts: string[] = [];
    if (d.exception) {
      parts.push(d.exception);
    }
    if (failed?.why && !parts.some((p) => p.includes(failed.why))) {
      parts.push(`Engine rejected move ${failed.index + 1} (${moveToText(failed.action)}): ${failed.why}`);
    }
    return parts.join('\n');
  });

  constructor() {
    effect(() => {
      const detail = this.detail();
      const gameId = this.gameId();
      const worldId = this.worldId();
      const replayable = this.replayable();
      untracked(() => this.startReplay(gameId, worldId, detail, replayable));
    });
    this.destroyRef.onDestroy(() => this.stopTimer());
    effect(() => {
      // keep the current move visible: when it leaves the list's viewport, re-centre it
      const turn = this.turn();
      const list = this.moveList()?.nativeElement;
      if (!list || turn <= 0) {
        return;
      }
      untracked(() => {
        window.requestAnimationFrame(() => {
          const current = list.querySelector<HTMLElement>('.rp-move.is-current');
          if (!current) {
            return;
          }
          const top = current.offsetTop - list.offsetTop;
          const bottom = top + current.offsetHeight;
          if (top < list.scrollTop || bottom > list.scrollTop + list.clientHeight) {
            list.scrollTop = Math.max(0, top - list.clientHeight / 2 + current.offsetHeight / 2);
          }
        });
      });
    });
  }

  private async startReplay(gameId: string, worldId: string, detail: MatchDetail, replayable: boolean): Promise<void> {
    const token = ++this.replayToken;
    this.stopTimer();
    this.playing.set(false);
    this.turn.set(0);
    this.replay.set(null);
    this.error.set(null);
    if (!replayable) {
      this.status.set('unavailable');
      return;
    }
    if (!detail.moves.length) {
      this.status.set('unavailable');
      this.error.set('No moves were recorded for this match.');
      return;
    }
    this.status.set('loading');
    try {
      const result = await this.history.replay(gameId, worldId, detail.seed, detail.moves);
      if (token !== this.replayToken) {
        return;
      }
      if (!result.ok) {
        this.status.set('error');
        this.error.set(result.why ?? 'Replay failed');
        return;
      }
      this.replay.set(result);
      this.status.set('ready');
      this.turn.set(0);
    } catch (err) {
      if (token !== this.replayToken) {
        return;
      }
      this.status.set('error');
      this.error.set(err instanceof Error ? err.message : String(err));
    }
  }

  retry(): void {
    void this.startReplay(this.gameId(), this.worldId(), this.detail(), this.replayable());
  }

  seek(turn: number): void {
    const clamped = Math.max(0, Math.min(this.lastTurn(), Math.round(turn)));
    this.turn.set(clamped);
    if (clamped >= this.lastTurn()) {
      this.pause();
    }
  }

  onSlider(event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    if (Number.isFinite(value)) {
      this.seek(value);
    }
  }

  first(): void {
    this.seek(0);
  }

  last(): void {
    this.seek(this.lastTurn());
  }

  prev(): void {
    this.seek(this.turn() - 1);
  }

  next(): void {
    this.seek(this.turn() + 1);
  }

  togglePlay(): void {
    if (this.playing()) {
      this.pause();
      return;
    }
    if (this.turn() >= this.lastTurn()) {
      this.turn.set(0);
    }
    this.playing.set(true);
    this.scheduleTick();
  }

  pause(): void {
    this.playing.set(false);
    this.stopTimer();
  }

  setSpeed(event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    if (Number.isFinite(value) && value > 0) {
      this.speed.set(value);
      if (this.playing()) {
        this.stopTimer();
        this.scheduleTick();
      }
    }
  }

  private scheduleTick(): void {
    this.stopTimer();
    this.timer = window.setInterval(() => {
      if (!this.playing()) {
        this.stopTimer();
        return;
      }
      if (this.turn() >= this.lastTurn()) {
        this.pause();
        return;
      }
      this.turn.set(this.turn() + 1);
    }, Math.max(40, 1000 / this.speed()));
  }

  private stopTimer(): void {
    if (this.timer !== null) {
      window.clearInterval(this.timer);
      this.timer = null;
    }
  }

  @HostListener('window:keydown', ['$event'])
  onKey(event: KeyboardEvent): void {
    const target = event.target as HTMLElement | null;
    if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) {
      return;
    }
    if (this.status() !== 'ready') {
      return;
    }
    switch (event.key) {
      case 'ArrowLeft':
        this.prev();
        event.preventDefault();
        break;
      case 'ArrowRight':
        this.next();
        event.preventDefault();
        break;
      case 'Home':
        this.first();
        event.preventDefault();
        break;
      case 'End':
        this.last();
        event.preventDefault();
        break;
      case ' ':
        this.togglePlay();
        event.preventDefault();
        break;
      default:
        break;
    }
  }

  thinkStyle(line: MoveLine): Record<string, string> {
    const share = line.think === null ? 0 : Math.min(1, line.think / this.maxThink());
    return { '--think': `${Math.round(share * 100)}%` };
  }

  playerLabel(player: number): string {
    return player === 0 ? this.labelA() : player === 1 ? this.labelB() : `Player ${player}`;
  }

  jumpTo(line: MoveLine): void {
    if (!line.applied && !line.failed) {
      return;
    }
    this.pause();
    this.seek(line.failed ? line.index : line.turn);
  }
}
