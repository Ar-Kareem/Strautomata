
from __future__ import annotations

import time

_INF = 10**9
_WIN = 10**7

_EXACT = 0
_LOWER = 1
_UPPER = 2

_BIT = [1 << i for i in range(64)]
_ROW = [i >> 3 for i in range(64)]
_COL = [i & 7 for i in range(64)]

_FWD = [[-1] * 64 for _ in range(2)]
_DIAG = [[() for _ in range(64)] for _ in range(2)]
_FRONT_DIAG_MASK = [[0] * 64 for _ in range(2)]
_BACK_DIAG_MASK = [[0] * 64 for _ in range(2)]
_FRONT_CONE_MASK = [[0] * 64 for _ in range(2)]
_PROGRESS = [[0] * 64 for _ in range(2)]
_DIST = [[0] * 64 for _ in range(2)]
_GOAL_MASK = [0, 0]
_SIDE_MASK = [0] * 64

_CENTER = [4, 10, 16, 22, 22, 16, 10, 4]
_ADVANCE = [0, 8, 22, 45, 80, 130, 220, 0]
_PASSED = [0, 1400, 650, 360, 210, 120, 65, 25]
_MATERIAL = 175

for k, d in enumerate((1, -1)):
    goal = 7 if d == 1 else 0
    gm = 0
    for c in range(8):
        gm |= _BIT[goal * 8 + c]
    _GOAL_MASK[k] = gm

    for idx in range(64):
        r = _ROW[idx]
        c = _COL[idx]

        prog = r if d == 1 else 7 - r
        _PROGRESS[k][idx] = prog
        _DIST[k][idx] = 7 - prog

        nr = r + d
        if 0 <= nr < 8:
            _FWD[k][idx] = nr * 8 + c
            ds = []
            md = 0
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    ni = nr * 8 + nc
                    ds.append(ni)
                    md |= _BIT[ni]
            _DIAG[k][idx] = tuple(ds)
            _FRONT_DIAG_MASK[k][idx] = md

        br = r - d
        mb = 0
        if 0 <= br < 8:
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    mb |= _BIT[br * 8 + nc]
        _BACK_DIAG_MASK[k][idx] = mb

        cone = 0
        rr = r + d
        while 0 <= rr < 8:
            for dc in (-1, 0, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    cone |= _BIT[rr * 8 + nc]
            rr += d
        _FRONT_CONE_MASK[k][idx] = cone

for idx in range(64):
    r = _ROW[idx]
    c = _COL[idx]
    m = 0
    if c > 0:
        m |= _BIT[r * 8 + c - 1]
    if c < 7:
        m |= _BIT[r * 8 + c + 1]
    _SIDE_MASK[idx] = m


class _Timeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_tt = {}
_max_dir = 1
_min_dir = -1


def _dir_key(d: int) -> int:
    return 0 if d == 1 else 1


def _check_time() -> None:
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() > _deadline:
        raise _Timeout


def _to_bb(pieces) -> int:
    bb = 0
    for r, c in pieces:
        r = int(r)
        c = int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= _BIT[r * 8 + c]
    return bb


def _idx_to_move(m):
    a, b = m
    return ((_ROW[a], _COL[a]), (_ROW[b], _COL[b]))


def _gen_moves(own: int, enemy: int, d: int):
    k = _dir_key(d)
    occ = own | enemy
    moves = []
    b = own
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        b ^= lsb

        f = _FWD[k][idx]
        if f >= 0 and not (occ & _BIT[f]):
            moves.append((idx, f))

        for t in _DIAG[k][idx]:
            if not (own & _BIT[t]):
                moves.append((idx, t))

    return moves


def _apply(own: int, enemy: int, move):
    fr, to = move
    fb = _BIT[fr]
    tb = _BIT[to]
    return ((own ^ fb) | tb, enemy & ~tb)


def _terminal_value(max_bb: int, min_bb: int):
    if min_bb == 0 or (max_bb & _GOAL_MASK[_dir_key(_max_dir)]):
        return _WIN
    if max_bb == 0 or (min_bb & _GOAL_MASK[_dir_key(_min_dir)]):
        return -_WIN
    return None


def _piece_has_goal_move(idx: int, own: int, enemy: int, d: int) -> bool:
    k = _dir_key(d)
    if _DIST[k][idx] != 1:
        return False

    occ = own | enemy
    f = _FWD[k][idx]
    if f >= 0 and not (occ & _BIT[f]):
        return True

    for t in _DIAG[k][idx]:
        if _DIST[k][t] == 0 and not (own & _BIT[t]):
            return True

    return False


def _winning_threat_count(own: int, enemy: int, d: int, limit: int = 3) -> int:
    count = 0
    b = own
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        b ^= lsb
        if _piece_has_goal_move(idx, own, enemy, d):
            count += 1
            if count >= limit:
                return count
    return count


def _has_winning_move(own: int, enemy: int, d: int) -> bool:
    return _winning_threat_count(own, enemy, d, 1) > 0


def _side_score(own: int, enemy: int, d: int):
    k = _dir_key(d)
    score = 0
    best_dist = 99
    threats = 0

    b = own
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        b ^= lsb

        prog = _PROGRESS[k][idx]
        dist = _DIST[k][idx]
        best_dist = min(best_dist, dist)

        score += _ADVANCE[prog] + _CENTER[_COL[idx]]

        protect = own & _BACK_DIAG_MASK[k][idx]
        if protect:
            score += (22 + 4 * prog) * protect.bit_count()

        if own & _SIDE_MASK[idx]:
            score += 8

        attack = enemy & _FRONT_DIAG_MASK[k][idx]
        if attack:
            n = attack.bit_count()
            score += 18 * n
            if protect:
                score -= 10 * n
            else:
                score -= (55 + 8 * prog) * n

        if (enemy & _FRONT_CONE_MASK[k][idx]) == 0:
            score += _PASSED[dist]
            if protect:
                score += 35 + 10 * prog
            if dist <= 3:
                score += (4 - dist) * 60

        if dist == 1 and _piece_has_goal_move(idx, own, enemy, d):
            threats += 1
            score += 900

    return score, best_dist, threats


def _evaluate(max_bb: int, min_bb: int, side_to_move: int) -> int:
    tv = _terminal_value(max_bb, min_bb)
    if tv is not None:
        return tv

    max_count = max_bb.bit_count()
    min_count = min_bb.bit_count()

    max_s, max_dist, max_thr = _side_score(max_bb, min_bb, _max_dir)
    min_s, min_dist, min_thr = _side_score(min_bb, max_bb, _min_dir)

    score = _MATERIAL * (max_count - min_count)
    score += max_s - min_s
    score += 75 * (min_dist - max_dist)
    score += 12 if side_to_move == 0 else -12

    if side_to_move == 0 and max_thr:
        return _WIN // 2 + 1000 * max_thr + score
    if side_to_move == 1 and min_thr:
        return -_WIN // 2 - 1000 * min_thr + score

    if max_thr:
        score += 2500 + 800 * (max_thr - 1)
    if min_thr:
        score -= 2500 + 800 * (min_thr - 1)

    return int(score)


def _move_score(move, own: int, enemy: int, d: int) -> int:
    fr, to = move
    k = _dir_key(d)
    ok = _dir_key(-d)
    fb = _BIT[fr]
    tb = _BIT[to]

    if _DIST[k][to] == 0:
        return 10_000_000 + (1000 if (enemy & tb) else 0)

    score = 0
    if enemy & tb:
        score += 700 + 35 * _PROGRESS[ok][to]
        if (enemy & ~tb) == 0:
            score += 9_000_000
    else:
        score += 20

    prog = _PROGRESS[k][to]
    dist = _DIST[k][to]
    score += 25 * prog + _CENTER[_COL[to]]

    if dist == 1:
        score += 1500

    new_own = (own ^ fb) | tb
    new_enemy = enemy & ~tb

    protect = new_own & _BACK_DIAG_MASK[k][to]
    attack = new_enemy & _FRONT_DIAG_MASK[k][to]

    if protect:
        score += 80 + 5 * prog

    if attack:
        if protect:
            score -= 20
        else:
            score -= 160 + 10 * prog

    if (new_enemy & _FRONT_CONE_MASK[k][to]) == 0:
        score += _PASSED[dist]

    return score


def _ordered_moves(moves, own: int, enemy: int, d: int, tt_move=None):
    if len(moves) <= 1:
        return moves[:]

    if tt_move is None:
        return sorted(moves, key=lambda m: _move_score(m, own, enemy, d), reverse=True)

    return sorted(
        moves,
        key=lambda m: (1_000_000_000 if m == tt_move else 0) + _move_score(m, own, enemy, d),
        reverse=True,
    )


def _store_tt(key, depth: int, value: int, alpha0: int, beta0: int, best) -> None:
    if value <= alpha0:
        flag = _UPPER
    elif value >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_tt) < 400000:
        _tt[key] = (depth, value, flag, best)


