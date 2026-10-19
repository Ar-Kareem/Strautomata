
from __future__ import annotations

import time


# ----------------------------- Bitboard constants -----------------------------

_FULL_MASK = (1 << 64) - 1
_FILE_A = 0x0101010101010101
_FILE_H = 0x8080808080808080
_NOT_FILE_A = _FULL_MASK ^ _FILE_A
_NOT_FILE_H = _FULL_MASK ^ _FILE_H

_BIT = [1 << i for i in range(64)]
_ROW = [i >> 3 for i in range(64)]
_COL = [i & 7 for i in range(64)]

_ROW_MASKS = [0] * 8
for _r in range(8):
    _m = 0
    for _c in range(8):
        _m |= 1 << ((_r << 3) | _c)
    _ROW_MASKS[_r] = _m

# Direction index: 0 => black-like/downward/-1, 1 => white-like/upward/+1
_GOAL_MASK = [_ROW_MASKS[0], _ROW_MASKS[7]]
_PREGOAL_MASK = [_ROW_MASKS[1], _ROW_MASKS[6]]

_FWD = [[-1] * 64 for _ in range(2)]
_DL = [[-1] * 64 for _ in range(2)]
_DR = [[-1] * 64 for _ in range(2)]
_PRED_MASK = [[0] * 64 for _ in range(2)]
_FRONT_SPAN = [[0] * 64 for _ in range(2)]
_FRONT_CONE = [[0] * 64 for _ in range(2)]
_PROGRESS = [[0] * 64 for _ in range(2)]
_DIST = [[0] * 64 for _ in range(2)]
_PST = [[0] * 64 for _ in range(2)]
_CENTER_ORDER = [0] * 64

_PROGRESS_VALUE = [0, 8, 24, 52, 95, 165, 300, 5000]
_CENTER_EVAL = [0, 4, 9, 13, 13, 9, 4, 0]
_CENTER_MOVE = [0, 20, 45, 65, 65, 45, 20, 0]

for _sq in range(64):
    _r = _sq >> 3
    _c = _sq & 7
    _CENTER_ORDER[_sq] = _CENTER_MOVE[_c]

    for _idx, _d in enumerate((-1, 1)):
        _nr = _r + _d
        if 0 <= _nr < 8:
            _FWD[_idx][_sq] = (_nr << 3) | _c
            if _c > 0:
                _DL[_idx][_sq] = (_nr << 3) | (_c - 1)
            if _c < 7:
                _DR[_idx][_sq] = (_nr << 3) | (_c + 1)

        # Squares from which a piece moving in direction _d attacks _sq.
        _pr = _r - _d
        _pm = 0
        if 0 <= _pr < 8:
            if _c > 0:
                _pm |= 1 << ((_pr << 3) | (_c - 1))
            if _c < 7:
                _pm |= 1 << ((_pr << 3) | (_c + 1))
        _PRED_MASK[_idx][_sq] = _pm

        _span = 0
        _cone = 0
        _rr = _r + _d
        _step = 1
        while 0 <= _rr < 8:
            for _cc in range(max(0, _c - 1), min(7, _c + 1) + 1):
                _span |= 1 << ((_rr << 3) | _cc)
            for _cc in range(max(0, _c - _step), min(7, _c + _step) + 1):
                _cone |= 1 << ((_rr << 3) | _cc)
            _rr += _d
            _step += 1
        _FRONT_SPAN[_idx][_sq] = _span
        _FRONT_CONE[_idx][_sq] = _cone

        _prog = _r if _d == 1 else 7 - _r
        _PROGRESS[_idx][_sq] = _prog
        _DIST[_idx][_sq] = 7 - _prog
        _PST[_idx][_sq] = _PROGRESS_VALUE[_prog] + _CENTER_EVAL[_c]


# ------------------------------- Search globals -------------------------------

_WIN = 10_000_000
_TT_LIMIT = 250_000
_MAX_EXTENSION_PLY = 10

_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0
_KILLERS = [[-1, -1] for _ in range(80)]
_HISTORY = [0] * 4096


class _Timeout(Exception):
    pass


# ------------------------------ Basic utilities -------------------------------

def _dir_index(direction: int) -> int:
    return 1 if direction > 0 else 0


