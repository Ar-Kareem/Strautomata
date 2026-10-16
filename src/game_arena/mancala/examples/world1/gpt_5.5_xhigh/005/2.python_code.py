
import time

_INF = 10 ** 30
_WIN = 10 ** 15

_TIME_LIMIT = 0.88
_MAX_DEPTH = 32
_CHECK_MASK = 511

_EXACT_SEEDS = 12
_EXACT_DEPTH = 10 ** 9

_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_TT_BONUS = 10 ** 20

_RINGS = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
    (7, 8, 9, 10, 11, 12, 13, 0, 1, 2, 3, 4, 5),
)
_OFF = (0, 7)
_OTHER = (7, 0)
_STORE = (6, 13)

_OPENING_STATE = (4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0)

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _Timeout(Exception):
    pass


def _tick():
    global _NODES
    _NODES += 1
    if (_NODES & _CHECK_MASK) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout()


def _sum0(s):
    return s[0] + s[1] + s[2] + s[3] + s[4] + s[5]


def _sum1(s):
    return s[7] + s[8] + s[9] + s[10] + s[11] + s[12]


def _terminal_from_sums(s, my_side, op_side):
    diff = (s[6] + my_side) - (s[13] + op_side)
    if diff > 0:
        return _WIN + diff
    if diff < 0:
        return -_WIN + diff
    return 0


def _save_tt(key, depth, value, flag, move):
    old = _TT.get(key)
    if old is None or depth > old[0] or (
        depth == old[0] and (old[2] != _TT_EXACT or flag == _TT_EXACT)
    ):
        _TT[key] = (depth, value, flag, move)


def _make_move(s, player, move):
    ring = _RINGS[player]
    off = _OFF[player]
    other = _OTHER[player]
    store = _STORE[player]

    idx = off + move
    seeds = s[idx]

    b = list(s)
    b[idx] = 0

    q, r = divmod(seeds, 13)

    if q:
        for p in ring:
            b[p] += q

    pos = move
    for _ in range(r):
        pos += 1
        if pos == 13:
            pos = 0
        b[ring[pos]] += 1

    last_pos = (move + seeds) % 13
    last = ring[last_pos]

    # Capture.
    if off <= last < off + 6:
        loc = last - off
        opp_idx = other + (5 - loc)
        if b[last] == 1 and b[opp_idx] > 0:
            b[store] += b[opp_idx] + 1
            b[last] = 0
            b[opp_idx] = 0

    my_side = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    op_side = b[7] + b[8] + b[9] + b[10] + b[11] + b[12]

    # End of game: collect remaining seeds.
    if my_side == 0 or op_side == 0:
        if my_side:
            b[6] += my_side
            b[0] = b[1] = b[2] = b[3] = b[4] = b[5] = 0
        if op_side:
            b[13] += op_side
            b[7] = b[8] = b[9] = b[10] = b[11] = b[12] = 0
        return tuple(b), 1 - player, True

    return tuple(b), (player if last == store else 1 - player), False


def _side_potential(s, off, other):
    extra = 0
    cap_max = 0
    store_max = 0
    nonempty = 0

    for i in range(6):
        n = s[off + i]
        if n <= 0:
            continue

        nonempty += 1
        q, r = divmod(n, 13)

        # Seeds that would land in this side's own store.
        store_gain = q
        if r >= 6 - i:
            store_gain += 1
        if store_gain > store_max:
            store_max = store_gain

        last = (i + n) % 13
        if last == 6:
            extra += 1
        elif last < 6:
            j = last

            # Final number of seeds in the landing house.
            base = 0 if j == i else s[off + j]
            added_to_landing = q + (1 if r else 0)

            if base + added_to_landing == 1:
                # Opposite pit after any seeds dropped there during this move.
                opp_ring_pos = 12 - j
                dist_to_opp = opp_ring_pos - i
                if dist_to_opp <= 0:
                    dist_to_opp += 13

                opp_added = q + (1 if r and r >= dist_to_opp else 0)
                opp_final = s[other + 5 - j] + opp_added

                if opp_final > 0:
                    capture = opp_final + 1
                    if capture > cap_max:
                        cap_max = capture

    return extra, cap_max, store_max, nonempty


