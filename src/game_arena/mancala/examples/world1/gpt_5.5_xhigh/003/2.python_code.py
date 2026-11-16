
from time import perf_counter
import sys

try:
    sys.setrecursionlimit(10000)
except Exception:
    pass


# Search/value constants
INF = 10 ** 30
WIN_BONUS = 10 ** 12
STORE_W = 1000
TIME_LIMIT = 0.90
TT_LIMIT = 250000

EXACT, LOWER, UPPER = 0, 1, 2

_TT = {}
_HISTORY = [0, 0, 0, 0, 0, 0]
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _score_to_value(diff):
    """Exact terminal value from the current side's perspective."""
    if diff > 0:
        return WIN_BONUS + diff * STORE_W
    if diff < 0:
        return -WIN_BONUS + diff * STORE_W
    return 0


def _terminal_value(ch, cs, oh, os):
    sc = sum(ch)
    so = sum(oh)
    if sc == 0 or so == 0:
        return _score_to_value((cs + sc) - (os + so))
    return None


def _store_gain(m, n):
    q, r = divmod(n, 13)
    return q + (1 if r >= 6 - m else 0)


def _quick_capture(ch, oh, m):
    """Exact capture amount for move m, without fully playing the move."""
    n = ch[m]
    if n <= 0:
        return 0

    q, r = divmod(n, 13)
    last = (m + n) % 13
    if last >= 6:
        return 0

    base = 0 if last == m else ch[last]
    added_to_last = q + (1 if r else 0)
    if base + added_to_last != 1:
        return 0

    opp_idx = 5 - last
    opp_pos = 7 + opp_idx
    dist = opp_pos - m
    if dist <= 0:
        dist += 13

    opp_added = q + (1 if r and dist <= r else 0)
    opp_final = oh[opp_idx] + opp_added
    if opp_final <= 0:
        return 0
    return opp_final + 1


def _play(ch, cs, oh, os, m):
    """Play move m for the current side. Returns normalized current-side state."""
    n = ch[m]
    cl = list(ch)
    ol = list(oh)

    cl[m] = 0
    q, r = divmod(n, 13)

    if q:
        for i in range(6):
            cl[i] += q
            ol[i] += q
        cs += q

    last = (m + n) % 13

    for s in range(1, r + 1):
        p = m + s
        if p >= 13:
            p -= 13

        if p < 6:
            cl[p] += 1
        elif p == 6:
            cs += 1
        else:
            ol[p - 7] += 1

    extra = last == 6

    # Capture
    if last < 6 and cl[last] == 1:
        opp_idx = 5 - last
        captured = ol[opp_idx]
        if captured:
            cs += captured + 1
            cl[last] = 0
            ol[opp_idx] = 0

    # End of game sweep
    sc = sum(cl)
    so = sum(ol)
    terminal = False
    if sc == 0 or so == 0:
        terminal = True
        if sc:
            cs += sc
            cl = [0, 0, 0, 0, 0, 0]
        if so:
            os += so
            ol = [0, 0, 0, 0, 0, 0]

    return tuple(cl), cs, tuple(ol), os, extra, terminal


def _side_features(ch, oh):
    legal = 0
    store = 0
    extra = 0
    cap = 0

    for m in range(6):
        n = ch[m]
        if n <= 0:
            continue

        legal += 1
        q, r = divmod(n, 13)

        if r >= 6 - m:
            store += q + 1
        else:
            store += q

        last = (m + n) % 13
        if last == 6:
            extra += 1

        if last < 6:
            base = 0 if last == m else ch[last]
            added_to_last = q + (1 if r else 0)
            if base + added_to_last == 1:
                opp_idx = 5 - last
                opp_pos = 7 + opp_idx
                dist = opp_pos - m
                if dist <= 0:
                    dist += 13
                opp_added = q + (1 if r and dist <= r else 0)
                opp_final = oh[opp_idx] + opp_added
                if opp_final > 0:
                    cap += opp_final + 1

    return legal, store, extra, cap


def _evaluate(ch, cs, oh, os):
    """Static evaluation from the side-to-move perspective."""
    tv = _terminal_value(ch, cs, oh, os)
    if tv is not None:
        return tv

    sc = sum(ch)
    so = sum(oh)

    score = (cs - os) * STORE_W

    # Small tempo bonus for the player to move.
    score += 25

    # Seeds and advancement toward own store.
    score += (sc - so) * 12
    score += (
        (ch[0] + 2 * ch[1] + 3 * ch[2] + 4 * ch[3] + 5 * ch[4] + 6 * ch[5])
        - (oh[0] + 2 * oh[1] + 3 * oh[2] + 4 * oh[3] + 5 * oh[4] + 6 * oh[5])
    ) * 6

    cl, cs_gain, ce, cc = _side_features(ch, oh)
    ol, os_gain, oe, oc = _side_features(oh, ch)

    score += (cl - ol) * 10
    score += (cs_gain - os_gain) * 35
    score += (ce - oe) * 150
    score += (cc - oc) * 85

    # Empty houses opposite stones are capture opportunities.
    cur_empty_targets = 0
    opp_empty_targets = 0
    for i in range(6):
        if ch[i] == 0:
            cur_empty_targets += oh[5 - i]
        if oh[i] == 0:
            opp_empty_targets += ch[5 - i]

    score += (cur_empty_targets - opp_empty_targets) * 8

    # Light end-race pressure.
    if so <= 3:
        score += (3 - so) * 30
    if sc <= 3:
        score -= (3 - sc) * 30

    return score


