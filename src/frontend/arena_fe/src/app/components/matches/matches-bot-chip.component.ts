import { ChangeDetectionStrategy, Component, computed, DestroyRef, inject, input, output } from '@angular/core';
import type { ModelAutomaton } from '@main/history.types';
import { AutomatonTipService, automatonRecord, recordScore, type TipBody } from './automaton-tip';
import { botShortLabel } from './history-format';

/**
 * One automaton as a chip: crown for the model's best, highlighted when it qualified, its score
 * filling it from the left. Hover shows the shared tooltip.
 */
@Component({
  selector: 'matches-bot-chip',
  standalone: true,
  template: `
    <button
      type="button"
      class="chip"
      [class.is-qualified]="automaton().qualified"
      [class.is-top]="top()"
      [class.is-active]="active()"
      [style.--score.%]="score() * 100"
      [attr.aria-label]="label()"
      (pointerenter)="tips.show($event, tip())"
      (pointerleave)="tips.hide()"
      (focus)="tips.show($event, tip())"
      (blur)="tips.hide()"
      (click)="onClick($event)"
    >
      @if (top()) {
        <i class="fa-solid fa-crown" aria-hidden="true"></i>
      }
      {{ label() }}
    </button>
  `,
  styles: `
    :host {
      display: inline-flex;
    }
    .chip {
      --score: 0%;
      appearance: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 7px;
      border: 1px solid rgba(145, 166, 204, 0.25);
      background:
        linear-gradient(90deg, rgba(145, 166, 204, 0.16) var(--score), transparent var(--score)),
        rgba(5, 10, 18, 0.6);
      color: var(--ink-500);
      font: inherit;
      font-size: 0.72rem;
      font-variant-numeric: tabular-nums;
      cursor: pointer;
    }
    .chip.is-qualified {
      border-color: rgba(45, 212, 191, 0.5);
      background:
        linear-gradient(90deg, rgba(45, 212, 191, 0.22) var(--score), transparent var(--score)),
        rgba(5, 10, 18, 0.6);
      color: var(--ink-900);
    }
    .chip.is-top i {
      color: #ffd166;
      font-size: 0.85em;
    }
    .chip:hover,
    .chip.is-active {
      border-color: var(--accent-1);
      color: var(--accent-1);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesBotChipComponent {
  readonly tips = inject(AutomatonTipService);
  // the tip lives in a shared host, so a hovered element destroyed mid-hover never fires pointerleave
  private readonly hideTipOnDestroy = inject(DestroyRef).onDestroy(() => this.tips.hide());

  readonly automaton = input.required<ModelAutomaton>();
  readonly tip = input.required<TipBody>();
  readonly top = input(false);
  readonly active = input(false);
  readonly pick = output<void>();

  readonly label = computed(() => botShortLabel(this.automaton().bot));
  readonly score = computed(() => recordScore(automatonRecord(this.automaton())) ?? 0);

  onClick(event: Event): void {
    event.stopPropagation();
    this.tips.hide();
    this.pick.emit();
  }
}
