
import numpy as np
import time
from typing import Dict, Tuple, Optional

# ---------------------------
# Bitboard helpers / constants
# ---------------------------

FULL = (1 << 64) - 1

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# X-squares (diagonal adjacent to corners): b2, g2, b7, g7
X_SQUARES = (1 << 9) | (1 << 14) | (1 << 49) | (1 << 54)

# C-squares (edge-adjacent to corners): a2,b1,g1,h2,a7,b8,g8,h7
C_SQUARES = (1 << 8) | (1 << 1) | (1 << 6) | (1 << 15) | (1 << 48) | (1 << 57) | (1 << 62) | (1 << 55)

# Positional weight table (a1 is bit 0, h8 is bit 63; rows are 1..8)
W = [
    100, -20,  10,   5,   5,  10, -20, 100,
    -20, -50,  -2,  -2,  -2,  -2, -50, -20,
     10,  -2,  -1,  -1,  -1,  -1,  -2,  10,
      5,  -2,  -1,  -1,  -1,  -1,  -2,   5,
      5,  -2,  -1,  -1,  -1,  -1,  -2,   5,
     10,  -2,  -1,  -1,  -1,  -1,  -2,  10,
    -20, -50,  -2,  -2,  -2,  -2, -50, -20,
    100, -20,  10,   5,   5,  10, -20, 100,
]

INF = 10**18


def _shift_n(x: int) -> int:
    return (x << 8) & FULL


def _shift_s(x: int) -> int:
    return (x >> 8) & FULL


def _shift_e(x: int) -> int:
    return ((x & ~FILE_H) << 1) & FULL


def _shift_w(x: int) -> int:
    return ((x & ~FILE_A) >> 1) & FULL


def _shift_ne(x: int) -> int:
    return ((x & ~FILE_H) << 9) & FULL


def _shift_nw(x: int) -> int:
    return ((x & ~FILE_A) << 7) & FULL


def _shift_se(x: int) -> int:
    return ((x & ~FILE_H) >> 7) & FULL


def _shift_sw(x: int) -> int:
    return ((x & ~FILE_A) >> 9) & FULL


_SHIFTS = (_shift_n, _shift_s, _shift_e, _shift_w, _shift_ne, _shift_nw, _shift_se, _shift_sw)


def _bb_from_array(a: np.ndarray) -> int:
    # a is 8x8 with rows 0..7 corresponding to ranks 1..8
    # bit index = r*8 + c, with a1 = bit 0
    rr, cc = np.nonzero(a)
    bb = 0
    for r, c in zip(rr.tolist(), cc.tolist()):
        bb |= 1 << (r * 8 + c)
    return bb


def _idx_to_move(idx: int) -> str:
    c = idx % 8
    r = idx // 8
    return f"{chr(ord('a') + c)}{r + 1}"


def _iter_bits(x: int):
    while x:
        lsb = x & -x
        yield lsb
        x ^= lsb


def _popcount(x: int) -> int:
    return x.bit_count()


# ---------------------------
# Move generation / applying
# ---------------------------

def _legal_moves(player: int, opp: int) -> int:
    empty = FULL ^ (player | opp)
    moves = 0

    # Standard bitboard move-gen:
    # For each direction, expand a run of opponent discs adjacent to player,
    # then one more step into an empty square.
    for sh in _SHIFTS:
        m = sh(player) & opp
        # Maximum line length is 6 on 8x8 (beyond immediate adjacency), loop 5 more times.
        m |= sh(m) & opp
        m |= sh(m) & opp
        m |= sh(m) & opp
        m |= sh(m) & opp
        m |= sh(m) & opp
        moves |= sh(m) & empty

    return moves & empty


def _flips_for_move(player: int, opp: int, move: int) -> int:
    flips = 0
    for sh in _SHIFTS:
        x = sh(move)
        captured = 0
        while x and (x & opp):
            captured |= x
            x = sh(x)
        if x & player:
            flips |= captured
    return flips


