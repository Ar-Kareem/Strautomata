import { createActionGroup, createReducer, emptyProps, on, props } from '@ngrx/store';
import { DEFAULT_ENTRYPOINTS } from './arena.constants';
import type {
  BotOption,
  EloByColumn,
  EntrypointOption,
  GameWorldOption,
  MatchResultSummary,
  StatusTone,
} from './arena.constants';
import { buildBotOptions } from './arena.utils';

export type MatchupMode = 'ai-vs-ai' | 'human-vs-ai' | 'human-vs-human';

export type ArenaSelectionState = {
  entryId: string | null;
  id: string | null;  // gameId/worldId
  gameId: string | null;
  worldId: string | null;
  botAId: string | null;
  botBId: string | null;
  /** null until the player picks how to play; no match runs before that */
  matchup: MatchupMode | null;
};

export type ArenaCatalogState = {
  entrypoints: EntrypointOption[];
  games: GameWorldOption[];
  bots: BotOption[];
  eloByColumn: EloByColumn | null;
};

export type ArenaStatusState = {
  tone: StatusTone;
  message: string;
};

export type ArenaOpenSpielState = {
  tone: StatusTone;
  message: string;
  errorLines: string[];
};

export type ArenaBotStrategyState = {
  text: string | null;
  loading: boolean;
  error: string | null;
};

export type MatchState = {
  isPlaying: boolean;
  stepInFlight: boolean;
  matchReady: boolean;
  outputLines: string[];
  matchObservation: unknown | null;
  moveSpeed: number;
  maxMoveSpeed: number;
  awaitingHumanMove: boolean;
  legalMoves: string[];
  scoreboard: { games: number; botAWins: number; botBWins: number; draws: number };
  activeBotAId: string | null;
  activeBotBId: string | null;
  illegalAction: string | null;
  lastMatchResult: MatchResultSummary | null;
  botsStatus: 'loading' | 'ready' | 'none';
};

export type CorewarLeaveAction = 'reset-entry' | 'reset-match';

export type CorewarLeaveRequest = {
  id: number;
  action: CorewarLeaveAction | null;
};

export type CorewarViewSettings = {
  inspectorViewSize: number;
  detailedScoreboard: boolean;
  showIcons: boolean;
  showLastModifiedColor: boolean;
  maxColumns: number;
  cellSize: number;
  makeNonDatWhite: boolean;
  makeWarriorDatWhite: boolean;
};

type CorewarGridState = {
  cols: number;
  rows: number;
};

export type CorewarState = {
  matchInProgress: boolean;
  leaveRequest: CorewarLeaveRequest;
  viewSettings: CorewarViewSettings;
  grid: CorewarGridState;
  configDialogOpen: boolean;
};

export interface ArenaState {
  selection: ArenaSelectionState;
  catalog: ArenaCatalogState;
  status: ArenaStatusState;
  openSpiel: ArenaOpenSpielState;
  botStrategies: Record<'a' | 'b', ArenaBotStrategyState>;
  match: MatchState;
  heroTheme: 'default' | 'corewar';
  corewar: CorewarState;
}

const initialMatchState: MatchState = {
  isPlaying: false,
  stepInFlight: false,
  matchReady: false,
  outputLines: [],
  matchObservation: null,
  moveSpeed: 2,
  maxMoveSpeed: 20,
  awaitingHumanMove: false,
  legalMoves: [],
  scoreboard: { games: 0, botAWins: 0, botBWins: 0, draws: 0 },
  activeBotAId: null,
  activeBotBId: null,
  illegalAction: null,
  lastMatchResult: null,
  botsStatus: 'none'
};

