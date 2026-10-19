
# Kalah policy for 6-house standard board.
# Implements: def policy(you: list[int], opponent: list[int]) -> int

import time
from functools import lru_cache

HOUSES = 6
STORE = 6
INF = 10**9

# Conservative time budget for 1s arena limit.
_TIME_LIMIT = 0.88
_deadline = 0.0


def _legal(side):
    return [i for i in range(HOUSES) if side[i] > 0]


def _final_score(you, opp):
    """Score from root/current player's perspective after game-end sweep."""
    ys = you[STORE]
    os = opp[STORE]
    yhouses = sum(you[:HOUSES])
    ohouses = sum(opp[:HOUSES])
    if yhouses == 0:
        os += ohouses
    elif ohouses == 0:
        ys += yhouses
    return ys - os


def _is_terminal(you, opp):
    return sum(you[:HOUSES]) == 0 or sum(opp[:HOUSES]) == 0


def _move(you_t, opp_t, m):
    """
    Apply move for side 'you_t' to move.
    Returns (new_you, new_opp, same_player_turn).
    If same_player_turn is False, perspective is swapped for next node:
      returned new_you is the next player to move.
    """
    you = list(you_t)
    opp = list(opp_t)
    seeds = you[m]
    you[m] = 0

    # Positions in sowing cycle:
    # 0..5 => own houses, 6 => own store, 7..12 => opponent houses 0..5
    pos = m
    last_side = 0
    last_idx = -1

    while seeds:
        pos = (pos + 1) % 13
        if pos < 6:
            you[pos] += 1
            last_side = 0
            last_idx = pos
        elif pos == 6:
            you[STORE] += 1
            last_side = 0
            last_idx = STORE
        else:
            oi = pos - 7
            opp[oi] += 1
            last_side = 1
            last_idx = oi
        seeds -= 1

    same = (last_side == 0 and last_idx == STORE)

    # Capture: last seed in own empty house and opposite has seeds.
    if last_side == 0 and 0 <= last_idx < HOUSES and you[last_idx] == 1:
        oi = 5 - last_idx
        if opp[oi] > 0:
            you[STORE] += opp[oi] + 1
            opp[oi] = 0
            you[last_idx] = 0

    # If game ended, sweep remaining seeds immediately.
    if sum(you[:HOUSES]) == 0 or sum(opp[:HOUSES]) == 0:
        you[STORE] += sum(you[:HOUSES])
        opp[STORE] += sum(opp[:HOUSES])
        for i in range(HOUSES):
            you[i] = 0
            opp[i] = 0

    if same:
        return tuple(you), tuple(opp), True
    else:
        # Swap perspective for opponent's turn.
        return tuple(opp), tuple(you), False


def _immediate_features(you, opp, m):
    """For move ordering only: larger is better."""
    before_store = you[STORE]
    ny, no, same = _move(tuple(you), tuple(opp), m)

    if same:
        my_after, op_after = ny, no
        store_gain = my_after[STORE] - before_store
        score = 1000 + 35 * store_gain
    else:
        # returned perspective is swapped; original player is no
        my_after, op_after = no, ny
        store_gain = my_after[STORE] - before_store
        score = 35 * store_gain

    # Prefer moves that end game favorably.
    if _is_terminal(my_after, op_after):
        score += 10000 + 100 * (my_after[STORE] - op_after[STORE])

    # Prefer captures and extra turns, modestly prefer right-side moves.
    score += 2 * m
    return score


def _ordered_moves(you, opp):
    moves = _legal(you)
    moves.sort(key=lambda x: _immediate_features(you, opp, x), reverse=True)
    return moves


def _static_eval(you, opp):
    """
    Evaluation from side-to-move perspective.
    Store difference dominates; additional terms improve play before conversion.
    """
    if _is_terminal(you, opp):
        return 10000 * _final_score(you, opp)

    ys = you[STORE]
    os = opp[STORE]
    yh = sum(you[:HOUSES])
    oh = sum(opp[:HOUSES])

    val = 120 * (ys - os) + 6 * (yh - oh)

    # Extra-turn opportunities.
    for i in range(HOUSES):
        if you[i] > 0 and you[i] % 13 == (6 - i):
            val += 25
        if opp[i] > 0 and opp[i] % 13 == (6 - i):
            val -= 25

    # Capture opportunities/threats based on exact landing in own empty pit.
    for i in range(HOUSES):
        if you[i] == 0:
            oppo = opp[5 - i]
            if oppo:
                # Any previous house j that lands on i.
                for j in range(i):
                    if you[j] == i - j:
                        val += 18 + 10 * oppo
                        break
        if opp[i] == 0:
            oppo = you[5 - i]
            if oppo:
                for j in range(i):
                    if opp[j] == i - j:
                        val -= 18 + 10 * oppo
                        break

    # Mobility and starvation/endgame considerations.
    val += 3 * len(_legal(you)) - 3 * len(_legal(opp))
    if yh == 0:
        val -= 500
    if oh == 0:
        val += 500

    return val


def policy(you: list[int], opponent: list[int]) -> int:
    global _deadline
    start = time.perf_counter()
    _deadline = start + _TIME_LIMIT

    legal = _legal(you)
    # Guaranteed legal fallback.
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    you_t = tuple(int(x) for x in you)
    opp_t = tuple(int(x) for x in opponent)

    # Tactical fallback: best immediate move.
    best_move = max(legal, key=lambda m: _immediate_features(you, opponent, m))

    @lru_cache(maxsize=250000)
    def search(y, o, depth, alpha, beta):
        # alpha/beta are included in cache key due to simplicity; still useful enough.
        if time.perf_counter() > _deadline:
            raise TimeoutError

        if depth <= 0 or _is_terminal(y, o):
            return _static_eval(y, o)

        moves = _ordered_moves(y, o)
        if not moves:
            return _static_eval(y, o)

        best = -INF
        a = alpha

        for m in moves:
            ny, no, same = _move(y, o, m)
            if same:
                # Same player moves again; don't penalize depth as much, but avoid endless depth.
                val = search(ny, no, depth - 1, a, beta)
            else:
                # Perspective swapped: negate opponent's evaluation.
                val = -search(ny, no, depth - 1, -beta, -a)

            if val > best:
                best = val
            if best > a:
                a = best
            if a >= beta:
                break

        return best

    # Iterative deepening. Depth 8-12 is often reachable; lower depths always safe.
    try:
        max_depth = 14
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _deadline:
                break

            current_best = best_move
            current_val = -INF
            alpha = -INF
            beta = INF

            for m in _ordered_moves(you_t, opp_t):
                if time.perf_counter() > _deadline:
                    raise TimeoutError

                ny, no, same = _move(you_t, opp_t, m)
                if same:
                    val = search(ny, no, depth - 1, alpha, beta)
                else:
                    val = -search(ny, no, depth - 1, -beta, -alpha)

                if val > current_val:
                    current_val = val
                    current_best = m
                if val > alpha:
                    alpha = val

            # Only commit after a complete depth finishes.
            if current_best in legal:
                best_move = current_best

    except TimeoutError:
        pass
    except Exception:
        # Never risk returning illegal due to unexpected issue.
        pass

    if best_move not in legal or you[best_move] <= 0:
        best_move = legal[0]
    return int(best_move)
