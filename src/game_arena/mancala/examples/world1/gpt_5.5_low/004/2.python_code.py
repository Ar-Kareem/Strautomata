
import time
from math import inf

class _Timeout(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move index 0..5 for the current player.
    """

    start_time = time.perf_counter()
    TIME_LIMIT = 0.88  # keep margin under 1 second

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # should never happen per specification

    # Simple strong tactical fallback: prefer immediate extra move, then capture.
    fallback = legal[0]
    best_tactical_score = -10**18
    for m in legal:
        ny, no, extra, terminal = _apply_move(tuple(you), tuple(opponent), m)
        score = (ny[6] - you[6]) * 100
        if extra:
            score += 500
        score += _static_eval(ny, no)
        if score > best_tactical_score:
            best_tactical_score = score
            fallback = m

    best_move = fallback
    tt = {}
    nodes = [0]

    def time_check():
        nodes[0] += 1
        if nodes[0] & 255 == 0:
            if time.perf_counter() - start_time > TIME_LIMIT:
                raise _Timeout()

    def negamax(my, opp, depth, alpha, beta):
        time_check()

        key = (my, opp, depth)
        cached = tt.get(key)
        if cached is not None:
            return cached

        my_empty = not any(my[:6])
        opp_empty = not any(opp[:6])
        if my_empty or opp_empty:
            val = _terminal_value(my, opp)
            tt[key] = val
            return val

        if depth <= 0:
            val = _static_eval(my, opp)
            tt[key] = val
            return val

        moves = [i for i in range(6) if my[i] > 0]
        if not moves:
            val = _terminal_value(my, opp)
            tt[key] = val
            return val

        moves.sort(key=lambda m: _move_order_score(my, opp, m), reverse=True)

        best = -10**18
        original_alpha = alpha

        for m in moves:
            nmy, nopp, extra, terminal = _apply_move(my, opp, m)

            if terminal:
                val = _terminal_value(nmy, nopp)
            elif extra:
                val = negamax(nmy, nopp, depth - 1, alpha, beta)
            else:
                val = -negamax(nopp, nmy, depth - 1, -beta, -alpha)

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        tt[key] = best
        return best

    # Iterative deepening. Depths beyond this are often reachable in endgames.
    max_depth = 32

    try:
        for depth in range(1, max_depth + 1):
            current_best_move = best_move
            current_best_score = -10**18

            root_moves = [i for i in range(6) if you[i] > 0]
            root_moves.sort(
                key=lambda m: _move_order_score(tuple(you), tuple(opponent), m),
                reverse=True
            )

            alpha = -10**18
            beta = 10**18

            for m in root_moves:
                if time.perf_counter() - start_time > TIME_LIMIT:
                    raise _Timeout()

                nmy, nopp, extra, terminal = _apply_move(tuple(you), tuple(opponent), m)

                if terminal:
                    val = _terminal_value(nmy, nopp)
                elif extra:
                    val = negamax(nmy, nopp, depth - 1, alpha, beta)
                else:
                    val = -negamax(nopp, nmy, depth - 1, -beta, -alpha)

                if val > current_best_score:
                    current_best_score = val
                    current_best_move = m

                if val > alpha:
                    alpha = val

            best_move = current_best_move

    except _Timeout:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        return fallback

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return fallback


def _apply_move(my, opp, move):
    """
    Apply move for current player.
    Returns: new_my, new_opp, extra_turn, terminal
    my and opp are tuples/lists length 7.
    """
    my = list(my)
    opp = list(opp)

    seeds = my[move]
    my[move] = 0

    # Ring positions excluding opponent store:
    # 0..5 = my houses, 6 = my store, 7..12 = opponent houses
    pos = move
    last_side = None
    last_idx = None

    while seeds > 0:
        pos = (pos + 1) % 13

        if pos <= 5:
            my[pos] += 1
            last_side = 0
            last_idx = pos
        elif pos == 6:
            my[6] += 1
            last_side = 0
            last_idx = 6
        else:
            oi = pos - 7
            opp[oi] += 1
            last_side = 1
            last_idx = oi

        seeds -= 1

    extra = (last_side == 0 and last_idx == 6)

    # Capture rule.
    if last_side == 0 and 0 <= last_idx <= 5 and my[last_idx] == 1:
        opposite = 5 - last_idx
        if opp[opposite] > 0:
            my[6] += opp[opposite] + my[last_idx]
            opp[opposite] = 0
            my[last_idx] = 0

    terminal = False
    if not any(my[:6]) or not any(opp[:6]):
        terminal = True
        my[6] += sum(my[:6])
        opp[6] += sum(opp[:6])
        for i in range(6):
            my[i] = 0
            opp[i] = 0

    return tuple(my), tuple(opp), extra, terminal


def _terminal_value(my, opp):
    """
    Large exact terminal score from current side's perspective.
    """
    diff = my[6] - opp[6]
    if diff > 0:
        return 1_000_000 + diff * 10_000
    if diff < 0:
        return -1_000_000 + diff * 10_000
    return 0


def _static_eval(my, opp):
    """
    Heuristic score from current side's perspective.
    """
    if not any(my[:6]) or not any(opp[:6]):
        return _terminal_value(my, opp)

    store_diff = my[6] - opp[6]
    my_side = sum(my[:6])
    opp_side = sum(opp[:6])

    score = 0
    score += store_diff * 120
    score += (my_side - opp_side) * 4

    # Prefer houses closer to our store because they can create extra turns.
    for i in range(6):
        score += my[i] * (i + 1)
        score -= opp[i] * (i + 1)

    # Immediate extra-turn opportunities.
    for i in range(6):
        if my[i] > 0 and my[i] == 6 - i:
            score += 80
        if opp[i] > 0 and opp[i] == 6 - i:
            score -= 80

    # Immediate capture opportunities and capture threats.
    for i in range(6):
        if my[i] > 0:
            landing = i + my[i]
            if landing < 6 and my[landing] == 0 and opp[5 - landing] > 0:
                score += 35 + 12 * opp[5 - landing]

        if opp[i] > 0:
            landing = i + opp[i]
            if landing < 6 and opp[landing] == 0 and my[5 - landing] > 0:
                score -= 35 + 12 * my[5 - landing]

    # Slightly reward having legal flexibility.
    score += sum(1 for x in my[:6] if x > 0) * 6
    score -= sum(1 for x in opp[:6] if x > 0) * 6

    return score


def _move_order_score(my, opp, move):
    """
    Fast move ordering heuristic.
    """
    nmy, nopp, extra, terminal = _apply_move(my, opp, move)

    if terminal:
        return _terminal_value(nmy, nopp)

    score = 0
    score += (nmy[6] - my[6]) * 1000
    if extra:
        score += 5000

    # Reward store gain and captures.
    captured_gain = nmy[6] - my[6]
    score += captured_gain * 300

    # Prefer moves that do not leave us empty unless winning.
    if not any(nmy[:6]):
        score -= 200

    score += _static_eval(nmy, nopp) // 4
    return score
