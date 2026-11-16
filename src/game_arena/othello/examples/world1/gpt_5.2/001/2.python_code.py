
import numpy as np
import time
from typing import Dict, Tuple, Optional

# ========= Bitboard Othello (8x8) =========
# Bit indexing: bit i corresponds to (r=i//8, c=i%8) where r=0 is rank "1".
# So a1 is bit 0, h1 is bit 7, a8 is bit 56.

FULL = (1 << 64) - 1

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

# Directions in bit-shift delta form (relative to our indexing).
DIRS = (1, -1, 8, -8, 9, 7, -7, -9)

# Corners
A1 = 1 << 0
H1 = 1 << 7
A8 = 1 << 56
H8 = 1 << 63
CORNERS = A1 | H1 | A8 | H8

# X-squares (diagonal adjacent to corners): b2, g2, b7, g7
X_SQUARES = (1 << 9) | (1 << 14) | (1 << 49) | (1 << 54)

# Piece-square table (classic strong heuristic)
_PST_2D = [
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120],
]
# Flattened PST indexed by bit index i = r*8+c
PST = [0] * 64
for r in range(8):
    for c in range(8):
        PST[r * 8 + c] = _PST_2D[r][c]


def _shift(bb: int, d: int) -> int:
    """Shift bitboard bb by direction d with wrap prevention."""
    if d == 1:      # East
        return (bb & NOT_H) << 1
    if d == -1:     # West
        return (bb & NOT_A) >> 1
    if d == 8:      # North
        return ((bb << 8) & FULL)
    if d == -8:     # South
        return (bb >> 8)
    if d == 9:      # NE
        return ((bb & NOT_H) << 9) & FULL
    if d == 7:      # NW
        return ((bb & NOT_A) << 7) & FULL
    if d == -7:     # SE
        return (bb & NOT_H) >> 7
    if d == -9:     # SW
        return (bb & NOT_A) >> 9
    return 0


def _iter_bits(bb: int):
    """Yield each 1-bit as a separate int (LSB first)."""
    while bb:
        lsb = bb & -bb
        yield lsb
        bb ^= lsb


def _bit_index(b: int) -> int:
    """Index 0..63 of single-bit b."""
    return b.bit_length() - 1


def _legal_moves(P: int, O: int) -> int:
    """Compute legal moves bitboard for player P vs opponent O."""
    empty = FULL ^ (P | O)
    moves = 0
    for d in DIRS:
        t = _shift(P, d) & O
        # expand up to 6 opponent discs in a line (board width limit)
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        moves |= _shift(t, d) & empty
    return moves


