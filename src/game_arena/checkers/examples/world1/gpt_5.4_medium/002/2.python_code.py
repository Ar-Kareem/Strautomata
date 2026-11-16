
from __future__ import annotations

import time
from functools import lru_cache


# =========================
# Constants and precompute
# =========================

INF = 10**9
MATE = 10**6

ROW = [sq >> 3 for sq in range(64)]
COL = [sq & 7 for sq in range(64)]

PROGRESS_B = [7 - ROW[sq] for sq in range(64)]  # black promotes at row 0
PROGRESS_W = [ROW[sq] for sq in range(64)]      # white promotes at row 7

CENTER_MAN = [
    4 if 2 <= ROW[sq] <= 5 and 2 <= COL[sq] <= 5 else 0
    for sq in range(64)
]
CENTER_KING = [
    (8 if 2 <= ROW[sq] <= 5 and 2 <= COL[sq] <= 5 else 0) +
    (4 if 1 <= ROW[sq] <= 6 and 1 <= COL[sq] <= 6 else 0)
    for sq in range(64)
]
EDGE_BONUS = [2 if COL[sq] in (0, 7) else 0 for sq in range(64)]

HOME_B = [5 if ROW[sq] == 7 else 0 for sq in range(64)]
HOME_W = [5 if ROW[sq] == 0 else 0 for sq in range(64)]

NEAR_PROMO_B = [10 if ROW[sq] == 1 else 0 for sq in range(64)]
NEAR_PROMO_W = [10 if ROW[sq] == 6 else 0 for sq in range(64)]

KING_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
B_MAN_DIRS = ((-1, -1), (-1, 1))
W_MAN_DIRS = ((1, -1), (1, 1))

DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def _other(side: str) -> str:
    return 'w' if side == 'b' else 'b'


def _bit(sq: int) -> int:
    return 1 << sq


def _coords_to_bb(coords) -> int:
    bb = 0
    for r, c in coords:
        bb |= 1 << (r * 8 + c)
    return bb


def _sq_to_coord(sq: int) -> tuple[int, int]:
    return (sq >> 3, sq & 7)


def _iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def _check_time():
    global NODE_COUNTER, DEADLINE
    NODE_COUNTER += 1
    if (NODE_COUNTER & 255) == 0:
        if time.perf_counter() > DEADLINE:
            raise SearchTimeout


# =========================
# Move generation
# Move tuple: (from_sq, to_sq, captured_sq) where captured_sq == -1 if non-capture
# =========================

@lru_cache(maxsize=200000)
def _gen_moves(bm: int, bk: int, wm: int, wk: int, side: str):
    occ = bm | bk | wm | wk

    if side == 'b':
        my_men, my_kings = bm, bk
        opp_all = wm | wk
        opp_kings = wk
        man_dirs = B_MAN_DIRS
        promo_row = 0
        home_row = 7
    else:
        my_men, my_kings = wm, wk
        opp_all = bm | bk
        opp_kings = bk
        man_dirs = W_MAN_DIRS
        promo_row = 7
        home_row = 0

    captures = []
    simples = []

    # Men
    bb = my_men
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        r = ROW[sq]
        c = COL[sq]

        for dr, dc in man_dirs:
            r1 = r + dr
            c1 = c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                s1 = r1 * 8 + c1
                b1 = 1 << s1

                if occ & b1:
                    if opp_all & b1:
                        r2 = r + 2 * dr
                        c2 = c + 2 * dc
                        if 0 <= r2 < 8 and 0 <= c2 < 8:
                            s2 = r2 * 8 + c2
                            b2 = 1 << s2
                            if not (occ & b2):
                                score = 60
                                if opp_kings & b1:
                                    score += 45
                                else:
                                    score += 25
                                if r2 == promo_row:
                                    score += 100
                                score += CENTER_MAN[s2]
                                captures.append((score, sq, s2, s1))
                else:
                    score = 0
                    if r1 == promo_row:
                        score += 120
                    score += 2 * (PROGRESS_B[s1] if side == 'b' else PROGRESS_W[s1])
                    score += CENTER_MAN[s1]
                    if r == home_row:
                        score -= 4
                    simples.append((score, sq, s1, -1))

    # Kings
    bb = my_kings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        r = ROW[sq]
        c = COL[sq]

        for dr, dc in KING_DIRS:
            r1 = r + dr
            c1 = c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                s1 = r1 * 8 + c1
                b1 = 1 << s1

                if occ & b1:
                    if opp_all & b1:
                        r2 = r + 2 * dr
                        c2 = c + 2 * dc
                        if 0 <= r2 < 8 and 0 <= c2 < 8:
                            s2 = r2 * 8 + c2
                            b2 = 1 << s2
                            if not (occ & b2):
                                score = 70
                                if opp_kings & b1:
                                    score += 50
                                else:
                                    score += 25
                                score += CENTER_KING[s2]
                                captures.append((score, sq, s2, s1))
                else:
                    score = 8 + CENTER_KING[s1]
                    simples.append((score, sq, s1, -1))

    if captures:
        captures.sort(reverse=True)
        return tuple((f, t, cap) for _, f, t, cap in captures)

    simples.sort(reverse=True)
    return tuple((f, t, cap) for _, f, t, cap in simples)


