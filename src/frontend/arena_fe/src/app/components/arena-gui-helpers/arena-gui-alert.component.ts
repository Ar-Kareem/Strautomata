import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  HostBinding,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges
} from '@angular/core';

const ALERT_FADE_MS = 320;

@Component({
  selector: 'arena-gui-alert',
  standalone: true,
  templateUrl: './arena-gui-alert.component.html',
  styleUrl: './arena-gui-alert.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaGuiAlertComponent implements OnChanges, OnDestroy {
  @Input() message: string | null = null;

  /** Host hides entirely when there is nothing to render. */
  @HostBinding('style.display')
  get hostDisplay(): string {
    return this.renderedMessage ? 'block' : 'none';
  }

  visible = false;
  renderedMessage: string | null = null;

  private hideTimerId: number | null = null;
  private showRafId: number | null = null;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['message']) return;

    const next = this.normalizeMessage(this.message);

    if (next) {
      this.show(next);
    } else {
      this.hide();
    }
  }

  ngOnDestroy(): void {
    this.clearHideTimer();
    this.clearShowRaf();
  }

  private show(msg: string): void {
    this.clearHideTimer();
    const isNewMessage = this.renderedMessage !== msg;
    this.renderedMessage = msg;

    // if already visible, just update text
    if (this.visible) {
      if (isNewMessage) this.cdr.markForCheck();
      return;
    }

    // start from hidden state to allow CSS transitions to run
    this.visible = false;
    this.cdr.markForCheck();

    // next animation frame: flip visible to true so transitions trigger
    this.clearShowRaf();
    this.showRafId = window.requestAnimationFrame(() => {
      this.showRafId = null;

      // only show if the input is still non-empty (guard against race)
      if (!this.normalizeMessage(this.message)) return;

      this.visible = true;
      this.cdr.markForCheck();
    });
  }

  private hide(): void {
    if (!this.renderedMessage) return;
    // fade-out
    if (this.visible) {
      this.visible = false;
      this.cdr.markForCheck();
    }
    // after fade duration, drop the rendered message (if still empty)
    this.clearHideTimer();
    this.hideTimerId = window.setTimeout(() => {
      this.hideTimerId = null;

      // if a message came back, keep rendering
      if (this.normalizeMessage(this.message)) return;

      this.renderedMessage = null;
      this.cdr.markForCheck();
    }, ALERT_FADE_MS);
  }

  private normalizeMessage(value: string | null): string {
    return typeof value === 'string' ? value.trim() : '';
  }

  private clearHideTimer(): void {
    if (this.hideTimerId !== null) {
      window.clearTimeout(this.hideTimerId);
      this.hideTimerId = null;
    }
  }

  private clearShowRaf(): void {
    if (this.showRafId !== null) {
      window.cancelAnimationFrame(this.showRafId);
      this.showRafId = null;
    }
  }
}
