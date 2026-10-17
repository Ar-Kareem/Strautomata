
from time import perf_counter

HOUSES = 6
STORE = 6
INF = 10**18

def _legal_moves(you):
    return [i for i in range(6) if you[i] > 0]

def _is_terminal(you, opp):
    return all(x == 0 for x in you[:6]) or all(x == 0 for x in opp[:6])

def _finalize(you, opp):
    y = list(you)
    o = list(opp)
    sy = sum(y[:6])
    so = sum(o[:6])
    if sy == 0 or so == 0:
        y[STORE] += sy
        o[STORE] += so
        for i in range(6):
            y[i] = 0
            o[i] = 0
    return y, o

def _apply_move(you, opp, move):
    y = list(you)
    o = list(opp)
    seeds = y[move]
    y[move] = 0

    side = 0
    idx = move + 1
    last_side = None
    last_idx = None

    while seeds > 0:
        if side == 0:
            while idx <= 6 and seeds > 0:
                y[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
                idx += 1
            if seeds == 0:
                break
            side = 1
            idx = 0
        else:
            while idx <= 5 and seeds > 0:
                o[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
                idx += 1
            if seeds == 0:
                break
            side = 0
            idx = 0

    extra = (last_side == 0 and last_idx == STORE)

    if last_side == 0 and last_idx is not None and 0 <= last_idx < 6 and y[last_idx] == 1 and o[5 - last_idx] > 0:
        y[STORE] += y[last_idx] + o[5 - last_idx]
        y[last_idx] = 0
        o[5 - last_idx] = 0

    if all(v == 0 for v in y[:6]) or all(v == 0 for v in o[:6]):
        y, o = _finalize(y, o)

    return y, o, extra

def _extra_turn_moves(you):
    c = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        r = s % 13
        if r == 0:
            r = 13
        if i + r == 6:
            c += 1
    return c

def _capture_potential(you, opp):
    score = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        pos = i
        rem = s
        side = 0
        while rem > 0:
            pos += 1
            if side == 0:
                if pos == 7:
                    side = 1
                    pos = 0
                else:
                    rem -= 1
            else:
                if pos == 6:
                    side = 0
                    pos = 0
                else:
                    rem -= 1
        if side == 0 and 0 <= pos < 6:
            if you[pos] == 0 and opp[5 - pos] > 0:
                score += 1 + opp[5 - pos]
    return score

def _evaluate(you, opp):
    if _is_terminal(you, opp):
        y, o = _finalize(you, opp)
        return 100000 * (y[STORE] - o[STORE])

    store_diff = you[STORE] - opp[STORE]
    side_diff = sum(you[:6]) - sum(opp[:6])

    extra_me = _extra_turn_moves(you)
    extra_opp = _extra_turn_moves(opp)

    cap_me = _capture_potential(you, opp)
    cap_opp = _capture_potential(opp, you)

    remaining = sum(you[:6]) + sum(opp[:6])

    v = 0
    v += 120 * store_diff
    v += 8 * side_diff
    v += 18 * (extra_me - extra_opp)
    v += 10 * (cap_me - cap_opp)

    if remaining <= 18:
        v += 20 * side_diff
        v += 30 * store_diff

    if sum(you[:6]) == 0:
        y, o = _finalize(you, opp)
        v += 100000 * (y[STORE] - o[STORE])
    elif sum(opp[:6]) == 0:
        y, o = _finalize(you, opp)
        v += 100000 * (y[STORE] - o[STORE])

    return v

def _move_order(you, opp, moves):
    scored = []
    for m in moves:
        ny, no, extra = _apply_move(you, opp, m)
        gain = ny[STORE] - you[STORE]
        opp_loss = opp[STORE] - no[STORE]
        tactical = 0
        if extra:
            tactical += 1000
        tactical += 20 * gain
        tactical += 5 * opp_loss
        tactical += ny[STORE] - no[STORE]
        tactical += sum(ny[:6]) - sum(no[:6])
        scored.append((tactical, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]

def _search(you, opp, depth, alpha, beta, deadline, tt):
    if perf_counter() >= deadline:
        raise TimeoutError

    key = (tuple(you), tuple(opp), depth)
    if key in tt:
        return tt[key]

    if depth <= 0 or _is_terminal(you, opp):
        val = _evaluate(you, opp)
        tt[key] = val
        return val

    moves = _legal_moves(you)
    if not moves:
        y, o = _finalize(you, opp)
        val = 100000 * (y[STORE] - o[STORE])
        tt[key] = val
        return val

    best = -INF
    ordered = _move_order(you, opp, moves)

    for m in ordered:
        ny, no, extra = _apply_move(you, opp, m)
        if extra:
            val = _search(ny, no, depth - 1, alpha, beta, deadline, tt)
        else:
            val = -_search(no, ny, depth - 1, -beta, -alpha, deadline, tt)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best

def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0

    fallback = legal[0]

    total = sum(you[:6]) + sum(opponent[:6])
    if total <= 10:
        max_depth = 16
    elif total <= 18:
        max_depth = 12
    elif total <= 30:
        max_depth = 10
    else:
        max_depth = 8

    start = perf_counter()
    deadline = start + 0.92

    best_move = fallback
    best_val = -INF

    tt = {}

    try:
        for depth in range(1, max_depth + 1):
            current_best_move = best_move
            current_best_val = -INF

            ordered = _move_order(you, opponent, legal)
            if current_best_move in ordered:
                ordered.remove(current_best_move)
                ordered = [current_best_move] + ordered

            alpha = -INF
            beta = INF

            for m in ordered:
                ny, no, extra = _apply_move(you, opponent, m)
                if extra:
                    val = _search(ny, no, depth - 1, alpha, beta, deadline, tt)
                else:
                    val = -_search(no, ny, depth - 1, -beta, -alpha, deadline, tt)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = m
                if val > alpha:
                    alpha = val

            best_move = current_best_move
            best_val = current_best_val

    except TimeoutError:
        pass
    except Exception:
        return fallback

    if best_move in legal:
        return best_move
    return fallback
