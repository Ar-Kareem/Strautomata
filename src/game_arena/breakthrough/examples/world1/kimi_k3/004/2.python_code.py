
from __future__ import annotations

import time

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

ROW0 = 0x00000000000000FF
ROW1 = 0x000000000000FF00
ROW6 = 0x00FF000000000000
ROW7 = 0xFF00000000000000

# didx: 1 means moving toward higher rows (white), 0 means moving toward lower rows (black)
GOAL_MASK = (ROW0, ROW7)
ONE_STEP = (ROW1, ROW6)

PROG = [[0] * 64 for _ in range(2)]
FWD_SPAN = [[0] * 64 for _ in range(2)]
STRAIGHT = [[0] * 64 for _ in range(2)]

for r in range(8):
    for c in range(8):
        sq = (r << 3) | c
        PROG[1][sq] = r
        PROG[0][sq] = 7 - r
        for didx in (0, 1):
            rows = range(r + 1, 8) if didx == 1 else range(0, r)
            span = 0
            straight = 0
            c0 = c - 1 if c > 0 else 0
            c1 = c + 1 if c < 7 else 7
            for rr in rows:
                base = rr << 3
                straight |= 1 << (base | c)
                for cc in range(c0, c1 + 1):
                    span |= 1 << (base | cc)
            FWD_SPAN[didx][sq] = span
            STRAIGHT[didx][sq] = straight

CENTER = (0, 4, 10, 16, 16, 10, 4, 0)

WIN_SCORE = 100_000_000
INF = 10**30

PIECE = 1000
ADV_W = 70
ADV_SQ_W = 22
BEST_W = 300
BEST_SQ_W = 100
CENTER_W = 7

RUNNER_CLEAR_BASE = 2600
RUNNER_CLEAR_PROG = 250
RUNNER_BLOCK_BASE = 450
RUNNER_BLOCK_PROG = 55

HANG_UNDEF_BASE = 430
HANG_UNDEF_PROG = 115
HANG_DEF_BASE = 70
SUPPORT_BASE = 18
SUPPORT_PROG = 4

EXACT, LOWER, UPPER = 0, 1, 2

try:
    _popcount = int.bit_count
except AttributeError:  # very old Python fallback
    def _popcount(x: int) -> int:
        return bin(x).count("1")

TT = {}
KILLERS = [[-1, -1] for _ in range(128)]
HISTORY = {}
NODES = 0
DEADLINE = 0.0


class SearchTimeout(Exception):
    pass


def _didx(d: int) -> int:
    return 1 if d > 0 else 0


def _attack_map(bits: int, didx: int) -> int:
    if didx == 1:
        return ((((bits & NOT_H) << 9) | ((bits & NOT_A) << 7)) & FULL)
    return (((bits & NOT_H) >> 7) | ((bits & NOT_A) >> 9)) & FULL


def _gen_moves(cur: int, oth: int, d: int) -> list[int]:
    occ = cur | oth
    moves = []
    b = cur
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        r = sq >> 3
        c = sq & 7
        nr = r + d
        if 0 <= nr < 8:
            base = nr << 3
            to = base | c
            bit = 1 << to
            if not (occ & bit):
                moves.append((sq << 6) | to)
            nc = c - 1
            if nc >= 0:
                to = base | nc
                bit = 1 << to
                if (bit & oth) or not (bit & occ):
                    moves.append((sq << 6) | to)
            nc = c + 1
            if nc < 8:
                to = base | nc
                bit = 1 << to
                if (bit & oth) or not (bit & occ):
                    moves.append((sq << 6) | to)
    return moves


def _apply(cur: int, oth: int, d: int, m: int) -> tuple[int, int, bool]:
    frm = m >> 6
    to = m & 63
    fb = 1 << frm
    tb = 1 << to
    cur2 = (cur & ~fb) | tb
    if tb & oth:
        oth2 = oth & ~tb
    else:
        oth2 = oth
    win = ((tb & GOAL_MASK[_didx(d)]) != 0) or oth2 == 0
    return cur2, oth2, win


def _has_winning_move(cur: int, oth: int, d: int) -> bool:
    didx = _didx(d)
    occ = cur | oth
    p = cur & ONE_STEP[didx]
    if not p:
        return False
    if didx == 1:
        straight = ((p << 8) & FULL) & ~occ
        diag = ((((p & NOT_H) << 9) | ((p & NOT_A) << 7)) & FULL) & ~cur
        return ((straight | diag) & ROW7) != 0
    straight = (p >> 8) & ~occ
    diag = ((((p & NOT_H) >> 7) | ((p & NOT_A) >> 9)) & FULL) & ~cur
    return ((straight | diag) & ROW0) != 0


