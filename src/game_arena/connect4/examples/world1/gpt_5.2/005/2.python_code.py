
# connect4_policy.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

ROWS = 6
COLS = 7

# Bitboard layout (classic Connect4 solver layout):
# - Each column uses 7 bits (6 playable rows + 1 sentinel).
# - Bit index = col*7 + row, where row=0 is the bottom playable cell.
# - Sentinel row at row=6 is unused for pieces, but helps move generation.
STRIDE = 7  # bits per column

BOTTOM_MASK = [1 << (c * STRIDE) for c in range(COLS)]
TOP_MASK = [1 << (c * STRIDE + (ROWS - 1)) for c in range(COLS)]
COLUMN_MASK = [((1 << ROWS) - 1) << (c * STRIDE) for c in range(COLS)]
FULL_MASK = 0
for cm in COLUMN_MASK:
    FULL_MASK |= cm

MOVE_ORDER = [3, 4, 2, 5, 1, 6, 0]  # center-first ordering

MATE = 1_000_000
# Heuristic weights by how many of our discs are in a 4-cell window (with no opponent discs).
WINDOW_WEIGHTS = [0, 1, 10, 60, 10_000]  # 4 is handled by terminal detection; keep large anyway.

# Precompute all 4-in-a-row window masks (on playable cells only, excluding sentinel bits).
WINDOW_MASKS: List[int] = []


def _bit(col: int, row: int) -> int:
    """row: 0=bottom .. 5=top"""
    return 1 << (col * STRIDE + row)


def _precompute_windows() -> None:
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            m = _bit(c, r) | _bit(c + 1, r) | _bit(c + 2, r) | _bit(c + 3, r)
            WINDOW_MASKS.append(m)
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            m = _bit(c, r) | _bit(c, r + 1) | _bit(c, r + 2) | _bit(c, r + 3)
            WINDOW_MASKS.append(m)
    # Diagonal up-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            m = _bit(c, r) | _bit(c + 1, r + 1) | _bit(c + 2, r + 2) | _bit(c + 3, r + 3)
            WINDOW_MASKS.append(m)
    # Diagonal up-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            m = _bit(c, r) | _bit(c - 1, r + 1) | _bit(c - 2, r + 2) | _bit(c - 3, r + 3)
            WINDOW_MASKS.append(m)


_precompute_windows()


def board_to_bitboards(board: List[List[int]]) -> Tuple[int, int]:
    """
    Convert 6x7 board (rows 0..5 top->bottom) to (current, mask) bitboards.
    'current' contains bits for player=1 (the caller), 'mask' contains all occupied bits.
    """
    cur = 0
    mask = 0
    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            if v == 0:
                continue
            # Convert input row index (0 top..5 bottom) to bitboard row (0 bottom..5 top)
            br = (ROWS - 1) - r
            b = 1 << (c * STRIDE + br)
            mask |= b
            if v == 1:
                cur |= b
    return cur, mask


def is_win(bb: int) -> bool:
    """Check if bitboard bb contains a 4-in-a-row."""
    # Directions in bitboard indexing:
    # vertical: 1, horizontal: 7, diag1: 6, diag2: 8
    for d in (1, STRIDE, STRIDE - 1, STRIDE + 1):
        m = bb & (bb >> d)
        if (m & (m >> (2 * d))) != 0:
            return True
    return False


def move_bit(mask: int, col: int) -> int:
    """Return the bit corresponding to the next disc dropped in column col, or 0 if full."""
    if (mask & TOP_MASK[col]) != 0:
        return 0
    # Classic move generation:
    # Add bottom bit; carry propagates to first empty within column mask.
    return (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]


def make_move(cur: int, mask: int, mv_bit: int) -> Tuple[int, int]:
    """
    Apply move mv_bit for current player, returning (new_cur, new_mask) for next player to move.
    new_cur is the bitboard of the next player (previous opponent).
    """
    new_cur = mask ^ cur
    new_mask = mask | mv_bit
    return new_cur, new_mask


def legal_columns(mask: int) -> List[int]:
    return [c for c in range(COLS) if (mask & TOP_MASK[c]) == 0]


def evaluate(cur: int, mask: int) -> int:
    """Static evaluation from the perspective of 'cur' (player to move in this node)."""
    opp = mask ^ cur
    score = 0

    # Center column preference (column 3)
    center_col = 3
    center_bits = COLUMN_MASK[center_col]
    score += 3 * ((cur & center_bits).bit_count() - (opp & center_bits).bit_count())

    # Window-based pattern scoring
    for w in WINDOW_MASKS:
        pc = (cur & w).bit_count()
        oc = (opp & w).bit_count()
        if pc and oc:
            continue
        if pc:
            score += WINDOW_WEIGHTS[pc]
        elif oc:
            score -= WINDOW_WEIGHTS[oc]

    return score


@dataclass
class TTEntry:
    depth: int
    value: int
    flag: int  # 0 exact, 1 lowerbound, 2 upperbound
    best_col: int


class _Timeout(Exception):
    pass