export const initialArenaState: ArenaState = {
  selection: {
    entryId: null,
    id: null,
    gameId: null,
    worldId: null,
    botAId: null,
    botBId: null,
    matchup: null
  },
  catalog: {
    entrypoints: DEFAULT_ENTRYPOINTS,
    games: [],
    bots: buildBotOptions([], false),
    eloByColumn: null
  },
  status: {
    tone: 'idle',
    message: 'Pyodide idle'
  },
  openSpiel: {
    tone: 'idle',
    message: 'OpenSpiel idle',
    errorLines: []
  },
  botStrategies: {
    a: { text: null, loading: false, error: null },
    b: { text: null, loading: false, error: null }
  },
  match: initialMatchState,
  heroTheme: 'default',
  corewar: {
    matchInProgress: false,
    leaveRequest: { id: 0, action: null },
    viewSettings: {
      inspectorViewSize: 1,
      detailedScoreboard: false,
      showIcons: false,
      showLastModifiedColor: false,
      maxColumns: 100,
      cellSize: 12,
      makeNonDatWhite: false,
      makeWarriorDatWhite: false
    },
    grid: {
      cols: 100,
      rows: 0
    },
    configDialogOpen: false,
  }
};

export const arenaActions = createActionGroup({
  source: 'Arena',
  events: {
    'Init Requested': emptyProps(),
    'Select Entry': props<{ entryId: string }>(),
    'Reset Entry': emptyProps(),
    'Game Change Requested': props<{ id: string; gameId: string | null; worldId: string | null }>(),
    'Matchup Change Requested': props<{ mode: MatchupMode }>(),
    'Bot Change Requested': props<{ slot: 'a' | 'b'; botId: string | null }>(),
    'Random Bot Requested': props<{ slot: 'a' | 'b' }>(),
    'Toggle Play Requested': emptyProps(),
    'Step Requested': emptyProps(),
    'Restart Series Requested': emptyProps(),
    'Speed Change Requested': props<{ speed: number }>(),
    'Human Move Submitted': props<{ action: string; forceApply?: boolean }>(),
    'Patch State': props<Partial<ArenaState>>(),
    'Reset Scoreboard': emptyProps(),
    'Update Scoreboard': props<{ delta: { games: number; botAWins: number; botBWins: number; draws: number } }>(),
    'Update Match Speed': props<{ speed: number }>(),
    'Update Is Playing': props<{ isPlaying: boolean }>(),
    'Update Step In Flight': props<{ stepInFlight: boolean }>(),
    'Update Match Ready': props<{ matchReady: boolean }>(),
    'Update Output Lines': props<{ outputLines: string[] }>(),
    'Update Match Observation': props<{ matchObservation: unknown | null }>(),
    'Update Awaiting Human Move': props<{ awaitingHumanMove: boolean }>(),
    'Update Legal Moves': props<{ legalMoves: string[] }>(),
    'Update Active Bot A Id': props<{ activeBotAId: string | null }>(),
    'Update Active Bot B Id': props<{ activeBotBId: string | null }>(),
    'Update Illegal Action': props<{ illegalAction: string | null }>(),
    'Update Last Match Result': props<{ lastMatchResult: MatchResultSummary | null }>(),
    'Update Hero Theme': props<{ theme: 'default' | 'corewar' }>(),
    'Update Corewar Match In Progress': props<{ inProgress: boolean }>(),
    'Update Corewar View Settings': props<{ patch: Partial<CorewarViewSettings> }>(),
    'Update Corewar Grid': props<{ grid: CorewarGridState }>(),
    'Update Corewar Config Dialog Open': props<{ open: boolean }>(),
    'Reset Corewar View Settings': emptyProps(),
    'Request Corewar Leave': props<{ action: CorewarLeaveAction }>(),
    'Clear Corewar Leave Request': emptyProps(),

    'Bots Load Successful': emptyProps(),
    'Bots Load Loading': emptyProps(),
    'Bots Load Failed': emptyProps(),
  }
});

