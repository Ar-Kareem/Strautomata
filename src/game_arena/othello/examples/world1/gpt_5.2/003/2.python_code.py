
import numpy as np
import time
from typing import Dict, Tuple, Optional, List

# =========================
# Bitboard helpers (a1 = bit 0, h8 = bit 63)
# =========================

FULL = (1 << 64) - 1

A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

# Corners: a1, h1, a8, h8
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# "X-squares" (diagonal adjacent to corners): b2, g2, b7, g7
X_SQUARES = (1 << 9) | (1 << 14) | (1 << 49) | (1 << 54)

# "C-squares" (edge adjacent to corners): b1,g1,a2,h2,b8,g8,a7,h7
C_SQUARES = (
    (1 << 1) | (1 << 6) | (1 << 8) | (1 << 15) |
    (1 << 57) | (1 << 62) | (1 << 48) | (1 << 55)
)

# Edges (including corners)
TOP_EDGE = 0xFF00000000000000
BOT_EDGE = 0x00000000000000FF
LEFT_EDGE = 0x0101010101010101
RIGHT_EDGE = 0x8080808080808080
EDGES = TOP_EDGE | BOT_EDGE | LEFT_EDGE | RIGHT_EDGE


def _shift_e(x: int) -> int:
    return ((x & NOT_H) << 1) & FULL


def _shift_w(x: int) -> int:
    return ((x & NOT_A) >> 1) & FULL


def _shift_n(x: int) -> int:
    return ((x << 8) & FULL)


def _shift_s(x: int) -> int:
    return (x >> 8) & FULL


def _shift_ne(x: int) -> int:
    return ((x & NOT_H) << 9) & FULL


def _shift_nw(x: int) -> int:
    return ((x & NOT_A) << 7) & FULL


def _shift_se(x: int) -> int:
    return ((x & NOT_H) >> 7) & FULL


def _shift_sw(x: int) -> int:
    return ((x & NOT_A) >> 9) & FULL


SHIFT_FUNCS = (_shift_n, _shift_s, _shift_e, _shift_w, _shift_ne, _shift_nw, _shift_se, _shift_sw)


def _bb_from_array(arr: np.ndarray) -> int:
    # arr is 8x8 with ravel index = r*8+c matching a1=bit0, h8=bit63.
    idxs = np.nonzero(arr.ravel())[0]
    bb = 0
    for i in idxs:
        bb |= 1 << int(i)
    return bb


def _moves_bb(p: int, o: int) -> int:
    """Compute legal moves bitboard for player p against opponent o."""
    empty = (~(p | o)) & FULL
    moves = 0

    # Use standard propagation method for each direction (max line length 6 on 8x8).
    # East
    t = o & _shift_e(p)
    for _ in range(5):
        t |= o & _shift_e(t)
    moves |= empty & _shift_e(t)

    # West
    t = o & _shift_w(p)
    for _ in range(5):
        t |= o & _shift_w(t)
    moves |= empty & _shift_w(t)

    # North
    t = o & _shift_n(p)
    for _ in range(5):
        t |= o & _shift_n(t)
    moves |= empty & _shift_n(t)

    # South
    t = o & _shift_s(p)
    for _ in range(5):
        t |= o & _shift_s(t)
    moves |= empty & _shift_s(t)

    # NE
    t = o & _shift_ne(p)
    for _ in range(5):
        t |= o & _shift_ne(t)
    moves |= empty & _shift_ne(t)

    # NW
    t = o & _shift_nw(p)
    for _ in range(5):
        t |= o & _shift_nw(t)
    moves |= empty & _shift_nw(t)

    # SE
    t = o & _shift_se(p)
    for _ in range(5):
        t |= o & _shift_se(t)
    moves |= empty & _shift_se(t)

    # SW
    t = o & _shift_sw(p)
    for _ in range(5):
        t |= o & _shift_sw(t)
    moves |= empty & _shift_sw(t)

    return moves & FULL


def _flips_for_move(p: int, o: int, m: int) -> int:
    """Return bitboard of opponent discs flipped if player p plays move m."""
    flips = 0
    for sh in SHIFT_FUNCS:
        x = sh(m)
        captured = 0
        while x and (x & o):
            captured |= x
            x = sh(x)
        if x & p:
            flips |= captured
    return flips & FULL


