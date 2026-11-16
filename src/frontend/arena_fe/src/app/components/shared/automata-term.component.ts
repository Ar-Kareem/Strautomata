import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** The word "automata" with a hover/focus explainer: the self-operating-machine sense, not finite-state automata. */
@Component({
  selector: 'automata-term',
  standalone: true,
  host: { tabindex: '0', '[class.is-below]': "placement() === 'below'" },
  template: `
    <ng-content />
    <span class="tip" role="tooltip">
      <b>automaton</b>, from Greek <i>autómatos</i>, "acting of itself": a self-operating machine. We mean this older
      sense, not the finite-state automata of computer science.
    </span>
  `,
  styles: `
    :host {
      position: relative;
      color: var(--ink-900);
      border-bottom: 1px dotted var(--accent-3);
      cursor: help;
      outline: none;
    }
    .tip {
      position: absolute;
      z-index: 20;
      left: 50%;
      bottom: calc(100% + 10px);
      width: 300px;
      padding: 10px 12px;
      border: 1px solid rgba(255, 177, 74, 0.45);
      border-radius: 8px;
      background: rgba(8, 14, 26, 0.97);
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.55), 0 0 14px rgba(255, 177, 74, 0.15);
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 400;
      letter-spacing: normal;
      text-transform: none;
      line-height: 1.5;
      white-space: normal;
      color: var(--ink-700);
      opacity: 0;
      pointer-events: none;
      transform: translate(-50%, 4px);
      transition: opacity 0.15s ease, transform 0.15s ease;
    }
    .tip::after {
      content: '';
      position: absolute;
      top: 100%;
      left: 50%;
      margin-left: -6px;
      border: 6px solid transparent;
      border-top-color: rgba(255, 177, 74, 0.45);
    }
    :host(.is-below) .tip {
      bottom: auto;
      top: calc(100% + 10px);
      transform: translate(-50%, -4px);
    }
    :host(.is-below) .tip::after {
      top: auto;
      bottom: 100%;
      border-top-color: transparent;
      border-bottom-color: rgba(255, 177, 74, 0.45);
    }
    .tip b {
      font-family: var(--font-display);
      font-weight: 400;
      color: var(--accent-3);
    }
    :host(:hover) .tip,
    :host(:focus) .tip {
      opacity: 1;
      transform: translate(-50%, 0);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AutomataTermComponent {
  /** Where the explainer opens relative to the word. */
  readonly placement = input<'above' | 'below'>('above');
}
