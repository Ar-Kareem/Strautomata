import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges } from '@angular/core';

@Component({
  selector: 'arena-human-move-panel',
  standalone: true,
  templateUrl: './human-move-panel.component.html',
  styleUrl: './human-move-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HumanMovePanelComponent implements OnChanges, OnDestroy {
  @Input() show = false;
  @Input() hint = '';
  @Input() errorMessage: string | null = null;
  @Input() errorToken = 0;
  @Input() actionLabel: string | null = null;
  @Input() actionDisabled = false;
  @Output() action = new EventEmitter<void>();

  transientError: string | null = null;
  private errorTimer: number | null = null;
  private destroyed = false;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['errorToken'] && this.errorMessage) {
      this.showError(this.errorMessage);
    }
    if (changes['show'] && !this.show) {
      this.clearError();
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.clearErrorTimer();
  }

  private showError(message: string): void {
    this.transientError = message;
    this.cdr.markForCheck();
    this.clearErrorTimer();
    this.errorTimer = window.setTimeout(() => {
      if (this.destroyed) {
        return;
      }
      this.transientError = null;
      this.cdr.markForCheck();
      this.cdr.detectChanges();
    }, 1000);
  }

  private clearError(): void {
    this.clearErrorTimer();
    this.transientError = null;
    this.cdr.markForCheck();
  }

  private clearErrorTimer(): void {
    if (this.errorTimer !== null) {
      window.clearTimeout(this.errorTimer);
      this.errorTimer = null;
    }
  }
}
