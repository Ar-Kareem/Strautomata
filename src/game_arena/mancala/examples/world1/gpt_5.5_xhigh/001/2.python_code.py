
from __future__ import annotations

import time

PITS = 6
STORE = 6
OPP_OFFSET = 7
OPP_STORE = 13
CYCLE = 13

SCALE = 10_000
WIN_BASE = 10_000_000
INF = 10**18

EXACT = 0
LOWER = 1
UPPER = 2

TIME_LIMIT = 0.93
TT_LIMIT = 200_000

_INITIAL = (4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0)

# Sowing sequences for each move, in the oriented state:
# own houses 0..5, own store 6, opponent houses 7..12, skipping opponent store.
_SEQS = []
_STORE_INDEX = []
for _m in range(PITS):
    _seq = tuple(
        list(range(_m + 1, PITS))
        + [STORE]
        + list(range(OPP_OFFSET, OPP_OFFSET + PITS))
        + list(range(0, _m + 1))
    )
    _SEQS.append(_seq)
    _STORE_INDEX.append(PITS - 1 - _m)

# Small precomputation for fast move application on normal Kalah seed counts.
_MAX_PRE = 96
_PRECOMP = []
_INFO = []
for _m in range(PITS):
    _seq = _SEQS[_m]
    _app_table = [None] * (_MAX_PRE + 1)
    _info_table = [None] * (_MAX_PRE + 1)
    _store_idx = _STORE_INDEX[_m]

    for _n in range(1, _MAX_PRE + 1):
        _q, _r = divmod(_n, CYCLE)
        _counts = {}

        if _q:
            for _loc in _seq:
                _counts[_loc] = _counts.get(_loc, 0) + _q

        for _k in range(_r):
            _loc = _seq[_k]
            _counts[_loc] = _counts.get(_loc, 0) + 1

        _last = _seq[_r - 1] if _r else _seq[-1]
        _gain = _q + (1 if _r > _store_idx else 0)

        _app_table[_n] = (tuple(_counts.items()), _last)
        _info_table[_n] = (_q, 1 if _r else 0, _last, _gain)

    _PRECOMP.append(_app_table)
    _INFO.append(_info_table)


class _TimeUp(Exception):
    pass


_DEADLINE = 0.0
_NODES = 0
_TT = {}
_HISTORY = [0] * PITS


def _terminal_value(margin: int) -> int:
    if margin > 0:
        return WIN_BASE + margin * SCALE
    if margin < 0:
        return -WIN_BASE + margin * SCALE
    return 0


def _sum_own(st) -> int:
    return st[0] + st[1] + st[2] + st[3] + st[4] + st[5]


def _sum_opp(st) -> int:
    return st[7] + st[8] + st[9] + st[10] + st[11] + st[12]


def _final_value_state(st) -> int:
    sa = _sum_own(st)
    sb = _sum_opp(st)
    a_store = st[STORE]
    b_store = st[OPP_STORE]

    if sa == 0 or sb == 0:
        a_store += sa
        b_store += sb

    return _terminal_value(a_store - b_store)


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _TimeUp()


def _swap_child(lst):
    return (
        lst[7], lst[8], lst[9], lst[10], lst[11], lst[12], lst[13],
        lst[0], lst[1], lst[2], lst[3], lst[4], lst[5], lst[6],
    )


def _apply_move(st, mv: int):
    """Return child, same_turn, terminal_score_or_None, metadata."""
    lst = list(st)
    n = lst[mv]
    lst[mv] = 0
    store_before = st[STORE]

    if 0 < n <= _MAX_PRE:
        incs, last = _PRECOMP[mv][n]
        for loc, add in incs:
            lst[loc] += add
    else:
        seq = _SEQS[mv]
        q, r = divmod(n, CYCLE)

        if q:
            for loc in seq:
                lst[loc] += q

        for k in range(r):
            lst[seq[k]] += 1

        last = seq[r - 1] if r else seq[-1]

    capture_gain = 0

    # Capture: last seed lands in an own empty house and opposite has seeds.
    if last < PITS and lst[last] == 1:
        opp = 12 - last
        cap = lst[opp]
        if cap:
            capture_gain = cap + 1
            lst[STORE] += capture_gain
            lst[opp] = 0
            lst[last] = 0

    sa = lst[0] + lst[1] + lst[2] + lst[3] + lst[4] + lst[5]
    sb = lst[7] + lst[8] + lst[9] + lst[10] + lst[11] + lst[12]

    # End of game: sweep remaining seeds.
    if sa == 0 or sb == 0:
        if sa:
            lst[STORE] += sa
            lst[0] = lst[1] = lst[2] = lst[3] = lst[4] = lst[5] = 0
        if sb:
            lst[OPP_STORE] += sb
            lst[7] = lst[8] = lst[9] = lst[10] = lst[11] = lst[12] = 0

        margin = lst[STORE] - lst[OPP_STORE]
        meta = (lst[STORE] - store_before, capture_gain, last)
        return None, False, _terminal_value(margin), meta

    same_turn = last == STORE
    child = tuple(lst) if same_turn else _swap_child(lst)
    meta = (lst[STORE] - store_before, capture_gain, last)
    return child, same_turn, None, meta


