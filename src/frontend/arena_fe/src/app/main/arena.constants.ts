export type StatusTone = 'idle' | 'loading' | 'ready' | 'error';

export interface EntrypointOption {
  id: string;
  label: string;
  summary: string;
  available: boolean;
}

export interface GameWorldOption {
  id: string;
  gameId: string;
  worldId: string;
  config: string | null;
  label: string;
  description: string;
  hasGui: boolean;
}

export interface BotOption {
  id: string;
  label: string;
  blurb: string;
}

export interface MatchPayload {
  logs?: string[];
  done?: boolean;
  final?: { winner?: number | null; done?: boolean };
  error?: string;
  illegal?: boolean;
  illegal_bot?: string;
  illegal_action?: string;
  awaiting_input?: boolean;
  legal_moves?: string[];
  invalid_move?: string;
  state_player?: {
    state: unknown;
    player: number | null;
  };
}

export interface MatchResultSummary {
  winner: number | null;
  illegal: boolean;
  finishedAt: number;
}

export type EloByColumn = Record<string, Record<string, number>>;

export interface PyodideRuntime {  // standard pyodide runtime interface. not defined by me.
  globals: {
    set: (name: string, value: unknown) => void;
    get: (name: string) => unknown;
  };
  toPy: (value: unknown) => unknown;
  runPythonAsync: (code: string) => Promise<unknown>;
  loadPackage: (packages: string[]) => Promise<void>;
  /** loads the Pyodide packages a piece of code imports (e.g. scipy), if not loaded yet */
  loadPackagesFromImports: (code: string) => Promise<unknown>;
  runPython: (code: string) => void;
  FS: {
    mkdir: (path: string) => void;
    writeFile: (path: string, data: string) => void;
  };
}

export const GAME_GUI_IDS = [
  'amazons',
  'backgammon',
  'battleships',
  'breakthrough',
  'chess',
  'clobber',
  'connect4',
  'dots_and_boxes',
  'go',
  'havannah',
  'hex',
  'lines_of_action',
  'checkers',
  'mancala',
  'nim',
  'othello',
  'pentago',
  'tic_tac_toe',
  'tic_tac_toe_3d'
];

export const DEFAULT_GAME_ID = 'connect4/world1';

export const GAME_WORLD_LABELS: Record<string, Record<string, string>> = {
  amazons: {world1: 'Amazons'},
  backgammon: {world1: 'Backgammon'},
  battleships: {world1: 'Battleships'},
  // blackjack: {world1: 'Blackjack'},
  breakthrough: {world1: 'Breakthrough'},
  checkers: {world1: 'Checkers'},
  connect4: {world1: 'Connect 4'},
  chess: {worlduci1: 'Chess'},
  clobber: {world1: 'Clobber'},
  dots_and_boxes: {world1: 'Dots and Boxes'},
  go: {world1: 'Go'},
  havannah: {world1: 'Havannah'},
  hex: {world1: 'Hex'},
  lines_of_action: {world1: 'Lines of Action'},
  mancala: {world1: 'Mancala'},
  nim: {world1: 'Nim'},
  othello: {world1: 'Othello'},
  pentago: {world1: 'Pentago'},
  // poker: {world1: 'Poker'},
  tic_tac_toe_3d: {world1: 'Tic Tac Toe 3D'},
  // phantom_ttt: {
  //   world1: 'Phantom TTT (1)',
  //   world2: 'Phantom TTT (2)'
  // },
  tic_tac_toe: {
    world1: 'Tic Tac Toe (3x3)',
    world2: 'Tic Tac Toe (4x4)'
  }
};

export const GAME_DESCRIPTIONS: Record<string, string> = {
  tic_tac_toe_3d: '3 Dimensional Board, hard to visualize.',
  battleships: 'Ships are placed randomly on the board (not chosen by the player).',
};

export const OPEN_SPIEL_ARCHIVE = 'py/open_spiel-1.6.9-cp312-cp312-pyodide_2024_0_wasm32.whl';

export const DEFAULT_ENTRYPOINTS: EntrypointOption[] = [
  {
    id: 'ga',
    label: 'Game Arena',
    summary: 'Watch automata play each other in-browser, or set up any lineup.',
    available: true
  },
  // {
  //   id: 'corewars',
  //   label: 'Core Wars',
  //   summary: 'Small assembly-like programs (“warriors”) battle in a simulated computer memory.',
  //   available: false
  // },
  {
    id: 'matches',
    label: 'Match Viewer',
    summary: 'Browse every recorded match: qualification rounds, the tournament, and turn-by-turn replays.',
    available: true
  },
  {
    id: 'create',
    label: 'Create your own Automata',
    summary: 'Write a policy for a game, get a live Elo.',
    available: true
  },
  {
    id: 'paper',
    label: 'Paper',
    summary: 'The Strautomata paper.',
    available: true
  },
  {
    id: 'team',
    label: 'Team',
    summary: 'The people behind Strautomata.',
    available: true
  },
  // {
  //   id: 'sim',
  //   label: 'Lorem ipsum',
  //   summary: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
  //   available: false
  // }
];
