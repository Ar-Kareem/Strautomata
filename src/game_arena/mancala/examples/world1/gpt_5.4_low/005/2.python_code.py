
from __future__ import annotations

import time
from typing import List, Tuple, Dict

# ----------------------------------------------------------------------
# Kalah policy
# ----------------------------------------------------------------------

INF = 10**9


class _Timeout(Exception):
    pass


def _legal_moves(you: List[int]) -> List[int]:
    return [i for i in range(6) if you[i] > 0]


def _finalize_if_game_over(you: List[int], opp: List[int]) -> bool:
    """If either side has no seeds in houses, sweep remaining seeds to stores."""
    you_empty = (you[0] | you[1] | you[2] | you[3] | you[4] | you[5]) == 0
    opp_empty = (opp[0] | opp[1] | opp[2] | opp[3] | opp[4] | opp[5]) == 0
    if not (you_empty or opp_empty):
        return False

    if not you_empty:
        rem = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
        you[6] += rem
        you[0] = you[1] = you[2] = you[3] = you[4] = you[5] = 0
    if not opp_empty:
        rem = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]
        opp[6] += rem
        opp[0] = opp[1] = opp[2] = opp[3] = opp[4] = opp[5] = 0
    return True


def _apply_move(you: List[int], opp: List[int], move: int) -> Tuple[List[int], List[int], bool]:
    """
    Apply move for current player.
    Returns (new_you, new_opp, extra_turn).
    """
    y = you[:]   # small fixed-size lists, copying is cheap
    o = opp[:]

    seeds = y[move]
    y[move] = 0

    side = 0  # 0 = your side (houses/store), 1 = opp houses
    pos = move

    while seeds > 0:
        if side == 0:
            pos += 1
            if pos == 6:
                y[6] += 1
                seeds -= 1
                if seeds == 0:
                    extra = True
                    _finalize_if_game_over(y, o)
                    return y, o, extra
                side = 1
                pos = -1
            else:
                y[pos] += 1
                seeds -= 1
        else:
            pos += 1
            if pos == 6:
                side = 0
                pos = -1
            else:
                o[pos] += 1
                seeds -= 1

    # Last seed landed somewhere that is not your store.
    extra = False

    # Capture rule: last seed landed in your empty house, and opposite has seeds.
    if side == 0 and 0 <= pos <= 5 and y[pos] == 1 and o[5 - pos] > 0:
        y[6] += 1 + o[5 - pos]
        y[pos] = 0
        o[5 - pos] = 0

    _finalize_if_game_over(y, o)
    return y, o, extra


def _is_terminal(you: List[int], opp: List[int]) -> bool:
    return ((you[0] | you[1] | you[2] | you[3] | you[4] | you[5]) == 0 or
            (opp[0] | opp[1] | opp[2] | opp[3] | opp[4] | opp[5]) == 0)


def _count_extra_turn_moves(you: List[int]) -> int:
    cnt = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        # Exact sowing path length to own store in a 13-slot cycle (excluding opp store).
        # We can detect by simulating modularly.
        # Positions in cycle from current pit:
        # your pits after i, your store, opp pits, your pits...
        # Simpler and safe: small bounded simulation.
        pos_side = 0
        pos = i
        rem = s
        while rem > 0:
            if pos_side == 0:
                pos += 1
                if pos == 6:
                    rem -= 1
                    if rem == 0:
                        cnt += 1
                        break
                    pos_side = 1
                    pos = -1
                else:
                    rem -= 1
            else:
                pos += 1
                if pos == 6:
                    pos_side = 0
                    pos = -1
                else:
                    rem -= 1
    return cnt


def _capture_potential(you: List[int], opp: List[int]) -> int:
    """
    Rough tactical heuristic:
    sum opponent seeds that could be captured by landing exactly in an empty house.
    """
    pot = 0
    for target in range(6):
        if you[target] != 0 or opp[5 - target] == 0:
            continue
        # Can some move end at target?
        for i in range(6):
            s = you[i]
            if s <= 0:
                continue
            # Simulate last landing spot only, on 13-slot cycle excluding opp store.
            side = 0
            pos = i
            rem = s
            while rem > 0:
                if side == 0:
                    pos += 1
                    if pos == 6:
                        rem -= 1
                        if rem == 0:
                            # store, no capture
                            break
                        side = 1
                        pos = -1
                    else:
                        rem -= 1
                        if rem == 0 and pos == target:
                            pot += opp[5 - target]
                            rem = -1
                            break
                else:
                    pos += 1
                    if pos == 6:
                        side = 0
                        pos = -1
                    else:
                        rem -= 1
            if rem == -1:
                break
    return pot


