import { Injectable, NgZone } from '@angular/core';
import { Store } from '@ngrx/store';
import type { StatusTone } from '@main/arena.constants';
import type { ArenaState } from '@main/arena.store';
import { arenaActions } from '@main/arena.store';
import { CorewarPyodideClient } from '../workers/corewar-pyodide.client';

@Injectable({ providedIn: 'root' })
export class CorewarConsoleRunner {
  private readonly client: CorewarPyodideClient;

  constructor(
    private readonly store: Store<{ arena: ArenaState }>,
    private readonly zone: NgZone
  ) {
    this.client = new CorewarPyodideClient({
      setStatus: (tone, message) => this.patchStatus(tone, message)
    });
    (window as any).corewarRunner = this;
  }

  private patchStatus(tone: StatusTone, message: string): void {
    this.zone.run(() => {
      this.store.dispatch(arenaActions.patchState({ status: { tone, message } }));
    });
  }

  ensureRunner(): Promise<{ ok?: boolean }> {
    return this.client.request({ type: 'ensureRunner' });
  }

  async listFileWarriors(): Promise<unknown> {
    const result = await this.client.request({ type: 'listFileWarriors' });
    return result;
  }

  loadWarriorCode(path: string): Promise<unknown> {
    return this.client.request({ type: 'loadWarriorCode', payload: { path } });
  }

  compileWarrior(payload: { code: string; config?: Record<string, unknown> }): Promise<unknown> {
    return this.client.request({ type: 'compileWarrior', payload });
  }

  initMatch(payload: { config?: Record<string, unknown>; warriorSpecs?: Record<string, unknown>[] }): Promise<unknown> {
    return this.client.request({ type: 'initMatch', payload });
  }

  stepMatch(payload: { matchId: number; steps?: number; view?: string; centerAddr?: number | null; window?: number | null }): Promise<unknown> {
    return this.client.request({ type: 'stepMatch', payload });
  }

  nextRound(matchId: number): Promise<unknown> {
    return this.client.request({ type: 'nextRound', matchId });
  }

  reloadRound(matchId: number): Promise<unknown> {
    return this.client.request({ type: 'reloadRound', matchId });
  }

  getProcesses(matchId: number): Promise<unknown> {
    return this.client.request({ type: 'getProcesses', matchId });
  }

  destroyMatch(matchId: number): Promise<unknown> {
    return this.client.request({ type: 'destroyMatch', matchId });
  }
}