def _has_any_move(cur: int, oth: int, d: int) -> bool:
    didx = _didx(d)
    occ = cur | oth
    if didx == 1:
        straight = ((cur << 8) & FULL) & ~occ
        diag = ((((cur & NOT_H) << 9) | ((cur & NOT_A) << 7)) & FULL) & ~cur
    else:
        straight = (cur >> 8) & ~occ
        diag = ((((cur & NOT_H) >> 7) | ((cur & NOT_A) >> 9)) & FULL) & ~cur
    return (straight | diag) != 0


def _side_score(bits: int, enemy: int, didx: int, self_att: int, enemy_att: int) -> int:
    occ = bits | enemy
    score = _popcount(bits) * PIECE
    adv = 0
    adv2 = 0
    best = -1

    b = bits
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb

        prog = PROG[didx][sq]
        p1 = prog + 1
        adv += prog
        adv2 += prog * prog
        if prog > best:
            best = prog
        score += CENTER[sq & 7] * CENTER_W

        if (enemy & FWD_SPAN[didx][sq]) == 0:
            if (occ & STRAIGHT[didx][sq]) == 0:
                score += RUNNER_CLEAR_BASE + RUNNER_CLEAR_PROG * p1 * p1
            else:
                score += RUNNER_BLOCK_BASE + RUNNER_BLOCK_PROG * p1 * p1

        if lsb & enemy_att:
            if lsb & self_att:
                score -= HANG_DEF_BASE + prog * 8
            else:
                score -= HANG_UNDEF_BASE + HANG_UNDEF_PROG * prog
        elif lsb & self_att:
            score += SUPPORT_BASE + SUPPORT_PROG * prog

    score += adv * ADV_W + adv2 * ADV_SQ_W
    if best >= 0:
        score += best * BEST_W + best * best * BEST_SQ_W
    return score


def _evaluate(cur: int, oth: int, d: int) -> int:
    if cur == 0:
        return WIN_SCORE if oth == 0 else -WIN_SCORE
    if oth == 0:
        return WIN_SCORE
    didx = _didx(d)
    od = 1 - didx
    ca = _attack_map(cur, didx)
    oa = _attack_map(oth, od)
    return _side_score(cur, oth, didx, ca, oa) - _side_score(oth, cur, od, oa, ca)


