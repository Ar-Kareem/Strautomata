import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { TooltipModule } from 'primeng/tooltip';

import { OWNER_COLORS, type CorewarWarriorState, getCorewarMatchWinner } from './corewar.constants';

@Component({
  selector: 'corewar-match-summary-card',
  standalone: true,
  imports: [TooltipModule],
  templateUrl: './corewar-match-summary-card.component.html',
  styleUrl: './corewar-match-summary-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CorewarMatchSummaryCardComponent {
  @Input() matchDone = false;
  @Input() roundDone = false;
  @Input() matchSummaryDismissed = false;
  @Input() roundSummaryDismissed = false;
  @Input() perWarrior: CorewarWarriorState[] = [];
  @Input() roundWins: number[] = [];

  @Output() dismissMatch = new EventEmitter<void>();
  @Output() openMainMenu = new EventEmitter<void>();
  @Output() dismissRound = new EventEmitter<void>();
  @Output() goNextRound = new EventEmitter<void>();

  get showMatchSummary(): boolean {
    return this.matchDone && !this.matchSummaryDismissed;
  }

  get showRoundSummary(): boolean {
    return this.roundDone && !this.matchDone && !this.roundSummaryDismissed;
  }

  get matchWinner(): { name: string; roundsWon: number; color: string } | null {
    return getCorewarMatchWinner(this.perWarrior, this.roundWins, this.matchDone);
  }

  get matchResults(): Array<{ id: number; name: string; roundsWon: number; color: string; isWinner: boolean }> {
    if (!this.matchDone || this.perWarrior.length === 0) {
      return [];
    }
    const maxWins = this.roundWins.length ? Math.max(...this.roundWins.map((wins) => wins ?? 0)) : 0;
    const winnerCount = this.roundWins.filter((wins) => (wins ?? 0) === maxWins).length;
    const rows = this.perWarrior.map((warrior, index) => {
      const wins = this.roundWins[index] ?? 0;
      return {
        id: warrior?.id ?? index,
        name: warrior?.name?.trim() || `Warrior ${index + 1}`,
        roundsWon: wins,
        color: OWNER_COLORS[index % OWNER_COLORS.length],
        isWinner: winnerCount === 1 && wins === maxWins && maxWins > 0
      };
    });
    rows.sort((a, b) => b.roundsWon - a.roundsWon || a.id - b.id);
    return rows;
  }

  get roundSummaryWinner(): { name: string; color: string; index: number } | null {
    if (!this.roundDone || this.matchDone) {
      return null;
    }
    const alive = this.perWarrior.filter((warrior) => warrior.alive);
    if (alive.length !== 1) {
      return null;
    }
    const winner = alive[0];
    const index = this.perWarrior.indexOf(winner);
    const color = OWNER_COLORS[index % OWNER_COLORS.length];
    return {
      name: winner?.name?.trim() || 'Unknown warrior',
      color,
      index
    };
  }

  get roundSummarySurvivors(): Array<{ name: string; color: string; index: number }> {
    if (!this.roundDone || this.matchDone) {
      return [];
    }
    const survivors: Array<{ name: string; color: string; index: number }> = [];
    this.perWarrior.forEach((warrior, index) => {
      if (!warrior.alive) {
        return;
      }
      survivors.push({
        name: warrior?.name?.trim() || `Warrior ${index + 1}`,
        color: OWNER_COLORS[index % OWNER_COLORS.length],
        index
      });
    });
    return survivors;
  }
}
