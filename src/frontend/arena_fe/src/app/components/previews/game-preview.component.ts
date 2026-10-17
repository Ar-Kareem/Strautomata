import { NgComponentOutlet } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
  type Type
} from '@angular/core';
import { GAME_GUI_MAP } from '@game-gui/game-gui-map';

type PreviewFrame = { state: unknown; player: number | null };
type PreviewFile = { frames: PreviewFrame[] };

/** Frames per preview file, shared by every card showing the same game. */
const previewCache = new Map<string, Promise<PreviewFrame[]>>();

const loadPreview = (key: string): Promise<PreviewFrame[]> => {
  let cached = previewCache.get(key);
  if (!cached) {
    const url = new URL(`previews/${encodeURIComponent(key)}.json`, document.baseURI).toString();
    cached = fetch(url).then(async (response) => {
      if (!response.ok) {
        throw new Error(`${response.status} while loading preview ${key}`);
      }
      return ((await response.json()) as PreviewFile).frames ?? [];
    });
    cached.catch(() => previewCache.delete(key));
    previewCache.set(key, cached);
  }
  return cached;
};

/** last scroll/touch time on the page; previews hold still while the user scrolls (phones lag otherwise) */
let lastScrollAt = 0;
const SCROLL_QUIET_MS = 100;
if (typeof window !== 'undefined') {
  const mark = () => (lastScrollAt = performance.now());
  window.addEventListener('scroll', mark, { passive: true, capture: true });
  window.addEventListener('touchmove', mark, { passive: true });
}

const NATURAL_WIDTH = 420;
const MOVE_MS = 650;
const END_HOLD_MS = 1300;

/**
 * Looping, non-interactive replay of a recorded game (public/previews/<game>_<world>.json,
 * written by `export_previews.py`) rendered with the game's own GUI, scaled to fit its box.
 * Only animates while on screen.
 */
@Component({
  selector: 'game-preview',
  standalone: true,
  imports: [NgComponentOutlet],
  templateUrl: './game-preview.component.html',
  styleUrl: './game-preview.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class GamePreviewComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly destroyRef = inject(DestroyRef);

  readonly gameId = input.required<string>();
  readonly worldId = input.required<string>();
  /** false: hold one frame instead of looping the replay */
  readonly animate = input(true);

  readonly frames = signal<PreviewFrame[]>([]);
  readonly turn = signal(0);
  readonly scale = signal(0.5);
  readonly naturalWidth = NATURAL_WIDTH;
  private visible = false;
  private timer: number | null = null;

  readonly guiComponent = computed<Type<unknown> | null>(() => GAME_GUI_MAP[this.gameId()] ?? null);

  readonly guiInputs = computed<Record<string, unknown>>(() => {
    const frame = this.frames()[this.turn()] ?? null;
    return {
      observation: frame ? { state: frame.state, player: frame.player } : null,
      botA: 'Automaton A',
      botB: 'Automaton B',
      statusTone: 'ready',
      statusMessage: '',
      showHumanControls: false,
      awaitingHumanMove: false,
      legalMoves: [],
      submitHumanMove: () => undefined,
      illegalAction: null,
      matchResult: null
    };
  });

  constructor() {
    effect(() => {
      const key = `${this.gameId()}_${this.worldId()}`;
      untracked(() => {
        loadPreview(key)
          .then((frames) => {
            this.frames.set(frames);
            // start part-way in so a grid of previews does not all open on empty boards
            this.turn.set(Math.floor(frames.length * (0.2 + Math.random() * 0.4)));
            window.requestAnimationFrame(() => this.measure());
            this.schedule(MOVE_MS);
          })
          .catch(() => this.frames.set([]));
      });
    });

    const element = this.host.nativeElement;
    const resize = new ResizeObserver(() => this.measure());
    resize.observe(element);
    const intersection = new IntersectionObserver((entries) => {
      this.visible = entries.some((entry) => entry.isIntersecting);
      if (this.visible) {
        this.schedule(MOVE_MS);
      } else {
        this.stop();
      }
    });
    intersection.observe(element);
    this.destroyRef.onDestroy(() => {
      resize.disconnect();
      intersection.disconnect();
      this.stop();
    });
  }

  /**
   * Fit the GUI (laid out at least NATURAL_WIDTH wide, wider boards grow it) inside the host box.
   * Shrinks with `zoom` rather than `transform: scale`: zoom keeps the boards' 1px grid lines at
   * least one device pixel wide, while a scaled transform thins them until some vanish.
   */
  private measure(): void {
    const element = this.host.nativeElement;
    const inner = element.querySelector<HTMLElement>('.gp-inner');
    const width = element.clientWidth;
    const height = element.clientHeight;
    if (!inner || width <= 0 || height <= 0) {
      return;
    }
    // offset sizes are the GUI's own (unzoomed) layout size
    const innerWidth = Math.max(NATURAL_WIDTH, inner.offsetWidth);
    const next = Math.min(width / innerWidth, height / Math.max(1, inner.offsetHeight));
    // border rounding under zoom moves the measured size a hair; re-zooming for that would re-layout every step
    if (Math.abs(next - this.scale()) > this.scale() * 0.01) {
      this.scale.set(next);
    }
  }

  /** this preview's own offset in the step cycle, so the 20 boards don't all step at the same moment */
  private readonly phase = Math.random() * MOVE_MS;

  /** Step after at least `minDelay`, landing on this preview's own beat (multiples of MOVE_MS + phase). */
  private schedule(minDelay: number): void {
    if (this.timer !== null || !this.visible || !this.animate() || this.frames().length < 2) {
      return;
    }
    const now = performance.now();
    // timers fire a few ms late; without this slack every step would skip a beat (1.3s instead of 0.65s)
    const slack = 80;
    const beats = Math.ceil((now + minDelay - slack - this.phase) / MOVE_MS);
    const delay = Math.max(0, this.phase + beats * MOVE_MS - now);
    this.timer = window.setTimeout(() => {
      this.timer = null;
      this.advance();
    }, delay);
  }

  private advance(): void {
    const sinceScroll = performance.now() - lastScrollAt;
    if (sinceScroll < SCROLL_QUIET_MS) {
      this.schedule(SCROLL_QUIET_MS - sinceScroll); // scrolling: resume on our next beat after it stops
      return;
    }
    const last = this.frames().length - 1;
    const next = this.turn() >= last ? 0 : this.turn() + 1;
    this.turn.set(next);
    this.measure();
    this.schedule(next >= last ? END_HOLD_MS : MOVE_MS);
  }

  private stop(): void {
    if (this.timer !== null) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
  }
}
