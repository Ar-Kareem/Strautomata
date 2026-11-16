
from __future__ import annotations

import time


# Directions: black moves toward lower rows, white toward higher rows.
# Index order is used by the precomputed adjacency tables.
_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
_B_MAN_DIRS = (0, 1)
_W_MAN_DIRS = (2, 3)
_KING_DIRS = (0, 1, 2, 3)

_INF = 10**9
_WIN = 10**7


_ADJ = [[-1] * 64 for _ in range(4)]
_LAND = [[-1] * 64 for _ in range(4)]

for sq in range(64):
    r, c = divmod(sq, 8)
    for i, (dr, dc) in enumerate(_DIRS):
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            _ADJ[i][sq] = nr * 8 + nc
        lr, lc = r + 2 * dr, c + 2 * dc
        if 0 <= lr < 8 and 0 <= lc < 8:
            _LAND[i][sq] = lr * 8 + lc


class _SearchTimeout(Exception):
    pass


def _other_color(color):
    return "w" if color == "b" else "b"


def _to_mask(pieces):
    mask = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            mask |= 1 << (r * 8 + c)
    return mask


def _promotes(color, sq):
    r = sq >> 3
    return r == 0 if color == "b" else r == 7


def _generate(side_men, side_kings, enemy_men, enemy_kings, color):
    """Return legal moves for one side. Captures are mandatory.

    Move tuple: (from_sq, to_sq, captured_sq_or_-1, moving_piece_is_king)
    """
    occ = side_men | side_kings | enemy_men | enemy_kings
    enemy_occ = enemy_men | enemy_kings
    man_dirs = _B_MAN_DIRS if color == "b" else _W_MAN_DIRS

    captures = []

    m = side_men
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb
        for d in man_dirs:
            adj = _ADJ[d][sq]
            land = _LAND[d][sq]
            if adj >= 0 and land >= 0:
                if (enemy_occ & (1 << adj)) and not (occ & (1 << land)):
                    captures.append((sq, land, adj, 0))

    k = side_kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb
        for d in _KING_DIRS:
            adj = _ADJ[d][sq]
            land = _LAND[d][sq]
            if adj >= 0 and land >= 0:
                if (enemy_occ & (1 << adj)) and not (occ & (1 << land)):
                    captures.append((sq, land, adj, 1))

    if captures:
        return captures, True

    moves = []

    m = side_men
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb
        for d in man_dirs:
            to_sq = _ADJ[d][sq]
            if to_sq >= 0 and not (occ & (1 << to_sq)):
                moves.append((sq, to_sq, -1, 0))

    k = side_kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb
        for d in _KING_DIRS:
            to_sq = _ADJ[d][sq]
            if to_sq >= 0 and not (occ & (1 << to_sq)):
                moves.append((sq, to_sq, -1, 1))

    return moves, False


def _legal_for_state(state, side, root_color):
    rm, rk, om, ok = state
    if side == 0:
        return _generate(rm, rk, om, ok, root_color)
    return _generate(om, ok, rm, rk, _other_color(root_color))


def _apply_move(state, side, move, root_color):
    rm, rk, om, ok = state
    frm, to, cap, is_king = move
    fb = 1 << frm
    tb = 1 << to

    if side == 0:
        color = root_color

        if is_king:
            rk = (rk & ~fb) | tb
        else:
            rm &= ~fb
            if _promotes(color, to):
                rk |= tb
            else:
                rm |= tb

        if cap >= 0:
            cb = 1 << cap
            if om & cb:
                om &= ~cb
            else:
                ok &= ~cb

    else:
        color = _other_color(root_color)

        if is_king:
            ok = (ok & ~fb) | tb
        else:
            om &= ~fb
            if _promotes(color, to):
                ok |= tb
            else:
                om |= tb

        if cap >= 0:
            cb = 1 << cap
            if rm & cb:
                rm &= ~cb
            else:
                rk &= ~cb

    return rm, rk, om, ok


def _side_score(men, kings, color):
    score = 0

    m = men
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb

        r, c = divmod(sq, 8)
        progress = 7 - r if color == "b" else r

        score += 100
        score += progress * 7

        # Men near promotion become tactically valuable.
        if progress >= 5:
            score += (progress - 4) * 10

        # Edge men are harder to capture; central men are flexible.
        if c == 0 or c == 7:
            score += 4
        elif 2 <= c <= 5:
            score += 4

        # Home-row men can stop enemy kings from invading.
        if (color == "b" and r == 7) or (color == "w" and r == 0):
            score += 6

    k = kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb

        r, c = divmod(sq, 8)
        score += 182

        # Kings like central mobility, but edges can be safe.
        center_dist = abs(3.5 - r) + abs(3.5 - c)
        score += int(18 - 3 * center_dist)
        if c == 0 or c == 7:
            score += 2

    return score


def _evaluate(state, root_color):
    rm, rk, om, ok = state
    opp_color = _other_color(root_color)

    score = _side_score(rm, rk, root_color) - _side_score(om, ok, opp_color)

    root_units = rm.bit_count() + 2 * rk.bit_count()
    opp_units = om.bit_count() + 2 * ok.bit_count()
    material_diff = root_units - opp_units

    total_pieces = rm.bit_count() + rk.bit_count() + om.bit_count() + ok.bit_count()

    # If ahead, prefer simplification; if behind, prefer keeping complexity.
    score += material_diff * (24 - total_pieces) * 2

    my_moves, my_cap = _generate(rm, rk, om, ok, root_color)
    op_moves, op_cap = _generate(om, ok, rm, rk, opp_color)

    if not my_moves:
        score -= _WIN // 2
    if not op_moves:
        score += _WIN // 2

    score += 3 * (len(my_moves) - len(op_moves))

    if my_cap:
        score += 45 + 8 * len(my_moves)
    if op_cap:
        score -= 45 + 8 * len(op_moves)

    return score


