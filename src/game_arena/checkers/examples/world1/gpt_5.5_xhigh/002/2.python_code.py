
from __future__ import annotations

import time

# Internal side encoding
BLACK = 0  # moves toward lower row numbers
WHITE = 1  # moves toward higher row numbers

INF = 1_000_000_000
MATE = 1_000_000

# Keep comfortably below the 1 second limit.
TIME_LIMIT = 0.88
MAX_DEPTH = 14
Q_DEPTH = 6

MAN_VALUE = 100
KING_VALUE = 175

TT_MAX = 180_000

EXACT = 0
LOWER = 1
UPPER = 2

BIT = tuple(1 << i for i in range(64))
ROW = tuple(i // 8 for i in range(64))
COL = tuple(i % 8 for i in range(64))
COORD = tuple((ROW[i], COL[i]) for i in range(64))


def _build_move_tables():
    man_steps = [[None for _ in range(64)] for _ in range(2)]
    man_jumps = [[None for _ in range(64)] for _ in range(2)]
    king_steps = [None for _ in range(64)]
    king_jumps = [None for _ in range(64)]

    side_dirs = (
        (BLACK, ((-1, -1), (-1, 1))),
        (WHITE, ((1, -1), (1, 1))),
    )
    king_dirs = ((-1, -1), (-1, 1), (1, -1), (1, 1))

    for side, dirs in side_dirs:
        for sq in range(64):
            r, c = ROW[sq], COL[sq]
            steps = []
            jumps = []
            for dr, dc in dirs:
                r1, c1 = r + dr, c + dc
                if 0 <= r1 < 8 and 0 <= c1 < 8:
                    dst = r1 * 8 + c1
                    steps.append((dst, BIT[dst]))

                    r2, c2 = r + 2 * dr, c + 2 * dc
                    if 0 <= r2 < 8 and 0 <= c2 < 8:
                        land = r2 * 8 + c2
                        jumps.append((dst, land, BIT[dst], BIT[land]))
            man_steps[side][sq] = tuple(steps)
            man_jumps[side][sq] = tuple(jumps)

    for sq in range(64):
        r, c = ROW[sq], COL[sq]
        steps = []
        jumps = []
        for dr, dc in king_dirs:
            r1, c1 = r + dr, c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                dst = r1 * 8 + c1
                steps.append((dst, BIT[dst]))

                r2, c2 = r + 2 * dr, c + 2 * dc
                if 0 <= r2 < 8 and 0 <= c2 < 8:
                    land = r2 * 8 + c2
                    jumps.append((dst, land, BIT[dst], BIT[land]))
        king_steps[sq] = tuple(steps)
        king_jumps[sq] = tuple(jumps)

    return (
        (tuple(man_steps[BLACK]), tuple(man_steps[WHITE])),
        (tuple(man_jumps[BLACK]), tuple(man_jumps[WHITE])),
        tuple(king_steps),
        tuple(king_jumps),
    )


MAN_STEPS, MAN_JUMPS, KING_STEPS, KING_JUMPS = _build_move_tables()


def _build_position_tables():
    man_pos = [[0 for _ in range(64)] for _ in range(2)]
    king_pos = [0 for _ in range(64)]

    for sq in range(64):
        r, c = ROW[sq], COL[sq]

        # 0 at corners, 12 near the four central squares.
        center = 14 - (abs(2 * r - 7) + abs(2 * c - 7))
        edge_bonus = 2 if c == 0 or c == 7 else 0

        king_pos[sq] = center

        black_advance = 7 - r
        white_advance = r

        black_promo = 10 if r == 1 else 0
        white_promo = 10 if r == 6 else 0

        black_back_guard = 4 if r == 7 else 0
        white_back_guard = 4 if r == 0 else 0

        man_pos[BLACK][sq] = (
            4 * black_advance
            + center // 2
            + edge_bonus
            + black_promo
            + black_back_guard
        )
        man_pos[WHITE][sq] = (
            4 * white_advance
            + center // 2
            + edge_bonus
            + white_promo
            + white_back_guard
        )

    return (tuple(man_pos[BLACK]), tuple(man_pos[WHITE])), tuple(king_pos)


MAN_POS, KING_POS = _build_position_tables()

TT = {}
HISTORY = {}

DEADLINE = 0.0
NODES = 0

# Small memory aid for engines that implement multi-jump as repeated policy calls.
_FORCED_SIDE = -1
_FORCED_STATE = None
_FORCED_SRC = -1


class _Timeout(Exception):
    pass


def _check_time():
    if time.perf_counter() > DEADLINE:
        raise _Timeout()


def _mask_from_squares(squares):
    mask = 0
    if squares is None:
        return 0
    for sq in squares:
        r, c = sq
        r = int(r)
        c = int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            mask |= BIT[r * 8 + c]
    return mask


def _clear_forced():
    global _FORCED_SIDE, _FORCED_STATE, _FORCED_SRC
    _FORCED_SIDE = -1
    _FORCED_STATE = None
    _FORCED_SRC = -1


def _generate_moves(state, side):
    bm, bk, wm, wk = state

    if side == BLACK:
        men, kings = bm, bk
        opp_men, opp_kings = wm, wk
    else:
        men, kings = wm, wk
        opp_men, opp_kings = bm, bk

    opp = opp_men | opp_kings
    occ = bm | bk | wm | wk

    captures = []

    m = men
    jumps = MAN_JUMPS[side]
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb
        for mid, dst, mid_bit, dst_bit in jumps[sq]:
            if (opp & mid_bit) and not (occ & dst_bit):
                captures.append((sq, dst, mid))

    k = kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb
        for mid, dst, mid_bit, dst_bit in KING_JUMPS[sq]:
            if (opp & mid_bit) and not (occ & dst_bit):
                captures.append((sq, dst, mid))

    if captures:
        return captures, True

    quiets = []

    m = men
    steps = MAN_STEPS[side]
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb
        for dst, dst_bit in steps[sq]:
            if not (occ & dst_bit):
                quiets.append((sq, dst, -1))

    k = kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb
        for dst, dst_bit in KING_STEPS[sq]:
            if not (occ & dst_bit):
                quiets.append((sq, dst, -1))

    return quiets, False


def _capture_moves_from(state, side, src):
    bm, bk, wm, wk = state

    if side == BLACK:
        men, kings = bm, bk
        opp = wm | wk
    else:
        men, kings = wm, wk
        opp = bm | bk

    src_bit = BIT[src]
    is_man = bool(men & src_bit)
    if not is_man and not (kings & src_bit):
        return []

    occ = bm | bk | wm | wk
    jumps = MAN_JUMPS[side][src] if is_man else KING_JUMPS[src]

    result = []
    for mid, dst, mid_bit, dst_bit in jumps:
        if (opp & mid_bit) and not (occ & dst_bit):
            result.append((src, dst, mid))
    return result


def _count_legal_moves(state, side):
    bm, bk, wm, wk = state

    if side == BLACK:
        men, kings = bm, bk
        opp_men, opp_kings = wm, wk
    else:
        men, kings = wm, wk
        opp_men, opp_kings = bm, bk

    opp = opp_men | opp_kings
    occ = bm | bk | wm | wk

    cap_count = 0

    m = men
    jumps = MAN_JUMPS[side]
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb
        for _mid, _dst, mid_bit, dst_bit in jumps[sq]:
            if (opp & mid_bit) and not (occ & dst_bit):
                cap_count += 1

    k = kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb
        for _mid, _dst, mid_bit, dst_bit in KING_JUMPS[sq]:
            if (opp & mid_bit) and not (occ & dst_bit):
                cap_count += 1

    if cap_count:
        return cap_count, True

    quiet_count = 0

    m = men
    steps = MAN_STEPS[side]
    while m:
        lsb = m & -m
        sq = lsb.bit_length() - 1
        m ^= lsb
        for _dst, dst_bit in steps[sq]:
            if not (occ & dst_bit):
                quiet_count += 1

    k = kings
    while k:
        lsb = k & -k
        sq = lsb.bit_length() - 1
        k ^= lsb
        for _dst, dst_bit in KING_STEPS[sq]:
            if not (occ & dst_bit):
                quiet_count += 1

    return quiet_count, False


def _make_move(state, side, move):
    bm, bk, wm, wk = state
    src, dst, cap = move
    src_bit = BIT[src]
    dst_bit = BIT[dst]

    if side == BLACK:
        if bm & src_bit:
            bm &= ~src_bit
            if ROW[dst] == 0:
                bk |= dst_bit
            else:
                bm |= dst_bit
        else:
            bk &= ~src_bit
            bk |= dst_bit

        if cap >= 0:
            cap_bit = BIT[cap]
            wm &= ~cap_bit
            wk &= ~cap_bit

    else:
        if wm & src_bit:
            wm &= ~src_bit
            if ROW[dst] == 7:
                wk |= dst_bit
            else:
                wm |= dst_bit
        else:
            wk &= ~src_bit
            wk |= dst_bit

        if cap >= 0:
            cap_bit = BIT[cap]
            bm &= ~cap_bit
            bk &= ~cap_bit

    return bm, bk, wm, wk


def _score_mask(mask, table):
    score = 0
    while mask:
        lsb = mask & -mask
        score += table[lsb.bit_length() - 1]
        mask ^= lsb
    return score


def _color_score(men, kings, side):
    return (
        MAN_VALUE * men.bit_count()
        + KING_VALUE * kings.bit_count()
        + _score_mask(men, MAN_POS[side])
        + _score_mask(kings, KING_POS)
    )


def _evaluate(state, side):
    bm, bk, wm, wk = state

    black_score = _color_score(bm, bk, BLACK)
    white_score = _color_score(wm, wk, WHITE)

    score = black_score - white_score
    if side == WHITE:
        score = -score

    own_moves, own_cap = _count_legal_moves(state, side)
    opp_moves, opp_cap = _count_legal_moves(state, side ^ 1)

    score += 2 * (own_moves - opp_moves)

    if own_cap:
        score += 30 + 4 * own_moves
    if opp_cap:
        score -= 30 + 4 * opp_moves

    if opp_moves == 0:
        score += 200
    if own_moves == 0:
        score -= 200

    return score


def _move_order_score(state, side, move, tt_move=None):
    if move == tt_move:
        score = 10_000_000
    else:
        score = 0

    src, dst, cap = move
    src_bit = BIT[src]

    if side == BLACK:
        own_men = state[0]
        opp_kings = state[3]
        promo_row = 0
    else:
        own_men = state[2]
        opp_kings = state[1]
        promo_row = 7

    is_man = bool(own_men & src_bit)

    if cap >= 0:
        score += 100_000
        score += 900 if (opp_kings & BIT[cap]) else 500
    else:
        score += HISTORY.get((side, src, dst), 0)

    if is_man:
        score += MAN_POS[side][dst] - MAN_POS[side][src]
        if ROW[dst] == promo_row:
            score += 2_000
    else:
        score += KING_POS[dst] - KING_POS[src]

    return score


def _quiescence(state, side, alpha, beta, ply, qdepth):
    global NODES

    NODES += 1
    if (NODES & 1023) == 0:
        _check_time()

    moves, is_capture = _generate_moves(state, side)

    if not moves:
        return -MATE + ply

    if qdepth <= 0 or not is_capture:
        return _evaluate(state, side)

    moves.sort(key=lambda mv: _move_order_score(state, side, mv), reverse=True)

    best = -INF
    for move in moves:
        child = _make_move(state, side, move)
        value = -_quiescence(child, side ^ 1, -beta, -alpha, ply + 1, qdepth - 1)

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _negamax(state, side, depth, alpha, beta, ply):
    global NODES

    NODES += 1
    if (NODES & 1023) == 0:
        _check_time()

    if depth <= 0:
        return _quiescence(state, side, alpha, beta, ply, Q_DEPTH)

    key = (state, side)
    entry = TT.get(key)
    tt_move = None

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        entry_depth, entry_flag, entry_value, entry_move = entry
        tt_move = entry_move

        if entry_depth >= depth:
            if entry_flag == EXACT:
                return entry_value
            if entry_flag == LOWER:
                if entry_value > alpha:
                    alpha = entry_value
            elif entry_flag == UPPER:
                if entry_value < beta:
                    beta = entry_value
            if alpha >= beta:
                return entry_value

    moves, _is_capture = _generate_moves(state, side)

    if not moves:
        return -MATE + ply

    moves.sort(key=lambda mv: _move_order_score(state, side, mv, tt_move), reverse=True)

    best = -INF
    best_move = moves[0]

    for move in moves:
        child = _make_move(state, side, move)
        value = -_negamax(child, side ^ 1, depth - 1, -beta, -alpha, ply + 1)

        if value > best:
            best = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if move[2] < 0:
                hkey = (side, move[0], move[1])
                HISTORY[hkey] = min(HISTORY.get(hkey, 0) + depth * depth, 1_000_000)
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    if len(TT) < TT_MAX:
        TT[key] = (depth, flag, best, best_move)

    return best


def _choose_move(state, side, legal_moves):
    best_move = legal_moves[0]

    for depth in range(1, MAX_DEPTH + 1):
        try:
            if time.perf_counter() > DEADLINE:
                break

            moves = list(legal_moves)
            moves.sort(
                key=lambda mv: _move_order_score(state, side, mv, best_move),
                reverse=True,
            )

            alpha = -INF
            beta = INF
            current_best = moves[0]
            current_value = -INF

            for move in moves:
                child = _make_move(state, side, move)
                value = -_negamax(child, side ^ 1, depth - 1, -beta, -alpha, 1)

                if value > current_value:
                    current_value = value
                    current_best = move

                if value > alpha:
                    alpha = value

            best_move = current_best

            if len(TT) < TT_MAX:
                TT[(state, side)] = (depth, EXACT, current_value, current_best)

            if current_value > MATE - 5_000:
                break

        except _Timeout:
            break

    return best_move


def _remember_continuation(state, side, move):
    global _FORCED_SIDE, _FORCED_STATE, _FORCED_SRC

    if move[2] < 0:
        _clear_forced()
        return

    src, dst, _cap = move
    src_bit = BIT[src]

    if side == BLACK:
        was_man = bool(state[0] & src_bit)
        promotes = was_man and ROW[dst] == 0
    else:
        was_man = bool(state[2] & src_bit)
        promotes = was_man and ROW[dst] == 7

    if promotes:
        _clear_forced()
        return

    child = _make_move(state, side, move)
    continuations = _capture_moves_from(child, side, dst)

    if continuations:
        _FORCED_SIDE = side
        _FORCED_STATE = child
        _FORCED_SRC = dst
    else:
        _clear_forced()


def _fallback_no_legal_move(my_men, my_kings):
    # This should only be reached in already-lost/game-over positions.
    for group in (my_men, my_kings):
        if group is None:
            continue
        for sq in group:
            r, c = sq
            r = int(r)
            c = int(c)
            return ((r, c), (r, c))
    return ((0, 0), (0, 0))


def policy(
    my_men,
    my_kings,
    opp_men,
    opp_kings,
    color,
) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODES

    DEADLINE = time.perf_counter() + TIME_LIMIT
    NODES = 0

    if len(TT) > TT_MAX:
        TT.clear()

    color = str(color).lower()
    side = BLACK if color.startswith("b") else WHITE

    my_men_mask = _mask_from_squares(my_men)
    my_kings_mask = _mask_from_squares(my_kings)
    opp_men_mask = _mask_from_squares(opp_men)
    opp_kings_mask = _mask_from_squares(opp_kings)

    if side == BLACK:
        state = (my_men_mask, my_kings_mask, opp_men_mask, opp_kings_mask)
    else:
        state = (opp_men_mask, opp_kings_mask, my_men_mask, my_kings_mask)

    legal_moves, is_capture = _generate_moves(state, side)

    # If the engine is enforcing a multi-jump through repeated calls, restrict
    # the next move to the same piece when we can prove this is that state.
    if _FORCED_STATE == state and _FORCED_SIDE == side and is_capture:
        restricted = [mv for mv in legal_moves if mv[0] == _FORCED_SRC and mv[2] >= 0]
        if restricted:
            legal_moves = restricted
        else:
            _clear_forced()
    elif _FORCED_STATE != state or _FORCED_SIDE != side:
        _clear_forced()

    if not legal_moves:
        _clear_forced()
        return _fallback_no_legal_move(my_men, my_kings)

    legal_moves.sort(key=lambda mv: _move_order_score(state, side, mv), reverse=True)

    if len(legal_moves) == 1:
        chosen = legal_moves[0]
    else:
        chosen = _choose_move(state, side, legal_moves)

    _remember_continuation(state, side, chosen)

    src, dst, _cap = chosen
    return (COORD[src], COORD[dst])
