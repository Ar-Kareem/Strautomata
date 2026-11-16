import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';
import { kbdSquare } from '../../components/arena-gui-helpers/arena-kbd-keys';

type ChessPiece = {
  color: 'w' | 'b';
  type: 'K' | 'Q' | 'R' | 'B' | 'N' | 'P';
};

type ChessCell = {
  key: string;
  row: number;
  col: number;
  square: string;
  isDark: boolean;
  piece: ChessPiece | null;
  legalFrom: boolean;
  legalTo: boolean;
  lastMove: boolean;
};

@Component({
  selector: 'arena-chess-gui',
  standalone: true,
  templateUrl: './arena-chess-gui.component.html',
  styleUrl: './arena-chess-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaChessGuiComponent implements OnDestroy {
  readonly boardSize = 8;
  cells: ChessCell[] = [];
  whiteCount = 0;
  blackCount = 0;
  currentPlayer: number | null = null;
  toPlay: 'white' | 'black' | null = null;
  matchBannerMessage: string | null = null;

  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    if (!value) {
      this.selectedFromSquare = null;
    } else {
      this.suppressLegalHighlights = false;
    }
    this.cells = this.buildCells(this.pieces);
    this.cdr.markForCheck();
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }
  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    if (this.awaitingHumanMove) {
      this.suppressLegalHighlights = false;
    }
    this.rebuildMoveMaps();
  }
  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }
  @Input() submitHumanMove?: (move: string) => void;
  @Input() illegalAction: string | null = null;

  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchFinished = false;
  private currentLegalMoves: string[] = [];
  private movesByKey = new Map<string, string>();
  private fromSquares = new Set<string>();
  private pieces: Record<string, string> = {};
  private suppressLegalHighlights = false;
  private lastMoveSquares = new Set<string>();
  private pawnDirByColor: Record<'w' | 'b', number> = { w: 1, b: -1 };
  private pawnDirLocked = false;
  private playerColorByIndex: Record<0 | 1, 'white' | 'black' | null> = {
    0: null,
    1: null
  };
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  selectedFromSquare: string | null = null;

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.clearBanner();
      this.matchFinished = false;
      this.lastMoveSquares = new Set<string>();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
    if (value.illegal) {
      this.clearBanner();
      this.matchFinished = false;
      this.cells = this.buildCells(this.pieces);
      this.cdr.markForCheck();
      return;
    }
    this.matchFinished = true;
    this.matchBannerMessage = this.resolveResultMessage(value.winner);
    this.resetBannerTimer();
    this.cells = this.buildCells(this.pieces);
    this.cdr.markForCheck();
  }

  @Input() set observation(value: unknown | null) {
    const parsed = this.parseObservation(value);
    if (!parsed) {
      this.cells = [];
      this.whiteCount = 0;
      this.blackCount = 0;
      this.currentPlayer = null;
      this.toPlay = null;
      this.pieces = {};
      this.lastMoveSquares = new Set<string>();
      this.rebuildMoveMaps();
      return;
    }
    const moveSquares = this.resolveLastMoveSquares(this.pieces, parsed.pieces);
    if (moveSquares.size > 0) {
      this.lastMoveSquares = moveSquares;
    }
    this.currentPlayer = parsed.player;
    this.toPlay = parsed.toPlay;
    this.updatePlayerColorMapping(parsed.player, parsed.toPlay);
    this.pieces = parsed.pieces;
    this.inferPawnDirections(this.pieces);
    this.cells = this.buildCells(this.pieces);
    const counts = this.countPieces(this.pieces);
    this.whiteCount = counts.white;
    this.blackCount = counts.black;
    this.rebuildMoveMaps();
  }

  cellLabel(cell: ChessCell): string {
    if (!cell.piece) {
      return `${cell.square}: empty`;
    }
    const names = { K: 'king', Q: 'queen', R: 'rook', B: 'bishop', N: 'knight', P: 'pawn' };
    return `${cell.square}: ${cell.piece.color === 'w' ? 'white' : 'black'} ${names[cell.piece.type]}`;
  }

  /** keyboard hint: movable pieces, then the selected piece's destinations */
  kbdLabel(cell: ChessCell): string | null {
    const target = this.selectedFromSquare ? cell.legalTo : cell.legalFrom;
    return target ? kbdSquare(cell.col, cell.row, this.boardSize) : null;
  }

  onCellClick(cell: ChessCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const square = cell.square;
    if (!this.selectedFromSquare) {
      if (!this.fromSquares.has(square)) {
        this.showIllegalClick('Select a movable piece.');
        return;
      }
      this.selectedFromSquare = square;
      this.cells = this.buildCells(this.pieces);
      this.cdr.markForCheck();
      return;
    }
    if (this.selectedFromSquare === square) {
      this.selectedFromSquare = null;
      this.cells = this.buildCells(this.pieces);
      this.cdr.markForCheck();
      return;
    }
    if (this.fromSquares.has(square)) {
      this.selectedFromSquare = square;
      this.cells = this.buildCells(this.pieces);
      this.cdr.markForCheck();
      return;
    }
    const fromSquare = this.selectedFromSquare;
    this.selectedFromSquare = null;
    this.cells = this.buildCells(this.pieces);
    this.cdr.markForCheck();
    const move = this.movesByKey.get(`${fromSquare}|${square}`);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.suppressLegalHighlights = true;
    this.cells = this.buildCells(this.pieces);
    this.cdr.markForCheck();
    this.submitHumanMove(move);
  }


  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(
    value: unknown | null
  ): {
    pieces: Record<string, string>;
    toPlay: 'white' | 'black' | null;
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as {
      pieces?: unknown;
      to_play?: unknown;
      turn?: unknown;
    };
    if (!record || typeof record !== 'object') {
      return null;
    }
    const pieces = record.pieces as Record<string, string>;
    if (!pieces || typeof pieces !== 'object') {
      return null;
    }
    const toPlay =
      record.to_play === 'white' || record.to_play === 'black' ? record.to_play : null;
    const player =
      typeof record.turn === 'number'
        ? record.turn
        : statePlayer.player === 0 || statePlayer.player === 1
          ? statePlayer.player
          : null;
    return { pieces, toPlay, player };
  }

  private buildCells(pieces: Record<string, string>): ChessCell[] {
    const cells: ChessCell[] = [];
    const allowLegal = this.awaitingHumanMove && !this.suppressLegalHighlights;
    const legalTargets =
      this.selectedFromSquare && allowLegal
        ? this.collectLegalTargets(this.selectedFromSquare)
        : new Set<string>();
    const showLastMove = this.matchFinished ? this.lastMoveSquares : new Set<string>();
    for (let row = this.boardSize - 1; row >= 0; row -= 1) {
      for (let col = 0; col < this.boardSize; col += 1) {
        const square = this.coordToSquare(row, col);
        const piece = this.parsePiece(pieces[square]);
        const isDark = (row + col) % 2 === 1;
        cells.push({
          key: `${row},${col}`,
          row,
          col,
          square,
          isDark,
          piece,
          legalFrom: allowLegal && this.fromSquares.has(square),
          legalTo: allowLegal && legalTargets.has(square),
          lastMove: showLastMove.has(square)
        });
      }
    }
    return cells;
  }

  private resolveLastMoveSquares(
    previous: Record<string, string>,
    next: Record<string, string>
  ): Set<string> {
    const changed = new Set<string>();
    for (const key of Object.keys(next)) {
      if (previous[key] !== next[key]) {
        changed.add(key);
      }
    }
    return changed;
  }

  private parsePiece(code: string | undefined): ChessPiece | null {
    if (!code || typeof code !== 'string' || code.length < 2) {
      return null;
    }
    const color = code[0] as ChessPiece['color'];
    const type = code[1] as ChessPiece['type'];
    if ((color !== 'w' && color !== 'b') || !'KQRBNP'.includes(type)) {
      return null;
    }
    return { color, type };
  }

  private countPieces(pieces: Record<string, string>): { white: number; black: number } {
    let white = 0;
    let black = 0;
    for (const code of Object.values(pieces)) {
      if (typeof code !== 'string' || code.length < 2) {
        continue;
      }
      if (code[0] === 'w') {
        white += 1;
      } else if (code[0] === 'b') {
        black += 1;
      }
    }
    return { white, black };
  }

  private coordToSquare(row: number, col: number): string {
    const file = String.fromCharCode(97 + col);
    return `${file}${row + 1}`;
  }

  private rebuildMoveMaps(): void {
    this.movesByKey.clear();
    this.fromSquares.clear();
    this.selectedFromSquare = null;
    if (this.currentLegalMoves.length === 0) {
      this.cells = this.buildCells(this.pieces);
      return;
    }
    const buildForSide = (side: 'white' | 'black') => {
      const movesByKey = new Map<string, string>();
      const fromSquares = new Set<string>();
      let count = 0;
      for (const move of this.currentLegalMoves) {
        const pairs = this.resolveMovePairs(move, this.pieces, side);
        count += pairs.length;
        for (const pair of pairs) {
          const key = `${pair.from}|${pair.to}`;
          const existing = movesByKey.get(key);
          if (!existing || this.isPreferredPromotion(move, existing)) {
            movesByKey.set(key, move);
          }
          fromSquares.add(pair.from);
        }
      }
      return { count, movesByKey, fromSquares };
    };

    if (!this.toPlay) {
      const whiteResult = buildForSide('white');
      const blackResult = buildForSide('black');
      const useWhite = whiteResult.count >= blackResult.count;
      const chosen = useWhite ? whiteResult : blackResult;
      this.movesByKey = chosen.movesByKey;
      this.fromSquares = chosen.fromSquares;
      this.toPlay = useWhite ? 'white' : 'black';
      this.updatePlayerColorMapping(this.currentPlayer, this.toPlay);
      this.cells = this.buildCells(this.pieces);
      return;
    }

    const primary = buildForSide(this.toPlay);
    if (primary.count > 0) {
      this.movesByKey = primary.movesByKey;
      this.fromSquares = primary.fromSquares;
      this.cells = this.buildCells(this.pieces);
      return;
    }
    const fallbackSide = this.toPlay === 'white' ? 'black' : 'white';
    const fallback = buildForSide(fallbackSide);
    if (fallback.count > 0) {
      this.movesByKey = fallback.movesByKey;
      this.fromSquares = fallback.fromSquares;
      this.toPlay = fallbackSide;
      this.updatePlayerColorMapping(this.currentPlayer, this.toPlay);
      this.cells = this.buildCells(this.pieces);
    }
  }

  private collectLegalTargets(fromSquare: string): Set<string> {
    const targets = new Set<string>();
    if (!this.toPlay) {
      return targets;
    }
    for (const move of this.currentLegalMoves) {
      const pairs = this.resolveMovePairs(move, this.pieces, this.toPlay);
      for (const pair of pairs) {
        if (pair.from === fromSquare) {
          targets.add(pair.to);
        }
      }
    }
    return targets;
  }

  private isPreferredPromotion(candidate: string, existing: string): boolean {
    if (existing.includes('=Q')) {
      return false;
    }
    return candidate.includes('=Q');
  }

  private resolveMovePairs(
    move: string,
    pieces: Record<string, string>,
    toPlay: 'white' | 'black'
  ): Array<{ from: string; to: string }> {
    const uci = this.parseMoveKeys(move);
    if (uci) {
      return [uci];
    }
    const parsed = this.parseSan(move);
    if (!parsed) {
      return [];
    }
    if (parsed.castle) {
      const colorChar = toPlay === 'white' ? 'w' : 'b';
      const kingSquare = this.findPieceSquare(pieces, `${colorChar}K`);
      const kingCoord = kingSquare ? this.squareToCoord(kingSquare) : null;
      if (!kingSquare || !kingCoord) {
        return [];
      }
      const fileShift = parsed.castle === 'O-O' ? 2 : -2;
      const toFile = kingCoord.file + fileShift;
      if (toFile < 0 || toFile > 7) {
        return [];
      }
      const to = `${String.fromCharCode(97 + toFile)}${kingCoord.rank}`;
      return [{ from: kingSquare, to }];
    }
    const colorChar = toPlay === 'white' ? 'w' : 'b';
    const destCoord = this.squareToCoord(parsed.dest);
    if (!destCoord) {
      return [];
    }
    const results: Array<{ from: string; to: string }> = [];
    for (const [square, code] of Object.entries(pieces)) {
      if (code !== `${colorChar}${parsed.piece}`) {
        continue;
      }
      if (parsed.fromFile && square[0] !== parsed.fromFile) {
        continue;
      }
      if (parsed.fromRank && Number(square[1]) !== parsed.fromRank) {
        continue;
      }
      const fromCoord = this.squareToCoord(square);
      if (!fromCoord) {
        continue;
      }
      if (this.canPieceReach(parsed, fromCoord, destCoord, pieces, colorChar)) {
        results.push({ from: square, to: parsed.dest });
      }
    }
    return results;
  }

  private parseSan(move: string): {
    castle?: 'O-O' | 'O-O-O';
    piece: ChessPiece['type'];
    dest: string;
    capture: boolean;
    fromFile?: string;
    fromRank?: number;
  } | null {
    let normalized = String(move ?? '').trim();
    if (!normalized) {
      return null;
    }
    normalized = normalized.replace(/0-0-0/gi, 'O-O-O').replace(/0-0/gi, 'O-O');
    normalized = normalized.replace(/^OOO/i, 'O-O-O').replace(/^OO/i, 'O-O');
    normalized = normalized.replace(/[+#?!]+$/g, '');
    normalized = normalized.replace(/\s*e\.p\.$/i, '').replace(/\s*ep$/i, '');
    if (normalized.startsWith('O-O-O')) {
      return { castle: 'O-O-O', piece: 'K', dest: '', capture: false };
    }
    if (normalized.startsWith('O-O')) {
      return { castle: 'O-O', piece: 'K', dest: '', capture: false };
    }
    const promotionMatch = normalized.match(/=([QRBN])/i);
    if (promotionMatch) {
      normalized = normalized.replace(/=([QRBN])/i, '');
    }
    const destMatch = normalized.match(/([a-h][1-8])$/i);
    if (!destMatch) {
      return null;
    }
    const dest = destMatch[1].toLowerCase();
    const pieceLetter = normalized[0];
    const isPiece = 'KQRBN'.includes(pieceLetter);
    const piece = (isPiece ? pieceLetter : 'P') as ChessPiece['type'];
    const capture = normalized.includes('x');
    let core = normalized.slice(isPiece ? 1 : 0, normalized.length - 2);
    core = core.replace('x', '');
    let fromFile: string | undefined;
    let fromRank: number | undefined;
    if (piece === 'P') {
      if (capture && core.length >= 1) {
        fromFile = core[0].toLowerCase();
      }
    } else if (core.length > 0) {
      const fileMatch = core.match(/[a-h]/i);
      const rankMatch = core.match(/[1-8]/);
      if (fileMatch) {
        fromFile = fileMatch[0].toLowerCase();
      }
      if (rankMatch) {
        fromRank = Number(rankMatch[0]);
      }
    }
    return { piece, dest, capture, fromFile, fromRank };
  }

  private squareToCoord(square: string): { file: number; rank: number } | null {
    if (!square || square.length < 2) {
      return null;
    }
    const file = square.charCodeAt(0) - 97;
    const rank = Number(square[1]);
    if (!Number.isFinite(rank) || file < 0 || file > 7 || rank < 1 || rank > 8) {
      return null;
    }
    return { file, rank };
  }

  private findPieceSquare(pieces: Record<string, string>, code: string): string | null {
    for (const [square, piece] of Object.entries(pieces)) {
      if (piece === code) {
        return square;
      }
    }
    return null;
  }

  private inferPawnDirections(pieces: Record<string, string>): void {
    if (this.pawnDirLocked) {
      return;
    }
    const whiteKing = this.findPieceSquare(pieces, 'wK');
    const blackKing = this.findPieceSquare(pieces, 'bK');
    if (!whiteKing || !blackKing) {
      return;
    }
    const whiteRank = Number(whiteKing[1]);
    if (!Number.isFinite(whiteRank)) {
      return;
    }
    this.pawnDirByColor.w = whiteRank >= 5 ? -1 : 1;
    this.pawnDirByColor.b = -this.pawnDirByColor.w;
    this.pawnDirLocked = true;
  }

  private canPieceReach(
    parsed: { piece: ChessPiece['type']; capture: boolean },
    from: { file: number; rank: number },
    to: { file: number; rank: number },
    pieces: Record<string, string>,
    colorChar: 'w' | 'b'
  ): boolean {
    const dx = to.file - from.file;
    const dy = to.rank - from.rank;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);
    const destSquare = `${String.fromCharCode(97 + to.file)}${to.rank}`;
    const destPiece = pieces[destSquare];
    const destOccupiedBySelf = destPiece?.startsWith(colorChar);
    const destOccupied = Boolean(destPiece);

    if (destOccupiedBySelf) {
      return false;
    }
    if (!parsed.capture && destOccupied) {
      return false;
    }
    if (parsed.capture && parsed.piece !== 'P' && !destOccupied) {
      return false;
    }

    switch (parsed.piece) {
      case 'P': {
        const dir = this.pawnDirByColor[colorChar] ?? (colorChar === 'w' ? 1 : -1);
        const startRank = dir === 1 ? 2 : 7;
        if (parsed.capture) {
          return absDx === 1 && dy === dir;
        }
        if (dx === 0 && dy === dir) {
          return true;
        }
        if (dx === 0 && dy === 2 * dir && from.rank === startRank) {
          const midRank = from.rank + dir;
          const midSquare = `${String.fromCharCode(97 + from.file)}${midRank}`;
          return !pieces[midSquare];
        }
        return false;
      }
      case 'N':
        return (absDx === 1 && absDy === 2) || (absDx === 2 && absDy === 1);
      case 'B':
        return absDx === absDy && this.isPathClear(from, to, pieces);
      case 'R':
        return (dx === 0 || dy === 0) && this.isPathClear(from, to, pieces);
      case 'Q':
        return ((absDx === absDy) || dx === 0 || dy === 0) && this.isPathClear(from, to, pieces);
      case 'K':
        return Math.max(absDx, absDy) === 1;
      default:
        return false;
    }
  }

  private isPathClear(
    from: { file: number; rank: number },
    to: { file: number; rank: number },
    pieces: Record<string, string>
  ): boolean {
    const stepFile = Math.sign(to.file - from.file);
    const stepRank = Math.sign(to.rank - from.rank);
    let file = from.file + stepFile;
    let rank = from.rank + stepRank;
    while (file !== to.file || rank !== to.rank) {
      const square = `${String.fromCharCode(97 + file)}${rank}`;
      if (pieces[square]) {
        return false;
      }
      file += stepFile;
      rank += stepRank;
    }
    return true;
  }

  private parseMoveKeys(value: string): { from: string; to: string } | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const match = trimmed.match(/^([a-h][1-8])([a-h][1-8])/i);
    if (!match) {
      return null;
    }
    return { from: match[1].toLowerCase(), to: match[2].toLowerCase() };
  }

  private showIllegalClick(message: string): void {
    this.illegalClickMessage = message;
    this.illegalClickToken += 1;
    this.cdr.markForCheck();
  }

  private resolveResultMessage(winner: number | null): string {
    if (winner === 0) {
      return `${this.botA} won`;
    }
    if (winner === 1) {
      return `${this.botB} won`;
    }
    return 'Draw';
  }

  private updatePlayerColorMapping(
    playerIndex: number | null,
    toPlay: 'white' | 'black' | null
  ): void {
    if (playerIndex !== 0 && playerIndex !== 1) {
      return;
    }
    if (!toPlay) {
      return;
    }
    this.playerColorByIndex[playerIndex] = toPlay;
    this.playerColorByIndex[playerIndex === 0 ? 1 : 0] = toPlay === 'white' ? 'black' : 'white';
  }

  private resetBannerTimer(): void {
    this.clearBannerTimer();
    this.bannerTimer = window.setTimeout(() => {
      this.matchBannerMessage = null;
      this.cdr.markForCheck();
    }, 3000);
  }

  private clearBanner(): void {
    this.clearBannerTimer();
    this.matchBannerMessage = null;
  }

  private clearBannerTimer(): void {
    if (this.bannerTimer !== null) {
      window.clearTimeout(this.bannerTimer);
      this.bannerTimer = null;
    }
  }
}
