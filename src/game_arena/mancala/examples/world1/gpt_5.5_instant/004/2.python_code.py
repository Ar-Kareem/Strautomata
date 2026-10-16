
# Kalah policy for a 6-house standard board.
# Implements: policy(you: list[int], opponent: list[int]) -> int

from functools import lru_cache
import time
import math

N = 6
STORE = 6
INF = 10**9


def _legal(side):
    return [i for i in range(N) if side[i] > 0]


def _game_over(a, b):
    return all(x == 0 for x in a[:N]) or all(x == 0 for x in b[:N])


def _collect_terminal(a, b):
    a = list(a)
    b = list(b)
    if all(x == 0 for x in a[:N]):
        s = sum(b[:N])
        for i in range(N):
            b[i] = 0
        b[STORE] += s
    elif all(x == 0 for x in b[:N]):
        s = sum(a[:N])
        for i in range(N):
            a[i] = 0
        a[STORE] += s
    return tuple(a), tuple(b)


def _apply_move(me, opp, move):
    """
    Returns (new_me, new_opp, extra_turn), from the perspective of the mover.
    me/opp are tuples/lists length 7.
    """
    me = list(me)
    opp = list(opp)
    seeds = me[move]
    me[move] = 0

    # Ring positions skip opponent store:
    # 0..5: my houses, 6: my store, 7..12: opponent houses 0..5
    pos = move
    last_zone = None
    last_idx = None

    while seeds:
        pos = (pos + 1) % 13
        if pos < 6:
            me[pos] += 1
            last_zone = 0
            last_idx = pos
        elif pos == 6:
            me[STORE] += 1
            last_zone = 1
            last_idx = STORE
        else:
            oi = pos - 7
            opp[oi] += 1
            last_zone = 2
            last_idx = oi
        seeds -= 1

    extra = (last_zone == 1)

    # Capture: last seed in own empty house, opposite has seeds.
    if last_zone == 0 and me[last_idx] == 1:
        opp_idx = N - 1 - last_idx
        if opp[opp_idx] > 0:
            me[STORE] += opp[opp_idx] + 1
            me[last_idx] = 0
            opp[opp_idx] = 0

    return tuple(me), tuple(opp), extra


def _immediate_features(me, opp, move):
    """Used for move ordering."""
    seeds = me[move]
    # Last position on 13-slot ring from mover's view.
    last = (move + seeds) % 13
    extra = 1 if last == 6 else 0

    cap = 0
    if 0 <= last <= 5:
        # Last lands in own house. It must have been empty before last drop.
        # If seeds < 13, no full lap revisits; for larger, estimate exactly enough.
        # Simpler conservative simulation for ordering only:
        m2, o2, ex = _apply_move(me, opp, move)
        cap = max(0, m2[STORE] - me[STORE] - (1 if extra else 0))
        extra = 1 if ex else extra

    return extra, cap, seeds


def _evaluate(me, opp):
    """
    Evaluation from current root player's perspective.
    me is root player's side, opp is opponent side.
    """
    if _game_over(me, opp):
        a, b = _collect_terminal(me, opp)
        diff = a[STORE] - b[STORE]
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    store_diff = me[STORE] - opp[STORE]
    my_seeds = sum(me[:N])
    op_seeds = sum(opp[:N])

    # Extra move opportunities.
    my_extra = sum(1 for i in range(N) if me[i] > 0 and (i + me[i]) % 13 == 6)
    op_extra = sum(1 for i in range(N) if opp[i] > 0 and (i + opp[i]) % 13 == 6)

    # Immediate capture potentials.
    my_caps = 0
    for i in range(N):
        if me[i] <= 0:
            continue
        m2, o2, _ = _apply_move(me, opp, i)
        gain = m2[STORE] - me[STORE]
        if gain > 1:
            my_caps += gain

    op_caps = 0
    for i in range(N):
        if opp[i] <= 0:
            continue
        o2, m2, _ = _apply_move(opp, me, i)
        gain = o2[STORE] - opp[STORE]
        if gain > 1:
            op_caps += gain

    # Slight preference for seeds on own side when ahead in tempo,
    # but store lead dominates.
    return (
        120 * store_diff
        + 4 * (my_seeds - op_seeds)
        + 18 * (my_extra - op_extra)
        + 7 * (my_caps - op_caps)
    )


