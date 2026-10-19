import { ChangeDetectorRef, Component, HostBinding, Input, OnChanges, OnDestroy, SimpleChanges } from '@angular/core';

const BANNER_FADE_MS = 320;

@Component({
  selector: 'arena-banner',
  standalone: true,
  templateUrl: './arena-banner.component.html',
  styleUrl: './arena-banner.component.scss',
})
export class ArenaBannerComponent implements OnChanges, OnDestroy {
  @Input() message: string | null = null;
  @Input() role: 'status' | 'alert' = 'status';

  @HostBinding('style.display')
  get hostDisplay(): string {
    return this.renderedMessage ? 'block' : 'none';
  }

  visible = false;
  renderedMessage: string | null = null;
  private hideTimer: number | null = null;
  private showFrame: number | null = null;
  private destroyed = false;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['message']) {
      return;
    }
    const nextMessage = typeof this.message === 'string' ? this.message.trim() : '';
    if (nextMessage) {
      this.clearHideTimer();
      this.renderedMessage = nextMessage;
      if (!this.visible) {
        this.visible = false;
        this.cdr.markForCheck();
        this.queueShow();
      } else {
        this.cdr.markForCheck();
      }
      return;
    }
    if (this.renderedMessage) {
      this.visible = false;
      this.cdr.markForCheck();
      this.scheduleHide();
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.clearHideTimer();
    this.clearShowFrame();
  }

  private scheduleHide(): void {
    this.clearHideTimer();
    this.hideTimer = window.setTimeout(() => {
      if (this.destroyed) {
        return;
      }
      const hasMessage = typeof this.message === 'string' && this.message.trim().length > 0;
      if (hasMessage) {
        return;
      }
      this.renderedMessage = null;
      this.cdr.markForCheck();
      this.cdr.detectChanges();
    }, BANNER_FADE_MS);
  }

  private queueShow(): void {
    this.clearShowFrame();
    this.showFrame = window.requestAnimationFrame(() => {
      this.showFrame = window.requestAnimationFrame(() => {
        this.showFrame = null;
        if (this.destroyed) {
          return;
        }
        const hasMessage = typeof this.message === 'string' && this.message.trim().length > 0;
        if (!hasMessage) {
          return;
        }
        this.visible = true;
        this.cdr.markForCheck();
        this.cdr.detectChanges();
      });
    });
  }

  private clearHideTimer(): void {
    if (this.hideTimer !== null) {
      window.clearTimeout(this.hideTimer);
      this.hideTimer = null;
    }
  }

  private clearShowFrame(): void {
    if (this.showFrame !== null) {
      window.cancelAnimationFrame(this.showFrame);
      this.showFrame = null;
    }
  }
}
