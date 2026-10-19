import { ModelLogoComponent } from '../shared/model-logo.component';
import { ChangeDetectionStrategy, Component, ElementRef, HostListener, computed, inject, input, output, signal } from '@angular/core';

export type FilterGroup = { family: string; color: string; models: { id: string; count: number }[] };

/** "Filter" button with a popup of families and their models; unchecked models are hidden. */
@Component({
  selector: 'matches-heatmap-filter',
  standalone: true,
  imports: [ModelLogoComponent],
  templateUrl: './matches-heatmap-filter.component.html',
  styleUrl: './matches-heatmap-filter.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesHeatmapFilterComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly groups = input.required<FilterGroup[]>();
  readonly hidden = input.required<ReadonlySet<string>>();
  readonly hiddenChange = output<Set<string>>();

  readonly open = signal(false);
  readonly hiddenCount = computed(() => {
    const hidden = this.hidden();
    return this.groups().reduce((sum, group) => sum + group.models.filter((m) => hidden.has(m.id)).length, 0);
  });

  familyState(group: FilterGroup): 'all' | 'some' | 'none' {
    const shown = group.models.filter((m) => !this.hidden().has(m.id)).length;
    return shown === group.models.length ? 'all' : shown === 0 ? 'none' : 'some';
  }

  toggleFamily(group: FilterGroup): void {
    const next = new Set(this.hidden());
    const showAll = this.familyState(group) !== 'all';
    for (const model of group.models) {
      if (showAll) {
        next.delete(model.id);
      } else {
        next.add(model.id);
      }
    }
    this.hiddenChange.emit(next);
  }

  toggleModel(id: string): void {
    const next = new Set(this.hidden());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this.hiddenChange.emit(next);
  }

  showAll(): void {
    this.hiddenChange.emit(new Set());
  }

  showNone(): void {
    this.hiddenChange.emit(new Set(this.groups().flatMap((group) => group.models.map((m) => m.id))));
  }

  @HostListener('document:pointerdown', ['$event'])
  onDocumentPointerDown(event: PointerEvent): void {
    if (this.open() && !this.host.nativeElement.contains(event.target as Node)) {
      this.open.set(false);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.open.set(false);
  }
}