def _apply_move(bm: int, bk: int, wm: int, wk: int, side: str, move):
    f, t, cap = move
    fb = 1 << f
    tb = 1 << t

    if side == 'b':
        if bm & fb:
            bm ^= fb
            if cap != -1:
                cb = 1 << cap
                if wm & cb:
                    wm ^= cb
                else:
                    wk ^= cb
            if ROW[t] == 0:
                bk |= tb
            else:
                bm |= tb
        else:
            bk ^= fb
            bk |= tb
            if cap != -1:
                cb = 1 << cap
                if wm & cb:
                    wm ^= cb
                else:
                    wk ^= cb
    else:
        if wm & fb:
            wm ^= fb
            if cap != -1:
                cb = 1 << cap
                if bm & cb:
                    bm ^= cb
                else:
                    bk ^= cb
            if ROW[t] == 7:
                wk |= tb
            else:
                wm |= tb
        else:
            wk ^= fb
            wk |= tb
            if cap != -1:
                cb = 1 << cap
                if bm & cb:
                    bm ^= cb
                else:
                    bk ^= cb

    return bm, bk, wm, wk


# =========================
# Evaluation
# =========================

def _side_static(men: int, kings: int, color: str) -> int:
    score = men.bit_count() * 100 + kings.bit_count() * 175

    if color == 'b':
        bb = men
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            score += 7 * PROGRESS_B[sq]
            score += CENTER_MAN[sq]
            score += EDGE_BONUS[sq]
            score += HOME_B[sq]
            score += NEAR_PROMO_B[sq]
    else:
        bb = men
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            score += 7 * PROGRESS_W[sq]
            score += CENTER_MAN[sq]
            score += EDGE_BONUS[sq]
            score += HOME_W[sq]
            score += NEAR_PROMO_W[sq]

    bb = kings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        score += 10
        score += CENTER_KING[sq]

    return score


@lru_cache(maxsize=200000)
def _threatened_weight(bm: int, bk: int, wm: int, wk: int, side: str) -> int:
    opp = _other(side)
    opp_moves = _gen_moves(bm, bk, wm, wk, opp)
    if not opp_moves or opp_moves[0][2] == -1:
        return 0

    threatened_mask = 0
    for _, _, cap in opp_moves:
        threatened_mask |= 1 << cap

    if side == 'b':
        return 24 * (threatened_mask & bm).bit_count() + 40 * (threatened_mask & bk).bit_count()
    else:
        return 24 * (threatened_mask & wm).bit_count() + 40 * (threatened_mask & wk).bit_count()


def _mobility_score(moves) -> int:
    if not moves:
        return -50
    if moves[0][2] != -1:
        return 6 + 2 * len(moves)
    return len(moves)


def _evaluate(bm: int, bk: int, wm: int, wk: int, side: str) -> int:
    base = _side_static(bm, bk, 'b') - _side_static(wm, wk, 'w')
    score = base if side == 'b' else -base

    my_moves = _gen_moves(bm, bk, wm, wk, side)
    opp_moves = _gen_moves(bm, bk, wm, wk, _other(side))

    score += 2 * (_mobility_score(my_moves) - _mobility_score(opp_moves))

    my_threat = _threatened_weight(bm, bk, wm, wk, side)
    opp_threat = _threatened_weight(bm, bk, wm, wk, _other(side))
    score += opp_threat - my_threat

    return score


# =========================
# Search
# =========================

