import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'arena-gui-legend',
  standalone: true,
  templateUrl: './arena-gui-legend.component.html',
  styleUrl: './arena-gui-legend.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None
})
export class ArenaGuiLegendComponent {}
