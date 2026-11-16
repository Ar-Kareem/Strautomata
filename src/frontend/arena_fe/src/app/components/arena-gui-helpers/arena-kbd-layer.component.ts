import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ElementRef, HostBinding, NgZone, OnDestroy, OnInit } from '@angular/core';

export type KbdMatch = {
  /** indexes of the labels that start with what was typed */
  visible: number[];
  /** the label typed in full, if any */
  exact: number | null;
  /** the label to click now: typed in full and no longer label starts with it */
  pick: number | null;
};

export function matchKbd(labels: readonly string[], typed: string): KbdMatch {
  const visible: number[] = [];
  let exact: number | null = null;
  labels.forEach((label, index) => {
    if (label.startsWith(typed)) {
      visible.push(index);
      if (label === typed && exact === null) {
        exact = index;
      }
    }
  });
  return { visible, exact, pick: exact !== null && visible.length === 1 ? exact : null };
}

type KbdHint = { el: Element; label: string; x: number; y: number };

function isTextEntry(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  if (target.isContentEditable || ['TEXTAREA', 'SELECT'].includes(target.tagName)) {
    return true;
  }
  if (target instanceof HTMLInputElement) {
    return !['button', 'checkbox', 'radio', 'range', 'reset', 'submit', 'color', 'file'].includes(target.type);
  }
  return false;
}

/**
 * Keyboard hints for the board it sits in (see arena-kbd-keys.ts). Space turns keyboard mode on
 * (when the board has targets) and off, Escape turns it off. While on, every `data-kbd` target shows
 * a hint whenever the board has any, typing a hint clicks the target, Backspace clicks
 * `data-kbd-back` (the selected piece) to go back a step.
 */