class Searcher:
    __slots__ = ("tt", "t0", "time_limit", "nodes", "max_tt_size")

    def __init__(self, time_limit: float = 0.98, max_tt_size: int = 250_000):
        self.tt: Dict[int, TTEntry] = {}
        self.t0 = 0.0
        self.time_limit = time_limit
        self.nodes = 0
        self.max_tt_size = max_tt_size

    def _key(self, cur: int, mask: int) -> int:
        # mask uses <= 49 bits; shift by 49 to avoid overlap
        return cur | (mask << 49)

    def _check_time(self) -> None:
        if (time.perf_counter() - self.t0) >= self.time_limit:
            raise _Timeout

    def negamax(self, cur: int, mask: int, depth: int, alpha: int, beta: int, ply: int) -> int:
        self.nodes += 1
        if (self.nodes & 2047) == 0:
            self._check_time()

        # If previous player (opponent at this node) has already won, it's a loss.
        opp = mask ^ cur
        if is_win(opp):
            return -MATE + ply

        if mask == FULL_MASK:
            return 0  # draw

        if depth <= 0:
            return evaluate(cur, mask)

        key = self._key(cur, mask)
        entry = self.tt.get(key)
        if entry is not None and entry.depth >= depth:
            if entry.flag == 0:
                return entry.value
            if entry.flag == 1:  # lowerbound
                alpha = max(alpha, entry.value)
            elif entry.flag == 2:  # upperbound
                beta = min(beta, entry.value)
            if alpha >= beta:
                return entry.value

        # Move ordering: TT best move first, then center-first heuristic order
        best_col = -1
        best_val = -10**18

        cols = []
        if entry is not None and entry.best_col is not None and 0 <= entry.best_col < COLS:
            cols.append(entry.best_col)
        for c in MOVE_ORDER:
            if c not in cols:
                cols.append(c)

        alpha0 = alpha

        for c in cols:
            mv = move_bit(mask, c)
            if mv == 0:
                continue

            # Immediate win for current player
            if is_win(cur | mv):
                val = MATE - ply
                best_val = val
                best_col = c
                alpha = max(alpha, val)
                break

            ncur, nmask = make_move(cur, mask, mv)
            val = -self.negamax(ncur, nmask, depth - 1, -beta, -alpha, ply + 1)

            if val > best_val:
                best_val = val
                best_col = c
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        # Store in TT
        if len(self.tt) > self.max_tt_size:
            # simple aging strategy
            self.tt.clear()

        flag = 0
        if best_val <= alpha0:
            flag = 2  # upperbound
        elif best_val >= beta:
            flag = 1  # lowerbound
        self.tt[key] = TTEntry(depth=depth, value=int(best_val), flag=flag, best_col=int(best_col))

        return int(best_val)

    def search(self, cur: int, mask: int) -> int:
        self.t0 = time.perf_counter()
        self.nodes = 0

        legal = legal_columns(mask)
        if not legal:
            return 0  # shouldn't happen in valid games, but must return something

        # Fast tactical layer: immediate win
        for c in MOVE_ORDER:
            mv = move_bit(mask, c)
            if mv and is_win(cur | mv):
                return c

        # Fast tactical layer: block opponent immediate win (if they have a winning reply)
        # If opponent can win by playing in some column next, we must play there if possible.
        opp = mask ^ cur
        must_block = []
        for c in range(COLS):
            mv_opp = move_bit(mask, c)
            if mv_opp and is_win(opp | mv_opp):
                must_block.append(c)
        if must_block:
            # If multiple, choose best by ordering
            for c in MOVE_ORDER:
                if c in must_block and move_bit(mask, c):
                    return c
            # fallback
            return must_block[0]

        best_move = None
        best_score = -10**18

        # Iterative deepening
        try:
            for depth in range(1, 12):  # usually enough under 1s with bitboards+TT
                alpha, beta = -MATE, MATE
                local_best_move = None
                local_best_score = -10**18

                # Root move ordering: center first
                for c in MOVE_ORDER:
                    mv = move_bit(mask, c)
                    if mv == 0:
                        continue

                    if is_win(cur | mv):
                        return c

                    ncur, nmask = make_move(cur, mask, mv)
                    val = -self.negamax(ncur, nmask, depth - 1, -beta, -alpha, 1)

                    if val > local_best_score:
                        local_best_score = val
                        local_best_move = c
                    if val > alpha:
                        alpha = val

                if local_best_move is not None:
                    best_move = local_best_move
                    best_score = local_best_score

        except _Timeout:
            pass

        # Ensure legal fallback
        if best_move is None or move_bit(mask, best_move) == 0:
            for c in MOVE_ORDER:
                if move_bit(mask, c) != 0:
                    return c
            return legal[0]

        return int(best_move)


# Keep a module-level searcher so the TT persists across calls (often beneficial).
_SEARCHER = Searcher(time_limit=0.98)


def policy(board: List[List[int]]) -> int:
    """
    Arena API: returns a legal column 0..6 that is not full.
    You are always player 1 in the given board encoding.
    """
    cur, mask = board_to_bitboards(board)

    # Absolute must: if something goes wrong, return a legal move.
    try:
        col = _SEARCHER.search(cur, mask)
    except Exception:
        col = None

    if col is not None:
        mv = move_bit(mask, int(col))
        if mv != 0:
            return int(col)

    # Fallback: first available by preferred order
    for c in MOVE_ORDER:
        if move_bit(mask, c) != 0:
            return c
    # Last resort
    for c in range(COLS):
        if move_bit(mask, c) != 0:
            return c
    return 0