def _apply_move(player: int, opp: int, move: int) -> Tuple[int, int]:
    flips = _flips_for_move(player, opp, move)
    player2 = player | move | flips
    opp2 = opp & ~flips
    return player2, opp2


# ---------------------------
# Evaluation
# ---------------------------

def _positional_score(p: int, o: int) -> int:
    s = 0
    for b in _iter_bits(p):
        s += W[(b.bit_length() - 1)]
    for b in _iter_bits(o):
        s -= W[(b.bit_length() - 1)]
    return s


def _empty_corners_mask(p: int, o: int) -> int:
    occ = p | o
    return CORNERS & ~occ


def _adjacent_to_corner_penalty(p: int, o: int) -> int:
    # Penalize occupying X/C squares only when the corresponding corner is empty.
    # This is a simplified but effective heuristic.
    occ = p | o
    score = 0

    # corner a1 -> x=b2 (9), c=a2(8), b1(1)
    if not (occ & (1 << 0)):
        score -= 12 * _popcount(p & ((1 << 9) | (1 << 8) | (1 << 1)))
        score += 12 * _popcount(o & ((1 << 9) | (1 << 8) | (1 << 1)))

    # corner h1 -> x=g2 (14), c=h2(15), g1(6)
    if not (occ & (1 << 7)):
        score -= 12 * _popcount(p & ((1 << 14) | (1 << 15) | (1 << 6)))
        score += 12 * _popcount(o & ((1 << 14) | (1 << 15) | (1 << 6)))

    # corner a8 -> x=b7 (49), c=a7(48), b8(57)
    if not (occ & (1 << 56)):
        score -= 12 * _popcount(p & ((1 << 49) | (1 << 48) | (1 << 57)))
        score += 12 * _popcount(o & ((1 << 49) | (1 << 48) | (1 << 57)))

    # corner h8 -> x=g7 (54), c=h7(55), g8(62)
    if not (occ & (1 << 63)):
        score -= 12 * _popcount(p & ((1 << 54) | (1 << 55) | (1 << 62)))
        score += 12 * _popcount(o & ((1 << 54) | (1 << 55) | (1 << 62)))

    return score


def _evaluate(player: int, opp: int) -> int:
    occ = player | opp
    empties = 64 - _popcount(occ)

    my_moves = _popcount(_legal_moves(player, opp))
    op_moves = _popcount(_legal_moves(opp, player))

    # Terminal-ish: if no one can move, score by disc difference heavily.
    if my_moves == 0 and op_moves == 0:
        return 10_000 * (_popcount(player) - _popcount(opp))

    corner_score = 40 * (_popcount(player & CORNERS) - _popcount(opp & CORNERS))
    mobility_score = 6 * (my_moves - op_moves)
    pos_score = _positional_score(player, opp)
    corner_adj = _adjacent_to_corner_penalty(player, opp)

    # Disc difference grows in importance late.
    disc_diff = _popcount(player) - _popcount(opp)
    if empties <= 12:
        disc_w = 30
    elif empties <= 24:
        disc_w = 10
    else:
        disc_w = 2

    return corner_score + mobility_score + pos_score + corner_adj + disc_w * disc_diff


# ---------------------------
# Search (iterative deepening, alpha-beta, TT)
# ---------------------------

class _Timeout(Exception):
    pass


# TT entry: depth, value, best_move (bit or 0), flag ('EXACT' only for simplicity)
TT: Dict[Tuple[int, int], Tuple[int, int, int]] = {}


