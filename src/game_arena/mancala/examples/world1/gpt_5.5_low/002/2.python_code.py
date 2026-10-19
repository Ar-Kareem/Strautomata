
import time
import math

# Time budget per policy call. Kept below 1s to avoid arena timeouts.
_TIME_LIMIT = 0.88
_DEADLINE = 0.0
_NODE_COUNT = 0


class _Timeout(Exception):
    pass


def _legal_moves(side):
    return [i for i in range(6) if side[i] > 0]


def _is_empty_houses(side):
    return side[0] == 0 and side[1] == 0 and side[2] == 0 and side[3] == 0 and side[4] == 0 and side[5] == 0


def _finish_game(you, opp):
    """Collect remaining house seeds into stores and return finished copies."""
    y = you[:]
    o = opp[:]
    y_rem = sum(y[:6])
    o_rem = sum(o[:6])
    if y_rem:
        y[6] += y_rem
        for i in range(6):
            y[i] = 0
    if o_rem:
        o[6] += o_rem
        for i in range(6):
            o[i] = 0
    return y, o


def _simulate_move(you, opp, move):
    """
    Simulate move for the side represented by 'you'.
    Returns: new_you, new_opp, extra_turn, terminal
    """
    y = you[:]
    o = opp[:]

    seeds = y[move]
    y[move] = 0

    # Ring positions:
    # 0..5   -> own houses
    # 6      -> own store
    # 7..12  -> opponent houses 0..5
    # Opponent store is skipped.
    pos = move

    while seeds:
        pos += 1
        if pos == 13:
            pos = 0

        if pos <= 5:
            y[pos] += 1
        elif pos == 6:
            y[6] += 1
        else:
            o[pos - 7] += 1
        seeds -= 1

    extra = (pos == 6)

    # Capture: last seed in own house that was empty before the drop.
    if 0 <= pos <= 5 and y[pos] == 1:
        opposite = 5 - pos
        if o[opposite] > 0:
            y[6] += o[opposite] + 1
            y[pos] = 0
            o[opposite] = 0

    terminal = _is_empty_houses(y) or _is_empty_houses(o)
    if terminal:
        y, o = _finish_game(y, o)
        extra = False

    return y, o, extra, terminal


def _move_tactical_score(you, opp, move):
    """Cheap ordering score for alpha-beta move ordering."""
    y2, o2, extra, terminal = _simulate_move(you, opp, move)
    score = 0

    # Store gain is usually very important.
    score += 10 * (y2[6] - you[6])

    # Extra turns are extremely valuable in Kalah.
    if extra:
        score += 60

    # Terminal winning positions should be searched first.
    if terminal:
        score += 1000 * (y2[6] - o2[6])

    # Prefer moves that reduce opponent material and preserve ours.
    score += 2 * (sum(y2[:6]) - sum(o2[:6]))

    # Slight preference for rightmost pits because they more often reach store.
    score += move

    return score


def _ordered_moves(you, opp):
    moves = _legal_moves(you)
    moves.sort(key=lambda m: _move_tactical_score(you, opp, m), reverse=True)
    return moves


def _static_eval(you, opp):
    """
    Evaluation from the point of view of the side to move represented by 'you'.
    Positive is good for 'you'.
    """
    if _is_empty_houses(you) or _is_empty_houses(opp):
        fy, fo = _finish_game(you, opp)
        return 10000 * (fy[6] - fo[6])

    store_diff = you[6] - opp[6]
    house_diff = sum(you[:6]) - sum(opp[:6])

    val = 100.0 * store_diff + 4.0 * house_diff

    # Bonus for immediate extra-turn opportunities.
    for i in range(6):
        if you[i] > 0 and you[i] == 6 - i:
            val += 18.0

    # Bonus for immediate capture opportunities.
    for i in range(6):
        seeds = you[i]
        if seeds <= 0:
            continue
        # For small/normal seed counts, determine if last lands on own side.
        # Simpler exact check via simulation; only six moves, acceptable.
        y2, o2, extra, terminal = _simulate_move(you, opp, i)
        gained = y2[6] - you[6]
        if gained > 1:
            val += 10.0 * gained

    # Penalize giving opponent obvious extra turns.
    for i in range(6):
        if opp[i] > 0 and opp[i] == 6 - i:
            val -= 12.0

    return val


def _negamax(you, opp, depth, alpha, beta):
    global _NODE_COUNT, _DEADLINE

    _NODE_COUNT += 1
    if (_NODE_COUNT & 1023) == 0:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout()

    if depth <= 0 or _is_empty_houses(you) or _is_empty_houses(opp):
        return _static_eval(you, opp)

    moves = _ordered_moves(you, opp)
    if not moves:
        return _static_eval(you, opp)

    best = -math.inf

    for m in moves:
        y2, o2, extra, terminal = _simulate_move(you, opp, m)

        if terminal:
            val = _static_eval(y2, o2)
        elif extra:
            # Same player moves again, so no perspective swap.
            val = _negamax(y2, o2, depth - 1, alpha, beta)
        else:
            # Turn passes: swap sides and negate value.
            val = -_negamax(o2, y2, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _root_search(you, opp, depth):
    moves = _ordered_moves(you, opp)
    best_move = moves[0]
    best_val = -math.inf
    alpha = -math.inf
    beta = math.inf

    for m in moves:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout()

        y2, o2, extra, terminal = _simulate_move(you, opp, m)

        if terminal:
            val = _static_eval(y2, o2)
        elif extra:
            val = _negamax(y2, o2, depth - 1, alpha, beta)
        else:
            val = -_negamax(o2, y2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if best_val > alpha:
            alpha = best_val

    return best_move, best_val


def _fallback_move(you, opp):
    """Always returns a legal move, using a quick tactical heuristic."""
    moves = _legal_moves(you)
    # policy is never called with no legal move, but be defensive anyway.
    if not moves:
        return 0
    return max(moves, key=lambda m: _move_tactical_score(you, opp, m))


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move index 0..5 for the current player.
    """
    global _DEADLINE, _NODE_COUNT

    legal = _legal_moves(you)
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    _DEADLINE = time.perf_counter() + _TIME_LIMIT
    _NODE_COUNT = 0

    best_move = _fallback_move(you, opponent)

    # Iterative deepening: keep best completed depth.
    # Depth can grow high in forced/low-branching endgames.
    try:
        depth = 1
        while depth <= 40:
            move, val = _root_search(you, opponent, depth)
            best_move = move
            depth += 1
            if time.perf_counter() >= _DEADLINE:
                break
    except _Timeout:
        pass
    except Exception:
        # Never risk returning an illegal move due to an unexpected issue.
        best_move = _fallback_move(you, opponent)

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return int(best_move)

    return int(_fallback_move(you, opponent))
