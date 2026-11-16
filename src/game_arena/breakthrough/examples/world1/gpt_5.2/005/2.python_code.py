
#!/usr/bin/env python3
"""
Breakthrough 8x8 policy: iterative deepening alpha-beta (negamax) with heuristics.

API:
def policy(me, opp, color) -> ((from_r, from_c), (to_r, to_c))
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import List, Tuple, Dict, Optional

# --- Bitboard helpers ---

def rc_to_idx(r: int, c: int) -> int:
    return (r << 3) | c

def idx_to_rc(i: int) -> Tuple[int, int]:
    return (i >> 3), (i & 7)

def list_to_bb(pieces: List[Tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << rc_to_idx(r, c)
    return bb

def iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        i = (lsb.bit_length() - 1)
        yield i
        bb ^= lsb

# --- Precomputation ---

GOAL_WHITE = sum(1 << i for i in range(56, 64))  # row 7
GOAL_BLACK = sum(1 << i for i in range(0, 8))    # row 0

ADV_W = [i >> 3 for i in range(64)]              # row
ADV_B = [7 - (i >> 3) for i in range(64)]        # 7-row

DIST_W = [7 - (i >> 3) for i in range(64)]       # moves-to-promote (approx)
DIST_B = [(i >> 3) for i in range(64)]

CENTER_BONUS = [0] * 64
for i in range(64):
    r, c = idx_to_rc(i)
    # prefer central files; mild preference only
    CENTER_BONUS[i] = 3 - abs(3.5 - c)

# Passed-pawn masks: for each square, squares "ahead" in same/adjacent files.
PASSED_AHEAD_W = [0] * 64
PASSED_AHEAD_B = [0] * 64
for i in range(64):
    r, c = idx_to_rc(i)
    # White: ahead = higher rows
    m = 0
    for cc in (c - 1, c, c + 1):
        if 0 <= cc <= 7:
            for rr in range(r + 1, 8):
                m |= 1 << rc_to_idx(rr, cc)
    PASSED_AHEAD_W[i] = m
    # Black: ahead = lower rows
    m = 0
    for cc in (c - 1, c, c + 1):
        if 0 <= cc <= 7:
            for rr in range(0, r):
                m |= 1 << rc_to_idx(rr, cc)
    PASSED_AHEAD_B[i] = m

def flip_color(side: str) -> str:
    return 'b' if side == 'w' else 'w'

@dataclass(frozen=True)
class Move:
    frm: int
    to: int
    is_capture: bool

# --- Move generation ---

def generate_moves(my: int, opp: int, side: str) -> List[Move]:
    occ = my | opp
    moves: List[Move] = []
    if side == 'w':
        for i in iter_bits(my):
            r, c = idx_to_rc(i)
            # forward
            if r < 7:
                f = i + 8
                if ((occ >> f) & 1) == 0:
                    moves.append(Move(i, f, False))
                # diag left
                if c > 0:
                    t = i + 7
                    if ((my >> t) & 1) == 0:
                        cap = ((opp >> t) & 1) == 1
                        moves.append(Move(i, t, cap))
                # diag right
                if c < 7:
                    t = i + 9
                    if ((my >> t) & 1) == 0:
                        cap = ((opp >> t) & 1) == 1
                        moves.append(Move(i, t, cap))
    else:
        for i in iter_bits(my):
            r, c = idx_to_rc(i)
            if r > 0:
                f = i - 8
                if ((occ >> f) & 1) == 0:
                    moves.append(Move(i, f, False))
                # diag left (to col-1)
                if c > 0:
                    t = i - 9
                    if ((my >> t) & 1) == 0:
                        cap = ((opp >> t) & 1) == 1
                        moves.append(Move(i, t, cap))
                # diag right (to col+1)
                if c < 7:
                    t = i - 7
                    if ((my >> t) & 1) == 0:
                        cap = ((opp >> t) & 1) == 1
                        moves.append(Move(i, t, cap))
    return moves

def apply_move(my: int, opp: int, mv: Move) -> Tuple[int, int]:
    # remove from
    my2 = my & ~(1 << mv.frm)
    # place to
    my2 |= (1 << mv.to)
    opp2 = opp
    if mv.is_capture:
        opp2 &= ~(1 << mv.to)
    return my2, opp2

# --- Evaluation & terminal detection ---

MATE = 10**9

def has_promoted(bb: int, side: str) -> bool:
    if side == 'w':
        return (bb & GOAL_WHITE) != 0
    else:
        return (bb & GOAL_BLACK) != 0

def evaluate(my: int, opp: int, side: str) -> int:
    # Terminal-ish checks first (static).
    if my == 0:
        return -MATE + 1
    if opp == 0:
        return MATE - 1
    if has_promoted(my, side):
        return MATE - 1
    if has_promoted(opp, flip_color(side)):
        return -MATE + 1

    my_cnt = my.bit_count()
    opp_cnt = opp.bit_count()
    material = (my_cnt - opp_cnt) * 110

    # Advancement & center
    adv = 0
    center = 0
    if side == 'w':
        for i in iter_bits(my):
            adv += ADV_W[i]
            center += CENTER_BONUS[i]
        for i in iter_bits(opp):
            adv -= ADV_B[i]  # opponent progress toward us is bad
            center -= 0.5 * CENTER_BONUS[i]
    else:
        for i in iter_bits(my):
            adv += ADV_B[i]
            center += CENTER_BONUS[i]
        for i in iter_bits(opp):
            adv -= ADV_W[i]
            center -= 0.5 * CENTER_BONUS[i]

    # Passed pawns and promotion proximity
    passed = 0
    promo_pressure = 0
    if side == 'w':
        for i in iter_bits(my):
            if (opp & PASSED_AHEAD_W[i]) == 0:
                passed += 1
                d = DIST_W[i]
                promo_pressure += (7 - d)  # closer is better
        for i in iter_bits(opp):
            # opponent passed pawns are dangerous
            if (my & PASSED_AHEAD_B[i]) == 0:
                passed -= 1
                d = DIST_B[i]
                promo_pressure -= (7 - d)
    else:
        for i in iter_bits(my):
            if (opp & PASSED_AHEAD_B[i]) == 0:
                passed += 1
                d = DIST_B[i]
                promo_pressure += (7 - d)
        for i in iter_bits(opp):
            if (my & PASSED_AHEAD_W[i]) == 0:
                passed -= 1
                d = DIST_W[i]
                promo_pressure -= (7 - d)

    # Mobility and threats (captures available)
    my_moves = generate_moves(my, opp, side)
    opp_moves = generate_moves(opp, my, flip_color(side))
    mobility = len(my_moves) - len(opp_moves)
    threats = sum(1 for m in my_moves if m.is_capture) - sum(1 for m in opp_moves if m.is_capture)

    # Slight preference for having multiple advanced pawns rather than one.
    # (encourage broad front)
    file_presence = 0
    my_files = 0
    for i in iter_bits(my):
        _, c = idx_to_rc(i)
        my_files |= (1 << c)
    file_presence = (my_files.bit_count() - 4)  # centered around ~4 files

    score = (
        material
        + adv * 9
        + int(center * 4)
        + passed * 35
        + promo_pressure * 10
        + mobility * 3
        + threats * 9
        + file_presence * 5
    )
    return score

# --- Search ---

def move_order_key(mv: Move, side: str) -> Tuple[int, int, int, float]:
    # Higher is better; used in reverse sort.
    to_r, to_c = idx_to_rc(mv.to)

    # immediate promotion is top priority
    if side == 'w':
        promote = 1 if to_r == 7 else 0
        advance = to_r
    else:
        promote = 1 if to_r == 0 else 0
        advance = 7 - to_r

    cap = 1 if mv.is_capture else 0
    center = 3 - abs(3.5 - to_c)
    return (promote, cap, advance, center)

class Searcher:
    __slots__ = ("t_end", "tt")

    def __init__(self, t_end: float):
        self.t_end = t_end
        # TT stores exact scores at given depth: key=(my, opp, side, depth) -> score
        self.tt: Dict[Tuple[int, int, str, int], int] = {}

    def negamax(self, my: int, opp: int, side: str, depth: int, alpha: int, beta: int, ply: int) -> int:
        if time.perf_counter() >= self.t_end:
            raise TimeoutError

        # terminal
        if opp == 0 or has_promoted(my, side):
            return MATE - ply
        if my == 0 or has_promoted(opp, flip_color(side)):
            return -MATE + ply
        if depth == 0:
            return evaluate(my, opp, side)

        key = (my, opp, side, depth)
        if key in self.tt:
            return self.tt[key]

        moves = generate_moves(my, opp, side)
        if not moves:
            # no legal moves => losing in typical breakthrough rules
            return -MATE + ply

        moves.sort(key=lambda m: move_order_key(m, side), reverse=True)

        best = -MATE
        a = alpha
        for mv in moves:
            my2, opp2 = apply_move(my, opp, mv)
            # next ply: swap sides, swap roles
            score = -self.negamax(opp2, my2, flip_color(side), depth - 1, -beta, -a, ply + 1)
            if score > best:
                best = score
            if best > a:
                a = best
            if a >= beta:
                break

        self.tt[key] = best
        return best

def choose_move(me_bb: int, opp_bb: int, color: str, time_limit: float = 0.95) -> Move:
    moves = generate_moves(me_bb, opp_bb, color)
    if not moves:
        # Shouldn't happen in normal play; but if it does, there is no legal move to return.
        # We'll still avoid crashing; caller likely won't create such states.
        return Move(0, 0, False)

    # Quick tactical: if any immediate promotion exists, do it.
    for mv in moves:
        to_r, _ = idx_to_rc(mv.to)
        if (color == 'w' and to_r == 7) or (color == 'b' and to_r == 0):
            return mv

    t_end = time.perf_counter() + max(0.02, time_limit)

    # Order root moves once for stability.
    moves.sort(key=lambda m: move_order_key(m, color), reverse=True)
    best_move = moves[0]

    searcher = Searcher(t_end)

    # Iterative deepening.
    depth = 1
    # Keep last best for move ordering by searching it first next depth.
    while True:
        if time.perf_counter() >= t_end:
            break
        try:
            best_score = -MATE
            alpha, beta = -MATE, MATE

            # Try best_move first
            ordered = [best_move] + [m for m in moves if m != best_move]

            for mv in ordered:
                my2, opp2 = apply_move(me_bb, opp_bb, mv)
                score = -searcher.negamax(opp2, my2, flip_color(color), depth - 1, -beta, -alpha, 1)
                if score > best_score:
                    best_score = score
                    best_move = mv
                if best_score > alpha:
                    alpha = best_score
                if time.perf_counter() >= t_end:
                    break

            depth += 1
            # cap depth to keep TT from exploding in worst-case; time stops us anyway
            if depth > 7:
                break
        except TimeoutError:
            break

    return best_move

# --- Required API ---

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_bb = list_to_bb(me)
    opp_bb = list_to_bb(opp)

    mv = choose_move(me_bb, opp_bb, color, time_limit=0.95)

    frm = idx_to_rc(mv.frm)
    to = idx_to_rc(mv.to)

    # Safety: ensure we return a legal move string even if something odd happened.
    # If chosen move is bogus, fall back to first legal generated move.
    legal = generate_moves(me_bb, opp_bb, color)
    if legal:
        ok = any(m.frm == mv.frm and m.to == mv.to for m in legal)
        if not ok:
            m0 = sorted(legal, key=lambda m: move_order_key(m, color), reverse=True)[0]
            frm = idx_to_rc(m0.frm)
            to = idx_to_rc(m0.to)

    return (frm, to)