def _max_value(max_bb: int, min_bb: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    tv = _terminal_value(max_bb, min_bb)
    if tv is not None:
        return tv

    if depth <= 0:
        return _evaluate(max_bb, min_bb, 0)

    key = (max_bb, min_bb, 0)
    alpha0, beta0 = alpha, beta
    best_hint = None

    entry = _tt.get(key)
    if entry is not None:
        ed, val, flag, best_hint = entry
        if ed >= depth:
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                alpha = max(alpha, val)
            elif flag == _UPPER:
                beta = min(beta, val)
            if alpha >= beta:
                return val

    moves = _gen_moves(max_bb, min_bb, _max_dir)
    if not moves:
        return -_WIN

    moves = _ordered_moves(moves, max_bb, min_bb, _max_dir, best_hint)

    value = -_INF
    best = moves[0]
    goal_mask = _GOAL_MASK[_dir_key(_max_dir)]

    for m in moves:
        max2, min2 = _apply(max_bb, min_bb, m)

        if min2 == 0 or (_BIT[m[1]] & goal_mask):
            child = _WIN
        else:
            child = _min_value(max2, min2, depth - 1, alpha, beta)

        if child > value:
            value = child
            best = m

        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    _store_tt(key, depth, value, alpha0, beta0, best)
    return value


def _min_value(max_bb: int, min_bb: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    tv = _terminal_value(max_bb, min_bb)
    if tv is not None:
        return tv

    if depth <= 0:
        return _evaluate(max_bb, min_bb, 1)

    key = (max_bb, min_bb, 1)
    alpha0, beta0 = alpha, beta
    best_hint = None

    entry = _tt.get(key)
    if entry is not None:
        ed, val, flag, best_hint = entry
        if ed >= depth:
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                alpha = max(alpha, val)
            elif flag == _UPPER:
                beta = min(beta, val)
            if alpha >= beta:
                return val

    moves = _gen_moves(min_bb, max_bb, _min_dir)
    if not moves:
        return _WIN

    moves = _ordered_moves(moves, min_bb, max_bb, _min_dir, best_hint)

    value = _INF
    best = moves[0]
    goal_mask = _GOAL_MASK[_dir_key(_min_dir)]

    for m in moves:
        min2, max2 = _apply(min_bb, max_bb, m)

        if max2 == 0 or (_BIT[m[1]] & goal_mask):
            child = -_WIN
        else:
            child = _max_value(max2, min2, depth - 1, alpha, beta)

        if child < value:
            value = child
            best = m

        if value < beta:
            beta = value
        if alpha >= beta:
            break

    _store_tt(key, depth, value, alpha0, beta0, best)
    return value


def _search_root(max_bb: int, min_bb: int, root_moves, depth: int, previous_best):
    _check_time()

    moves = _ordered_moves(root_moves, max_bb, min_bb, _max_dir, previous_best)

    best_move = moves[0]
    best_value = -_INF
    alpha = -_INF
    beta = _INF
    goal_mask = _GOAL_MASK[_dir_key(_max_dir)]

    for m in moves:
        max2, min2 = _apply(max_bb, min_bb, m)

        if min2 == 0 or (_BIT[m[1]] & goal_mask):
            value = _WIN
        else:
            value = _min_value(max2, min2, depth - 1, alpha, beta)

        if value > best_value:
            best_value = value
            best_move = m

        if best_value > alpha:
            alpha = best_value

    return best_value, best_move


def _emergency_move(me, opp, color):
    d = -1 if color == "b" else 1
    mine = {(int(r), int(c)) for r, c in me}
    theirs = {(int(r), int(c)) for r, c in opp}

    for r, c in mine:
        nr = r + d
        if 0 <= nr < 8:
            if (nr, c) not in mine and (nr, c) not in theirs:
                return ((r, c), (nr, c))
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8 and (nr, nc) not in mine:
                    return ((r, c), (nr, nc))

    if me:
        r, c = me[0]
        return ((int(r), int(c)), (int(r), int(c)))
    return ((0, 0), (0, 0))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _deadline, _nodes, _tt, _max_dir, _min_dir

    _deadline = time.perf_counter() + 0.85
    _nodes = 0
    _tt = {}

    _max_dir = -1 if color == "b" else 1
    _min_dir = -_max_dir

    max_bb = _to_bb(me)
    min_bb = _to_bb(opp)

    root_moves = _gen_moves(max_bb, min_bb, _max_dir)
    if not root_moves:
        return _emergency_move(me, opp, color)

    root_moves = _ordered_moves(root_moves, max_bb, min_bb, _max_dir)

    goal_mask = _GOAL_MASK[_dir_key(_max_dir)]

    for m in root_moves:
        max2, min2 = _apply(max_bb, min_bb, m)
        if min2 == 0 or (_BIT[m[1]] & goal_mask):
            return _idx_to_move(m)

    if _has_winning_move(min_bb, max_bb, _min_dir):
        safe = []
        for m in root_moves:
            max2, min2 = _apply(max_bb, min_bb, m)
            if not _has_winning_move(min2, max2, _min_dir):
                safe.append(m)
        if safe:
            root_moves = safe

    if len(root_moves) == 1:
        return _idx_to_move(root_moves[0])

    completed_best = root_moves[0]
    total_pieces = max_bb.bit_count() + min_bb.bit_count()

    if total_pieces <= 6:
        max_depth = 11
    elif total_pieces <= 10:
        max_depth = 10
    elif total_pieces <= 16:
        max_depth = 8
    elif total_pieces <= 24:
        max_depth = 7
    else:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _deadline:
                break

            value, best = _search_root(max_bb, min_bb, root_moves, depth, completed_best)
            completed_best = best

            if value >= _WIN or value <= -_WIN:
                break

            if _deadline - time.perf_counter() < 0.012:
                break

    except _Timeout:
        pass

    return _idx_to_move(completed_best)
