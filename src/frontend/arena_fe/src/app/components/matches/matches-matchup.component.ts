import { ModelLogoComponent } from '../shared/model-logo.component';
import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import type { MatchRow, OpponentSummary, PlayerResult } from '@main/history.types';
import { RESULT_LABEL, describeMatch, familyColor, formatSecs, matchPoints, resultTone } from './history-format';

@Component({
  selector: 'matches-matchup',
  standalone: true,
  imports: [ModelLogoComponent, DecimalPipe],
  templateUrl: './matches-matchup.component.html',
  styleUrl: './matches-matchup.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesMatchupComponent {
  /** every decoded row of the current stage */
  readonly rows = input.required<MatchRow[]>();
  readonly botA = input.required<string>();
  readonly botB = input<string | null>(null);
  readonly labels = input.required<Record<string, string>>();
  readonly families = input<Record<string, string>>({});
  readonly ranks = input<Record<string, number>>({});
  /** bots that qualified for the tournament; null hides the column (outside the qualification stage) */
  readonly qualified = input<Set<string> | null>(null);
  readonly openRowIndex = input<number | null>(null);
  readonly pickOpponent = output<string>();
  readonly openMatch = output<MatchRow>();

  readonly familyColor = familyColor;
  readonly formatSecs = formatSecs;
  readonly resultLabel = RESULT_LABEL;
  readonly resultTone = resultTone;

  labelOf(bot: string): string {
    return this.labels()[bot] ?? bot;
  }

  /** rows in which the selected bot(s) took part, with the selected bot A normalised to "me" */
  readonly myRows = computed(() => {
    const a = this.botA();
    const b = this.botB();
    return this.rows().filter((row) => {
      if (b) {
        return (row.a === a && row.b === b) || (row.a === b && row.b === a);
      }
      return row.a === a || row.b === a;
    });
  });

  readonly opponents = computed<OpponentSummary[]>(() => {
    const a = this.botA();
    const byOpp = new Map<string, OpponentSummary>();
    for (const row of this.myRows()) {
      const meIsA = row.a === a;
      const opp = meIsA ? row.b : row.a;
      const my = meIsA ? row.resA : row.resB;
      let entry = byOpp.get(opp);
      if (!entry) {
        entry = {
          id: opp,
          label: this.labelOf(opp),
          family: this.families()[opp] ?? 'Other',
          rank: this.ranks()[opp] ?? null,
          n: 0,
          wins: 0,
          losses: 0,
          draws: 0,
          ownErrors: 0,
          ownTimeouts: 0,
          oppErrors: 0,
          oppTimeouts: 0,
          score: 0
        };
        byOpp.set(opp, entry);
      }
      entry.n += 1;
      switch (my) {
        case 'win':
          entry.wins += 1;
          break;
        case 'loss':
          entry.losses += 1;
          break;
        case 'draw':
          entry.draws += 1;
          break;
        case 'error':
          entry.ownErrors += 1;
          break;
        case 'timeout':
          entry.ownTimeouts += 1;
          break;
        case 'enemy_error':
          entry.oppErrors += 1;
          break;
        case 'enemy_timeout':
          entry.oppTimeouts += 1;
          break;
        default:
          break;
      }
    }
    const list = [...byOpp.values()];
    for (const entry of list) {
      entry.score = entry.n ? matchPoints(entry.wins + entry.oppErrors + entry.oppTimeouts, entry.draws) / entry.n : 0;
    }
    list.sort((x, y) => (x.rank ?? 1e9) - (y.rank ?? 1e9) || x.label.localeCompare(y.label));
    return list;
  });

  readonly totals = computed(() => {
    const a = this.botA();
    const t = { n: 0, win: 0, loss: 0, draw: 0, fault: 0, gift: 0 };
    for (const row of this.myRows()) {
      const my = row.a === a ? row.resA : row.resB;
      t.n += 1;
      if (my === 'win') t.win += 1;
      else if (my === 'loss') t.loss += 1;
      else if (my === 'draw') t.draw += 1;
      else if (my === 'error' || my === 'timeout') t.fault += 1;
      else if (my === 'enemy_error' || my === 'enemy_timeout') t.gift += 1;
    }
    return { ...t, pointsA: matchPoints(t.win + t.gift, t.draw), pointsB: matchPoints(t.loss + t.fault, t.draw) };
  });

  myResult(row: MatchRow): PlayerResult {
    return row.a === this.botA() ? row.resA : row.resB;
  }

  sideOf(row: MatchRow): string {
    return row.a === this.botA() ? 'first' : 'second';
  }

  describe(row: MatchRow): string {
    return describeMatch(row, this.labelOf(row.a), this.labelOf(row.b));
  }

  scoreStyle(opp: OpponentSummary): Record<string, string> {
    const n = opp.n || 1;
    const pct = (count: number) => `${(count / n) * 100}%`;
    // wins and losses split into games played to the end and games decided by a fault
    return {
      '--score': `${Math.round(opp.score * 100)}%`,
      '--win': pct(opp.wins),
      '--win-fault': pct(opp.oppErrors + opp.oppTimeouts),
      '--draw': pct(opp.draws),
      '--loss-fault': pct(opp.ownErrors + opp.ownTimeouts),
      '--loss': pct(opp.losses)
    };
  }

}