def _ordered_moves(player: int, opp: int, moves_bb: int) -> list:
    # Order: corners first, then by heuristic square weight and avoiding X/C squares early.
    occ = player | opp
    empties = 64 - _popcount(occ)

    moves = []
    for m in _iter_bits(moves_bb):
        idx = m.bit_length() - 1
        score = 0

        if m & CORNERS:
            score += 100000
        score += 200 * W[idx]

        # Strongly discourage X/C squares early if the corner is empty (classic trap).
        if empties > 18:
            if m & X_SQUARES:
                score -= 8000
            if m & C_SQUARES:
                score -= 2500

        # Mild preference for lower flip count early (reduces giving mobility), opposite late.
        flips = _flips_for_move(player, opp, m).bit_count()
        if empties > 20:
            score -= 20 * flips
        else:
            score += 10 * flips

        moves.append((score, m))

    moves.sort(key=lambda t: t[0], reverse=True)
    return [m for _, m in moves]


def _negamax(player: int, opp: int, depth: int, alpha: int, beta: int, passed: bool,
             t_end: float) -> Tuple[int, int]:
    if time.perf_counter() >= t_end:
        raise _Timeout

    key = (player, opp)
    if key in TT:
        tt_depth, tt_val, tt_best = TT[key]
        if tt_depth >= depth:
            return tt_val, tt_best

    moves_bb = _legal_moves(player, opp)

    if depth == 0:
        return _evaluate(player, opp), 0

    if moves_bb == 0:
        # Must pass if no legal moves.
        if passed:
            # Game over
            return _evaluate(player, opp), 0
        val, _ = _negamax(opp, player, depth - 1, -beta, -alpha, True, t_end)
        return -val, 0

    best_move = 0
    best_val = -INF

    moves = _ordered_moves(player, opp, moves_bb)

    # If TT has a suggested best move, try it first
    if key in TT:
        _, _, tt_best = TT[key]
        if tt_best and (tt_best & moves_bb):
            # Move tt_best to front
            moves = [tt_best] + [m for m in moves if m != tt_best]

    for move in moves:
        p2, o2 = _apply_move(player, opp, move)
        val, _ = _negamax(o2, p2, depth - 1, -beta, -alpha, False, t_end)
        val = -val

        if val > best_val:
            best_val = val
            best_move = move

        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    TT[key] = (depth, best_val, best_move)
    return best_val, best_move


def _choose_move(player: int, opp: int, time_limit: float) -> int:
    moves_bb = _legal_moves(player, opp)
    if moves_bb == 0:
        return 0

    occ = player | opp
    empties = 64 - _popcount(occ)

    # Depth schedule: deeper near end; otherwise keep within time.
    if empties <= 10:
        max_depth = empties + 2  # usually reaches end with passes
    elif empties <= 18:
        max_depth = 9
    elif empties <= 28:
        max_depth = 7
    else:
        max_depth = 6

    t_end = time.perf_counter() + time_limit

    # Fallback: best static-ordered move (ensures we always return something legal)
    ordered = _ordered_moves(player, opp, moves_bb)
    best_move = ordered[0]

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        try:
            val, mv = _negamax(player, opp, depth, -INF, INF, False, t_end)
            if mv != 0:
                best_move = mv
        except _Timeout:
            break

    # Ensure legal
    if not (best_move & moves_bb):
        # pick first legal
        for m in _iter_bits(moves_bb):
            best_move = m
            break
    return best_move


# ---------------------------
# Public API
# ---------------------------

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the next move for the player to move given 8x8 numpy arrays (0/1).
    Must return a legal move "a1".."h8" or "pass" if no legal moves exist.
    """
    player = _bb_from_array(you)
    opp = _bb_from_array(opponent)

    moves_bb = _legal_moves(player, opp)
    if moves_bb == 0:
        return "pass"

    # Clear TT opportunistically if it grows too large (keeps memory/time stable)
    if len(TT) > 250_000:
        TT.clear()

    # Use most of the 1s budget, keep safety margin
    best_move = _choose_move(player, opp, time_limit=0.93)

    idx = best_move.bit_length() - 1
    if idx < 0:
        # Should not happen since we checked moves exist, but be safe.
        # Return the first legal move.
        for m in _iter_bits(moves_bb):
            idx = m.bit_length() - 1
            break

    return _idx_to_move(idx)
