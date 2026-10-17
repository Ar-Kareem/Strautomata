
# Kalah policy for a standard 6-house board.
# API:
#   policy(you: list[int], opponent: list[int]) -> int

import time
import math

_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _legal_moves(side):
    return [i for i in range(6) if side[i] > 0]


def _game_score(cur, opp):
    """Exact score from current player's perspective, assuming stores are final."""
    return cur[6] - opp[6]


def _apply_move(cur, opp, move):
    """
    Apply move for current player.
    Returns: (new_cur, new_opp, same_turn, terminal)
    """
    c = cur[:]
    o = opp[:]

    seeds = c[move]
    c[move] = 0
    pos = move

    # Board positions in sowing order:
    # 0..5 = current player's houses
    # 6    = current player's store
    # 7..12 = opponent houses 0..5
    # Opponent store is skipped.
    last_pos = None

    while seeds:
        pos = (pos + 1) % 13
        if pos <= 5:
            c[pos] += 1
        elif pos == 6:
            c[6] += 1
        else:
            o[pos - 7] += 1
        last_pos = pos
        seeds -= 1

    # Capture: last seed lands in an own empty house, opposite has seeds.
    if last_pos is not None and 0 <= last_pos <= 5:
        idx = last_pos
        opp_idx = 5 - idx
        if c[idx] == 1 and o[opp_idx] > 0:
            c[6] += c[idx] + o[opp_idx]
            c[idx] = 0
            o[opp_idx] = 0

    # Endgame sweep.
    terminal = False
    if sum(c[:6]) == 0 or sum(o[:6]) == 0:
        c[6] += sum(c[:6])
        o[6] += sum(o[:6])
        for i in range(6):
            c[i] = 0
            o[i] = 0
        terminal = True

    same_turn = (last_pos == 6) and not terminal
    return c, o, same_turn, terminal


def _extra_turn_move(side, i):
    # Last seed lands in own store iff seeds exactly reach store modulo cycle length 13.
    return side[i] > 0 and ((side[i] - (6 - i)) % 13 == 0)


def _capture_gain(cur, opp, i):
    """Fast approximate capture gain for move ordering only."""
    seeds = cur[i]
    if seeds <= 0:
        return 0

    # Simulate just enough to find final position and whether target was empty before.
    pos = i
    for _ in range(seeds):
        pos = (pos + 1) % 13

    if 0 <= pos <= 5:
        # Number of seeds dropped into this own pit during sowing.
        # A capture requires that it was empty before the final drop.
        # Use full simulation for correctness in ordering approximation.
        c = cur[:]
        o = opp[:]
        before = c[pos]
        cc, oo, _, _ = _apply_move(c, o, i)
        # If store increased by more than direct store sowing, likely capture.
        return max(0, cc[6] - cur[6])
    return 0


def _heuristic(cur, opp):
    """
    Evaluation from current player's perspective.
    Store difference dominates; other terms guide non-terminal positions.
    """
    if sum(cur[:6]) == 0 or sum(opp[:6]) == 0:
        c = cur[:]
        o = opp[:]
        c[6] += sum(c[:6])
        o[6] += sum(o[:6])
        return 100000 * (c[6] - o[6])

    store_diff = cur[6] - opp[6]
    house_diff = sum(cur[:6]) - sum(opp[:6])

    cur_moves = _legal_moves(cur)
    opp_moves = _legal_moves(opp)

    extra = 0
    for i in cur_moves:
        if _extra_turn_move(cur, i):
            extra += 1
    for i in opp_moves:
        if _extra_turn_move(opp, i):
            extra -= 1

    # Potential captures.
    cap = 0
    for i in cur_moves:
        cap += _capture_gain(cur, opp, i)
    for i in opp_moves:
        cap -= _capture_gain(opp, cur, i)

    mobility = len(cur_moves) - len(opp_moves)

    # Seeds closer to store are slightly better for current player.
    positional = 0
    for i in range(6):
        positional += (i + 1) * cur[i]
        positional -= (i + 1) * opp[i]

    return (
        1200 * store_diff
        + 20 * house_diff
        + 80 * extra
        + 45 * cap
        + 8 * mobility
        + 2 * positional
    )


def _ordered_moves(cur, opp):
    moves = _legal_moves(cur)

    def key(m):
        nc, no, same, terminal = _apply_move(cur, opp, m)
        if terminal:
            return 10_000_000 + 100000 * _game_score(nc, no)
        score = 0
        score += 5000 if same else 0
        score += 1000 * (nc[6] - cur[6])
        score += 20 * (sum(nc[:6]) - sum(no[:6]))
        # Prefer moves that do not leave us empty unless terminal is favorable.
        score += _heuristic(nc, no) // 50
        return score

    moves.sort(key=key, reverse=True)
    return moves


def _search(cur, opp, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()

    if depth <= 0:
        return _heuristic(cur, opp)

    moves = _legal_moves(cur)
    if not moves:
        # Should not happen for calls from policy, but keep safe.
        c = cur[:]
        o = opp[:]
        c[6] += sum(c[:6])
        o[6] += sum(o[:6])
        return 100000 * (c[6] - o[6])

    best = -math.inf

    for m in _ordered_moves(cur, opp):
        nc, no, same, terminal = _apply_move(cur, opp, m)

        if terminal:
            val = 100000 * _game_score(nc, no)
        elif same:
            # Same player moves again, perspective unchanged.
            val = _search(nc, no, depth - 1, alpha, beta)
        else:
            # Turn changes; swap perspective and negate.
            val = -_search(no, nc, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal move index 0..5 with you[index] > 0.
    """
    global _DEADLINE, _NODES

    legal = _legal_moves(you)
    if not legal:
        # The prompt says this will never be called, but return safely anyway.
        return 0

    # Always have a legal fallback.
    best_move = legal[0]

    # Immediate tactical shortcut: if a move ends the game winning/tied best, consider it.
    immediate_best = None
    immediate_score = -math.inf
    for m in legal:
        nc, no, same, terminal = _apply_move(you, opponent, m)
        if terminal:
            sc = _game_score(nc, no)
            if sc > immediate_score:
                immediate_score = sc
                immediate_best = m
    if immediate_best is not None and immediate_score >= 0:
        return immediate_best

    # Time budget. Leave margin under a 1 second arena limit.
    _DEADLINE = time.perf_counter() + 0.88

    try:
        # Iterative deepening keeps the best completed result.
        # Depth counts individual moves, including extra-turn moves.
        for depth in range(1, 64):
            if time.perf_counter() > _DEADLINE:
                break

            _NODES = 0
            alpha = -math.inf
            beta = math.inf
            current_best = best_move
            current_score = -math.inf

            for m in _ordered_moves(you, opponent):
                if time.perf_counter() > _DEADLINE:
                    raise _Timeout()

                nc, no, same, terminal = _apply_move(you, opponent, m)

                if terminal:
                    val = 100000 * _game_score(nc, no)
                elif same:
                    val = _search(nc, no, depth - 1, alpha, beta)
                else:
                    val = -_search(no, nc, depth - 1, -beta, -alpha)

                if val > current_score:
                    current_score = val
                    current_best = m

                if val > alpha:
                    alpha = val

            # Completed this depth successfully.
            best_move = current_best

    except _Timeout:
        pass
    except Exception:
        # Never risk returning an illegal move due to an unexpected issue.
        return legal[0]

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return legal[0]