def _evaluate(you: List[int], opp: List[int]) -> int:
    """
    Static evaluation from current player's perspective.
    Large values are good for current player.
    """
    if _is_terminal(you, opp):
        # Terminal states should already be swept, but handle robustly.
        y_store = you[6] + sum(you[:6]) if sum(opp[:6]) == 0 else you[6]
        o_store = opp[6] + sum(opp[:6]) if sum(you[:6]) == 0 else opp[6]
        diff = y_store - o_store
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    your_side = sum(you[:6])
    opp_side = sum(opp[:6])

    store_diff = you[6] - opp[6]
    side_diff = your_side - opp_side

    your_extras = _count_extra_turn_moves(you)
    opp_extras = _count_extra_turn_moves(opp)

    your_caps = _capture_potential(you, opp)
    opp_caps = _capture_potential(opp, you)

    # Slight bias toward seeds closer to your store and against opponent's.
    positional = (
        1 * you[0] + 2 * you[1] + 3 * you[2] + 4 * you[3] + 5 * you[4] + 6 * you[5]
        - (1 * opp[5] + 2 * opp[4] + 3 * opp[3] + 4 * opp[2] + 5 * opp[1] + 6 * opp[0])
    )

    return (
        28 * store_diff +
        3 * side_diff +
        8 * (your_extras - opp_extras) +
        2 * (your_caps - opp_caps) +
        positional
    )


def _ordered_children(you: List[int], opp: List[int]):
    moves = []
    for m in range(6):
        if you[m] <= 0:
            continue
        ny, no, extra = _apply_move(you, opp, m)
        # Order by tactical promise.
        score = 0
        if extra:
            score += 1000
        score += 25 * ((ny[6] - you[6]) - (no[6] - opp[6]))
        # Reward reducing opponent tactical resources / increasing ours
        score += 2 * (_count_extra_turn_moves(ny) - _count_extra_turn_moves(no))
        # Prefer moves from rightmost pits slightly (often nearer store)
        score += m
        moves.append((score, m, ny, no, extra))
    moves.sort(reverse=True, key=lambda x: x[0])
    return moves


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Return a legal move index 0..5.
    """

    legal = _legal_moves(you)
    if not legal:
        return 0  # Should never happen per problem statement.
    if len(legal) == 1:
        return legal[0]

    start = time.perf_counter()
    TIME_LIMIT = 0.92  # keep some safety margin

    # Safe default: greedily prefer extra turn / capture / store gain.
    default_best = legal[0]
    best_score = -INF
    for _, m, ny, no, extra in _ordered_children(you, opponent):
        score = _evaluate(ny, no) if extra else -_evaluate(no, ny)
        if score > best_score:
            best_score = score
            default_best = m

    trans: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int], Tuple[int, int]] = {}

    def check_time():
        if time.perf_counter() - start > TIME_LIMIT:
            raise _Timeout

    def search(y: List[int], o: List[int], depth: int, alpha: int, beta: int) -> int:
        check_time()

        key = (tuple(y), tuple(o), depth)
        tt = trans.get(key)
        if tt is not None:
            stored_depth, stored_val = tt
            if stored_depth >= depth:
                return stored_val

        if depth <= 0 or _is_terminal(y, o):
            val = _evaluate(y, o)
            trans[key] = (depth, val)
            return val

        best = -INF
        children = _ordered_children(y, o)
        if not children:
            # Shouldn't happen unless terminal, but stay safe.
            val = _evaluate(y, o)
            trans[key] = (depth, val)
            return val

        for _, m, ny, no, extra in children:
            if extra:
                val = search(ny, no, depth - 1, alpha, beta)
            else:
                val = -search(no, ny, depth - 1, -beta, -alpha)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        trans[key] = (depth, best)
        return best

    # Iterative deepening.
    best_move = default_best
    depth = 1
    try:
        while True:
            check_time()
            current_best_move = best_move
            current_best_val = -INF

            alpha = -INF
            beta = INF

            children = _ordered_children(you, opponent)
            for _, m, ny, no, extra in children:
                check_time()
                if extra:
                    val = search(ny, no, depth - 1, alpha, beta)
                else:
                    val = -search(no, ny, depth - 1, -beta, -alpha)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = m
                if val > alpha:
                    alpha = val

            best_move = current_best_move
            depth += 1

    except _Timeout:
        pass

    # Absolute safety: ensure legal.
    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return legal[0]