def _heuristic(s, player, my_side=None, op_side=None):
    if my_side is None:
        my_side = _sum0(s)
        op_side = _sum1(s)

    if my_side == 0 or op_side == 0:
        return _terminal_from_sums(s, my_side, op_side)

    store_diff = s[6] - s[13]
    side_diff = my_side - op_side

    my_adv = s[0] + 2 * s[1] + 3 * s[2] + 4 * s[3] + 5 * s[4] + 6 * s[5]
    op_adv = s[7] + 2 * s[8] + 3 * s[9] + 4 * s[10] + 5 * s[11] + 6 * s[12]

    my_extra, my_cap, my_store, my_non = _side_potential(s, 0, 7)
    op_extra, op_cap, op_store, op_non = _side_potential(s, 7, 0)

    score = 110 * store_diff
    score += 7 * side_diff
    score += 2 * (my_adv - op_adv)

    score += 30 * (my_extra - op_extra)
    score += 10 * (my_cap - op_cap)
    score += 5 * (my_store - op_store)
    score += 3 * (my_non - op_non)

    # Side to move matters, especially with immediate tactical chances.
    if player == 0:
        score += 12 + 10 * my_extra + 2 * my_cap + 2 * my_store
    else:
        score -= 12 + 10 * op_extra + 2 * op_cap + 2 * op_store

    # Endgame sweep pressure.
    if op_non <= 2:
        score += 2 * my_side
    if my_non <= 2:
        score -= 2 * op_side

    return score


def _order_score(s, player):
    my_side = _sum0(s)
    op_side = _sum1(s)

    if my_side == 0 or op_side == 0:
        return _terminal_from_sums(s, my_side, op_side)

    my_adv = s[0] + 2 * s[1] + 3 * s[2] + 4 * s[3] + 5 * s[4] + 6 * s[5]
    op_adv = s[7] + 2 * s[8] + 3 * s[9] + 4 * s[10] + 5 * s[11] + 6 * s[12]

    score = 100 * (s[6] - s[13])
    score += 5 * (my_side - op_side)
    score += my_adv - op_adv
    score += 8 if player == 0 else -8
    return score


def _ordered_children(s, player, ttmove):
    off = _OFF[player]
    children = []

    for m in range(6):
        if s[off + m] > 0:
            child, next_player, _ = _make_move(s, player, m)
            priority = _order_score(child, next_player)

            if m == ttmove:
                if player == 0:
                    priority += _TT_BONUS
                else:
                    priority -= _TT_BONUS

            children.append((priority, m, child, next_player))

    children.sort(reverse=(player == 0))
    return children


def _solve_exact(s, player, alpha, beta):
    _tick()

    my_side = _sum0(s)
    op_side = _sum1(s)

    if my_side == 0 or op_side == 0:
        return _terminal_from_sums(s, my_side, op_side)

    key = (s, player)
    orig_alpha = alpha
    orig_beta = beta
    ttmove = None

    entry = _TT.get(key)
    if entry is not None:
        ed, ev, ef, em = entry
        ttmove = em
        if ed >= _EXACT_DEPTH:
            if ef == _TT_EXACT:
                return ev
            if ef == _TT_LOWER:
                if ev >= beta:
                    return ev
                if ev > alpha:
                    alpha = ev
            elif ef == _TT_UPPER:
                if ev <= alpha:
                    return ev
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev

    children = _ordered_children(s, player, ttmove)
    if not children:
        return _terminal_from_sums(s, my_side, op_side)

    if player == 0:
        best = -_INF
        best_move = children[0][1]

        for _, m, child, next_player in children:
            val = _solve_exact(child, next_player, alpha, beta)
            if val > best:
                best = val
                best_move = m
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = _INF
        best_move = children[0][1]

        for _, m, child, next_player in children:
            val = _solve_exact(child, next_player, alpha, beta)
            if val < best:
                best = val
                best_move = m
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    if best <= orig_alpha:
        flag = _TT_UPPER
    elif best >= orig_beta:
        flag = _TT_LOWER
    else:
        flag = _TT_EXACT

    _save_tt(key, _EXACT_DEPTH, best, flag, best_move)
    return best


