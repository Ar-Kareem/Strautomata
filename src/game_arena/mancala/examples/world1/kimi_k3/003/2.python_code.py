
import time

# Sowing cycle for the mover: own houses 0..5, own store, opponent houses 0..5
# (opponent store is skipped). Index of "own house k" in this cycle is k.
_CYCLE = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
          (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5))


class _Timeout(Exception):
    pass


def _simulate(you, opp, i):
    """Apply move i for the side to move. Returns (y, o, extra, terminal, diff, cap)."""
    y = list(you)
    o = list(opp)
    seeds = y[i]
    y[i] = 0
    last_side = 0
    last_idx = i
    base = i
    for j in range(1, seeds + 1):
        side, idx = _CYCLE[(base + j) % 13]
        if side == 0:
            y[idx] += 1
        else:
            o[idx] += 1
        last_side = side
        last_idx = idx

    cap_gain = 0
    # Capture: last seed in our house that was empty before the drop (==1 after sowing)
    if last_side == 0 and last_idx <= 5 and y[last_idx] == 1:
        opi = 5 - last_idx
        if o[opi] > 0:
            cap_gain = 1 + o[opi]
            y[6] += cap_gain
            o[opi] = 0
            y[last_idx] = 0

    extra = (last_side == 0 and last_idx == 6)

    ys = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    os_ = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]
    terminal = False
    diff = 0
    if ys == 0 or os_ == 0:
        terminal = True
        if os_ == 0:      # opponent side empty: we sweep our remaining seeds
            y[6] += ys
        if ys == 0:       # our side empty: opponent sweeps theirs
            o[6] += os_
        diff = y[6] - o[6]

    return y, o, extra, terminal, diff, cap_gain


def _eval(you, opp):
    """Heuristic from the side-to-move perspective."""
    sd = you[6] - opp[6]
    hd = (you[0] + you[1] + you[2] + you[3] + you[4] + you[5]) - \
         (opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5])
    e = 0
    # immediate extra-move setups: house k needs exactly 6-k seeds to land in store
    for k in range(6):
        need = 6 - k
        if you[k] == need:
            e += 1
        if opp[k] == need:
            e -= 1
    return sd * 4 + hd + e * 3


def _search(you, opp, depth, alpha, beta, tt, deadline, counter):
    counter[0] += 1
    if (counter[0] & 2047) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    key = (tuple(you), tuple(opp))
    ent = tt.get(key)
    if ent is not None and ent[0] >= depth:
        _, v, f = ent
        if f == 0:            # exact
            return v
        if f == 1:            # lower bound
            if v > alpha:
                alpha = v
        else:                 # upper bound
            if v < beta:
                beta = v
        if alpha >= beta:
            return v

    if depth == 0:
        return _eval(you, opp)

    orig_alpha = alpha
    best = -10 ** 9

    children = []
    for i in range(6):
        if you[i] > 0:
            y2, o2, extra, term, diff, _ = _simulate(you, opp, i)
            if term:
                av = diff
            elif extra:
                av = _eval(y2, o2)
            else:
                av = -_eval(o2, y2)
            children.append((av, i, y2, o2, extra, term, diff))
    children.sort(key=lambda t: t[0], reverse=True)

    for av, i, y2, o2, extra, term, diff in children:
        if term:
            v = diff
        elif extra:
            v = _search(y2, o2, depth - 1, alpha, beta, tt, deadline, counter)
        else:
            v = -_search(o2, y2, depth - 1, -beta, -alpha, tt, deadline, counter)
        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break

    if best <= orig_alpha:
        f = 2      # upper bound
    elif best >= beta:
        f = 1      # lower bound
    else:
        f = 0      # exact
    if ent is None or ent[0] <= depth:
        tt[key] = (depth, best, f)
    return best


def _root(you, opp, depth, tt, deadline, counter):
    alpha = -10 ** 9
    beta = 10 ** 9
    best_move = None
    best_val = -10 ** 9

    children = []
    for i in range(6):
        if you[i] > 0:
            y2, o2, extra, term, diff, _ = _simulate(you, opp, i)
            if term:
                av = diff
            elif extra:
                av = _eval(y2, o2)
            else:
                av = -_eval(o2, y2)
            children.append((av, i, y2, o2, extra, term, diff))
    children.sort(key=lambda t: t[0], reverse=True)

    for av, i, y2, o2, extra, term, diff in children:
        if term:
            v = diff
        elif extra:
            v = _search(y2, o2, depth - 1, alpha, beta, tt, deadline, counter)
        else:
            v = -_search(o2, y2, depth - 1, -beta, -alpha, tt, deadline, counter)
        if v > best_val:
            best_val = v
            best_move = i
        if v > alpha:
            alpha = v
    return best_move, best_val


def policy(you, opponent):
    legal = [i for i in range(6) if you[i] > 0]
    best = legal[0]
    if len(legal) == 1:
        return best

    deadline = time.perf_counter() + 0.90
    tt = {}
    counter = [0]

    depth = 1
    while depth <= 40:
        if time.perf_counter() > deadline:
            break
        try:
            m, _ = _root(you, opponent, depth, tt, deadline, counter)
        except _Timeout:
            break
        if m is not None:
            best = m
        depth += 1
    return best
