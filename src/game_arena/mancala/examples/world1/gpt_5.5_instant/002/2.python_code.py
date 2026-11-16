
# Kalah policy for a standard 6-house board.
# API:
#   policy(you: list[int], opponent: list[int]) -> int

import time
import math

_HOUSES = 6
_STORE = 6
_INF = 10**9


def _legal(side):
    return [i for i in range(_HOUSES) if side[i] > 0]


def _sweep_if_game_over(y, o):
    """Apply terminal sweeping if either side is empty. Return True if terminal."""
    if sum(y[:_HOUSES]) == 0:
        rem = sum(o[:_HOUSES])
        if rem:
            for i in range(_HOUSES):
                o[i] = 0
            o[_STORE] += rem
        return True
    if sum(o[:_HOUSES]) == 0:
        rem = sum(y[:_HOUSES])
        if rem:
            for i in range(_HOUSES):
                y[i] = 0
            y[_STORE] += rem
        return True
    return False


def _make_move(y, o, move):
    """
    Make a move for the side represented by y against o.
    Returns (new_y, new_o, extra_turn, terminal).
    If extra_turn is False and nonterminal, the caller should swap perspective.
    """
    y = y[:]
    o = o[:]

    seeds = y[move]
    y[move] = 0

    # Track positions in a 13-slot cycle:
    # 0..5 = own houses, 6 = own store, 7..12 = opponent houses 0..5.
    pos = move
    last_kind = None
    last_idx = -1

    while seeds:
        pos = (pos + 1) % 13
        if pos < 6:
            y[pos] += 1
            last_kind = 0
            last_idx = pos
        elif pos == 6:
            y[_STORE] += 1
            last_kind = 1
            last_idx = _STORE
        else:
            oi = pos - 7
            o[oi] += 1
            last_kind = 2
            last_idx = oi
        seeds -= 1

    extra = (last_kind == 1)

    # Capture: last seed lands in own empty house and opposite has seeds.
    if last_kind == 0 and y[last_idx] == 1:
        opp_idx = 5 - last_idx
        if o[opp_idx] > 0:
            y[_STORE] += o[opp_idx] + 1
            y[last_idx] = 0
            o[opp_idx] = 0

    terminal = _sweep_if_game_over(y, o)
    if terminal:
        extra = False

    return y, o, extra, terminal


def _static_eval(y, o):
    """Evaluation from current root player's perspective: y is root side, o is opponent side."""
    if sum(y[:6]) == 0 or sum(o[:6]) == 0:
        yy = y[:]
        oo = o[:]
        _sweep_if_game_over(yy, oo)
        diff = yy[6] - oo[6]
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    store_diff = y[6] - o[6]
    side_diff = sum(y[:6]) - sum(o[:6])

    # Extra-turn opportunities.
    extra_y = 0
    extra_o = 0
    for i in range(6):
        if y[i] > 0 and y[i] % 13 == 6 - i:
            extra_y += 1
        if o[i] > 0 and o[i] % 13 == 6 - i:
            extra_o += 1

    # Immediate capture opportunities.
    cap_y = 0
    cap_o = 0
    for i in range(6):
        if y[i] == 0 and o[5 - i] > 0:
            cap_y += o[5 - i]
        if o[i] == 0 and y[5 - i] > 0:
            cap_o += y[5 - i]

    # Seeds closer to store are slightly better.
    advancement = 0
    for i in range(6):
        advancement += (i + 1) * y[i]
        advancement -= (i + 1) * o[i]

    return (
        15 * store_diff
        + 2 * side_diff
        + 5 * (extra_y - extra_o)
        + 2 * (cap_y - cap_o)
        + 0.15 * advancement
    )


def _move_tactical_score(y, o, m):
    ny, no, extra, terminal = _make_move(y, o, m)
    score = 0
    score += 1000 if terminal else 0
    score += 150 if extra else 0
    score += 20 * (ny[6] - y[6])
    score += 2 * (sum(no[:6]) - sum(o[:6])) * -1
    # Prefer rightmost houses very slightly in ties, often improves tempo.
    score += m * 0.01
    return score


def _ordered_moves(y, o):
    moves = _legal(y)
    moves.sort(key=lambda m: _move_tactical_score(y, o, m), reverse=True)
    return moves


def _search(y, o, depth, alpha, beta, maximizing, end_time):
    if time.perf_counter() >= end_time:
        raise TimeoutError

    if depth <= 0 or sum(y[:6]) == 0 or sum(o[:6]) == 0:
        return _static_eval(y, o)

    # y/o are always from the side-to-move perspective when maximizing is True for root,
    # but evaluation is always root perspective. For minimizing nodes, y is opponent side
    # and o is root side, so convert for static at leaves by caller structure below.
    if maximizing:
        best = -_INF
        for m in _ordered_moves(y, o):
            ny, no, extra, terminal = _make_move(y, o, m)
            if terminal:
                val = _static_eval(ny, no)
            elif extra:
                val = _search(ny, no, depth - 1, alpha, beta, True, end_time)
            else:
                val = _search(no, ny, depth - 1, alpha, beta, False, end_time)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        # Here y is opponent-to-move and o is root side. Lower score is better for opponent.
        best = _INF
        for m in _ordered_moves(y, o):
            ny, no, extra, terminal = _make_move(y, o, m)
            if terminal:
                # After opponent move, no is root side and ny is opponent side.
                val = _static_eval(no, ny)
            elif extra:
                val = _search(ny, no, depth - 1, alpha, beta, False, end_time)
            else:
                val = _search(no, ny, depth - 1, alpha, beta, True, end_time)
            if val < best:
                best = val
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best


def policy(you: list[int], opponent: list[int]) -> int:
    legal = _legal(you)
    if not legal:
        return 0  # Should never happen per specification.
    fallback = legal[0]

    # Immediate winning/endgame or clearly best tactical fallback.
    ordered = _ordered_moves(you, opponent)
    best_move = ordered[0] if ordered else fallback

    # Keep a conservative budget under the 1 second arena limit.
    end_time = time.perf_counter() + 0.88

    # Iterative deepening. Kalah extra turns make ply counts irregular, so keep bounds practical.
    max_depth = 10
    try:
        for depth in range(1, max_depth + 1):
            cur_best = best_move
            cur_val = -_INF
            alpha = -_INF
            beta = _INF

            for m in ordered:
                if time.perf_counter() >= end_time:
                    raise TimeoutError
                ny, no, extra, terminal = _make_move(you, opponent, m)
                if terminal:
                    val = _static_eval(ny, no)
                elif extra:
                    val = _search(ny, no, depth - 1, alpha, beta, True, end_time)
                else:
                    val = _search(no, ny, depth - 1, alpha, beta, False, end_time)

                if val > cur_val:
                    cur_val = val
                    cur_best = m
                alpha = max(alpha, cur_val)

            best_move = cur_best

    except TimeoutError:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        return fallback

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return int(best_move)
    return fallback