def _qsearch(bm: int, bk: int, wm: int, wk: int, side: str, alpha: int, beta: int, qdepth: int) -> int:
    _check_time()

    moves = _gen_moves(bm, bk, wm, wk, side)
    if not moves:
        return -MATE

    # In mandatory-capture checkers, if no capture exists, settle statically.
    if qdepth <= 0 or moves[0][2] == -1:
        return _evaluate(bm, bk, wm, wk, side)

    best = -INF
    nxt = _other(side)

    for mv in moves:
        nbm, nbk, nwm, nwk = _apply_move(bm, bk, wm, wk, side, mv)
        score = -_qsearch(nbm, nbk, nwm, nwk, nxt, -beta, -alpha, qdepth - 1)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _search(bm: int, bk: int, wm: int, wk: int, side: str, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    moves = _gen_moves(bm, bk, wm, wk, side)
    if not moves:
        return -MATE + depth

    if depth <= 0:
        return _qsearch(bm, bk, wm, wk, side, alpha, beta, 4)

    best = -INF
    nxt = _other(side)

    for mv in moves:
        nbm, nbk, nwm, nwk = _apply_move(bm, bk, wm, wk, side, mv)
        score = -_search(nbm, nbk, nwm, nwk, nxt, depth - 1, -beta, -alpha)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _choose_depth(total_pieces: int, root_moves) -> int:
    if total_pieces >= 20:
        depth = 5
    elif total_pieces >= 14:
        depth = 6
    elif total_pieces >= 10:
        depth = 7
    else:
        depth = 8

    if root_moves and root_moves[0][2] != -1:
        depth = min(depth + 1, 10)
    if len(root_moves) <= 2 and total_pieces <= 12:
        depth = min(depth + 1, 10)

    return depth


# =========================
# Public policy
# =========================

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODE_COUNTER

    try:
        # Convert to absolute black/white bitboards
        if color == 'b':
            bm = _coords_to_bb(my_men)
            bk = _coords_to_bb(my_kings)
            wm = _coords_to_bb(opp_men)
            wk = _coords_to_bb(opp_kings)
        else:
            wm = _coords_to_bb(my_men)
            wk = _coords_to_bb(my_kings)
            bm = _coords_to_bb(opp_men)
            bk = _coords_to_bb(opp_kings)

        root_moves = _gen_moves(bm, bk, wm, wk, color)

        # If terminal is ever passed in, return a harmless placeholder.
        # Arena should normally not call policy on terminal positions.
        if not root_moves:
            # Best effort fallback; likely unreachable in valid arena play.
            if my_men:
                src = my_men[0]
                return (src, src)
            if my_kings:
                src = my_kings[0]
                return (src, src)
            return ((0, 0), (0, 0))

        # Immediate legal fallback
        best_move = root_moves[0]

        # If only one legal move, just play it.
        if len(root_moves) == 1:
            return (_sq_to_coord(best_move[0]), _sq_to_coord(best_move[1]))

        total_pieces = (bm | bk | wm | wk).bit_count()
        max_depth = _choose_depth(total_pieces, root_moves)

        DEADLINE = time.perf_counter() + 0.92
        NODE_COUNTER = 0

        pv_move = best_move
        completed_best = best_move

        for depth in range(1, max_depth + 1):
            try:
                alpha = -INF
                beta = INF

                ordered = list(root_moves)
                if pv_move is not None:
                    # Put prior best move first
                    for i, mv in enumerate(ordered):
                        if mv == pv_move:
                            ordered[0], ordered[i] = ordered[i], ordered[0]
                            break

                current_best = ordered[0]
                current_score = -INF

                for mv in ordered:
                    nbm, nbk, nwm, nwk = _apply_move(bm, bk, wm, wk, color, mv)
                    score = -_search(nbm, nbk, nwm, nwk, _other(color), depth - 1, -beta, -alpha)

                    if score > current_score:
                        current_score = score
                        current_best = mv
                    if score > alpha:
                        alpha = score

                completed_best = current_best
                pv_move = current_best

            except SearchTimeout:
                break

        best_move = completed_best
        return (_sq_to_coord(best_move[0]), _sq_to_coord(best_move[1]))

    except Exception:
        # Robust legal fallback
        try:
            if color == 'b':
                bm = _coords_to_bb(my_men)
                bk = _coords_to_bb(my_kings)
                wm = _coords_to_bb(opp_men)
                wk = _coords_to_bb(opp_kings)
            else:
                wm = _coords_to_bb(my_men)
                wk = _coords_to_bb(my_kings)
                bm = _coords_to_bb(opp_men)
                bk = _coords_to_bb(opp_kings)

            moves = _gen_moves(bm, bk, wm, wk, color)
            if moves:
                mv = moves[0]
                return (_sq_to_coord(mv[0]), _sq_to_coord(mv[1]))
        except Exception:
            pass

        # Last-ditch fallback; should be unreachable on valid non-terminal input.
        if my_men:
            src = my_men[0]
            return (src, src)
        if my_kings:
            src = my_kings[0]
            return (src, src)
        return ((0, 0), (0, 0))