def _order_score(ch, oh, m, best_hint):
    n = ch[m]
    last = (m + n) % 13

    score = _HISTORY[m] + m
    if m == best_hint:
        score += 100000000

    cap = _quick_capture(ch, oh, m)
    if cap:
        score += cap * 30000

    if last == 6:
        score += 300000

    score += _store_gain(m, n) * 1000
    return score


def _ordered_moves(ch, oh, best_hint=-1):
    scored = []
    for m in range(6):
        if ch[m] > 0:
            scored.append((_order_score(ch, oh, m, best_hint), m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _check_time():
    if perf_counter() >= _DEADLINE:
        raise _SearchTimeout()


def _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, beta):
    if terminal:
        return _score_to_value(ncs - nos)
    if extra:
        return _negamax(nch, ncs, noh, nos, depth, alpha, beta)
    return -_negamax(noh, nos, nch, ncs, depth - 1, -beta, -alpha)


def _negamax(ch, cs, oh, os, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0:
        _check_time()

    tv = _terminal_value(ch, cs, oh, os)
    if tv is not None:
        return tv

    if depth <= 0:
        return _evaluate(ch, cs, oh, os)

    key = ch + (cs,) + oh + (os,)
    entry = _TT.get(key)
    best_hint = -1

    if entry is not None:
        edepth, flag, val, bm = entry
        best_hint = bm
        if edepth >= depth:
            if flag == EXACT:
                return val
            if flag == LOWER and val >= beta:
                return val
            if flag == UPPER and val <= alpha:
                return val

    orig_alpha = alpha
    orig_beta = beta
    best_val = -INF
    best_move = -1
    first = True

    for m in _ordered_moves(ch, oh, best_hint):
        nch, ncs, noh, nos, extra, terminal = _play(ch, cs, oh, os, m)

        if first:
            val = _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, beta)
            first = False
        else:
            # Principal variation search: first try a narrow window.
            val = _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, alpha + 1)
            if alpha < val < beta:
                val = _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, beta)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            _HISTORY[m] += depth * depth
            break

    if best_val <= orig_alpha:
        flag = UPPER
    elif best_val >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _root_search(ch, cs, oh, os, depth, fallback):
    _check_time()

    key = ch + (cs,) + oh + (os,)
    entry = _TT.get(key)
    best_hint = fallback
    if entry is not None:
        best_hint = entry[3]

    moves = _ordered_moves(ch, oh, best_hint)
    if not moves:
        return -INF, fallback

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = fallback
    first = True

    for m in moves:
        _check_time()

        nch, ncs, noh, nos, extra, terminal = _play(ch, cs, oh, os, m)

        if first:
            val = _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, beta)
            first = False
        else:
            val = _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, alpha + 1)
            if val > alpha:
                val = _child_value(nch, ncs, noh, nos, extra, terminal, depth, alpha, beta)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    _TT[key] = (depth, EXACT, best_val, best_move)
    return best_val, best_move


def _heuristic_move(ch, cs, oh, os):
    best = -1
    best_val = -INF

    for m in range(6):
        if ch[m] <= 0:
            continue

        nch, ncs, noh, nos, extra, terminal = _play(ch, cs, oh, os, m)

        if terminal:
            val = _score_to_value(ncs - nos)
        elif extra:
            val = _evaluate(nch, ncs, noh, nos) + 150
        else:
            val = -_evaluate(noh, nos, nch, ncs)

        val += _quick_capture(ch, oh, m) * 20
        if (m + ch[m]) % 13 == 6:
            val += 120
        val += _store_gain(m, ch[m]) * 25

        if val > best_val:
            best_val = val
            best = m

    if best != -1:
        return best

    for i in range(6):
        if ch[i] > 0:
            return i
    return 0


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal house index 0..5 with you[index] > 0.
    """
    global _DEADLINE, _NODES

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return int(legal[0])

    ch = tuple(you[:6])
    oh = tuple(opponent[:6])
    cs = you[6]
    os = opponent[6]

    # Small standard Kalah(6,4) opening book.
    if cs == 0 and os == 0 and ch == (4, 4, 4, 4, 4, 4) and oh == (4, 4, 4, 4, 4, 4):
        return 2
    if cs == 1 and os == 0 and ch == (4, 4, 0, 5, 5, 5) and oh == (4, 4, 4, 4, 4, 4):
        return 5

    if len(_TT) > TT_LIMIT:
        _TT.clear()

    fallback = _heuristic_move(ch, cs, oh, os)
    if fallback not in legal:
        fallback = legal[0]

    best = fallback
    _DEADLINE = perf_counter() + TIME_LIMIT
    _NODES = 0

    try:
        depth = 1
        while depth <= 64:
            if perf_counter() >= _DEADLINE:
                break

            val, move = _root_search(ch, cs, oh, os, depth, best)

            if 0 <= move <= 5 and ch[move] > 0:
                best = move

            # A proven terminal win inside the horizon is good enough.
            if val >= WIN_BONUS:
                break

            depth += 1

    except _SearchTimeout:
        pass
    except Exception:
        # Never risk an illegal/no return because of an unexpected edge case.
        best = fallback

    if not (0 <= best <= 5) or you[best] <= 0:
        best = fallback
    if not (0 <= best <= 5) or you[best] <= 0:
        best = legal[0]

    return int(best)
