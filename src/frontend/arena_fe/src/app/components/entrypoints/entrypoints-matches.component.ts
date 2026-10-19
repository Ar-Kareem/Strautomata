import { ModelLogoComponent } from '../shared/model-logo.component';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  effect,
  inject,
  signal,
  untracked
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { arenaActions, type ArenaState } from '@main/arena.store';
import { GAME_GUI_IDS } from '@main/arena.constants';
import { getHashRouteState, setHashRouteState } from '@main/arena.utils';
import { GamePreviewComponent } from '../previews/game-preview.component';
import { GamePickerComponent, type GamePickerOption } from '../arena/game-picker.component';
import { MatchesOverallComponent } from '../matches/matches-overall.component';
import { NAV_HOME_EVENT } from '../../header.component';
import type {
  BotRecord,
  GameSummary,
  HistoryIndex,
  HistoryIndexGame,
  LeaderboardRow,
  MatchDetail,
  MatchRow,
  MatchesTable,
  QualsRanking,
  Stage,
  StageSummary,
  ViewStage
} from '@main/history.types';
import { HistoryService } from '../matches/history.service';
import { MatchesLeaderboardComponent } from '../matches/matches-leaderboard.component';
import { MatchesHeatmapComponent } from '../matches/matches-heatmap.component';
import { MatchesMatchupComponent } from '../matches/matches-matchup.component';
import { MatchesReplayComponent } from '../matches/matches-replay.component';
import { MatchesModelComponent } from '../matches/matches-model.component';
import { MatchesModelGameHeroComponent } from '../matches/matches-model-hero.component';
import { MatchesModelAutomataComponent } from '../matches/matches-model-automata.component';
import { MatchesAutomatonSourceComponent } from '../matches/matches-automaton-source.component';
import { MatchesTipComponent } from '../matches/automaton-tip';
import { MatchesFightButtonComponent } from '../matches/fight-button.component';
import { botLabel, botShortLabel, familyColor, formatRating, modelOf } from '../matches/history-format';

type View = 'overview' | 'model' | 'game' | 'bot' | 'pair';

interface QualsCard {
  model: string;
  family: string;
  bots: string[];
  rankings: QualsRanking[];
  qualifiedCount: number;
}


/** a view to return to with Back; `leaveTo` leaves the game for a model page (or the overall leaderboard) */
type BackEntry = {
  opened: string;
  stage: ViewStage;
  botA: string | null;
  openModel: string | null;
  leaveTo?: { profile: string | null };
};

