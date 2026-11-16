import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'arena-gui-empty',
  standalone: true,
  templateUrl: './arena-gui-empty.component.html',
  styleUrl: './arena-gui-empty.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaGuiEmptyComponent {
  @Input() message = 'Loading Game...';
}
