
from time import perf_counter

_INF = 10**30
_TERM_SCALE = 10**9

EXACT = 0
LOWER = 1
UPPER = 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class SearchTimeout(Exception):
    pass


def _side_empty(side: list[int]) -> bool:
    return not (side[0] or side[1] or side[2] or side[3] or side[4] or side[5])


def _side_sum(side: list[int]) -> int:
    return side[0] + side[1] + side[2] + side[3] + side[4] + side[5]


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0 and perf_counter() >= _DEADLINE:
        raise SearchTimeout


def _terminal_score(you: list[int], opponent: list[int]) -> int:
    return (you[6] - opponent[6]) * _TERM_SCALE


def _extra_turn_count(side: list[int]) -> int:
    count = 0
    for i in range(6):
        s = side[i]
        if s > 0 and s % 13 == 6 - i:
            count += 1
    return count


def _static_eval(you: list[int], opponent: list[int]) -> int:
    if _side_empty(you) or _side_empty(opponent):
        return _terminal_score(you, opponent)

    sy = _side_sum(you)
    so = _side_sum(opponent)
    store_diff = you[6] - opponent[6]

    # Seeds closer to the store are a bit more valuable.
    pos_you = you[0] + 2 * you[1] + 3 * you[2] + 4 * you[3] + 5 * you[4] + 6 * you[5]
    pos_opp = (
        opponent[0]
        + 2 * opponent[1]
        + 3 * opponent[2]
        + 4 * opponent[3]
        + 5 * opponent[4]
        + 6 * opponent[5]
    )

    moves_you = (
        (1 if you[0] else 0)
        + (1 if you[1] else 0)
        + (1 if you[2] else 0)
        + (1 if you[3] else 0)
        + (1 if you[4] else 0)
        + (1 if you[5] else 0)
    )
    moves_opp = (
        (1 if opponent[0] else 0)
        + (1 if opponent[1] else 0)
        + (1 if opponent[2] else 0)
        + (1 if opponent[3] else 0)
        + (1 if opponent[4] else 0)
        + (1 if opponent[5] else 0)
    )

    free_you = _extra_turn_count(you)
    free_opp = _extra_turn_count(opponent)

    # Empty houses opposite seeds can become capture targets.
    vuln_you = 0
    vuln_opp = 0
    if you[0] == 0:
        vuln_you += opponent[5]
    if you[1] == 0:
        vuln_you += opponent[4]
    if you[2] == 0:
        vuln_you += opponent[3]
    if you[3] == 0:
        vuln_you += opponent[2]
    if you[4] == 0:
        vuln_you += opponent[1]
    if you[5] == 0:
        vuln_you += opponent[0]

    if opponent[0] == 0:
        vuln_opp += you[5]
    if opponent[1] == 0:
        vuln_opp += you[4]
    if opponent[2] == 0:
        vuln_opp += you[3]
    if opponent[3] == 0:
        vuln_opp += you[2]
    if opponent[4] == 0:
        vuln_opp += you[1]
    if opponent[5] == 0:
        vuln_opp += you[0]

    return (
        120 * store_diff
        + 2 * (sy - so)
        + (pos_you - pos_opp)
        + 4 * (moves_you - moves_opp)
        + 18 * (free_you - free_opp)
        + (vuln_you - vuln_opp)
    )


def _apply_move(
    you: list[int], opponent: list[int], pit: int
) -> tuple[list[int], list[int], bool, int, int]:
    y = you[:]
    o = opponent[:]

    seeds = y[pit]
    y[pit] = 0

    side = 0  # 0 = your side/store, 1 = opponent houses
    pos = pit
    last_side = 0
    last_pos = pit

    while seeds:
        pos += 1

        if side == 0:
            if pos == 6:
                y[6] += 1
                seeds -= 1
                last_side = 0
                last_pos = 6
                if seeds == 0:
                    break
                side = 1
                pos = -1
            else:
                y[pos] += 1
                seeds -= 1
                last_side = 0
                last_pos = pos
        else:
            if pos == 6:
                side = 0
                pos = -1
                continue

            o[pos] += 1
            seeds -= 1
            last_side = 1
            last_pos = pos

            if pos == 5:
                side = 0
                pos = -1

    captured = 0
    if last_side == 0 and 0 <= last_pos <= 5 and y[last_pos] == 1 and o[5 - last_pos] > 0:
        captured = o[5 - last_pos] + 1
        y[6] += captured
        y[last_pos] = 0
        o[5 - last_pos] = 0

    terminal = False
    if _side_empty(y) or _side_empty(o):
        sy = _side_sum(y)
        so = _side_sum(o)

        if sy:
            y[6] += sy
            y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0
        if so:
            o[6] += so
            o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0

        terminal = True

    extra_turn = (not terminal) and last_side == 0 and last_pos == 6
    store_gain = y[6] - you[6]

    return y, o, extra_turn, store_gain, captured