@Component({
  selector: 'arena-kbd-layer',
  standalone: true,
  template: `
    @for (hint of shownHints; track hint.el) {
      <span class="kbd-hint" [style.left.px]="hint.x" [style.top.px]="hint.y"
        ><span class="kbd-hint-typed">{{ typed }}</span>{{ hint.label.slice(typed.length) }}</span
      >
    }
  `,
  styles: `
    :host {
      position: absolute;
      inset: 0;
      z-index: 6;
      pointer-events: none;
    }
    .kbd-hint {
      position: absolute;
      transform: translate(-50%, -50%);
      padding: 1px 4px;
      border: 1px solid #c38a22;
      border-radius: 3px;
      background: linear-gradient(to bottom, #fff785 0%, #ffc542 100%);
      box-shadow: 0 3px 7px rgba(0, 0, 0, 0.3);
      color: #302505;
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: nowrap;
    }
    .kbd-hint-typed {
      color: #d4ac3a;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaKbdLayerComponent implements OnInit, OnDestroy {
  active = false;
  typed = '';
  hints: KbdHint[] = [];
  shownHints: KbdHint[] = [];
  private observer: MutationObserver | null = null;
  private frame: number | null = null;
  private swallowSpaceUp = false;
  /** keys typed after a pick and before the board shows its next hints */
  private queued: string | null = null;

  @HostBinding('style.display') get display(): string {
    return this.active ? 'block' : 'none';
  }

  constructor(
    private readonly host: ElementRef<HTMLElement>,
    private readonly cdr: ChangeDetectorRef,
    private readonly zone: NgZone
  ) {}

  private get scope(): HTMLElement {
    return this.host.nativeElement.parentElement ?? this.host.nativeElement;
  }

  ngOnInit(): void {
    window.addEventListener('keydown', this.onKeyDown, true);
    window.addEventListener('keyup', this.onKeyUp, true);
  }

  ngOnDestroy(): void {
    window.removeEventListener('keydown', this.onKeyDown, true);
    window.removeEventListener('keyup', this.onKeyUp, true);
    this.close();
  }

  private readonly onKeyDown = (event: KeyboardEvent): void => {
    if (event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }
    if (!this.active) {
      if (event.key !== ' ' || isTextEntry(event.target) || !this.collect().length) {
        return;
      }
      this.consume(event);
      this.swallowSpaceUp = true;
      this.open();
      return;
    }
    if (isTextEntry(event.target)) {
      return;
    }
    // no hints between turns: only Space and Escape belong to the layer then
    const idle = !this.hints.length && this.queued === null;
    if (idle && event.key !== ' ' && event.key !== 'Escape') {
      return;
    }
    const labels = this.hints.map((hint) => hint.label);
    switch (event.key) {
      case ' ':
        this.swallowSpaceUp = true;
        this.consume(event);
        this.close();
        return;
      case 'Escape':
        this.consume(event);
        this.close();
        return;
      case 'Backspace':
        this.consume(event);
        if (this.typed) {
          this.setTyped(this.typed.slice(0, -1));
        } else {
          const back = this.scope.querySelector('[data-kbd-back]');
          if (back) {
            this.click(back);
          }
        }
        return;
      case 'Enter': {
        this.consume(event);
        const exact = matchKbd(labels, this.typed).exact;
        if (exact !== null) {
          this.click(this.hints[exact].el);
        }
        return;
      }
    }
    if (event.key.length !== 1) {
      return;
    }
    this.consume(event);
    this.type(event.key.toLowerCase());
  };

  private type(key: string): void {
    if (this.queued !== null) {
      this.queued += key;
      return;
    }
    const typed = this.typed + key;
    const match = matchKbd(this.hints.map((hint) => hint.label), typed);
    if (!match.visible.length) {
      return;
    }
    if (match.pick !== null) {
      this.click(this.hints[match.pick].el);
      return;
    }
    this.setTyped(typed);
  }

  private readonly onKeyUp = (event: KeyboardEvent): void => {
    if (event.key === ' ' && this.swallowSpaceUp) {
      this.swallowSpaceUp = false;
      this.consume(event);
    }
  };

  private consume(event: KeyboardEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }

  private open(): void {
    this.active = true;
    this.typed = '';
    this.refresh();
    this.zone.runOutsideAngular(() => {
      const host = this.host.nativeElement;
      this.observer = new MutationObserver((records) => {
        if (records.some((record) => !host.contains(record.target))) {
          this.scheduleRefresh();
        }
      });
      this.observer.observe(this.scope, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-kbd', 'disabled', 'class', 'style'] });
      window.addEventListener('scroll', this.scheduleRefresh, true);
      window.addEventListener('resize', this.scheduleRefresh);
      // pieces that slide or pop in are measured again once they settle
      this.scope.addEventListener('transitionend', this.scheduleRefresh, true);
      this.scope.addEventListener('animationend', this.scheduleRefresh, true);
    });
  }

  private close(): void {
    this.observer?.disconnect();
    this.observer = null;
    window.removeEventListener('scroll', this.scheduleRefresh, true);
    window.removeEventListener('resize', this.scheduleRefresh);
    this.scope.removeEventListener('transitionend', this.scheduleRefresh, true);
    this.scope.removeEventListener('animationend', this.scheduleRefresh, true);
    if (this.frame !== null) {
      cancelAnimationFrame(this.frame);
      this.frame = null;
    }
    if (!this.active) {
      return;
    }
    this.active = false;
    this.typed = '';
    this.queued = null;
    this.hints = [];
    this.shownHints = [];
    this.cdr.markForCheck();
  }

  /** click the target and hide the hints until the board shows its next set */
  private click(el: Element): void {
    this.typed = '';
    this.hints = [];
    this.shownHints = [];
    this.queued = '';
    this.cdr.markForCheck();
    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    this.scheduleRefresh();
  }

  private setTyped(typed: string): void {
    this.typed = typed;
    const visible = new Set(matchKbd(this.hints.map((hint) => hint.label), typed).visible);
    this.shownHints = this.hints.filter((_, index) => visible.has(index));
    this.cdr.markForCheck();
  }

  private readonly scheduleRefresh = (): void => {
    if (this.frame === null) {
      this.frame = requestAnimationFrame(() => {
        this.frame = null;
        this.zone.run(() => this.refresh());
      });
    }
  };

  /** rebuild the hints from the board; with nothing to pick (the other side's turn) the mode stays on */
  private refresh(): void {
    if (!this.active) {
      return;
    }
    this.hints = this.collect();
    if (!this.hints.length) {
      this.typed = '';
      this.queued = null;
      this.shownHints = [];
      this.cdr.markForCheck();
      return;
    }
    if (!matchKbd(this.hints.map((hint) => hint.label), this.typed).visible.length) {
      this.typed = '';
    }
    this.setTyped(this.typed);
    const queued = this.queued;
    this.queued = null;
    for (const key of queued ?? '') {
      this.type(key);
    }
  }

  private collect(): KbdHint[] {
    // the host fills the scope's padding box and is display:none until open, so measure from the scope
    const scopeRect = this.scope.getBoundingClientRect();
    const left = scopeRect.left + this.scope.clientLeft;
    const top = scopeRect.top + this.scope.clientTop;
    const hints: KbdHint[] = [];
    this.scope.querySelectorAll('[data-kbd]').forEach((el) => {
      const label = el.getAttribute('data-kbd');
      if (!label || el.matches(':disabled, [aria-disabled="true"]')) {
        return;
      }
      const rect = el.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        return;
      }
      const x = rect.left + rect.width / 2;
      const y = rect.top + rect.height / 2;
      if (this.clipped(el, x, y)) {
        return;
      }
      hints.push({ el, label, x: x - left, y: y - top });
    });
    return hints;
  }

  /** a target scrolled out of its board's scroll area gets no hint */
  private clipped(el: Element, x: number, y: number): boolean {
    for (let node = el.parentElement; node && node !== this.scope; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.overflowX === 'visible' && style.overflowY === 'visible') {
        continue;
      }
      const rect = node.getBoundingClientRect();
      if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
        return true;
      }
    }
    return false;
  }
}