export const arenaReducer = createReducer(
  initialArenaState,
  on(arenaActions.patchState, (state, patch) => ({ ...state, ...patch })),
  on(arenaActions.resetEntry, (state) => ({
    ...state,
    heroTheme: 'default',
    match: {
      ...state.match,
      botsStatus: 'none'
    },
    corewar: {
      ...state.corewar,
      matchInProgress: false,
      leaveRequest: { ...state.corewar.leaveRequest, action: null },
      configDialogOpen: false
    }
  })),
  on(arenaActions.resetScoreboard, (state) => ({...state, match: {...state.match,
      scoreboard: { games: 0, botAWins: 0, botBWins: 0, draws: 0 }
    }
  })),
  on(arenaActions.updateScoreboard, (state, { delta }) => ({...state, match: {...state.match,
      scoreboard: {
        games: state.match.scoreboard.games + delta.games,
        botAWins: state.match.scoreboard.botAWins + delta.botAWins,
        botBWins: state.match.scoreboard.botBWins + delta.botBWins,
        draws: state.match.scoreboard.draws + delta.draws
      }
    }
  })),
  on(arenaActions.updateMatchSpeed, (state, { speed }) => ({...state, match: { ...state.match, moveSpeed: speed }})),
  on(arenaActions.updateIsPlaying, (state, { isPlaying }) => ({...state, match: { ...state.match, isPlaying }})),
  on(arenaActions.updateStepInFlight, (state, { stepInFlight }) => ({...state, match: { ...state.match, stepInFlight }})),
  on(arenaActions.updateMatchReady, (state, { matchReady }) => ({...state, match: { ...state.match, matchReady }})),
  on(arenaActions.updateOutputLines, (state, { outputLines }) => ({...state, match: { ...state.match, outputLines }})),
  on(arenaActions.updateMatchObservation, (state, { matchObservation }) => ({...state, match: { ...state.match, matchObservation }})),
  on(arenaActions.updateAwaitingHumanMove, (state, { awaitingHumanMove }) => ({...state, match: { ...state.match, awaitingHumanMove }})),
  on(arenaActions.updateLegalMoves, (state, { legalMoves }) => ({...state, match: { ...state.match, legalMoves }})),
  on(arenaActions.updateActiveBotAId, (state, { activeBotAId }) => ({...state, match: { ...state.match, activeBotAId }})),
  on(arenaActions.updateActiveBotBId, (state, { activeBotBId }) => ({...state, match: { ...state.match, activeBotBId }})),
  on(arenaActions.updateIllegalAction, (state, { illegalAction }) => ({...state, match: { ...state.match, illegalAction }})),
  on(arenaActions.updateLastMatchResult, (state, { lastMatchResult }) => ({...state, match: { ...state.match, lastMatchResult }})),
  on(arenaActions.updateHeroTheme, (state, { theme }) => ({ ...state, heroTheme: theme })),
  on(arenaActions.updateCorewarMatchInProgress, (state, { inProgress }) => ({
    ...state,
    corewar: { ...state.corewar, matchInProgress: inProgress }
  })),
  on(arenaActions.updateCorewarViewSettings, (state, { patch }) => ({
    ...state,
    corewar: {
      ...state.corewar,
      viewSettings: {
        ...state.corewar.viewSettings,
        ...patch
      }
    }
  })),
  on(arenaActions.updateCorewarGrid, (state, { grid }) => ({
    ...state,
    corewar: {
      ...state.corewar,
      grid
    }
  })),
  on(arenaActions.updateCorewarConfigDialogOpen, (state, { open }) => ({
    ...state,
    corewar: {
      ...state.corewar,
      configDialogOpen: open
    }
  })),
  on(arenaActions.resetCorewarViewSettings, (state) => ({
    ...state,
    corewar: {
      ...state.corewar,
      viewSettings: {
        ...initialArenaState.corewar.viewSettings
      }
    }
  })),
  on(arenaActions.requestCorewarLeave, (state, { action }) => ({
    ...state,
    corewar: {
      ...state.corewar,
      leaveRequest: {
        id: state.corewar.leaveRequest.id + 1,
        action
      }
    }
  })),
  on(arenaActions.clearCorewarLeaveRequest, (state) => ({
    ...state,
    corewar: {
      ...state.corewar,
      leaveRequest: {
        ...state.corewar.leaveRequest,
        action: null
      }
    }
  })),

  on(arenaActions.botsLoadSuccessful, (state) => ({...state, match: { ...state.match, botsStatus: 'ready' }})),
  on(arenaActions.botsLoadLoading, (state) => ({...state, match: { ...state.match, botsStatus: 'loading' }})),
  on(arenaActions.botsLoadFailed, (state) => ({...state, match: { ...state.match, botsStatus: 'none' }})),
);
