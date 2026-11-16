
# Kalah policy for a 6-house standard board.
# Implements: policy(you: list[int], opponent: list[int]) -> int

from math import inf
import time

HOUSES = 6
STORE = 6
TOTAL_PITS = 13  # own 6 + own store + opp 6, skipping opponent store


def _legal(side):
    return [i for i in range(HOUSES) if side[i] > 0]


def _side_empty(side):
    return all(side[i] == 0 for i in range(HOUSES))


def _finish(y, o):
    y = y[:]
    o = o[:]
    if _side_empty(y) or _side_empty(o):
        y[STORE] += sum(y[:HOUSES])
        o[STORE] += sum(o[:HOUSES])
        for i in range(HOUSES):
            y[i] = 0
            o[i] = 0
    return y, o


def _terminal_score(y, o):
    yy, oo = _finish(y, o)
    return yy[STORE] - oo[STORE]


def _move(y, o, m):
    """Return (new_you_perspective, new_opp_perspective, same_player_turn, ended)."""
    y = y[:]
    o = o[:]
    stones = y[m]
    y[m] = 0

    # Track last pit as:
    # ('y', 0..5), ('ys', 6), ('o', 0..5)
    pos_type = None
    pos_idx = -1

    idx = m
    side = 'y'

    while stones:
        if side == 'y':
            idx += 1
            if idx <= 5:
                y[idx] += 1
                stones -= 1
                pos_type, pos_idx = 'y', idx
            elif idx == 6:
                y[STORE] += 1
                stones -= 1
                pos_type, pos_idx = 'ys', STORE
                side = 'o'
                idx = -1
            else:
                side = 'o'
                idx = -1
        else:
            idx += 1
            if idx <= 5:
                o[idx] += 1
                stones -= 1
                pos_type, pos_idx = 'o', idx
            else:
                side = 'y'
                idx = -1

    same = (pos_type == 'ys')

    # Capture
    if pos_type == 'y' and y[pos_idx] == 1:
        opp_idx = 5 - pos_idx
        if o[opp_idx] > 0:
            y[STORE] += o[opp_idx] + 1
            y[pos_idx] = 0
            o[opp_idx] = 0

    ended = _side_empty(y) or _side_empty(o)
    if ended:
        y, o = _finish(y, o)

    if same and not ended:
        return y, o, True, False
    else:
        # Switch perspective for search if turn passes.
        if ended:
            return y, o, False, True
        return o, y, False, False


def _is_extra(y, m):
    return (y[m] % TOTAL_PITS) == (STORE - m)


def _capture_gain(y, o, m):
    stones = y[m]
    if stones <= 0:
        return 0
    # Simulate only enough to identify last landing pit.
    pos = m
    side = 0  # 0 = y houses/store path, 1 = opp houses
    last_side = None
    last_idx = None
    s = stones
    while s:
        if side == 0:
            pos += 1
            if pos <= 5:
                s -= 1
                last_side, last_idx = 0, pos
            elif pos == 6:
                s -= 1
                last_side, last_idx = 2, 6
                side = 1
                pos = -1
            else:
                side = 1
                pos = -1
        else:
            pos += 1
            if pos <= 5:
                s -= 1
                last_side, last_idx = 1, pos
            else:
                side = 0
                pos = -1
    if last_side == 0:
        before = y[last_idx]
        # Since moving from m empties m first.
        if last_idx == m:
            before = 0
        if before == 0 and o[5 - last_idx] > 0:
            return o[5 - last_idx] + 1
    return 0


def _heuristic(y, o):
    if _side_empty(y) or _side_empty(o):
        return _terminal_score(y, o) * 10000

    store_diff = y[STORE] - o[STORE]
    house_diff = sum(y[:HOUSES]) - sum(o[:HOUSES])

    extra_count = 0
    cap_potential = 0
    for m in range(HOUSES):
        if y[m] > 0:
            if _is_extra(y, m):
                extra_count += 1
            cap_potential = max(cap_potential, _capture_gain(y, o, m))

    opp_extra = 0
    opp_cap = 0
    for m in range(HOUSES):
        if o[m] > 0:
            if _is_extra(o, m):
                opp_extra += 1
            opp_cap = max(opp_cap, _capture_gain(o, y, m))

    mobility = len(_legal(y)) - len(_legal(o))

    # Vulnerability: seeds opposite our non-empty pits can be captured by opponent.
    vulnerable = 0
    for i in range(HOUSES):
        if y[i] > 0 and o[5 - i] == 0:
            vulnerable += y[i]

    return (
        220 * store_diff
        + 18 * house_diff
        + 55 * extra_count
        - 45 * opp_extra
        + 42 * cap_potential
        - 40 * opp_cap
        + 8 * mobility
        - 3 * vulnerable
    )


def _ordered_moves(y, o):
    moves = _legal(y)

    def key(m):
        cap = _capture_gain(y, o, m)
        extra = 1 if _is_extra(y, m) else 0
        # Prefer rightmost small extra turns in common openings, captures, then store-feeding moves.
        store_reach = 1 if y[m] >= STORE - m else 0
        return (extra, cap, store_reach, -y[m], m)

    moves.sort(key=key, reverse=True)
    return moves


def _search(y, o, depth, alpha, beta, end_time):
    if time.perf_counter() > end_time:
        raise TimeoutError

    if depth <= 0 or _side_empty(y) or _side_empty(o):
        return _heuristic(y, o)

    moves = _ordered_moves(y, o)
    if not moves:
        return _heuristic(y, o)

    best = -inf
    for m in moves:
        ny, no, same, ended = _move(y, o, m)
        if ended:
            val = _terminal_score(ny, no) * 10000
        elif same:
            val = _search(ny, no, depth - 1, alpha, beta, end_time)
        else:
            # Perspective swapped; negate returned value.
            val = -_search(ny, no, depth - 1, -beta, -alpha, end_time)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def policy(you: list[int], opponent: list[int]) -> int:
    legal = _legal(you)
    if not legal:
        return 0  # Should never be called in this state.

    # Safe default.
    best_move = legal[0]

    # Tactical immediate checks: winning terminal/capture/extra moves often matter.
    ordered = _ordered_moves(you, opponent)
    best_move = ordered[0]

    start = time.perf_counter()
    end_time = start + 0.92

    # Iterative deepening. Extra-turn games can branch less/more unpredictably;
    # this keeps us inside the 1 second limit.
    max_depth = 10
    seeds_in_play = sum(you[:HOUSES]) + sum(opponent[:HOUSES])
    if seeds_in_play > 55:
        max_depth = 8
    if seeds_in_play < 25:
        max_depth = 12

    try:
        for depth in range(2, max_depth + 1):
            current_best = best_move
            current_val = -inf
            alpha = -inf
            beta = inf

            for m in ordered:
                if time.perf_counter() > end_time:
                    raise TimeoutError
                ny, no, same, ended = _move(you, opponent, m)
                if ended:
                    val = _terminal_score(ny, no) * 10000
                elif same:
                    val = _search(ny, no, depth - 1, alpha, beta, end_time)
                else:
                    val = -_search(ny, no, depth - 1, -beta, -alpha, end_time)

                if val > current_val:
                    current_val = val
                    current_best = m
                if val > alpha:
                    alpha = val

            best_move = current_best

            # Reorder next iteration using previous best first.
            ordered = [best_move] + [m for m in ordered if m != best_move]

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        return legal[0]

    if best_move not in legal or you[best_move] <= 0:
        return legal[0]
    return int(best_move)