def _ordered_moves(me, opp):
    moves = _legal(me)

    def key(m):
        extra, cap, seeds = _immediate_features(me, opp, m)
        # Prefer extra turns, captures, then rightward pits which often chain.
        return (extra, cap, -abs(6 - (m + seeds)), m)

    return sorted(moves, key=key, reverse=True)


def policy(you: list[int], opponent: list[int]) -> int:
    start = time.time()
    time_limit = 0.92

    you_t = tuple(int(x) for x in you)
    opp_t = tuple(int(x) for x in opponent)
    legal = _legal(you_t)

    # Absolute safety fallback.
    if not legal:
        return 0
    fallback = legal[0]

    # Tactical shortcut: if a move ends the game favorably, take it.
    best_static = fallback
    best_static_val = -INF
    for m in legal:
        nm, no, extra = _apply_move(you_t, opp_t, m)
        if _game_over(nm, no):
            cm, co = _collect_terminal(nm, no)
            val = 1000000 + cm[STORE] - co[STORE]
        else:
            val = _evaluate(nm, no)
            if not extra:
                # after opponent turn, rough discount
                val -= 10
        if val > best_static_val:
            best_static_val = val
            best_static = m

    best_move = best_static

    @lru_cache(maxsize=200000)
    def search(me, opp, turn, depth, alpha, beta):
        """
        me/opp are fixed as root player's side and opponent side.
        turn = 0 root to move, 1 opponent to move.
        """
        if time.time() - start > time_limit:
            return _evaluate(me, opp)

        if _game_over(me, opp):
            cm, co = _collect_terminal(me, opp)
            diff = cm[STORE] - co[STORE]
            if diff > 0:
                return 1000000 + diff
            if diff < 0:
                return -1000000 + diff
            return 0

        if depth <= 0:
            return _evaluate(me, opp)

        if turn == 0:
            moves = _ordered_moves(me, opp)
            if not moves:
                return _evaluate(me, opp)
            val = -INF
            for mv in moves:
                nme, nopp, extra = _apply_move(me, opp, mv)
                nt = 0 if extra else 1
                nd = depth if extra else depth - 1
                score = search(nme, nopp, nt, nd, alpha, beta)
                if score > val:
                    val = score
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break
            return val
        else:
            moves = _ordered_moves(opp, me)
            if not moves:
                return _evaluate(me, opp)
            val = INF
            for mv in moves:
                nopp, nme, extra = _apply_move(opp, me, mv)
                nt = 1 if extra else 0
                nd = depth if extra else depth - 1
                score = search(nme, nopp, nt, nd, alpha, beta)
                if score < val:
                    val = score
                if val < beta:
                    beta = val
                if alpha >= beta:
                    break
            return val

    # Iterative deepening. Kalah branching is small, but extra turns can extend lines.
    try:
        max_depth = 8
        total_seeds = sum(you_t[:N]) + sum(opp_t[:N])
        if total_seeds <= 18:
            max_depth = 11
        elif total_seeds <= 28:
            max_depth = 9

        for depth in range(1, max_depth + 1):
            if time.time() - start > time_limit:
                break

            current_best = best_move
            current_val = -INF
            alpha = -INF
            beta = INF

            for mv in _ordered_moves(you_t, opp_t):
                if time.time() - start > time_limit:
                    break
                nme, nopp, extra = _apply_move(you_t, opp_t, mv)
                nt = 0 if extra else 1
                nd = depth if extra else depth - 1
                val = search(nme, nopp, nt, nd, alpha, beta)
                if val > current_val:
                    current_val = val
                    current_best = mv
                if val > alpha:
                    alpha = val

            if current_best in legal:
                best_move = current_best

    except Exception:
        # Never risk an illegal or missing move.
        best_move = best_static if best_static in legal else fallback

    if best_move not in legal or you[best_move] <= 0:
        return fallback
    return int(best_move)
