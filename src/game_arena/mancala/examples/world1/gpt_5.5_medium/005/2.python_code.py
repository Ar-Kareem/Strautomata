
import time


INF = 10 ** 18
EXACT = 0
LOWER = 1
UPPER = 2


class _SearchTimeout(Exception):
    pass


def _apply_move(state, move):
    """
    State format:
        (my_houses_tuple, my_store, opp_houses_tuple, opp_store, turn)
    turn == 0 means root player to move.
    turn == 1 means opponent to move.
    """
    mh = list(state[0])
    ms = state[1]
    oh = list(state[2])
    os = state[3]
    turn = state[4]

    if turn == 0:
        own = mh
        opp = oh
        own_store = ms
    else:
        own = oh
        opp = mh
        own_store = os

    seeds = own[move]
    own[move] = 0

    # Relative 13-position cycle:
    # 0..5 own houses, 6 own store, 7..12 opponent houses.
    q, r = divmod(seeds, 13)

    if q:
        for i in range(6):
            own[i] += q
            opp[i] += q
        own_store += q

    for step in range(1, r + 1):
        p = (move + step) % 13
        if p < 6:
            own[p] += 1
        elif p == 6:
            own_store += 1
        else:
            opp[p - 7] += 1

    last = (move + seeds) % 13

    # Capture.
    if last < 6:
        opposite = 5 - last
        if own[last] == 1 and opp[opposite] > 0:
            own_store += own[last] + opp[opposite]
            own[last] = 0
            opp[opposite] = 0

    last_in_store = (last == 6)

    if turn == 0:
        ms = own_store
    else:
        os = own_store

    # Terminal sweep.
    sm = sum(mh)
    so = sum(oh)
    if sm == 0 or so == 0:
        if sm:
            ms += sm
            mh = [0] * 6
        if so:
            os += so
            oh = [0] * 6
        next_turn = turn
    else:
        next_turn = turn if last_in_store else 1 - turn

    return (tuple(mh), ms, tuple(oh), os, next_turn)


def _legal_moves_for(state):
    houses = state[0] if state[4] == 0 else state[2]
    return [i for i, v in enumerate(houses) if v > 0]


def _tactics(own, opp):
    """Return approximate counts/values for extra turns and capture threats."""
    extra = 0
    capture_gain = 0

    for i, n in enumerate(own):
        if n <= 0:
            continue

        last = (i + n) % 13

        if last == 6:
            extra += 1
        elif last < 6 and opp[5 - last] > 0:
            q, r = divmod(n, 13)

            # Final count of the landing house after sowing.
            # Capture occurs exactly when final count is 1.
            initial_after_pickup = 0 if last == i else own[last]
            drops_to_last = q + (1 if r > 0 else 0)
            final_count = initial_after_pickup + drops_to_last

            if final_count == 1:
                capture_gain += opp[5 - last] + 1

    return extra, capture_gain


def _evaluate(state):
    mh, ms, oh, os, turn = state
    sm = sum(mh)
    so = sum(oh)

    # Terminal or effectively terminal state.
    if sm == 0 or so == 0:
        final_diff = (ms + sm) - (os + so)
        return final_diff * 100000

    store_diff = ms - os
    house_diff = sm - so

    score = 0
    score += store_diff * 120
    score += house_diff * 4

    # Seeds closer to one's own store are slightly better.
    for i in range(6):
        score += (i + 1) * (mh[i] - oh[i])

    my_legal = sum(1 for x in mh if x > 0)
    op_legal = sum(1 for x in oh if x > 0)
    score += (my_legal - op_legal) * 2

    my_extra, my_cap = _tactics(mh, oh)
    op_extra, op_cap = _tactics(oh, mh)

    score += (my_extra - op_extra) * 18
    score += (my_cap - op_cap) * 6

    # Side to move matters because immediate tactical threats are actionable.
    if turn == 0:
        score += 4 + my_extra * 8 + my_cap * 3
    else:
        score -= 4 + op_extra * 8 + op_cap * 3

    return score


def _ordered_children(state, moves, tt_move):
    turn = state[4]
    items = []

    for m in moves:
        ns = _apply_move(state, m)
        s = _evaluate(ns)

        # Try the transposition-table best move first.
        if m == tt_move:
            s += 100000000 if turn == 0 else -100000000

        items.append((s, m, ns))

    items.sort(key=lambda x: x[0], reverse=(turn == 0))
    return [(m, ns) for _, m, ns in items]


def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]

    # The problem guarantees at least one legal move, but keep this safe.
    if not legal:
        return 0

    if len(legal) == 1:
        return legal[0]

    root = (tuple(you[:6]), int(you[6]), tuple(opponent[:6]), int(opponent[6]), 0)

    # Greedy fallback: always legal and usually decent if search is interrupted.
    best_move = legal[0]
    best_score = -INF
    for m in legal:
        sc = _evaluate(_apply_move(root, m))
        if sc > best_score:
            best_score = sc
            best_move = m

    deadline = time.perf_counter() + 0.88
    tt = {}
    nodes = 0

    def search(state, depth, alpha, beta):
        nonlocal nodes

        nodes += 1
        if (nodes & 511) == 0 and time.perf_counter() > deadline:
            raise _SearchTimeout()

        mh, ms, oh, os, turn = state
        if depth <= 0 or sum(mh) == 0 or sum(oh) == 0:
            return _evaluate(state)

        entry = tt.get(state)
        tt_move = None

        if entry is not None:
            entry_depth, entry_value, entry_flag, entry_move = entry
            tt_move = entry_move

            if entry_depth >= depth:
                if entry_flag == EXACT:
                    return entry_value
                elif entry_flag == LOWER:
                    alpha = max(alpha, entry_value)
                elif entry_flag == UPPER:
                    beta = min(beta, entry_value)

                if alpha >= beta:
                    return entry_value

        moves = _legal_moves_for(state)
        if not moves:
            return _evaluate(state)

        orig_alpha = alpha
        orig_beta = beta
        best_local_move = moves[0]

        if turn == 0:
            value = -INF
            for m, ns in _ordered_children(state, moves, tt_move):
                v = search(ns, depth - 1, alpha, beta)
                if v > value:
                    value = v
                    best_local_move = m
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = INF
            for m, ns in _ordered_children(state, moves, tt_move):
                v = search(ns, depth - 1, alpha, beta)
                if v < value:
                    value = v
                    best_local_move = m
                beta = min(beta, value)
                if alpha >= beta:
                    break

        if value <= orig_alpha:
            flag = UPPER
        elif value >= orig_beta:
            flag = LOWER
        else:
            flag = EXACT

        tt[state] = (depth, value, flag, best_local_move)
        return value

    def root_search(depth):
        alpha = -INF
        beta = INF
        value = -INF
        chosen = best_move

        entry = tt.get(root)
        tt_move = entry[3] if entry is not None else None

        for m, ns in _ordered_children(root, legal, tt_move):
            v = search(ns, depth - 1, alpha, beta)
            if v > value:
                value = v
                chosen = m
            alpha = max(alpha, value)

        return chosen, value

    # Iterative deepening. Completed depths only replace the chosen move.
    for depth in range(1, 64):
        if time.perf_counter() > deadline:
            break

        try:
            move, _ = root_search(depth)
            if move in legal:
                best_move = move
        except _SearchTimeout:
            break
        except Exception:
            # Safety: never risk returning an illegal move due to an unexpected issue.
            break

    if best_move not in legal:
        best_move = legal[0]

    return int(best_move)