def _apply_move(p: int, o: int, m: int) -> Tuple[int, int]:
    """Apply move m for player p, return (p2, o2) with same perspective (player to move just moved)."""
    flips = _flips_for_move(p, o, m)
    p2 = p | m | flips
    o2 = o & ~flips
    return p2 & FULL, o2 & FULL


def _iter_bits(bb: int) -> List[int]:
    """Return list of single-bit moves from bitboard."""
    res = []
    while bb:
        lsb = bb & -bb
        res.append(lsb)
        bb ^= lsb
    return res


def _bit_to_coord(m: int) -> str:
    idx = (m.bit_length() - 1)
    r = idx // 8
    c = idx % 8
    return chr(ord('a') + c) + chr(ord('1') + r)


# =========================
# Evaluation
# =========================

def _corner_danger_penalty(p: int, o: int) -> int:
    """Penalize occupying X/C squares when corresponding corner is empty."""
    penalty = 0

    # For each corner, if empty, penalize our discs on adjacent danger squares.
    # a1 corner (bit 0): X=b2 (9), C=b1(1), a2(8)
    if ((p | o) & (1 << 0)) == 0:
        if p & (1 << 9):
            penalty += 12
        if p & (1 << 1):
            penalty += 6
        if p & (1 << 8):
            penalty += 6

    # h1 corner (bit 7): X=g2(14), C=g1(6), h2(15)
    if ((p | o) & (1 << 7)) == 0:
        if p & (1 << 14):
            penalty += 12
        if p & (1 << 6):
            penalty += 6
        if p & (1 << 15):
            penalty += 6

    # a8 corner (bit 56): X=b7(49), C=b8(57), a7(48)
    if ((p | o) & (1 << 56)) == 0:
        if p & (1 << 49):
            penalty += 12
        if p & (1 << 57):
            penalty += 6
        if p & (1 << 48):
            penalty += 6

    # h8 corner (bit 63): X=g7(54), C=g8(62), h7(55)
    if ((p | o) & (1 << 63)) == 0:
        if p & (1 << 54):
            penalty += 12
        if p & (1 << 62):
            penalty += 6
        if p & (1 << 55):
            penalty += 6

    return penalty


def _evaluate(p: int, o: int) -> int:
    """Heuristic evaluation from perspective of side-to-move (p)."""
    discs_p = p.bit_count()
    discs_o = o.bit_count()
    empties = 64 - (discs_p + discs_o)

    # Terminal
    mp = _moves_bb(p, o)
    mo = _moves_bb(o, p)
    if mp == 0 and mo == 0:
        # Win/loss scaled large
        return (discs_p - discs_o) * 100000

    # Corners
    corner_p = (p & CORNERS).bit_count()
    corner_o = (o & CORNERS).bit_count()
    corner_score = 250 * (corner_p - corner_o)

    # Mobility
    mob_p = mp.bit_count()
    mob_o = mo.bit_count()
    mobility_score = 20 * (mob_p - mob_o)

    # Edge presence (lightweight)
    edge_score = 4 * (((p & EDGES).bit_count()) - ((o & EDGES).bit_count()))

    # Disc difference (de-emphasize early)
    if empties > 44:
        disc_w = 1
    elif empties > 20:
        disc_w = 3
    else:
        disc_w = 8
    disc_score = disc_w * (discs_p - discs_o)

    # Corner danger (X/C squares next to empty corners)
    danger_score = -_corner_danger_penalty(p, o) + _corner_danger_penalty(o, p)

    # Parity (small)
    parity_score = 0
    if empties <= 18:
        parity_score = 2 if (empties % 2 == 1) else -2

    return corner_score + mobility_score + edge_score + disc_score + danger_score + parity_score


# =========================
# Search (Negamax + AlphaBeta + Iterative deepening)
# =========================

class _Timeout(Exception):
    pass