def _order_moves(moves: list[int], cur: int, oth: int, d: int, tt_move: int, ply: int) -> list[int]:
    didx = _didx(d)
    od = 1 - didx
    occ = cur | oth
    opp_att = _attack_map(oth, od)
    if ply < len(KILLERS):
        k0, k1 = KILLERS[ply]
    else:
        k0 = k1 = -1

    scored = []
    for m in moves:
        frm = m >> 6
        to = m & 63
        fb = 1 << frm
        tb = 1 << to
        prog_to = PROG[didx][to]
        score = 0

        if m == tt_move:
            score += 20_000_000
        if tb & GOAL_MASK[didx]:
            score += 15_000_000

        if tb & oth:
            eprog = PROG[od][to]
            score += 2_000_000 + 1200 + eprog * 180 + eprog * eprog * 35 + CENTER[to & 7] * 25
            if (cur & FWD_SPAN[od][to]) == 0 and (occ & STRAIGHT[od][to]) == 0:
                score += 3_000_000 + eprog * eprog * 120
            oth2 = oth & ~tb
            if tb & _attack_map(oth2, od):
                if tb & _attack_map(cur & ~fb, didx):
                    score -= 120 + prog_to * 20
                else:
                    score -= 550 + prog_to * 90
        else:
            score += 1000 + prog_to * 25 + (CENTER[to & 7] - CENTER[frm & 7]) * 35
            if (oth & FWD_SPAN[didx][frm]) == 0:
                p1 = prog_to + 1
                if (occ & STRAIGHT[didx][frm]) == 0:
                    score += 180_000 + p1 * p1 * 7000
                else:
                    score += 45_000 + p1 * p1 * 1000
            if tb & opp_att:
                if tb & _attack_map(cur & ~fb, didx):
                    score -= 90 + prog_to * 15
                else:
                    score -= 800 + prog_to * 130
            elif tb & _attack_map(cur & ~fb, didx):
                score += 50 + prog_to * 8

        if m == k0:
            score += 120_000
        elif m == k1:
            score += 90_000
        h = HISTORY.get((didx, frm, to))
        if h:
            score += h if h < 200_000 else 200_000

        scored.append((score, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _search(cur: int, oth: int, d: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout

    if cur == 0:
        return -WIN_SCORE
    if oth == 0:
        return WIN_SCORE

    key = (cur, oth, d)
    tt_move = -1
    ent = TT.get(key)
    if ent is not None:
        ed, ev, flag, bm = ent
        if ed >= depth:
            if flag == EXACT:
                return ev
            if flag == LOWER:
                if ev > alpha:
                    alpha = ev
            else:
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev
        tt_move = bm

    if depth <= 0:
        if _has_winning_move(cur, oth, d):
            return WIN_SCORE
        if not _has_any_move(cur, oth, d):
            return -WIN_SCORE
        return _evaluate(cur, oth, d)

    moves = _gen_moves(cur, oth, d)
    if not moves:
        return -WIN_SCORE
    moves = _order_moves(moves, cur, oth, d, tt_move, ply)

    best = -INF
    bm = moves[0]
    a0 = alpha
    b0 = beta

    for m in moves:
        cur2, oth2, win = _apply(cur, oth, d, m)
        if win:
            val = WIN_SCORE
        else:
            val = -_search(oth2, cur2, -d, depth - 1, -beta, -alpha, ply + 1)

        if val > best:
            best = val
            bm = m
        if val > alpha:
            alpha = val
            if alpha >= beta:
                if ((1 << (m & 63)) & oth) == 0:
                    if ply < len(KILLERS):
                        if KILLERS[ply][0] != m:
                            KILLERS[ply][1] = KILLERS[ply][0]
                            KILLERS[ply][0] = m
                    hk = (_didx(d), m >> 6, m & 63)
                    HISTORY[hk] = HISTORY.get(hk, 0) + depth * depth
                break

    if best <= a0:
        flag = UPPER
    elif best >= b0:
        flag = LOWER
    else:
        flag = EXACT
    TT[key] = (depth, best, flag, bm)
    return best


def _root_search(cur: int, oth: int, d: int, depth: int) -> tuple[int, int]:
    global NODES
    key = (cur, oth, d)
    ent = TT.get(key)
    tt_move = ent[3] if ent is not None else -1

    moves = _gen_moves(cur, oth, d)
    if not moves:
        return -WIN_SCORE, -1
    moves = _order_moves(moves, cur, oth, d, tt_move, 0)

    best = -INF
    bm = moves[0]
    alpha = -INF
    beta = INF

    for m in moves:
        if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
            raise SearchTimeout
        cur2, oth2, win = _apply(cur, oth, d, m)
        if win:
            val = WIN_SCORE
        else:
            val = -_search(oth2, cur2, -d, depth - 1, -beta, -alpha, 1)
        if val > best:
            best = val
            bm = m
        if val > alpha:
            alpha = val

    TT[key] = (depth, best, EXACT, bm)
    return best, bm


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODES, KILLERS, HISTORY, TT

    DEADLINE = time.perf_counter() + 0.92
    NODES = 0
    KILLERS = [[-1, -1] for _ in range(128)]
    HISTORY = {}
    if len(TT) > 300_000:
        TT.clear()

    d = 1 if (color == "w" or color == "W") else -1
    cur = 0
    for r, c in me:
        cur |= 1 << ((r << 3) | c)
    oth = 0
    for r, c in opp:
        oth |= 1 << ((r << 3) | c)

    moves = _gen_moves(cur, oth, d)
    if not moves:
        # No legal move should occur in normal Breakthrough. This is only a last-resort fallback.
        if me:
            r, c = me[0]
            nr = r + d
            if 0 <= nr < 8:
                return ((r, c), (nr, c))
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    # Never miss an immediate win.
    for m in moves:
        _, _, win = _apply(cur, oth, d, m)
        if win:
            frm = m >> 6
            to = m & 63
            return ((frm >> 3, frm & 7), (to >> 3, to & 7))

    ent = TT.get((cur, oth, d))
    tt_move = ent[3] if ent is not None else -1
    ordered = _order_moves(moves, cur, oth, d, tt_move, 0)
    best_m = ordered[0]

    total = _popcount(cur) + _popcount(oth)
    if total <= 10:
        max_depth = 9
    elif total <= 16:
        max_depth = 8
    elif total <= 24:
        max_depth = 7
    else:
        max_depth = 6

    best_score = -INF
    for depth in range(1, max_depth + 1):
        if time.perf_counter() > DEADLINE:
            break
        try:
            score, m = _root_search(cur, oth, d, depth)
        except SearchTimeout:
            break
        best_score = score
        best_m = m
        if best_score >= WIN_SCORE:
            break

    frm = best_m >> 6
    to = best_m & 63
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))