def _alphabeta(s, player, depth, alpha, beta):
    _tick()

    my_side = _sum0(s)
    op_side = _sum1(s)

    if my_side == 0 or op_side == 0:
        return _terminal_from_sums(s, my_side, op_side)

    if my_side + op_side <= _EXACT_SEEDS:
        return _solve_exact(s, player, alpha, beta)

    key = (s, player)
    orig_alpha = alpha
    orig_beta = beta
    ttmove = None

    entry = _TT.get(key)
    if entry is not None:
        ed, ev, ef, em = entry
        ttmove = em
        if ed >= depth:
            if ef == _TT_EXACT:
                return ev
            if ef == _TT_LOWER:
                if ev >= beta:
                    return ev
                if ev > alpha:
                    alpha = ev
            elif ef == _TT_UPPER:
                if ev <= alpha:
                    return ev
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev

    if depth <= 0:
        val = _heuristic(s, player, my_side, op_side)
        _save_tt(key, 0, val, _TT_EXACT, -1)
        return val

    children = _ordered_children(s, player, ttmove)
    if not children:
        return _terminal_from_sums(s, my_side, op_side)

    if player == 0:
        best = -_INF
        best_move = children[0][1]

        for _, m, child, next_player in children:
            # Extra moves stay in the same turn and do not consume turn-depth.
            next_depth = depth if next_player == player else depth - 1
            val = _alphabeta(child, next_player, next_depth, alpha, beta)

            if val > best:
                best = val
                best_move = m
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = _INF
        best_move = children[0][1]

        for _, m, child, next_player in children:
            next_depth = depth if next_player == player else depth - 1
            val = _alphabeta(child, next_player, next_depth, alpha, beta)

            if val < best:
                best = val
                best_move = m
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    if best <= orig_alpha:
        flag = _TT_UPPER
    elif best >= orig_beta:
        flag = _TT_LOWER
    else:
        flag = _TT_EXACT

    _save_tt(key, depth, best, flag, best_move)
    return best


def _root_search(s, depth, hint):
    _tick()

    ttmove = hint
    entry = _TT.get((s, 0))
    if ttmove is None and entry is not None:
        ttmove = entry[3]

    children = _ordered_children(s, 0, ttmove)
    if not children:
        return _heuristic(s, 0), 0

    alpha = -_INF
    beta = _INF
    best = -_INF
    best_move = children[0][1]

    for _, m, child, next_player in children:
        next_depth = depth if next_player == 0 else depth - 1
        val = _alphabeta(child, next_player, next_depth, alpha, beta)

        if val > best:
            best = val
            best_move = m
        if best > alpha:
            alpha = best

    total_house_seeds = _sum0(s) + _sum1(s)
    save_depth = _EXACT_DEPTH if total_house_seeds <= _EXACT_SEEDS else depth
    _save_tt((s, 0), save_depth, best, _TT_EXACT, best_move)

    return best, best_move


def _greedy_move(s, legal):
    best_move = legal[0]
    best_score = -_INF

    for m in legal:
        child, next_player, _ = _make_move(s, 0, m)
        score = _heuristic(child, next_player)
        if next_player == 0:
            score += 25

        if score > best_score:
            best_score = score
            best_move = m

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global _DEADLINE, _NODES, _TT

    try:
        state = (
            int(you[0]), int(you[1]), int(you[2]), int(you[3]), int(you[4]), int(you[5]), int(you[6]),
            int(opponent[0]), int(opponent[1]), int(opponent[2]), int(opponent[3]), int(opponent[4]), int(opponent[5]), int(opponent[6]),
        )

        legal = [i for i in range(6) if state[i] > 0]
        if not legal:
            return 0
        if len(legal) == 1:
            return int(legal[0])

        # Strong standard 6x4 opening: pit index 2 reaches the store and earns an extra move.
        if state == _OPENING_STATE:
            return 2

        fallback = _greedy_move(state, legal)
        best_move = fallback
        hint = fallback

        _TT = {}
        _NODES = 0
        _DEADLINE = time.perf_counter() + _TIME_LIMIT

        root_house_seeds = _sum0(state) + _sum1(state)

        depth = 1
        while depth <= _MAX_DEPTH:
            if time.perf_counter() >= _DEADLINE - 0.012:
                break

            try:
                value, move = _root_search(state, depth, hint)
            except _Timeout:
                break

            if 0 <= move <= 5 and state[move] > 0:
                best_move = move
                hint = move

            # Exact endgame solved, or a forced terminal result found.
            if root_house_seeds <= _EXACT_SEEDS or abs(value) >= _WIN:
                break

            depth += 1

        if not (0 <= best_move <= 5 and state[best_move] > 0):
            best_move = legal[0]

        return int(best_move)

    except Exception:
        # Absolute safety fallback: never return an illegal move if a legal one exists.
        try:
            for i in range(6):
                if you[i] > 0:
                    return int(i)
        except Exception:
            pass
        return 0