def _make_move(P: int, O: int, move: int) -> Tuple[int, int]:
    """Apply move for P; return (P2, O2). Assumes move is legal."""
    flips = 0
    for d in DIRS:
        t = _shift(move, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        t |= _shift(t, d) & O
        if _shift(t, d) & P:
            flips |= t
    P2 = P | move | flips
    O2 = O & ~flips
    return P2, O2


def _pst_sum(bb: int) -> int:
    s = 0
    while bb:
        lsb = bb & -bb
        s += PST[_bit_index(lsb)]
        bb ^= lsb
    return s


def _frontier_count(P: int, empty: int) -> int:
    adj = 0
    for d in DIRS:
        adj |= _shift(empty, d)
    return (P & adj).bit_count()


def _evaluate(P: int, O: int) -> int:
    """Heuristic evaluation from perspective of current player P."""
    occ = P | O
    empty = FULL ^ occ
    empties = empty.bit_count()

    # Game over detection is handled by search; here is pure heuristic.
    corner_diff = ((P & CORNERS).bit_count() - (O & CORNERS).bit_count())

    # Mobility
    mP = _legal_moves(P, O).bit_count()
    mO = _legal_moves(O, P).bit_count()
    mob_diff = mP - mO

    # Frontier (fewer frontier discs is better)
    fP = _frontier_count(P, empty)
    fO = _frontier_count(O, empty)
    frontier_diff = fO - fP  # invert so positive is good for P

    # Disc difference (mostly endgame)
    disc_diff = P.bit_count() - O.bit_count()

    # PST
    pst = _pst_sum(P) - _pst_sum(O)

    # Penalize X-squares when corner is empty (classic trap squares)
    x_pen = 0
    if not (occ & A1):
        if P & (1 << 9):
            x_pen -= 60
        if O & (1 << 9):
            x_pen += 60
    if not (occ & H1):
        if P & (1 << 14):
            x_pen -= 60
        if O & (1 << 14):
            x_pen += 60
    if not (occ & A8):
        if P & (1 << 49):
            x_pen -= 60
        if O & (1 << 49):
            x_pen += 60
    if not (occ & H8):
        if P & (1 << 54):
            x_pen -= 60
        if O & (1 << 54):
            x_pen += 60

    # Phase-based weighting
    # Early: prioritize mobility and avoiding frontier; Mid: PST+corners; Late: discs.
    if empties > 44:
        w_corner, w_mob, w_front, w_pst, w_disc = 900, 80, 25, 8, 0
    elif empties > 20:
        w_corner, w_mob, w_front, w_pst, w_disc = 1100, 70, 18, 10, 2
    else:
        w_corner, w_mob, w_front, w_pst, w_disc = 1400, 25, 8, 6, 25

    return (
        w_corner * corner_diff
        + w_mob * mob_diff
        + w_front * frontier_diff
        + w_pst * pst
        + w_disc * disc_diff
        + x_pen
    )


def _final_score(P: int, O: int) -> int:
    """Terminal score at game end (huge magnitude to force correct play)."""
    diff = P.bit_count() - O.bit_count()
    if diff > 0:
        return 100000 + 1000 * diff
    if diff < 0:
        return -100000 + 1000 * diff
    return 0


class _Timeout(Exception):
    pass


def _move_to_str(move: int) -> str:
    i = _bit_index(move)
    r = i // 8
    c = i % 8
    return chr(ord('a') + c) + chr(ord('1') + r)


def _order_moves(moves: int) -> list:
    """Return list of move bits ordered by static desirability (best first)."""
    lst = []
    for m in _iter_bits(moves):
        idx = _bit_index(m)
        score = PST[idx]
        if m & CORNERS:
            score += 10000
        # Discourage X-squares directly (also in eval, but helps ordering)
        if m & X_SQUARES:
            score -= 200
        # Edges modest bonus
        r, c = divmod(idx, 8)
        if r == 0 or r == 7 or c == 0 or c == 7:
            score += 30
        lst.append((score, m))
    lst.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in lst]


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Arena API: you/opponent are 8x8 numpy arrays of 0/1, and it's always 'you' to move.
    Must return a legal move like 'd3' or 'pass' if no legal moves exist.
    """
    # Build bitboards from numpy arrays
    # Flattened index is r*8+c, matching our mapping.
    you_idx = np.flatnonzero(you)
    opp_idx = np.flatnonzero(opponent)

    P = 0
    for i in you_idx.tolist():
        P |= (1 << int(i))
    O = 0
    for i in opp_idx.tolist():
        O |= (1 << int(i))

    root_moves = _legal_moves(P, O)
    if root_moves == 0:
        return "pass"

    # Time-limited iterative deepening negamax with alpha-beta + transposition table
    start = time.perf_counter()
    TIME_LIMIT = 0.95  # seconds

    def time_up():
        return (time.perf_counter() - start) > TIME_LIMIT

    # TT: (P,O,depth,passed) -> (score)
    # Simple exact TT (works well with fixed-depth negamax here).
    TT: Dict[Tuple[int, int, int, int], int] = {}

    def negamax(Pn: int, On: int, depth: int, alpha: int, beta: int, passed: int) -> int:
        if time_up():
            raise _Timeout

        key = (Pn, On, depth, passed)
        if key in TT:
            return TT[key]

        moves = _legal_moves(Pn, On)
        if moves == 0:
            if passed:
                val = _final_score(Pn, On)
                TT[key] = val
                return val
            # pass turn (do not change discs, just swap players)
            val = -negamax(On, Pn, depth - 1, -beta, -alpha, 1) if depth > 0 else -_evaluate(On, Pn)
            TT[key] = val
            return val

        if depth <= 0:
            val = _evaluate(Pn, On)
            TT[key] = val
            return val

        best = -10**18
        # Order moves for pruning
        for mv in _order_moves(moves):
            P2, O2 = _make_move(Pn, On, mv)
            score = -negamax(O2, P2, depth - 1, -beta, -alpha, 0)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        TT[key] = best
        return best

    # Root search with iterative deepening
    ordered_root = _order_moves(root_moves)
    best_move = ordered_root[0]  # always legal fallback
    best_score = -10**18

    # Depth schedule: go deeper in endgame automatically
    empties = (FULL ^ (P | O)).bit_count()
    max_depth = 5
    if empties <= 18:
        max_depth = 8
    if empties <= 12:
        max_depth = 10

    for depth in range(1, max_depth + 1):
        if time_up():
            break
        # Reuse TT between depths (good in practice)
        cur_best_move = best_move
        cur_best_score = -10**18
        alpha = -10**18
        beta = 10**18
        try:
            for mv in ordered_root:
                if time_up():
                    raise _Timeout
                P2, O2 = _make_move(P, O, mv)
                score = -negamax(O2, P2, depth - 1, -beta, -alpha, 0)
                if score > cur_best_score:
                    cur_best_score = score
                    cur_best_move = mv
                if score > alpha:
                    alpha = score
        except _Timeout:
            break

        best_move = cur_best_move
        best_score = cur_best_score

    # Ensure returned move is legal
    if not (best_move & root_moves):
        # Fallback (shouldn't happen), pick first legal
        best_move = ordered_root[0]

    return _move_to_str(best_move)