def _tactical_features(houses, opp_houses):
    extra = 0
    cap_sum = 0
    best_cap = 0
    gain_sum = 0
    best_gain = 0

    for i in range(PITS):
        n = houses[i]
        if n <= 0:
            continue

        if n <= _MAX_PRE:
            q, has_rem, last, gain = _INFO[i][n]
        else:
            q, r = divmod(n, CYCLE)
            seq = _SEQS[i]
            last = seq[r - 1] if r else seq[-1]
            has_rem = 1 if r else 0
            gain = q + (1 if r > _STORE_INDEX[i] else 0)

        gain_sum += gain
        if gain > best_gain:
            best_gain = gain

        if last == STORE:
            extra += 1
        elif last < PITS:
            j = last
            base = 0 if j == i else houses[j]
            final_count = base + q + has_rem
            if final_count == 1:
                captured = opp_houses[5 - j]
                if captured > 0:
                    amount = captured + 1
                    cap_sum += amount
                    if amount > best_cap:
                        best_cap = amount

    return extra, cap_sum, best_cap, gain_sum, best_gain


def _evaluate(st) -> int:
    sa = _sum_own(st)
    sb = _sum_opp(st)

    if sa == 0 or sb == 0:
        return _final_value_state(st)

    rem = sa + sb
    lead = st[STORE] - st[OPP_STORE]

    if rem <= 12:
        house_weight = 2300
    elif rem <= 24:
        house_weight = 1700
    else:
        house_weight = 1200

    val = lead * SCALE
    val += (sa - sb) * house_weight

    # Seeds closer to the store are generally more flexible/valuable.
    pos_a = st[1] + 2 * st[2] + 3 * st[3] + 4 * st[4] + 5 * st[5]
    pos_b = st[8] + 2 * st[9] + 3 * st[10] + 4 * st[11] + 5 * st[12]
    val += (pos_a - pos_b) * 110

    ca = (
        (1 if st[0] else 0) + (1 if st[1] else 0) + (1 if st[2] else 0)
        + (1 if st[3] else 0) + (1 if st[4] else 0) + (1 if st[5] else 0)
    )
    cb = (
        (1 if st[7] else 0) + (1 if st[8] else 0) + (1 if st[9] else 0)
        + (1 if st[10] else 0) + (1 if st[11] else 0) + (1 if st[12] else 0)
    )
    val += (ca - cb) * 140

    a_h = (st[0], st[1], st[2], st[3], st[4], st[5])
    b_h = (st[7], st[8], st[9], st[10], st[11], st[12])

    ta = _tactical_features(a_h, b_h)
    tb = _tactical_features(b_h, a_h)

    # Extra turns and captures are the key tactical motifs in Kalah.
    val += (ta[0] - tb[0]) * 1800
    val += (ta[2] - tb[2]) * 2200
    val += (ta[1] - tb[1]) * 350
    val += (ta[4] - tb[4]) * 450
    val += (ta[3] - tb[3]) * 80

    # Small side-to-move tempo bonus.
    val += 60

    # If one side is already mathematically safe/unsafe, bias strongly.
    if lead > rem:
        val += 1_500_000 + (lead - rem) * 2000
    elif -lead > rem:
        val -= 1_500_000 + ((-lead) - rem) * 2000

    # Keep heuristic values below exact terminal values.
    lim = WIN_BASE - 1000
    if val > lim:
        return lim
    if val < -lim:
        return -lim
    return int(val)


def _store_tt(st, depth: int, flag: int, value: int, move: int) -> None:
    old = _TT.get(st)
    if old is None:
        if len(_TT) < TT_LIMIT:
            _TT[st] = (depth, flag, value, move)
    elif depth >= old[0]:
        _TT[st] = (depth, flag, value, move)