def _move_order_score(move, state, side, root_color, preferred=None):
    if preferred is not None and move == preferred:
        base = 100000000
    else:
        base = 0

    rm, rk, om, ok = state
    frm, to, cap, is_king = move

    moving_color = root_color if side == 0 else _other_color(root_color)

    if side == 0:
        enemy_men, enemy_kings = om, ok
    else:
        enemy_men, enemy_kings = rm, rk

    score = base

    if cap >= 0:
        cb = 1 << cap
        score += 100000
        score += 6000 if (enemy_kings & cb) else 3000
        if not is_king:
            score += 150

    if not is_king and _promotes(moving_color, to):
        score += 25000

    r, c = divmod(to, 8)

    if not is_king:
        progress = 7 - r if moving_color == "b" else r
        score += progress * 50
        if c == 0 or c == 7:
            score += 25
        elif 2 <= c <= 5:
            score += 18
    else:
        center_dist = abs(3.5 - r) + abs(3.5 - c)
        score += int(80 - 10 * center_dist)

    return score


def _ordered_moves(moves, state, side, root_color, preferred=None):
    if len(moves) <= 1:
        return moves
    return sorted(
        moves,
        key=lambda mv: _move_order_score(mv, state, side, root_color, preferred),
        reverse=True,
    )


def _fallback_move(my_men, my_kings):
    # This should only be used in terminal positions where no legal move exists.
    # The arena should normally not request a move then, but return a shaped tuple.
    if my_men:
        p = my_men[0]
        return (p, p)
    if my_kings:
        p = my_kings[0]
        return (p, p)
    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    if color not in ("b", "w"):
        color = "b"

    start_time = time.perf_counter()
    deadline = start_time + 0.86

    rm = _to_mask(my_men)
    rk = _to_mask(my_kings)
    om = _to_mask(opp_men)
    ok = _to_mask(opp_kings)

    state = (rm, rk, om, ok)

    root_moves, _ = _generate(rm, rk, om, ok, color)
    if not root_moves:
        return _fallback_move(my_men, my_kings)

    root_moves = _ordered_moves(root_moves, state, 0, color)
    best_move = root_moves[0]

    total_pieces = rm.bit_count() + rk.bit_count() + om.bit_count() + ok.bit_count()
    if total_pieces <= 6:
        max_depth = 10
    elif total_pieces <= 10:
        max_depth = 8
    elif total_pieces <= 16:
        max_depth = 7
    else:
        max_depth = 6

    tt = {}
    nodes = 0

    def search(pos, side, depth, alpha, beta, qleft):
        nonlocal nodes

        nodes += 1
        if (nodes & 2047) == 0 and time.perf_counter() > deadline:
            raise _SearchTimeout()

        key = (pos[0], pos[1], pos[2], pos[3], side, depth, qleft)
        entry = tt.get(key)
        tt_move = None

        if entry is not None:
            flag, val, stored_move = entry
            tt_move = stored_move
            if flag == 0:
                return val
            if flag == 1:
                alpha = max(alpha, val)
            elif flag == 2:
                beta = min(beta, val)
            if alpha >= beta:
                return val

        moves, has_capture = _legal_for_state(pos, side, color)

        if not moves:
            return -_WIN - depth if side == 0 else _WIN + depth

        if depth <= 0:
            if not (has_capture and qleft > 0):
                return _evaluate(pos, color)
            next_depth = 0
            next_q = qleft - 1
        else:
            next_depth = depth - 1
            next_q = qleft

        orig_alpha = alpha
        orig_beta = beta
        best_local = None

        ordered = _ordered_moves(moves, pos, side, color, tt_move)

        if side == 0:
            value = -_INF
            for mv in ordered:
                child = _apply_move(pos, side, mv, color)
                sc = search(child, 1, next_depth, alpha, beta, next_q)
                if sc > value:
                    value = sc
                    best_local = mv
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
        else:
            value = _INF
            for mv in ordered:
                child = _apply_move(pos, side, mv, color)
                sc = search(child, 0, next_depth, alpha, beta, next_q)
                if sc < value:
                    value = sc
                    best_local = mv
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

        if value <= orig_alpha:
            flag = 2  # upper bound
        elif value >= orig_beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact

        if len(tt) < 200000:
            tt[key] = (flag, value, best_local)

        return value

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            alpha = -_INF
            beta = _INF
            depth_best = best_move
            depth_best_score = -_INF

            ordered_root = _ordered_moves(root_moves, state, 0, color, best_move)

            for mv in ordered_root:
                if time.perf_counter() > deadline:
                    raise _SearchTimeout()

                child = _apply_move(state, 0, mv, color)
                sc = search(child, 1, depth - 1, alpha, beta, 2)

                if sc > depth_best_score:
                    depth_best_score = sc
                    depth_best = mv

                if sc > alpha:
                    alpha = sc

            best_move = depth_best

    except _SearchTimeout:
        pass

    frm, to = best_move[0], best_move[1]
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))
