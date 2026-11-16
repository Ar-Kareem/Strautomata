import { Injectable } from '@angular/core';

export type CorewarInspectorRow = {
  address: number;
  addressLabel: string;
  instruction: string;
  isSelected: boolean;
  isLockedCenter: boolean;
  isDat: boolean;
  opcodeDescription: string;
  color: string;
  textColor: string;
  isProcess: boolean;
  processCount: number;
  processColor: string | null;
  processTooltip: string | null;
};

export type CorewarHoverRange = {
  start: number;
  length: number;
  selectedIndex: number | null;
  lockMarkerIndex: number | null;
  locked: boolean;
};

@Injectable()
export class CorewarInspectorInteractionStore {
  hoverIndex: number | null = null;
  lockedIndex: number | null = null;
  lockedRange: { start: number; end: number } | null = null;
  private isDragging = false;
  private dragStartIndex: number | null = null;
  private dragCurrentIndex: number | null = null;
  private dragHadLock = false;

  clear(): void {
    this.hoverIndex = null;
    this.lockedIndex = null;
    this.lockedRange = null;
    this.isDragging = false;
    this.dragStartIndex = null;
    this.dragCurrentIndex = null;
    this.dragHadLock = false;
  }

  isDragActive(): boolean {
    return this.isDragging;
  }

  beginDrag(index: number): void {
    this.isDragging = true;
    this.dragStartIndex = index;
    this.dragCurrentIndex = index;
    this.dragHadLock = this.lockedIndex !== null || this.lockedRange !== null;
    this.hoverIndex = index;
  }

  updateDrag(index: number): boolean {
    if (!this.isDragging) {
      return false;
    }
    if (this.dragCurrentIndex === index) {
      return false;
    }
    this.dragCurrentIndex = index;
    this.hoverIndex = index;
    return true;
  }

  finishDrag(finalIndex: number | null): boolean {
    if (!this.isDragging || this.dragStartIndex === null) {
      return false;
    }
    if (finalIndex !== null) {
      this.dragCurrentIndex = finalIndex;
    }
    const startIndex = this.dragStartIndex;
    const endIndex = this.dragCurrentIndex ?? this.dragStartIndex;
    const start = Math.min(startIndex, endIndex);
    const end = Math.max(startIndex, endIndex);
    const dragged = start !== end;
    this.isDragging = false;
    this.dragStartIndex = null;
    this.dragCurrentIndex = null;
    if (dragged) {
      this.lockedIndex = null;
      this.lockedRange = { start, end };
      this.hoverIndex = end;
    } else if (this.dragHadLock) {
      this.lockedIndex = null;
      this.lockedRange = null;
      this.hoverIndex = start;
    } else {
      this.lockedRange = null;
      this.lockedIndex = start;
      this.hoverIndex = start;
    }
    this.dragHadLock = false;
    return true;
  }

  setHover(index: number | null): boolean {
    if (index === null) {
      if (this.hoverIndex === null) {
        return false;
      }
      this.hoverIndex = null;
      return true;
    }
    if (this.hoverIndex === index) {
      return false;
    }
    this.hoverIndex = index;
    return true;
  }

  hasLock(): boolean {
    return this.lockedIndex !== null || this.lockedRange !== null;
  }

  getHoverRange(size: number, viewSize: number): CorewarHoverRange | null {
    if (!size) {
      return null;
    }
    if (this.isDragging && this.dragStartIndex !== null && this.dragCurrentIndex !== null) {
      const start = Math.min(this.dragStartIndex, this.dragCurrentIndex);
      const end = Math.max(this.dragStartIndex, this.dragCurrentIndex);
      return {
        start,
        length: end - start + 1,
        selectedIndex: this.dragCurrentIndex,
        lockMarkerIndex: null,
        locked: false
      };
    }
    if (this.lockedRange) {
      const start = Math.max(0, Math.min(size - 1, this.lockedRange.start));
      const end = Math.max(0, Math.min(size - 1, this.lockedRange.end));
      return {
        start,
        length: end - start + 1,
        selectedIndex: this.hoverIndex ?? start,
        lockMarkerIndex: start,
        locked: true
      };
    }
    if (this.lockedIndex !== null) {
      const startOffset = -Math.floor(viewSize / 2);
      const start = (this.lockedIndex + startOffset + size) % size;
      return {
        start,
        length: viewSize,
        selectedIndex: this.lockedIndex,
        lockMarkerIndex: this.lockedIndex,
        locked: true
      };
    }
    if (this.hoverIndex !== null) {
      const startOffset = -Math.floor(viewSize / 2);
      const start = (this.hoverIndex + startOffset + size) % size;
      return {
        start,
        length: viewSize,
        selectedIndex: this.hoverIndex,
        lockMarkerIndex: null,
        locked: false
      };
    }
    return null;
  }
}