def _ordered_children(you: list[int], opponent: list[int], tt_move: int | None):
    children = []

    for m in range(6):
        if you[m] <= 0:
            continue

        ny, no, extra, store_gain, captured = _apply_move(you, opponent, m)

        if extra:
            score = _static_eval(ny, no) + 50000
        else:
            score = -_static_eval(no, ny)

        score += 50 * store_gain + 5 * captured

        if tt_move is not None and m == tt_move:
            score += 10**15

        children.append((score, m, ny, no, extra))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _search(you: list[int], opponent: list[int], depth: int, alpha: int, beta: int):
    _check_time()

    alpha_orig = alpha
    beta_orig = beta
    key = tuple(you + opponent)

    tt_move = None
    entry = _TT.get(key)
    if entry is not None:
        entry_depth, entry_value, entry_flag, entry_move = entry
        tt_move = entry_move

        if entry_depth >= depth:
            if entry_flag == EXACT:
                return entry_value, entry_move
            if entry_flag == LOWER:
                if entry_value > alpha:
                    alpha = entry_value
            else:
                if entry_value < beta:
                    beta = entry_value
            if alpha >= beta:
                return entry_value, entry_move

    if depth == 0 or _side_empty(you) or _side_empty(opponent):
        return _static_eval(you, opponent), None

    best_value = -_INF
    best_move = None

    for _, m, ny, no, extra in _ordered_children(you, opponent, tt_move):
        if extra:
            value, _ = _search(ny, no, depth - 1, alpha, beta)
        else:
            value, _ = _search(no, ny, depth - 1, -beta, -alpha)
            value = -value

        if value > best_value:
            best_value = value
            best_move = m

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_move is None:
        best_value = _static_eval(you, opponent)

    flag = EXACT
    if best_value <= alpha_orig:
        flag = UPPER
    elif best_value >= beta_orig:
        flag = LOWER

    _TT[key] = (depth, best_value, flag, best_move)
    return best_value, best_move


def policy(you: list[int], opponent: list[int]) -> int:
    root_you = list(you)
    root_opp = list(opponent)

    legal = [i for i in range(6) if root_you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    global _TT, _DEADLINE, _NODES
    _TT = {}
    _NODES = 0
    _DEADLINE = perf_counter() + 0.90

    # Safe fallback: best-looking 1-ply move.
    children = _ordered_children(root_you, root_opp, None)
    best_move = children[0][1]
    best_value = -_INF

    for _, m, ny, no, extra in children:
        if extra:
            value = _static_eval(ny, no)
        else:
            value = -_static_eval(no, ny)

        if value > best_value:
            best_value = value
            best_move = m

    total_outside = _side_sum(root_you) + _side_sum(root_opp)
    if total_outside <= 10:
        max_depth = 30
    elif total_outside <= 20:
        max_depth = 18
    else:
        max_depth = 12

    root_key = tuple(root_you + root_opp)

    for depth in range(1, max_depth + 1):
        if perf_counter() >= _DEADLINE:
            break

        try:
            alpha = -_INF
            beta = _INF

            root_entry = _TT.get(root_key)
            tt_move = best_move if root_entry is None else root_entry[3]

            local_best_move = None
            local_best_value = -_INF

            for _, m, ny, no, extra in _ordered_children(root_you, root_opp, tt_move):
                if extra:
                    value, _ = _search(ny, no, depth - 1, alpha, beta)
                else:
                    value, _ = _search(no, ny, depth - 1, -beta, -alpha)
                    value = -value

                if value > local_best_value:
                    local_best_value = value
                    local_best_move = m

                if value > alpha:
                    alpha = value

            if local_best_move is not None:
                best_move = local_best_move
                best_value = local_best_value
                _TT[root_key] = (depth, best_value, EXACT, best_move)

        except SearchTimeout:
            break

    if 0 <= best_move <= 5 and root_you[best_move] > 0:
        return best_move

    return legal[0]