def _to_bb(pieces: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << ((r << 3) | c)
    return bb


def _decode(move: int) -> tuple[tuple[int, int], tuple[int, int]]:
    frm = move >> 6
    to = move & 63
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def _make_move(me: int, opp: int, move: int) -> tuple[int, int]:
    frm = move >> 6
    to = move & 63
    tb = _BIT[to]
    return ((me ^ _BIT[frm]) | tb, opp & ~tb)


def _attacks(bb: int, direction: int) -> int:
    if direction > 0:
        return ((((bb & _NOT_FILE_A) << 7) | ((bb & _NOT_FILE_H) << 9)) & _FULL_MASK)
    return (((bb & _NOT_FILE_A) >> 9) | ((bb & _NOT_FILE_H) >> 7))


# ------------------------------ Immediate tactics -----------------------------

def _find_winning_move(me: int, opp: int, direction: int) -> int:
    """Return a legal move reaching the goal row, or -1."""
    di = _dir_index(direction)
    x = me & _PREGOAL_MASK[di]
    if not x:
        return -1

    occ = me | opp
    fwd = _FWD[di]
    dl = _DL[di]
    dr = _DR[di]
    quiet_win = -1

    while x:
        lsb = x & -x
        frm = lsb.bit_length() - 1
        x ^= lsb

        to = dl[frm]
        if to != -1:
            tb = _BIT[to]
            if not (me & tb):
                move = (frm << 6) | to
                if opp & tb:
                    return move
                if quiet_win == -1:
                    quiet_win = move

        to = dr[frm]
        if to != -1:
            tb = _BIT[to]
            if not (me & tb):
                move = (frm << 6) | to
                if opp & tb:
                    return move
                if quiet_win == -1:
                    quiet_win = move

        to = fwd[frm]
        if to != -1:
            tb = _BIT[to]
            if not (occ & tb):
                if quiet_win == -1:
                    quiet_win = (frm << 6) | to

    return quiet_win


def _find_finishing_capture(me: int, opp: int, direction: int) -> int:
    """Return a legal capture of the last enemy piece, or -1."""
    if opp == 0 or (opp & (opp - 1)) != 0:
        return -1
    target = opp.bit_length() - 1
    di = _dir_index(direction)
    attackers = me & _PRED_MASK[di][target]
    if attackers:
        frm = (attackers & -attackers).bit_length() - 1
        return (frm << 6) | target
    return -1


def _find_immediate_win(me: int, opp: int, direction: int) -> int:
    move = _find_winning_move(me, opp, direction)
    if move != -1:
        return move
    return _find_finishing_capture(me, opp, direction)


# ------------------------------ Move generation -------------------------------

def _ordered_moves(me: int, opp: int, direction: int, tt_move: int = -1, ply: int = 0) -> list[int]:
    di = _dir_index(direction)
    odi = 1 - di
    occ = me | opp

    fwd = _FWD[di]
    dl = _DL[di]
    dr = _DR[di]
    pred_own = _PRED_MASK[di]
    pred_enemy = _PRED_MASK[odi]
    prog = _PROGRESS[di]
    opp_prog = _PROGRESS[odi]
    center = _CENTER_ORDER
    hist = _HISTORY
    bits = _BIT
    goal_mask = _GOAL_MASK[di]

    if ply < len(_KILLERS):
        k0, k1 = _KILLERS[ply]
    else:
        k0, k1 = -1, -1

    opp_single = opp != 0 and (opp & (opp - 1)) == 0
    opp_att = _attacks(opp, -direction)

    scored: list[tuple[int, int]] = []
    x = me

    while x:
        lsb = x & -x
        frm = lsb.bit_length() - 1
        x ^= lsb

        base = frm << 6
        me_wo = me ^ lsb
        from_prog = prog[frm]
        from_threat = bool(lsb & opp_att)

        # Straight non-capturing move.
        to = fwd[frm]
        if to != -1:
            tb = bits[to]
            if not (occ & tb):
                move = base | to
                pto = prog[to]
                score = hist[move] + pto * 220 + center[to]

                if move == tt_move:
                    score += 10_000_000
                elif move == k0:
                    score += 85_000
                elif move == k1:
                    score += 75_000

                if tb & goal_mask:
                    score += 5_000_000
                if pto == 6:
                    score += 32_000
                if from_threat:
                    score += 900 + 80 * from_prog

                defended = bool(me_wo & pred_own[to])
                attacked = bool(opp & pred_enemy[to])
                if attacked:
                    if defended:
                        score -= 250
                    else:
                        score -= 2600 + 280 * pto
                elif defended:
                    score += 650 + 60 * pto

                scored.append((score, move))

        # Diagonal left: empty move or capture.
        to = dl[frm]
        if to != -1:
            tb = bits[to]
            if not (me & tb):
                move = base | to
                pto = prog[to]
                cap = bool(opp & tb)
                score = hist[move] + pto * 230 + center[to] + 250

                if move == tt_move:
                    score += 10_000_000
                elif move == k0:
                    score += 85_000
                elif move == k1:
                    score += 75_000

                if cap:
                    score += 95_000 + opp_prog[to] * 450
                    if opp_single:
                        score += 4_000_000

                if tb & goal_mask:
                    score += 5_000_000
                if pto == 6:
                    score += 36_000
                if from_threat:
                    score += 900 + 80 * from_prog

                defended = bool(me_wo & pred_own[to])
                attacked = bool(opp & pred_enemy[to])
                if attacked:
                    if defended:
                        score -= 150
                        if cap:
                            score += 400
                    else:
                        score -= 2400 + 260 * pto
                else:
                    if defended:
                        score += 700 + 60 * pto
                    if cap:
                        score += 700

                scored.append((score, move))

        # Diagonal right: empty move or capture.
        to = dr[frm]
        if to != -1:
            tb = bits[to]
            if not (me & tb):
                move = base | to
                pto = prog[to]
                cap = bool(opp & tb)
                score = hist[move] + pto * 230 + center[to] + 250

                if move == tt_move:
                    score += 10_000_000
                elif move == k0:
                    score += 85_000
                elif move == k1:
                    score += 75_000

                if cap:
                    score += 95_000 + opp_prog[to] * 450
                    if opp_single:
                        score += 4_000_000

                if tb & goal_mask:
                    score += 5_000_000
                if pto == 6:
                    score += 36_000
                if from_threat:
                    score += 900 + 80 * from_prog

                defended = bool(me_wo & pred_own[to])
                attacked = bool(opp & pred_enemy[to])
                if attacked:
                    if defended:
                        score -= 150
                        if cap:
                            score += 400
                    else:
                        score -= 2400 + 260 * pto
                else:
                    if defended:
                        score += 700 + 60 * pto
                    if cap:
                        score += 700

                scored.append((score, move))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _first_legal_move(me: int, opp: int, direction: int) -> int:
    di = _dir_index(direction)
    occ = me | opp
    x = me
    while x:
        lsb = x & -x
        frm = lsb.bit_length() - 1
        x ^= lsb

        to = _FWD[di][frm]
        if to != -1 and not (occ & _BIT[to]):
            return (frm << 6) | to

        to = _DL[di][frm]
        if to != -1 and not (me & _BIT[to]):
            return (frm << 6) | to

        to = _DR[di][frm]
        if to != -1 and not (me & _BIT[to]):
            return (frm << 6) | to

    return -1


# ------------------------------- Evaluation -----------------------------------

_SPEED_VALUE = [0, 1200, 650, 320, 150, 65, 20, 0]
_RUNNER_VALUE = [0, 1300, 760, 420, 210, 90, 30, 0]
_PASSED_VALUE = [0, 700, 420, 230, 110, 45, 15, 0]


def _sum_pst(bb: int, arr: list[int]) -> int:
    s = 0
    x = bb
    while x:
        lsb = x & -x
        s += arr[lsb.bit_length() - 1]
        x ^= lsb
    return s


def _min_dist(bb: int, di: int) -> int:
    if not bb:
        return 7
    arr = _DIST[di]
    best = 7
    x = bb
    while x:
        lsb = x & -x
        d = arr[lsb.bit_length() - 1]
        if d < best:
            best = d
        x ^= lsb
    return best


def _vulnerability_penalty(pieces: int, enemy_attacks: int, own_attacks: int, di: int) -> int:
    danger = pieces & enemy_attacks
    if not danger:
        return 0

    arr = _PROGRESS[di]
    penalty = 0
    x = danger
    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        p = arr[sq]
        if lsb & own_attacks:
            penalty += 25 + 8 * p
        else:
            penalty += 75 + 18 * p
        x ^= lsb
    return penalty


def _runner_score(pieces: int, enemies: int, direction: int, enemy_min_dist: int) -> int:
    di = _dir_index(direction)
    dist = _DIST[di]
    span = _FRONT_SPAN[di]
    cone = _FRONT_CONE[di]

    score = 0
    x = pieces
    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        x ^= lsb

        d = dist[sq]
        if d <= 0:
            continue

        if not (enemies & cone[sq]):
            bonus = _RUNNER_VALUE[d]
            if d <= enemy_min_dist:
                bonus += 90 * (enemy_min_dist - d + 1)
            score += bonus
        elif not (enemies & span[sq]):
            score += _PASSED_VALUE[d]

    return score


def _mobility_approx(pieces: int, enemies: int, direction: int) -> int:
    occ = pieces | enemies
    if direction > 0:
        straight = ((pieces << 8) & _FULL_MASK) & ~occ
    else:
        straight = (pieces >> 8) & ~occ

    diagonal = _attacks(pieces, direction) & ~pieces
    return straight.bit_count() + diagonal.bit_count()


def _evaluate(me: int, opp: int, direction: int) -> int:
    di = _dir_index(direction)
    odi = 1 - di

    my_count = me.bit_count()
    opp_count = opp.bit_count()

    score = 90 * (my_count - opp_count)
    score += _sum_pst(me, _PST[di]) - _sum_pst(opp, _PST[odi])

    my_min = _min_dist(me, di)
    opp_min = _min_dist(opp, odi)
    score += _SPEED_VALUE[my_min] - _SPEED_VALUE[opp_min]

    # Tempo/race tiebreak: if both fastest pawns are equally close, side to move
    # generally has the race advantage.
    if my_min <= opp_min:
        score += 35
    else:
        score -= 35

    my_att = _attacks(me, direction)
    opp_att = _attacks(opp, -direction)

    my_def = (me & my_att).bit_count()
    opp_def = (opp & opp_att).bit_count()
    score += 18 * (my_def - opp_def)

    score += _vulnerability_penalty(opp, my_att, opp_att, odi)
    score -= _vulnerability_penalty(me, opp_att, my_att, di)

    score += 20 * ((opp & my_att).bit_count() - (me & opp_att).bit_count())

    score += _runner_score(me, opp, direction, opp_min)
    score -= _runner_score(opp, me, -direction, my_min)

    score += 5 * (_mobility_approx(me, opp, direction) - _mobility_approx(opp, me, -direction))

    # Usually handled by the threat extension; retained for very deep extension
    # cutoffs.
    if _find_immediate_win(opp, me, -direction) != -1:
        score -= 5000

    return score


# --------------------------------- Negamax ------------------------------------

def _negamax(me: int, opp: int, direction: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout()

    if me == 0:
        return -_WIN
    if opp == 0:
        return _WIN

    di = _dir_index(direction)
    odi = 1 - di

    if opp & _GOAL_MASK[odi]:
        return -_WIN
    if me & _GOAL_MASK[di]:
        return _WIN

    # Exact tactical wins, even at nominal leaf nodes.
    if _find_immediate_win(me, opp, direction) != -1:
        return _WIN - 1

    # If the opponent has a one-move win threat at the horizon, extend one ply so
    # the search can see whether it can be parried.
    if depth <= 0:
        if ply < _MAX_EXTENSION_PLY and _find_immediate_win(opp, me, -direction) != -1:
            depth = 1
        else:
            return _evaluate(me, opp, direction)

    key = (me, opp, direction)
    tt_move = -1

    entry = _TT.get(key)
    if entry is not None:
        e_depth, e_value, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == _TT_EXACT:
                return e_value
            if e_flag == _TT_LOWER:
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == _TT_UPPER:
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    alpha_start = alpha
    beta_start = beta

    moves = _ordered_moves(me, opp, direction, tt_move, ply)
    if not moves:
        return -_WIN + 1

    best_score = -_WIN
    best_move = moves[0]
    searched = 0

    for move in moves:
        nme, nopp = _make_move(me, opp, move)

        if searched == 0:
            score = -_negamax(nopp, nme, -direction, depth - 1, -beta, -alpha, ply + 1)
        else:
            # Principal variation search.
            score = -_negamax(nopp, nme, -direction, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -_negamax(nopp, nme, -direction, depth - 1, -beta, -alpha, ply + 1)

        searched += 1

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            captured = bool(opp & _BIT[move & 63])
            if not captured and ply < len(_KILLERS):
                k0, _ = _KILLERS[ply]
                if move != k0:
                    _KILLERS[ply][1] = k0
                    _KILLERS[ply][0] = move

            if _HISTORY[move] < 50_000:
                _HISTORY[move] += depth * depth
            break

    if best_score <= alpha_start:
        flag = _TT_UPPER
    elif best_score >= beta_start:
        flag = _TT_LOWER
    else:
        flag = _TT_EXACT

    old = _TT.get(key)
    if old is not None:
        if depth >= old[0]:
            _TT[key] = (depth, best_score, flag, best_move)
    elif len(_TT) < _TT_LIMIT:
        _TT[key] = (depth, best_score, flag, best_move)

    return best_score


# -------------------------------- Root policy ---------------------------------

def _max_depth(total_pieces: int, legal_count: int) -> int:
    if legal_count <= 6 or total_pieces <= 6:
        return 12
    if total_pieces <= 10:
        return 10
    if total_pieces <= 14:
        return 9
    if total_pieces <= 20 or legal_count <= 18:
        return 8
    if total_pieces <= 26:
        return 7
    return 6


def _emergency_return(me: int, opp: int, direction: int) -> tuple[tuple[int, int], tuple[int, int]]:
    move = _first_legal_move(me, opp, direction)
    if move != -1:
        return _decode(move)

    # Should only happen in already-terminal or malformed positions.
    if me:
        sq = (me & -me).bit_length() - 1
        di = _dir_index(direction)
        to = _FWD[di][sq]
        if to != -1:
            return _decode((sq << 6) | to)
        return ((sq >> 3, sq & 7), (sq >> 3, sq & 7))

    return ((0, 0), (0, 0))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _TT, _DEADLINE, _NODES, _KILLERS, _HISTORY

    my_bb = _to_bb(me)
    opp_bb = _to_bb(opp)
    direction = -1 if color == "b" else 1
    di = _dir_index(direction)

    # Never miss a direct win.
    immediate = _find_immediate_win(my_bb, opp_bb, direction)
    if immediate != -1:
        return _decode(immediate)

    _TT = {}
    _NODES = 0
    _KILLERS = [[-1, -1] for _ in range(80)]
    _HISTORY = [0] * 4096
    _DEADLINE = time.perf_counter() + 0.90

    moves = _ordered_moves(my_bb, opp_bb, direction, -1, 0)
    if not moves:
        return _emergency_return(my_bb, opp_bb, direction)

    # If opponent currently has an immediate win threat, prefer only moves that
    # remove all such threats. This also gives a safe fallback if time expires.
    if _find_immediate_win(opp_bb, my_bb, -direction) != -1:
        safe_moves = []
        for move in moves:
            nme, nopp = _make_move(my_bb, opp_bb, move)
            if nopp == 0 or (nme & _GOAL_MASK[di]):
                safe_moves.append(move)
            elif _find_immediate_win(nopp, nme, -direction) == -1:
                safe_moves.append(move)
        if safe_moves:
            moves = safe_moves

    best_move = moves[0]
    best_score = -_WIN
    max_depth = _max_depth((my_bb | opp_bb).bit_count(), len(moves))

    for depth in range(1, max_depth + 1):
        try:
            if time.perf_counter() >= _DEADLINE:
                break

            if best_move in moves:
                root_order = [best_move]
                root_order.extend(m for m in moves if m != best_move)
            else:
                root_order = moves[:]

            alpha = -_WIN
            beta = _WIN
            local_best = root_order[0]
            local_score = -_WIN

            for move in root_order:
                if (_NODES & 1023) == 0 and time.perf_counter() >= _DEADLINE:
                    raise _Timeout()

                nme, nopp = _make_move(my_bb, opp_bb, move)
                score = -_negamax(nopp, nme, -direction, depth - 1, -beta, -alpha, 1)

                if score > local_score:
                    local_score = score
                    local_best = move

                if score > alpha:
                    alpha = score

                if alpha >= _WIN - 1:
                    break

            best_move = local_best
            best_score = local_score

            if best_score >= _WIN - 1:
                break

        except _Timeout:
            break

    return _decode(best_move)