@Component({
  selector: 'arena-entrypoint-matches',
  standalone: true,
  imports: [DecimalPipe, FormsModule, MatchesLeaderboardComponent, MatchesHeatmapComponent, MatchesMatchupComponent, MatchesReplayComponent, GamePreviewComponent, GamePickerComponent, MatchesOverallComponent, MatchesModelComponent, MatchesModelAutomataComponent, MatchesModelGameHeroComponent, MatchesAutomatonSourceComponent, MatchesTipComponent, MatchesFightButtonComponent, ModelLogoComponent],
  templateUrl: './entrypoints-matches.component.html',
  styleUrl: './entrypoints-matches.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaEntrypointMatchesComponent implements OnInit {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly history = inject(HistoryService);

  readonly familyColor = familyColor;
  readonly formatRating = formatRating;
  readonly botLabel = botLabel;
  readonly modelOf = modelOf;
  readonly botShortLabel = botShortLabel;

  // ---- data --------------------------------------------------------------------------
  readonly index = signal<HistoryIndex | null>(null);
  readonly indexError = signal<string | null>(null);
  readonly summary = signal<GameSummary | null>(null);
  readonly summaryLoading = signal(false);
  readonly table = signal<MatchesTable | null>(null);
  readonly tableLoading = signal(false);
  readonly loadError = signal<string | null>(null);
  readonly detail = signal<MatchDetail | null>(null);
  readonly detailLoading = signal(false);

  // ---- selection ----------------------------------------------------------------------
  readonly gameKey = signal<string | null>(null);
  /** a model's page across every game (no game selected) */
  readonly profile = signal<string | null>(null);
  readonly stage = signal<ViewStage>('models');
  readonly botA = signal<string | null>(null);
  readonly botB = signal<string | null>(null);
  readonly openRow = signal<MatchRow | null>(null);
  /** sidebar selection, as models (picking a family selects all of its models); empty = everything */
  readonly modelSel = signal<ReadonlySet<string>>(new Set());
  /**
   * the model whose page is open in the qualification or automaton view; kept apart from the sidebar
   * selection, which only the sidebar, Clear filters and leaving the page change
   */
  readonly openModel = signal<string | null>(null);
  /** the model page shown: the open one, else a sidebar selection of exactly one model */
  readonly singleModel = computed(() => this.openModel() ?? (this.modelSel().size === 1 ? [...this.modelSel()][0] : null));
  readonly isFullscreen = signal(false);
  /** model to open once the chosen game's summary has loaded (from the overall leaderboard) */
  private readonly pendingModel = signal<{ model: string; gameKey: string } | null>(null);
  /** where each opened model/automaton page came from, for its Back button; `opened` names the page it led to */
  private readonly backStack = signal<BackEntry[]>([]);
  readonly indexModelIds = computed(() => new Set((this.index()?.models ?? []).map((model) => model.id)));
  private readonly viewportHeight = signal(window.innerHeight);
  private readonly viewportWidth = signal(window.innerWidth);

  private summaryToken = 0;
  private tableToken = 0;
  private detailToken = 0;
  /** match to reopen once its table has loaded (from the URL) */
  private readonly pendingRowIndex = signal<number | null>(null);
  private hashReady = false;

  // ---- derived ------------------------------------------------------------------------
  readonly stageKey = computed<Stage>(() => (this.stage() === 'quals' ? 'quals' : 'tourney'));
  readonly game = computed<HistoryIndexGame | null>(() => {
    const key = this.gameKey();
    return key ? this.index()?.games.find((g) => g.id === key) ?? null : null;
  });
  readonly stageSummary = computed<StageSummary | null>(() => this.summary()?.stages[this.stageKey()] ?? null);

  readonly view = computed<View>(() => {
    if (!this.gameKey()) {
      return this.profile() ? 'model' : 'overview';
    }
    if (!this.botA()) {
      return 'game';
    }
    return this.botB() ? 'pair' : 'bot';
  });

  /** the open game, if it has a board to play on */
  readonly playable = computed(() => {
    const game = this.game();
    return game && GAME_GUI_IDS.includes(game.game) ? game : null;
  });

  readonly sortedGames = computed(() => [...(this.index()?.games ?? [])].sort((a, b) => a.label.localeCompare(b.label)));
  readonly pickerGames = computed<GamePickerOption[]>(() =>
    this.sortedGames().map((g) => ({ id: g.id, gameId: g.game, worldId: g.world, label: g.label }))
  );

  /** bot -> family, for every bot known in this game (tourney + quals) */
  readonly familyByBot = computed<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    const summary = this.summary();
    const index = this.index();
    const familyByModel = new Map<string, string>();
    for (const model of index?.models ?? []) {
      familyByModel.set(model.id, model.family);
    }
    if (summary) {
      for (const [bot, row] of Object.entries(summary.bots)) {
        out[bot] = row.family;
      }
      for (const stage of Object.values(summary.stages)) {
        for (const bot of stage?.bots ?? []) {
          if (!out[bot]) {
            out[bot] = familyByModel.get(modelOf(bot)) ?? 'Other';
          }
        }
      }
    }
    return out;
  });

  /** bots that reached the tournament, shown only while viewing the qualification */
  readonly qualifiedBots = computed<Set<string> | null>(() => {
    const summary = this.summary();
    if (!summary || this.stage() !== 'quals') {
      return null;
    }
    const out = new Set(summary.stages.tourney?.qualified ?? []);
    for (const rows of Object.values(summary.stages.quals?.rankings ?? {})) {
      for (const row of rows) {
        if (row.qualified) {
          out.add(row.bot);
        }
      }
    }
    return out;
  });

  /** rank inside the current stage view (tourney rank, model rank, or quals rank within the model) */
  readonly rankByBot = computed<Record<string, number>>(() => {
    const out: Record<string, number> = {};
    const summary = this.summary();
    if (!summary) {
      return out;
    }
    if (this.stage() === 'quals') {
      for (const rows of Object.values(summary.stages.quals?.rankings ?? {})) {
        for (const row of rows) {
          out[row.bot] = row.rank;
        }
      }
      return out;
    }
    if (this.stage() === 'models') {
      for (const row of Object.values(summary.models)) {
        if (row.top_bot) {
          out[row.top_bot] = row.rank;
        }
      }
      return out;
    }
    for (const [bot, row] of Object.entries(summary.bots)) {
      out[bot] = row.rank;
    }
    return out;
  });

  readonly topBots = computed<Set<string>>(() => {
    const set = new Set<string>();
    for (const row of Object.values(this.summary()?.models ?? {})) {
      if (row.top_bot) {
        set.add(row.top_bot);
      }
    }
    return set;
  });

  /** display labels: bots in tourney/quals, model names in the models view */
  readonly labels = computed<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    const summary = this.summary();
    if (!summary) {
      return out;
    }
    const useModel = this.stage() === 'models';
    for (const bot of Object.keys(this.familyByBot())) {
      out[bot] = useModel && this.topBots().has(bot) ? modelOf(bot) : botLabel(bot);
    }
    return out;
  });

  /** "#n" labels for views scoped to a single model (qualification cards) */
  readonly shortLabels = computed<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    for (const bot of Object.keys(this.familyByBot())) {
      out[bot] = botShortLabel(bot);
    }
    return out;
  });

  readonly allRows = computed<MatchRow[]>(() => {
    const table = this.table();
    return table ? this.history.decodeRows(table) : [];
  });

  /** rows visible in the current stage view (models view = tourney rows between top bots) */
  readonly stageRows = computed<MatchRow[]>(() => {
    const rows = this.allRows();
    if (this.stage() !== 'models') {
      return rows;
    }
    const top = this.topBots();
    return rows.filter((row) => top.has(row.a) && top.has(row.b));
  });

  /**
   * Records counted from the matches the current view shows. In the model view that is only
   * model-vs-model games (each model's top automaton), so a model's row and its page agree.
   */
  readonly viewRecords = computed<Record<string, BotRecord>>(() => {
    const out: Record<string, BotRecord & { moves: number; movesN: number; secs: number; secsN: number }> = {};
    const add = (bot: string, res: MatchRow['resA'], row: MatchRow) => {
      const r = (out[bot] ??= { n: 0, win: 0, loss: 0, draw: 0, error: 0, enemy_error: 0, timeout: 0, enemy_timeout: 0, unknown: 0, avg_moves: 0, avg_secs: 0, moves: 0, movesN: 0, secs: 0, secsN: 0 });
      r.n += 1;
      if (res === 'win') r.win += 1;
      else if (res === 'loss') r.loss += 1;
      else if (res === 'draw') r.draw += 1;
      else if (res === 'error') r.error += 1;
      else if (res === 'enemy_error') r.enemy_error += 1;
      else if (res === 'timeout') r.timeout += 1;
      else if (res === 'enemy_timeout') r.enemy_timeout += 1;
      else r.unknown += 1;
      if (row.moveCount !== null) {
        r.moves += row.moveCount;
        r.movesN += 1;
      }
      if (row.secs !== null) {
        r.secs += row.secs;
        r.secsN += 1;
      }
    };
    for (const row of this.stageRows()) {
      add(row.a, row.resA, row);
      add(row.b, row.resB, row);
    }
    const records: Record<string, BotRecord> = {};
    for (const [bot, r] of Object.entries(out)) {
      const { moves, movesN, secs, secsN, ...rest } = r;
      records[bot] = {
        ...rest,
        avg_moves: movesN ? Math.round((moves / movesN) * 10) / 10 : 0,
        avg_secs: secsN ? Math.round((secs / secsN) * 100) / 100 : 0
      };
    }
    return records;
  });

  private matchesFilter(_label: string, model: string, _family: string): boolean {
    const open = this.openModel();
    if (open) {
      return model === open;
    }
    const models = this.modelSel();
    return models.size === 0 || models.has(model);
  }

  /** family -> its models, from the sidebar tree */
  private readonly familyModels = computed(
    () => new Map(this.familyTree().map((f) => [f.id, f.models.map((m) => m.id)] as const))
  );
  /** families shown as picked: every one of their models is selected */
  readonly familySel = computed<ReadonlySet<string>>(() => {
    const models = this.modelSel();
    const out = new Set<string>();
    for (const [family, ids] of this.familyModels()) {
      if (ids.length > 0 && ids.every((id) => models.has(id))) {
        out.add(family);
      }
    }
    return out;
  });

  /** replace the sidebar selection; families stand for all of their models */
  private setSelection(families: string[], models: string[]): void {
    const tree = this.familyModels();
    this.modelSel.set(new Set([...models, ...families.flatMap((f) => tree.get(f) ?? [])]));
  }

  readonly leaderboardRows = computed<LeaderboardRow[]>(() => {
    const summary = this.summary();
    const stageSummary = this.stageSummary();
    if (!summary || !stageSummary) {
      return [];
    }
    const rows: LeaderboardRow[] = [];
    if (this.stage() === 'models') {
      for (const [model, row] of Object.entries(summary.models)) {
        if (!this.matchesFilter(model, model, row.family)) {
          continue;
        }
        rows.push({
          id: row.top_bot ?? model,
          label: model,
          sub: row.top_bot ? botShortLabel(row.top_bot) : null,
          family: row.family,
          rating: row.rating,
          q025: row.q025,
          q975: row.q975,
          rank: row.rank,
          n: row.n,
          record: row.top_bot ? this.viewRecords()[row.top_bot] ?? null : null,
          qualified: null,
          dnq: false
        });
      }
      return rows;
    }
    if (this.stage() === 'quals') {
      const qualified = new Set(summary.stages.tourney?.qualified ?? []);
      for (const [model, rankings] of Object.entries(stageSummary.rankings ?? {})) {
        const family = this.familyByBot()[rankings[0]?.bot ?? ''] ?? 'Other';
        for (const r of rankings) {
          if (!this.matchesFilter(botLabel(r.bot), model, family)) {
            continue;
          }
          rows.push({
            id: r.bot,
            label: botLabel(r.bot),
            sub: null,
            family,
            rating: r.rating,
            q025: r.q025,
            q975: r.q975,
            rank: r.rank,
            n: r.n,
            record: stageSummary.records[r.bot] ?? null,
            qualified: r.qualified || qualified.has(r.bot),
            dnq: false
          });
        }
      }
      return rows;
    }
    for (const [bot, row] of Object.entries(summary.bots)) {
      if (!this.matchesFilter(botLabel(bot), row.model, row.family)) {
        continue;
      }
      rows.push({
        id: bot,
        label: botLabel(bot),
        sub: null,
        family: row.family,
        rating: row.rating,
        q025: row.q025,
        q975: row.q975,
        rank: row.rank,
        n: row.n,
        record: stageSummary.records[bot] ?? null,
        qualified: true,
        dnq: false
      });
    }
    // bots that played the qualification but did not reach the tournament
    const inTourney = new Set(Object.keys(summary.bots));
    for (const [model, rankings] of Object.entries(summary.stages.quals?.rankings ?? {})) {
      for (const r of rankings) {
        if (inTourney.has(r.bot)) {
          continue;
        }
        const family = this.familyByBot()[r.bot] ?? 'Other';
        if (!this.matchesFilter(botLabel(r.bot), model, family)) {
          continue;
        }
        rows.push({
          id: r.bot,
          label: botLabel(r.bot),
          sub: null,
          family,
          rating: null,
          q025: null,
          q975: null,
          rank: 0,
          n: 0,
          record: null,
          qualified: false,
          dnq: true
        });
      }
    }
    return rows;
  });

  readonly heatmapBots = computed<string[]>(() => {
    const ranks = this.rankByBot();
    return this.leaderboardRows()
      .filter((row) => !row.dnq)
      .map((row) => row.id)
      .sort((a, b) => (ranks[a] ?? 1e9) - (ranks[b] ?? 1e9) || a.localeCompare(b));
  });

  /** in full screen, cells fill the screen; large grids keep readable 16px cells and scroll */
  readonly fullscreenCell = computed(() => {
    if (!this.isFullscreen()) {
      return null;
    }
    const n = Math.max(1, this.heatmapBots().length);
    const fitHeight = (this.viewportHeight() - 220) / n;
    const fitWidth = (this.viewportWidth() - 320) / n;
    return Math.max(16, Math.min(44, Math.floor(Math.min(fitHeight, fitWidth))));
  });

  readonly qualsCards = computed<QualsCard[]>(() => {
    const stageSummary = this.summary()?.stages.quals;
    if (!stageSummary?.rankings) {
      return [];
    }
    const cards: QualsCard[] = [];
    for (const [model, rankings] of Object.entries(stageSummary.rankings)) {
      if (model === 'random') {
        continue; // the random baseline has no siblings to qualify against
      }
      const family = this.familyByBot()[rankings[0]?.bot ?? ''] ?? 'Other';
      if (!this.matchesFilter(model, model, family)) {
        continue;
      }
      cards.push({
        model,
        family,
        bots: rankings.map((r) => r.bot),
        rankings,
        qualifiedCount: rankings.filter((r) => r.qualified).length
      });
    }
    cards.sort((a, b) => a.family.localeCompare(b.family) || a.model.localeCompare(b.model));
    return cards;
  });

  readonly familyTree = computed(() => {
    const index = this.index();
    if (!index) {
      return [];
    }
    // per-game counts: the index unions bot ids across games, so a model can list more bots than any one game has
    const botsByModel = this.automataByModel();
    return index.families.map((family) => ({
      id: family.id,
      color: familyColor(family.id),
      models: family.models.map((model) => ({ id: model, bots: botsByModel.get(model)?.size ?? null }))
    }));
  });

  readonly hasFilter = computed(() => this.modelSel().size > 0 || this.botA() !== null || this.openModel() !== null);

  /** the model being looked at in a game (its automaton, or the list filtered to it), for the link to its page */
  readonly contextModel = computed(() => {
    const bot = this.botA();
    return bot ? modelOf(bot) : this.singleModel();
  });

  /** every automaton of each model (qualified or not), from the qualification rankings plus the tournament */
  private readonly automataByModel = computed(() => {
    const summary = this.summary();
    const out = new Map<string, Set<string>>();
    const add = (bot: string) => {
      const model = modelOf(bot);
      const set = out.get(model) ?? new Set<string>();
      set.add(bot);
      out.set(model, set);
    };
    for (const rows of Object.values(summary?.stages.quals?.rankings ?? {})) {
      rows.forEach((r) => add(r.bot));
    }
    (summary?.stages.tourney?.bots ?? []).forEach(add);
    return out;
  });

  /** counts for the stat strip; when a family/model filter is active they cover only the visible bots */
  readonly stats = computed(() => {
    const game = this.game();
    const summary = this.summary();
    const stageSummary = this.stageSummary();
    const rows = this.leaderboardRows();
    const filtered = this.hasFilter();
    if (!filtered || !summary) {
      return {
        matches: stageSummary?.n_matches ?? game?.stages[this.stageKey()]?.matches ?? 0,
        bots: [...this.automataByModel().values()].reduce((n, set) => n + set.size, 0) || (stageSummary?.bots.length ?? 0),
        models: Object.keys(summary?.models ?? {}).length || game?.models || 0,
        qualified: summary?.stages.tourney?.qualified?.length ?? game?.qualified ?? 0,
        filtered
      };
    }
    const visible = new Set(rows.filter((row) => !row.dnq).map((row) => row.id));
    const models = new Set(rows.map((row) => (this.stage() === 'models' ? row.label : modelOf(row.id))));
    const tourneyQualified = new Set(summary.stages.tourney?.qualified ?? []);
    const qualified = [...models].reduce(
      (n, model) => n + [...(this.automataByModel().get(model) ?? [])].filter((bot) => tourneyQualified.has(bot)).length,
      0
    );
    const table = this.table();
    const matches = table
      ? this.stageRows().filter((row) => visible.has(row.a) || visible.has(row.b)).length
      : null;
    return {
      matches,
      bots: [...models].reduce((n, model) => n + (this.automataByModel().get(model)?.size ?? 0), 0),
      models: models.size,
      qualified,
      filtered
    };
  });

  /** the model whose page is showing, marked in the sidebar (apart from the filter's checkboxes) */
  readonly currentModel = computed<string | null>(() => {
    if (!this.gameKey()) {
      return this.profile();
    }
    const bot = this.botA();
    return bot ? modelOf(bot) : this.singleModel();
  });
  readonly modelCount = computed(() => this.familyTree().reduce((sum, family) => sum + family.models.length, 0));
  /** the one sidebar family open (by its chevron or name); opening it never touches the filter */
  readonly openFamily = signal<string | null>(null);
  private readonly familyOfModel = computed(
    () => new Map(this.familyTree().flatMap((f) => f.models.map((m) => [m.id, f.id] as const)))
  );
  /** families with only some of their models checked */
  readonly familyPartial = computed<ReadonlySet<string>>(() => {
    const out = new Set<string>();
    for (const model of this.modelSel()) {
      const family = this.familyOfModel().get(model);
      if (family && !this.familySel().has(family)) {
        out.add(family);
      }
    }
    return out;
  });

  readonly botAInfo = computed(() => this.botInfo(this.botA()));
  /** selected bot played qualification but is not part of the stage being viewed */
  readonly isBotADnq = computed(() => {
    const bot = this.botA();
    const summary = this.summary();
    if (!bot || !summary || this.stage() === 'quals') {
      return false;
    }
    return !(bot in summary.bots);
  });
  readonly botBInfo = computed(() => this.botInfo(this.botB()));
  /** rating axis of the CI bars: every model (model view) or automaton (automaton view) of this game, ignoring filters */
  readonly ciScale = computed<{ lo: number; hi: number } | null>(() => {
    const summary = this.summary();
    if (!summary) {
      return null;
    }
    const rows = this.stage() === 'models' ? Object.values(summary.models) : Object.values(summary.bots);
    let lo = Number.POSITIVE_INFINITY;
    let hi = Number.NEGATIVE_INFINITY;
    for (const row of rows) {
      const a = row.q025 ?? row.rating;
      const b = row.q975 ?? row.rating;
      if (a !== null && a !== undefined) {
        lo = Math.min(lo, a);
      }
      if (b !== null && b !== undefined) {
        hi = Math.max(hi, b);
      }
    }
    return Number.isFinite(lo) && Number.isFinite(hi) && hi > lo ? { lo, hi } : null;
  });

  /**
   * Rating axis of one qualification card. Each model's qualification is rated as its own pool,
   * so the axis spans that model's automata only (padded 10% each side) and is not shared.
   */
  private readonly qualsScales = computed(() => {
    const out = new Map<string, { lo: number; hi: number }>();
    for (const [model, rows] of Object.entries(this.summary()?.stages.quals?.rankings ?? {})) {
      let lo = Number.POSITIVE_INFINITY;
      let hi = Number.NEGATIVE_INFINITY;
      for (const r of rows) {
        lo = Math.min(lo, r.q025 ?? r.rating ?? lo);
        hi = Math.max(hi, r.q975 ?? r.rating ?? hi);
      }
      const pad = Math.max(10, (hi - lo) * 0.1);
      out.set(model, Number.isFinite(lo) && Number.isFinite(hi) ? { lo: lo - pad, hi: hi + pad } : { lo: 0, hi: 1 });
    }
    return out;
  });

  qualsCiStyle(r: QualsRanking): Record<string, string> {
    const { lo, hi } = this.qualsScales().get(modelOf(r.bot)) ?? { lo: 0, hi: 1 };
    const at = (v: number | null) => `${(((v ?? lo) - lo) / (hi - lo)) * 100}%`;
    const left = r.q025 ?? r.rating;
    const right = r.q975 ?? r.rating;
    return {
      '--ci-left': at(left),
      '--ci-width': `${Math.max(0.5, (((right ?? lo) - (left ?? lo)) / (hi - lo)) * 100)}%`,
      '--ci-point': at(r.rating)
    };
  }

  /** win/draw/loss bar; wins and losses decided by a fault are their own (hatched) segments */
  qualsScoreStyle(rec: BotRecord): Record<string, string> {
    const n = rec.n || 1;
    const pct = (count: number) => `${(count / n) * 100}%`;
    return {
      '--win': pct(rec.win),
      '--win-fault': pct(rec.enemy_error + rec.enemy_timeout),
      '--draw': pct(rec.draw),
      '--loss-fault': pct(rec.error + rec.timeout),
      '--loss': pct(rec.loss)
    };
  }

  qualsScorePct(rec: BotRecord): number {
    const n = rec.n || 1;
    return Math.round(((rec.win + rec.enemy_error + rec.enemy_timeout + rec.draw / 2) / n) * 100);
  }

  /** the open automaton's (or model's) leaderboard row, shown at the top of its tournament page */
  readonly botARow = computed<LeaderboardRow | null>(() => {
    const bot = this.botA();
    if (!bot || this.stage() === 'quals') {
      return null;
    }
    const row = this.leaderboardRows().find((r) => r.id === bot);
    return row && !row.dnq ? row : null;
  });

  readonly crumbs = computed(() => {
    const out: { label: string; action: () => void }[] = [{ label: 'Leaderboard', action: () => this.selectGame(null) }];
    const game = this.game();
    if (!game && this.profile()) {
      out.push({ label: this.profile()!, action: () => undefined });
    }
    if (game) {
      const clearView = () => {
        this.selectBot(null);
        this.openModel.set(null);
      };
      // game: its default page (tournament, by model); stage: the whole list of the current stage
      out.push({ label: game.label, action: () => (this.setStage('models'), clearView()) });
      out.push({ label: this.stage() === 'quals' ? 'Qualification' : 'Tournament', action: clearView });
    }
    const a = this.botA();
    if (a && this.stage() !== 'models') {
      // an automaton sits under its model: Leaderboard > game > model > #n
      const model = modelOf(a);
      out.push({ label: model, action: () => this.showModel(model) });
      out.push({ label: botShortLabel(a), action: () => this.selectOpponent(null) });
    } else if (a) {
      out.push({ label: this.labels()[a] ?? botLabel(a), action: () => this.selectOpponent(null) });
    } else if (this.stage() !== 'models' && this.singleModel()) {
      // the list filtered to one model is that model's page
      out.push({ label: this.singleModel()!, action: () => undefined });
    }
    const b = this.botB();
    if (b) {
      out.push({ label: `vs ${this.labels()[b] ?? botLabel(b)}`, action: () => this.closeMatch() });
    }
    return out;
  });

  constructor() {
    const onFullscreenChange = () => {
      this.isFullscreen.set(Boolean(document.fullscreenElement?.classList.contains('mv-h2h')));
      onResize();
    };
    const onResize = () => {
      this.viewportHeight.set(window.innerHeight);
      this.viewportWidth.set(window.innerWidth);
    };
    document.addEventListener('fullscreenchange', onFullscreenChange);
    window.addEventListener('resize', onResize);
    inject(DestroyRef).onDestroy(() => {
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      window.removeEventListener('resize', onResize);
    });
    // the header's Leaderboard button, clicked while already here, returns to the overview
    const onNavHome = (event: Event) => {
      if ((event as CustomEvent<string>).detail === 'matches') {
        this.selectGame(null);
      }
    };
    window.addEventListener(NAV_HOME_EVENT, onNavHome);
    inject(DestroyRef).onDestroy(() => window.removeEventListener(NAV_HOME_EVENT, onNavHome));
    // browser back/forward within the match viewer: show the view in the URL
    const onPopState = () => {
      if (getHashRouteState().path === '/matches') {
        this.backStack.set([]);
        this.pendingModel.set(null);
        const table = `${this.gameKey()}/${this.stageKey()}`;
        this.applyHash();
        // same game and stage: the loaded table has the match; otherwise the new table reopens it
        if (table === `${this.gameKey()}/${this.stageKey()}`) {
          this.openPendingRow();
        }
      }
    };
    window.addEventListener('popstate', onPopState);
    inject(DestroyRef).onDestroy(() => window.removeEventListener('popstate', onPopState));
    effect(() => {
      const pending = this.pendingModel();
      const summary = this.summary();
      if (!pending || !summary || `${summary.game}_${summary.world}` !== pending.gameKey) {
        return;
      }
      untracked(() => {
        this.pendingModel.set(null);
        const topBot = summary.models[pending.model]?.top_bot;
        if (topBot) {
          this.selectBot(topBot);
        } else {
          // no tournament rating for it in this game: its row alone on the model leaderboard
          this.openModel.set(pending.model);
        }
      });
    });
    effect(() => {
      const key = this.gameKey();
      untracked(() => void this.loadSummaryFor(key));
    });
    effect(() => {
      const key = this.gameKey();
      const stage = this.stageKey();
      untracked(() => void this.loadTableFor(key, stage));
    });
    effect(() => {
      const row = this.openRow();
      const key = this.gameKey();
      const stage = this.stageKey();
      untracked(() => void this.loadDetailFor(key, stage, row));
    });
    effect(() => {
      // the sidebar opens the family of the model being viewed
      const family = this.familyOfModel().get(this.currentModel() ?? '');
      if (family) {
        untracked(() => this.openFamily.set(family));
      }
    });
    effect(() => {
      // keep the URL in sync so every view is linkable
      const params = new URLSearchParams();
      const key = this.gameKey();
      if (key) {
        params.set('game', key);
      } else if (this.profile()) {
        params.set('profile', this.profile()!);
      }
      params.set('stage', this.stage());
      if (this.botA()) {
        params.set('bot', this.botA()!);
      }
      if (this.botB()) {
        params.set('vs', this.botB()!);
      }
      const row = this.openRow();
      if (row) {
        params.set('m', String(row.index));
      }
      if (this.openModel()) {
        params.set('open', this.openModel()!);
      }
      // every view gets its own history entry so the browser's Back returns to the one before; views
      // still settling (a model opening in a game, a match reopening from the URL) wait until they land
      if (untracked(() => this.hashReady) && !this.pendingModel() && this.pendingRowIndex() === null) {
        setHashRouteState('/matches', params, true);
      }
    });
  }

  ngOnInit(): void {
    if (getHashRouteState().path === '/matches') {
      this.applyHash();
    }
    this.hashReady = true;
    this.history.warmRuntime();
    this.history
      .loadIndex()
      .then((index) => this.index.set(index))
      .catch((err) => this.indexError.set(err instanceof Error ? err.message : String(err)));
  }

  /** the view named by the URL */
  private applyHash(): void {
    const { params } = getHashRouteState();
    const stage = params.get('stage');
    this.stage.set(stage === 'quals' || stage === 'tourney' ? stage : 'models');
    const game = params.get('game');
    this.gameKey.set(game);
    this.profile.set(game ? null : params.get('profile'));
    const bot = params.get('bot');
    const vs = bot ? params.get('vs') : null;
    this.botA.set(bot);
    this.botB.set(vs);
    this.openRow.set(null);
    const m = vs ? Number(params.get('m') ?? NaN) : NaN;
    this.pendingRowIndex.set(Number.isFinite(m) ? m : null);
    this.openModel.set(params.get('open'));
  }

  private botInfo(bot: string | null) {
    if (!bot) {
      return null;
    }
    const summary = this.summary();
    const family = this.familyByBot()[bot] ?? 'Other';
    const model = modelOf(bot);
    const tourney = summary?.bots[bot] ?? null;
    const siblings = summary?.stages.quals?.rankings?.[model] ?? [];
    const quals = siblings.find((r) => r.bot === bot) ?? null;
    const record = (this.stage() === 'models' ? this.viewRecords()[bot] : this.stageSummary()?.records[bot]) ?? null;
    // in the model view the page is the model's: show the model's rank and rating, not its top automaton's
    const rating = this.stage() === 'models' ? summary?.models[model] ?? tourney : tourney;
    return { id: bot, label: this.labels()[bot] ?? botLabel(bot), model, family, tourney, rating, quals, qualsOf: siblings.length, record };
  }

  // ---- loaders ------------------------------------------------------------------------
  private async loadSummaryFor(key: string | null): Promise<void> {
    const token = ++this.summaryToken;
    this.summary.set(null);
    if (!key) {
      return;
    }
    this.summaryLoading.set(true);
    this.loadError.set(null);
    try {
      const summary = await this.history.loadSummary(key);
      if (token === this.summaryToken) {
        this.summary.set(summary);
      }
    } catch (err) {
      if (token === this.summaryToken) {
        this.loadError.set(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (token === this.summaryToken) {
        this.summaryLoading.set(false);
      }
    }
  }

  private openPendingRow(): void {
    const index = this.pendingRowIndex();
    const table = this.table();
    if (index === null || !table) {
      return;
    }
    const row = this.history.decodeRows(table)[index] ?? null;
    this.pendingRowIndex.set(null);
    if (row && ((row.a === this.botA() && row.b === this.botB()) || (row.b === this.botA() && row.a === this.botB()))) {
      this.openRow.set(row);
    }
  }

  private async loadTableFor(key: string | null, stage: Stage): Promise<void> {
    const token = ++this.tableToken;
    this.table.set(null);
    if (!key) {
      return;
    }
    this.tableLoading.set(true);
    try {
      const table = await this.history.loadMatches(key, stage);
      if (token !== this.tableToken) {
        return;
      }
      this.table.set(table);
      this.openPendingRow();
    } catch (err) {
      if (token === this.tableToken) {
        this.loadError.set(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (token === this.tableToken) {
        this.tableLoading.set(false);
      }
    }
  }

  private async loadDetailFor(key: string | null, stage: Stage, row: MatchRow | null): Promise<void> {
    const token = ++this.detailToken;
    this.detail.set(null);
    if (!key || !row) {
      return;
    }
    this.detailLoading.set(true);
    try {
      const detail = await this.history.loadDetail(key, stage, row);
      if (token === this.detailToken) {
        this.detail.set(detail);
        if (!detail) {
          this.loadError.set('No move list was exported for this match.');
        }
      }
    } catch (err) {
      if (token === this.detailToken) {
        this.loadError.set(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (token === this.detailToken) {
        this.detailLoading.set(false);
      }
    }
  }

  // ---- actions ------------------------------------------------------------------------
  playGame(game: HistoryIndexGame): void {
    setHashRouteState('/arena', new URLSearchParams({ game: game.game, sub: game.world }));
    this.store.dispatch(arenaActions.selectEntry({ entryId: 'ga' }));
  }

  selectGame(key: string | null): void {
    this.backStack.set([]);
    this.pendingModel.set(null);
    this.profile.set(null);
    if (key === this.gameKey()) {
      return;
    }
    this.gameKey.set(key);
    this.openModel.set(null);
    this.botA.set(null);
    this.botB.set(null);
    this.openRow.set(null);
    this.loadError.set(null);
  }

  readonly isTournament = computed(() => this.stage() !== 'quals');

  setPrimaryStage(primary: 'tourney' | 'quals'): void {
    if (primary === 'quals') {
      this.setStage('quals');
      return;
    }
    if (!this.isTournament()) {
      // an open automaton keeps its own games; the model view only has each model's top automaton
      // (a model selected in qualification opens as that model's tournament page, see setStage)
      this.setStage(this.botA() ? 'tourney' : 'models');
    }
  }

  /** with a model or automaton open, back to where it was opened from */
  backToList(): void {
    const a = this.botA();
    if (a && this.popBack(`bot:${a}`)) {
      return;
    }
    this.selectBot(null);
  }

  /** a model's page in the qualification or automaton view */
  openModelPage(model: string): void {
    this.pushBack(`model:${model}`);
    this.selectBot(null);
    this.openModel.set(model);
  }

  backFromModel(): void {
    if (this.popBack(`model:${this.singleModel()}`)) {
      return;
    }
    this.selectBot(null);
    if (this.openModel()) {
      this.openModel.set(null);
    } else {
      // the page came from picking just this model in the sidebar
      this.setSelection([], []);
    }
  }

  private pushBack(opened: string): void {
    const entry = { opened, stage: this.stage(), botA: this.botA(), openModel: this.openModel() };
    this.backStack.set([...this.backStack(), entry]);
  }

  /** restore the view that opened `opened`, if that is what the top of the stack led to */
  private popBack(opened: string): boolean {
    const stack = this.backStack();
    const top = stack.at(-1);
    if (top?.leaveTo) {
      // the game was opened from outside it: Back returns there, whatever the game showed first
      const leaveTo = top.leaveTo;
      if (leaveTo.profile) {
        this.openProfile(leaveTo.profile);
      } else {
        this.selectGame(null);
      }
      return true;
    }
    if (!top || top.opened !== opened) {
      return false;
    }
    this.backStack.set(stack.slice(0, -1));
    this.stage.set(top.stage);
    this.selectBot(top.botA);
    this.openModel.set(top.openModel);
    return true;
  }

  private showModel(model: string): void {
    this.selectBot(null);
    this.openModel.set(model);
  }

  /** Switching stage keeps the open automaton (or pair) so its tournament and qualification views can be compared. */
  setStage(stage: ViewStage): void {
    if (stage === this.stage()) {
      return;
    }
    const from = this.stage();
    this.stage.set(stage);
    this.openRow.set(null);
    if (from === 'models' && stage !== 'models' && this.botA()) {
      // a model's page stays that model's page, not one picked automaton
      const bot = this.botA()!;
      this.selectBot(null);
      this.openModel.set(modelOf(bot));
      return;
    }
    if (stage === 'models') {
      // the model view only has each model's top automaton: show that one for the open model
      const swap = (bot: string | null) => (bot ? this.summary()?.models[modelOf(bot)]?.top_bot ?? null : null);
      const a = this.botA();
      const model = this.singleModel();
      if (!a && model) {
        // a model's page opens as that model's page here, its top automaton
        const topBot = this.summary()?.models[model]?.top_bot ?? null;
        if (topBot) {
          this.selectBot(topBot);
          this.openModel.set(null);
        }
      } else if (a && !this.topBots().has(a)) {
        this.botA.set(swap(a));
        this.botB.set(null);
      } else if (this.botB() && !this.topBots().has(this.botB()!)) {
        this.botB.set(swap(this.botB()));
      }
    }
  }

  selectBot(bot: string | null): void {
    this.botA.set(bot);
    this.botB.set(null);
    this.openRow.set(null);
  }

  viewQualification(bot: string): void {
    this.stage.set('quals');
    this.botA.set(bot);
    this.botB.set(null);
    this.openRow.set(null);
  }

  selectOpponent(bot: string | null): void {
    if (bot && bot === this.botA()) {
      return;
    }
    this.botB.set(bot);
    this.openRow.set(null);
  }

  /** Heatmap "View replays": the matches between two automata (leaves full screen first). */
  openPair({ row, col }: { row: string; col: string }): void {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    }
    this.botA.set(row);
    this.botB.set(col);
    this.openRow.set(null);
  }

  swapPair(): void {
    const a = this.botA();
    const b = this.botB();
    if (a && b) {
      this.botA.set(b);
      this.botB.set(a);
      this.openRow.set(null);
    }
  }

  openMatch(row: MatchRow): void {
    this.openRow.set(row);
  }

  closeMatch(): void {
    this.openRow.set(null);
  }

  /** Sidebar chevron or family name: open or close its list of models. */
  toggleFamilyOpen(family: string): void {
    this.openFamily.set(this.openFamily() === family ? null : family);
  }

  /** Sidebar model name: its page (across every game, or in the open game); the filter stays. */
  goToModel(model: string): void {
    const gameKey = this.gameKey();
    if (!gameKey) {
      this.openProfile(model);
      return;
    }
    this.backStack.set([]);
    this.selectBot(null);
    if (this.stage() === 'models') {
      // the model view's page of a model is its top automaton, known once the summary is in
      this.openModel.set(null);
      this.pendingModel.set({ model, gameKey });
    } else {
      this.openModel.set(model);
    }
    window.scrollTo({ top: 0 });
  }

  /** a filter change shows the filtered list: an open model or automaton page closes */
  private leaveForList(): void {
    // outside a game the filter narrows the overall leaderboard, so that is where it leads
    this.profile.set(null);
    this.openModel.set(null);
    this.backStack.set([]);
    this.selectBot(null);
  }

  /** A family's or model's checkbox: in or out of the filter (a family goes in whole unless it already is). */
  toggleFamilyInSelection(family: string, event: Event): void {
    event.stopPropagation();
    this.leaveForList();
    const models = this.familyModels().get(family) ?? [];
    const next = new Set(this.modelSel());
    const remove = this.familySel().has(family);
    for (const model of models) {
      if (remove) {
        next.delete(model);
      } else {
        next.add(model);
      }
    }
    this.modelSel.set(next);
  }

  toggleModelInSelection(model: string, event: Event): void {
    event.stopPropagation();
    this.leaveForList();
    const next = new Set(this.modelSel());
    if (next.has(model)) {
      next.delete(model);
    } else {
      next.add(model);
    }
    this.modelSel.set(next);
  }

  /** A model's page across every game. */
  openProfile(model: string): void {
    this.selectGame(null);
    this.profile.set(model);
    window.scrollTo({ top: 0 });
  }

  /** Model page -> one of its automata in one game: its tournament page, or its qualification if it did not qualify. */
  openProfileBot({ gameId, bot, qualified }: { gameId: string; bot: string; qualified: boolean }): void {
    const profile = this.profile();
    this.selectGame(gameId);
    this.leaveGameTo(profile);
    this.setSelection([], []);
    this.stage.set(qualified ? 'tourney' : 'quals');
    this.selectBot(bot);
    window.scrollTo({ top: 0 });
  }

  /**
   * A model's automata list -> one automaton: its tournament page, or its qualification if it did
   * not qualify or the list was opened from the qualification view.
   */
  openAutomaton({ bot, qualified }: { bot: string; qualified: boolean }): void {
    this.pushBack(`bot:${bot}`);
    this.stage.set(qualified && this.stage() !== 'quals' ? 'tourney' : 'quals');
    this.selectBot(bot);
    // its model's page is where it returns to without the back stack (after a reload)
    this.openModel.set(modelOf(bot));
    window.scrollTo({ top: 0 });
  }

  /** Overall leaderboard -> a model in one game: that game's Model view with the model opened. */
  openModelInGame({ model, gameId }: { model: string; gameId: string }): void {
    const profile = this.profile();
    this.selectGame(gameId);
    this.leaveGameTo(profile);
    this.setStage('models');
    this.pendingModel.set({ model, gameKey: gameId });
  }

  /** Back from the game just opened returns to this model's page, or the overall leaderboard */
  private leaveGameTo(profile: string | null): void {
    this.backStack.set([{ opened: '', stage: this.stage(), botA: null, openModel: null, leaveTo: { profile } }]);
  }

  toggleFullscreen(element: HTMLElement): void {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void element.requestFullscreen();
    }
  }

  /** back to the whole list: the selection goes, and so does an opened model or automaton */
  clearFilters(): void {
    this.openFamily.set(null);
    // outside a game the selection filters the overall leaderboard, so that is where it leads
    this.profile.set(null);
    this.openModel.set(null);
    this.backStack.set([]);
    this.selectBot(null);
    this.setSelection([], []);
  }

  detailLabelA(): string {
    const d = this.detail();
    return d ? this.labels()[d.a] ?? botLabel(d.a) : '';
  }

  detailLabelB(): string {
    const d = this.detail();
    return d ? this.labels()[d.b] ?? botLabel(d.b) : '';
  }

  trackGame(_i: number, game: HistoryIndexGame): string {
    return game.id;
  }
}
