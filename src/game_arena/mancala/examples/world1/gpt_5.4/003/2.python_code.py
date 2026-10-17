
import time
from math import inf

HOUSES = 6
STORE = 6


def _legal_moves(you, opp):
    return [i for i in range(HOUSES) if you[i] > 0]


def _is_side_empty(side):
    return side[0] == 0 and side[1] == 0 and side[2] == 0 and side[3] == 0 and side[4] == 0 and side[5] == 0


def _finalize_if_terminal(you, opp):
    if _is_side_empty(you):
        rem = sum(opp[:HOUSES])
        if rem:
            opp = opp[:]
            opp[STORE] += rem
            for i in range(HOUSES):
                opp[i] = 0
        return True, you, opp
    if _is_side_empty(opp):
        rem = sum(you[:HOUSES])
        if rem:
            you = you[:]
            you[STORE] += rem
            for i in range(HOUSES):
                you[i] = 0
        return True, you, opp
    return False, you, opp


def _apply_move(you, opp, move):
    you = you[:]
    opp = opp[:]
    seeds = you[move]
    you[move] = 0

    side = 0  # 0 = you, 1 = opp
    idx = move + 1
    last_side = None
    last_idx = None

    while seeds > 0:
        if side == 0:
            while idx <= STORE and seeds > 0:
                you[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                idx += 1
            side = 1
            idx = 0
        else:
            while idx < HOUSES and seeds > 0:  # skip opp store
                opp[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                idx += 1
            side = 0
            idx = 0

    extra_turn = (last_side == 0 and last_idx == STORE)

    if not extra_turn and last_side == 0 and 0 <= last_idx < HOUSES and you[last_idx] == 1 and opp[5 - last_idx] > 0:
        you[STORE] += you[last_idx] + opp[5 - last_idx]
        you[last_idx] = 0
        opp[5 - last_idx] = 0

    terminal, you, opp = _finalize_if_terminal(you, opp)
    return you, opp, extra_turn, terminal


def _count_extra_turn_moves(you):
    c = 0
    for i in range(HOUSES):
        s = you[i]
        if s <= 0:
            continue
        if ((i + s) % 13) == STORE:
            c += 1
    return c


def _capture_potential(you, opp):
    score = 0
    for i in range(HOUSES):
        if you[i] != 0:
            continue
        if opp[5 - i] <= 0:
            continue
        for j in range(HOUSES):
            s = you[j]
            if s <= 0:
                continue
            steps = i - j
            if steps <= 0:
                steps += 13
            if s % 13 == steps % 13:
                score += 1 + opp[5 - i]
                break
    return score


def _eval(you, opp):
    terminal, you2, opp2 = _finalize_if_terminal(you, opp)
    if terminal:
        diff = you2[STORE] - opp2[STORE]
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    store_diff = you[STORE] - opp[STORE]
    house_diff = sum(you[:HOUSES]) - sum(opp[:HOUSES])
    my_moves = len(_legal_moves(you, opp))
    opp_moves = len(_legal_moves(opp, you))
    my_extra = _count_extra_turn_moves(you)
    opp_extra = _count_extra_turn_moves(opp)
    my_cap = _capture_potential(you, opp)
    opp_cap = _capture_potential(opp, you)

    endgame_bias = 0
    total_houses = sum(you[:HOUSES]) + sum(opp[:HOUSES])
    if total_houses <= 18:
        endgame_bias = 2 * house_diff

    return (
        40 * store_diff
        + 3 * house_diff
        + 2 * (my_moves - opp_moves)
        + 10 * (my_extra - opp_extra)
        + 4 * (my_cap - opp_cap)
        + endgame_bias
    )


def _move_order(you, opp, moves):
    scored = []
    for m in moves:
        y2, o2, extra, terminal = _apply_move(you, opp, m)
        score = 0
        if terminal:
            score += 100000 + (y2[STORE] - o2[STORE])
        score += 20 * (y2[STORE] - you[STORE])
        if extra:
            score += 30
        if y2[STORE] - you[STORE] >= 2:
            score += 15
        score += _eval(y2, o2) * 0.1
        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _negamax(you, opp, depth, alpha, beta, end_time):
    if time.perf_counter() >= end_time:
        raise TimeoutError

    terminal, y, o = _finalize_if_terminal(you, opp)
    if terminal:
        diff = y[STORE] - o[STORE]
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    if depth <= 0:
        return _eval(you, opp)

    moves = _legal_moves(you, opp)
    if not moves:
        return _eval(you, opp)

    best = -inf
    ordered = _move_order(you, opp, moves)

    for m in ordered:
        y2, o2, extra, terminal = _apply_move(you, opp, m)
        if terminal:
            val = _eval(y2, o2)
        elif extra:
            val = _negamax(y2, o2, depth - 1, alpha, beta, end_time)
        else:
            val = -_negamax(o2, y2, depth - 1, -beta, -alpha, end_time)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(HOUSES) if you[i] > 0]
    if not legal:
        return 0

    if len(legal) == 1:
        return legal[0]

    start = time.perf_counter()
    end_time = start + 0.92

    ordered_root = _move_order(you, opponent, legal)
    best_move = ordered_root[0]

    # Quick tactical check for immediate winning terminal move
    best_terminal = None
    best_terminal_score = -inf
    for m in ordered_root:
        y2, o2, extra, terminal = _apply_move(you, opponent, m)
        if terminal:
            sc = _eval(y2, o2)
            if sc > best_terminal_score:
                best_terminal_score = sc
                best_terminal = m
    if best_terminal is not None:
        return best_terminal

    depth = 1
    try:
        while depth <= 12:
            current_best = None
            current_best_score = -inf
            alpha = -inf
            beta = inf

            root_moves = _move_order(you, opponent, legal)

            for m in root_moves:
                if time.perf_counter() >= end_time:
                    raise TimeoutError
                y2, o2, extra, terminal = _apply_move(you, opponent, m)
                if terminal:
                    val = _eval(y2, o2)
                elif extra:
                    val = _negamax(y2, o2, depth - 1, alpha, beta, end_time)
                else:
                    val = -_negamax(o2, y2, depth - 1, -beta, -alpha, end_time)

                if val > current_best_score:
                    current_best_score = val
                    current_best = m
                if val > alpha:
                    alpha = val

            if current_best is not None:
                best_move = current_best
            depth += 1
    except TimeoutError:
        pass

    if best_move not in legal:
        return legal[0]
    return best_move
