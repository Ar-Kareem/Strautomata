import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  Output,
  ViewChild,
  inject,
} from '@angular/core';
import { CorewarInspectorInteractionStore } from './corewar-inspector-interaction.store';

@Component({
  selector: 'corewar-viewer-input-layer',
  standalone: true,
  templateUrl: './corewar-viewer-input-layer.component.html',
  styleUrl: './corewar-viewer-input-layer.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CorewarViewerInputLayerComponent {
  private readonly inspectorStore = inject(CorewarInspectorInteractionStore);

  @Input() canvasSize = 0;
  @Input() instructionCount = 0;
  @Input() cellSize = 14;
  @Input() coreColumns = 1;
  @Output() interactionChanged = new EventEmitter<void>();

  @ViewChild('coreCanvas', { static: true }) coreCanvasRef!: ElementRef<HTMLCanvasElement>;

  get canvasElement(): HTMLCanvasElement {
    return this.coreCanvasRef.nativeElement;
  }

  @HostListener('window:pointerup', ['$event'])
  onWindowPointerUp(event: PointerEvent): void {
    this.onCanvasUp(event);
  }

  @HostListener('window:pointercancel', ['$event'])
  onWindowPointerCancel(event: PointerEvent): void {
    this.onCanvasUp(event);
  }

  onCanvasDown(event: MouseEvent | PointerEvent): void {
    if (event.button !== 0) {
      return;
    }
    if (event instanceof PointerEvent && !event.isPrimary) {
      return;
    }
    if (!this.canvasSize || this.instructionCount === 0) {
      return;
    }
    const index = this.indexFromEvent(event);
    if (index === null) {
      return;
    }
    if (event instanceof PointerEvent) {
      this.coreCanvasRef.nativeElement.setPointerCapture(event.pointerId);
    }
    event.preventDefault();
    this.inspectorStore.beginDrag(index);
    this.emitInteractionChanged();
  }

  onCanvasUp(event?: MouseEvent | PointerEvent): void {
    if (!this.inspectorStore.isDragActive()) {
      return;
    }
    if (event instanceof PointerEvent) {
      if (!event.isPrimary) {
        return;
      }
      if (this.coreCanvasRef.nativeElement.hasPointerCapture(event.pointerId)) {
        this.coreCanvasRef.nativeElement.releasePointerCapture(event.pointerId);
      }
      event.preventDefault();
    }
    if (event) {
      const index = this.indexFromEvent(event);
      const finalIndex = index ?? this.inspectorStore.hoverIndex;
      this.inspectorStore.finishDrag(finalIndex);
    } else {
      this.inspectorStore.finishDrag(this.inspectorStore.hoverIndex);
    }
    this.emitInteractionChanged();
  }

  onCanvasMove(event: MouseEvent | PointerEvent): void {
    if (event instanceof PointerEvent && !event.isPrimary) {
      return;
    }
    if (!this.canvasSize || this.instructionCount === 0) {
      if (!this.inspectorStore.hasLock() && !this.inspectorStore.isDragActive()) {
        this.applyHover(null);
      }
      return;
    }
    const index = this.indexFromEvent(event);
    if (this.inspectorStore.isDragActive()) {
      event.preventDefault();
      if (index === null) {
        return;
      }
      if (!this.inspectorStore.updateDrag(index)) {
        return;
      }
      this.emitInteractionChanged();
      return;
    }
    if (this.inspectorStore.hasLock()) {
      return;
    }
    this.applyHover(index);
  }

  onCanvasLeave(): void {
    if (this.inspectorStore.hasLock() || this.inspectorStore.isDragActive()) {
      return;
    }
    this.applyHover(null);
  }

  private indexFromEvent(event: Pick<MouseEvent, 'clientX' | 'clientY'>): number | null {
    const canvas = this.coreCanvasRef?.nativeElement;
    if (!canvas) {
      return null;
    }
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    if (x < 0 || y < 0 || x >= rect.width || y >= rect.height) {
      return null;
    }
    const axisPad = Math.max(8, Math.round(this.cellSize * 0.6));
    const localX = x - axisPad;
    const localY = y - axisPad;
    if (localX < 0 || localY < 0) {
      return null;
    }
    const col = Math.floor(localX / this.cellSize);
    const row = Math.floor(localY / this.cellSize);
    const rows = Math.ceil(this.instructionCount / this.coreColumns);
    if (col >= this.coreColumns || row >= rows) {
      return null;
    }
    const index = row * this.coreColumns + col;
    if (index < 0 || index >= this.instructionCount) {
      return null;
    }
    return index;
  }

  private applyHover(index: number | null, force = false): void {
    const changed = this.inspectorStore.setHover(index);
    if (!changed && !force) {
      return;
    }
    this.emitInteractionChanged();
  }

  private emitInteractionChanged(): void {
    this.interactionChanged.emit();
  }
}