def _ordered_children(st, preferred: int):
    children = []

    for m in range(PITS):
        if st[m] <= 0:
            continue

        child, same, term, meta = _apply_move(st, m)
        store_gain, capture_gain, _last = meta

        if term is not None:
            order = term
        else:
            order = (
                store_gain * 2500
                + capture_gain * 7000
                + _HISTORY[m]
                + m * 8
            )
            if same:
                order += 500_000

        if m == preferred:
            order += 5_000_000

        children.append((order, m, child, same, term))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _search(st, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    sa = _sum_own(st)
    sb = _sum_opp(st)
    if sa == 0 or sb == 0:
        return _final_value_state(st)

    if depth <= 0:
        return _evaluate(st)

    alpha_orig = alpha
    beta_orig = beta
    preferred = -1

    entry = _TT.get(st)
    if entry is not None:
        ent_depth, ent_flag, ent_value, ent_move = entry
        preferred = ent_move

        if ent_depth >= depth:
            if ent_flag == EXACT:
                return ent_value
            if ent_flag == LOWER:
                if ent_value > alpha:
                    alpha = ent_value
            elif ent_flag == UPPER:
                if ent_value < beta:
                    beta = ent_value

            if alpha >= beta:
                return ent_value

    children = _ordered_children(st, preferred)
    if not children:
        return _final_value_state(st)

    best = -INF
    best_move = children[0][1]

    for _order, m, child, same, term in children:
        if term is not None:
            val = term
        elif same:
            # Extra turns do not consume depth.
            val = _search(child, depth, alpha, beta)
        else:
            val = -_search(child, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val
            if alpha >= beta:
                _HISTORY[m] += depth * depth + 1
                break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(st, depth, flag, best, best_move)
    return best


def _root_search(st, depth: int, preferred: int):
    _check_time()

    children = _ordered_children(st, preferred)
    if not children:
        return preferred, _final_value_state(st)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = children[0][1]

    for _order, m, child, same, term in children:
        if time.perf_counter() > _DEADLINE:
            raise _TimeUp()

        if term is not None:
            val = term
        elif same:
            val = _search(child, depth, alpha, beta)
        else:
            val = -_search(child, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

    _store_tt(st, depth, EXACT, best, best_move)
    return best_move, best


def _first_legal(st) -> int:
    for i in range(PITS):
        if st[i] > 0:
            return i
    return 0


def _greedy_move(st) -> int:
    best_move = -1
    best_val = -INF

    for m in range(PITS):
        if st[m] <= 0:
            continue

        child, same, term, meta = _apply_move(st, m)
        store_gain, capture_gain, _last = meta

        if term is not None:
            val = term
        elif same:
            val = _evaluate(child)
        else:
            val = -_evaluate(child)

        val += store_gain * 10 + capture_gain * 20 + (100 if same else 0)

        if val > best_val:
            best_val = val
            best_move = m

    return best_move if best_move >= 0 else _first_legal(st)


def policy(you: list[int], opponent: list[int]) -> int:
    global _DEADLINE, _NODES, _TT, _HISTORY

    try:
        st = (
            int(you[0]), int(you[1]), int(you[2]), int(you[3]), int(you[4]), int(you[5]), int(you[6]),
            int(opponent[0]), int(opponent[1]), int(opponent[2]), int(opponent[3]), int(opponent[4]),
            int(opponent[5]), int(opponent[6]),
        )

        first = -1
        legal_count = 0
        for i in range(PITS):
            if st[i] > 0:
                if first < 0:
                    first = i
                legal_count += 1

        if first < 0:
            return 0
        if legal_count == 1:
            return int(first)

        # Strong standard opening: pit 2 gives an immediate extra turn.
        if st == _INITIAL:
            return 2

        fallback = _greedy_move(st)

        _DEADLINE = time.perf_counter() + TIME_LIMIT
        _NODES = 0
        _TT = {}
        _HISTORY = [0] * PITS

        rem = (
            st[0] + st[1] + st[2] + st[3] + st[4] + st[5]
            + st[7] + st[8] + st[9] + st[10] + st[11] + st[12]
        )

        if rem <= 8:
            max_depth = 80
        elif rem <= 12:
            max_depth = 60
        elif rem <= 18:
            max_depth = 42
        elif rem <= 28:
            max_depth = 28
        elif rem <= 38:
            max_depth = 22
        else:
            max_depth = 18

        best = fallback
        depth = 1

        while depth <= max_depth:
            if time.perf_counter() > _DEADLINE - 0.008:
                break

            try:
                move, _score = _root_search(st, depth, best)
            except _TimeUp:
                break

            if 0 <= move < PITS and st[move] > 0:
                best = move

            depth += 1

        if 0 <= best < PITS and st[best] > 0:
            return int(best)

        if 0 <= fallback < PITS and st[fallback] > 0:
            return int(fallback)

        return int(first)

    except Exception:
        # Absolute safety fallback: always return a legal move if one exists.
        for i in range(PITS):
            try:
                if you[i] > 0:
                    return int(i)
            except Exception:
                continue
        return 0