def _move_order_score(p: int, o: int, m: int) -> int:
    """Fast move ordering heuristic (higher is better)."""
    score = 0
    if m & CORNERS:
        score += 100000
    # Avoid X-squares if the related corner is empty (approx by global X_SQUARES)
    if m & X_SQUARES:
        score -= 5000
    if m & C_SQUARES:
        score -= 800

    flips = _flips_for_move(p, o, m).bit_count()
    score += 30 * flips

    # Prefer moves that reduce opponent mobility
    p2, o2 = _apply_move(p, o, m)
    opp_mob = _moves_bb(o2, p2).bit_count()
    score -= 40 * opp_mob
    return score


def _negamax(
    p: int,
    o: int,
    depth: int,
    alpha: int,
    beta: int,
    tt: Dict[Tuple[int, int, int], int],
    deadline: float
) -> int:
    if time.perf_counter() > deadline:
        raise _Timeout

    key = (p, o, depth)
    if key in tt:
        return tt[key]

    mp = _moves_bb(p, o)
    if depth == 0:
        val = _evaluate(p, o)
        tt[key] = val
        return val

    if mp == 0:
        # Pass or game over
        mo = _moves_bb(o, p)
        if mo == 0:
            val = _evaluate(p, o)  # terminal evaluation handles it
            tt[key] = val
            return val
        val = -_negamax(o, p, depth - 1, -beta, -alpha, tt, deadline)
        tt[key] = val
        return val

    moves = _iter_bits(mp)
    moves.sort(key=lambda m: _move_order_score(p, o, m), reverse=True)

    best = -10**18
    a = alpha
    for m in moves:
        p2, o2 = _apply_move(p, o, m)
        val = -_negamax(o2, p2, depth - 1, -beta, -a, tt, deadline)
        if val > best:
            best = val
        if best > a:
            a = best
        if a >= beta:
            break

    tt[key] = best
    return best


def _choose_move(p: int, o: int, max_time: float = 0.95) -> Optional[int]:
    start = time.perf_counter()
    deadline = start + max_time

    mp = _moves_bb(p, o)
    if mp == 0:
        return None
    moves = _iter_bits(mp)
    if len(moves) == 1:
        return moves[0]

    empties = 64 - ((p | o).bit_count())
    # Endgame: search to the end if feasible
    if empties <= 12:
        max_depth = empties  # exact
    else:
        max_depth = 7  # iterative deepening target (often reaches 5-7 within budget)

    best_move = moves[0]
    # Initial ordering for root
    moves.sort(key=lambda m: _move_order_score(p, o, m), reverse=True)

    # Iterative deepening with aspiration-ish window
    last_best_val = -10**18
    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break
        tt: Dict[Tuple[int, int, int], int] = {}

        # Re-order root moves: put previous best first
        if best_move in moves:
            moves2 = [best_move] + [m for m in moves if m != best_move]
        else:
            moves2 = moves

        alpha, beta = -10**18, 10**18
        cur_best_move = best_move
        cur_best_val = -10**18

        try:
            for m in moves2:
                if time.perf_counter() > deadline:
                    raise _Timeout
                p2, o2 = _apply_move(p, o, m)
                val = -_negamax(o2, p2, depth - 1, -beta, -alpha, tt, deadline)
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best_move = m
                if val > alpha:
                    alpha = val
        except _Timeout:
            break

        best_move = cur_best_move
        last_best_val = cur_best_val

        # Small extra cutoff: if we found a corner, usually lock it in
        if best_move & CORNERS:
            # still allow time check, but generally safe to stop early
            if time.perf_counter() + 0.02 > deadline:
                break

    return best_move


# =========================
# Required API
# =========================

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move in algebraic notation (e.g., 'd3') or 'pass' if no legal moves.
    """
    p = _bb_from_array(you)
    o = _bb_from_array(opponent)

    mp = _moves_bb(p, o)
    if mp == 0:
        return "pass"

    m = _choose_move(p, o, max_time=0.95)
    if m is None:
        # Should not happen since mp != 0, but be safe
        m = _iter_bits(mp)[0]

    # Safety: ensure chosen move is legal; otherwise fall back to first legal.
    if (m & mp) == 0:
        m = _iter_bits(mp)[0]

    return _bit_to_coord(m)
