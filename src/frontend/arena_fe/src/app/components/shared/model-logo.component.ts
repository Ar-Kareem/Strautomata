import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { resolveBotLogo, resolveFamilyLogo } from '@main/arena.utils';

/** Provider logo for a model family or bot id; a dice for the random baseline, a robot otherwise. */
@Component({
  selector: 'model-logo',
  standalone: true,
  template: `
    @if (src(); as url) {
      <img [src]="url" alt="" />
    } @else {
      <i class="fa-solid {{ isBaseline() ? 'fa-dice' : 'fa-robot' }}" aria-hidden="true"></i>
    }
  `,
  styles: `
    :host {
      display: inline-flex;
      flex-shrink: 0;
      align-items: center;
      justify-content: center;
      width: var(--logo-size, 14px);
      height: var(--logo-size, 14px);
      color: var(--ink-500);
      font-size: calc(var(--logo-size, 14px) * 0.8);
    }
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  `,
  host: { '[style.--logo-size.px]': 'size()' },
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ModelLogoComponent {
  readonly family = input<string | null | undefined>(null);
  readonly bot = input<string | null | undefined>(null);
  readonly size = input(14);

  readonly src = computed(() => resolveFamilyLogo(this.family()) ?? (this.bot() ? resolveBotLogo(this.bot()!) : null));
  readonly isBaseline = computed(() => this.family() === 'Baseline' || this.bot()?.split('/')[0] === 'random');
}
