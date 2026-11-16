import { Component, ElementRef, EventEmitter, Input, Output, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';

import { arenaActions, ArenaState } from '@main/arena.store';
import { DEFAULT_SIM_CONFIG, type CorewarSimConfig } from './corewar.constants';

@Component({
  selector: 'corewar-match-controls',
  standalone: true,
  imports: [DialogModule, FormsModule, InputTextModule],
  templateUrl: './corewar-match-controls.component.html',
  styleUrl: './corewar-match-controls.component.scss'
})
export class CorewarMatchControlsComponent {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly arenaState = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);

  @Input() matchId: number | null = null;
  @Input() loading = false;
  @Input() running = false;
  @Input() roundDone = false;
  @Input() matchDone = false;
  @Input() moveSpeed = 1;
  @Input() simConfig: CorewarSimConfig = { ...DEFAULT_SIM_CONFIG };

  @Output() startMatch = new EventEmitter<void>();
  @Output() toggleRunning = new EventEmitter<void>();
  @Output() stepOnce = new EventEmitter<void>();
  @Output() nextRound = new EventEmitter<void>();
  @Output() moveSpeedChange = new EventEmitter<number>();
  @Output() simConfigChange = new EventEmitter<CorewarSimConfig>();

  draftConfig: CorewarSimConfig = { ...DEFAULT_SIM_CONFIG };
  speedEditOpen = false;
  speedEditValue = '1';
  private readonly sliderMax = 600;
  private readonly sliderBreakOne = Math.round(this.sliderMax * 0.1); // 10%
  private readonly sliderBreakTwo = Math.round(this.sliderMax * 0.5); // 50%
  private readonly speedMax = 2000;
  private readonly lowSpeedMax = 10;
  private readonly midSpeedMax = 100;

  @ViewChild('speedPopoverInput') private speedPopoverInput?: ElementRef<HTMLInputElement>;

  get configVisible(): boolean {
    return this.arenaState().corewar.configDialogOpen;
  }

  onConfigShow(): void {
    this.draftConfig = { ...this.simConfig };
  }

  get sliderValue(): number {
    return this.speedToSlider(this.moveSpeed);
  }

  onSpeedInput(input: HTMLInputElement): void {
    const raw = input.value.trim();
    const parsed = Number.parseInt(raw, 10);
    const numeric = Number.isFinite(parsed) ? Math.floor(parsed) : 0;
    const clampedSlider = this.clampSlider(numeric);
    if (raw === '' || !Number.isFinite(parsed) || parsed !== clampedSlider) {
      input.value = String(clampedSlider);
    }
    const speed = this.sliderToSpeed(clampedSlider);
    this.moveSpeedChange.emit(speed);
  }

  openSpeedEdit(): void {
    this.speedEditValue = String(this.moveSpeed);
    this.speedEditOpen = true;
    queueMicrotask(() => {
      const input = this.speedPopoverInput?.nativeElement;
      if (input) {
        input.focus();
        input.select();
      }
    });
  }

  onSpeedEditInput(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    this.speedEditValue = target?.value ?? '';
  }

  closeSpeedEdit(apply: boolean): void {
    this.commitSpeedEdit(apply);
  }

  private commitSpeedEdit(apply: boolean): void {
    if (!this.speedEditOpen) {
      return;
    }
    if (apply) {
      const parsed = Number(this.speedEditValue);
      const numeric = Number.isFinite(parsed) ? Math.floor(parsed) : this.moveSpeed;
      const clamped = this.clampSpeed(numeric);
      this.moveSpeedChange.emit(clamped);
    }
    this.speedEditOpen = false;
  }

  closeConfig(): void {
    this.store.dispatch(arenaActions.updateCorewarConfigDialogOpen({ open: false }));
  }

  applyConfig(): void {
    const normalized: CorewarSimConfig = {
      rounds: this.normalizeValue(this.draftConfig.rounds, DEFAULT_SIM_CONFIG.rounds, 1),
      size: this.normalizeValue(this.draftConfig.size, DEFAULT_SIM_CONFIG.size, 1),
      cycles: this.normalizeValue(this.draftConfig.cycles, DEFAULT_SIM_CONFIG.cycles, 1),
      processes: this.normalizeValue(this.draftConfig.processes, DEFAULT_SIM_CONFIG.processes, 1),
      length: this.normalizeValue(this.draftConfig.length, DEFAULT_SIM_CONFIG.length, 1),
      distance: this.normalizeValue(this.draftConfig.distance, DEFAULT_SIM_CONFIG.distance, 0),
      seed: this.normalizeValue(this.draftConfig.seed, DEFAULT_SIM_CONFIG.seed, 0)
    };
    this.simConfigChange.emit(normalized);
    this.store.dispatch(arenaActions.updateCorewarConfigDialogOpen({ open: false }));
  }

  resetConfig(): void {
    this.draftConfig = { ...DEFAULT_SIM_CONFIG };
  }

  private normalizeValue(value: number | string | null, fallback: number, minValue: number): number {
    const parsed = Number(value);
    const numeric = Number.isFinite(parsed) ? Math.floor(parsed) : fallback;
    return Math.max(minValue, numeric);
  }

  private sliderToSpeed(value: number): number {
    const clamped = this.clampSlider(value);
    if (clamped <= this.sliderBreakOne) {
      const speed = Math.round((clamped / this.sliderBreakOne) * this.lowSpeedMax);
      return this.clampSpeed(speed);
    }
    if (clamped <= this.sliderBreakTwo) {
      const t = (clamped - this.sliderBreakOne) / (this.sliderBreakTwo - this.sliderBreakOne);
      const speed = Math.round(this.lowSpeedMax + t * (this.midSpeedMax - this.lowSpeedMax));
      return this.clampSpeed(speed);
    }
    const t = (clamped - this.sliderBreakTwo) / (this.sliderMax - this.sliderBreakTwo);
    const speed = Math.round(this.midSpeedMax * Math.pow(this.speedMax / this.midSpeedMax, t));
    return this.clampSpeed(speed);
  }

  private speedToSlider(value: number): number {
    const clamped = this.clampSpeed(value);
    if (clamped <= this.lowSpeedMax) {
      const slider = Math.round((clamped / this.lowSpeedMax) * this.sliderBreakOne);
      return this.clampSlider(slider);
    }
    if (clamped <= this.midSpeedMax) {
      const t = (clamped - this.lowSpeedMax) / (this.midSpeedMax - this.lowSpeedMax);
      const slider = Math.round(this.sliderBreakOne + t * (this.sliderBreakTwo - this.sliderBreakOne));
      return this.clampSlider(slider);
    }
    const t = Math.log(clamped / this.midSpeedMax) / Math.log(this.speedMax / this.midSpeedMax);
    const slider = Math.round(this.sliderBreakTwo + t * (this.sliderMax - this.sliderBreakTwo));
    return this.clampSlider(slider);
  }

  private clampSlider(value: number): number {
    return Math.max(0, Math.min(this.sliderMax, value));
  }

  private clampSpeed(value: number): number {
    return Math.max(0, Math.min(this.speedMax, value));
  }
}
