
import time
from typing import Tuple, List

INF = 10**9
WIN = 100000

# Transposition table:
# key -> (depth, score, flag, best_move)
# flag: 0 = exact, 1 = lower bound, 2 = upper bound
TT = {}

DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def terminal_value(you: Tuple[int, ...], opp: Tuple[int, ...], sy: int = None, so: int = None) -> int:
    if sy is None:
        sy = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
    if so is None:
        so = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]

    if sy == 0 and so > 0:
        diff = you[6] - (opp[6] + so)
    elif so == 0 and sy > 0:
        diff = (you[6] + sy) - opp[6]
    else:
        diff = you[6] - opp[6]

    if diff > 0:
        return WIN + diff
    if diff < 0:
        return -WIN + diff
    return 0


def extra_turn_count(side: Tuple[int, ...]) -> int:
    c = 0
    for i in range(6):
        s = side[i]
        if s and (i + s) % 13 == 6:
            c += 1
    return c


def immediate_capture_gain(cur: Tuple[int, ...], other: Tuple[int, ...]) -> int:
    best = 0
    for i in range(6):
        s = cur[i]
        if not s:
            continue
        last = (i + s) % 13
        if 0 <= last < 6:
            q, r = divmod(s, 13)
            init_after = 0 if last == i else cur[last]
            final_count = init_after + q + (1 if r > 0 else 0)
            if final_count == 1:
                gain = other[5 - last]
                if gain > 0:
                    total = gain + 1
                    if total > best:
                        best = total
    return best


def heuristic_value(you: Tuple[int, ...], opp: Tuple[int, ...], sy: int = None, so: int = None) -> int:
    if sy is None:
        sy = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
    if so is None:
        so = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]

    if sy == 0 or so == 0:
        return terminal_value(you, opp, sy, so)

    store_diff = you[6] - opp[6]
    seed_diff = sy - so
    mobility_diff = (
        (1 if you[0] > 0 else 0) + (1 if you[1] > 0 else 0) + (1 if you[2] > 0 else 0) +
        (1 if you[3] > 0 else 0) + (1 if you[4] > 0 else 0) + (1 if you[5] > 0 else 0)
        -
        ((1 if opp[0] > 0 else 0) + (1 if opp[1] > 0 else 0) + (1 if opp[2] > 0 else 0) +
         (1 if opp[3] > 0 else 0) + (1 if opp[4] > 0 else 0) + (1 if opp[5] > 0 else 0))
    )
    extra_diff = extra_turn_count(you) - extra_turn_count(opp)
    cap_diff = immediate_capture_gain(you, opp) - immediate_capture_gain(opp, you)

    pos_you = you[1] + 2 * you[2] + 3 * you[3] + 4 * you[4] + 5 * you[5]
    pos_opp = opp[1] + 2 * opp[2] + 3 * opp[3] + 4 * opp[4] + 5 * opp[5]
    pos_diff = pos_you - pos_opp

    return (
        250 * store_diff
        + 12 * seed_diff
        + 20 * extra_diff
        + 8 * cap_diff
        + 6 * mobility_diff
        + 3 * pos_diff
    )


def apply_move(you: Tuple[int, ...], opp: Tuple[int, ...], move: int):
    # Ring of sowable pits from current player's perspective:
    # you[0..5], you_store, opp[0..5]
    ring = [
        you[0], you[1], you[2], you[3], you[4], you[5], you[6],
        opp[0], opp[1], opp[2], opp[3], opp[4], opp[5]
    ]
    opp_store = opp[6]

    seeds = ring[move]
    ring[move] = 0

    q, r = divmod(seeds, 13)
    if q:
        for k in range(13):
            ring[k] += q

    for t in range(1, r + 1):
        ring[(move + t) % 13] += 1

    last = (move + seeds) % 13
    extra = (last == 6)

    # Capture
    if 0 <= last < 6 and ring[last] == 1:
        opp_idx = 12 - last  # opposite house in ring coordinates
        captured = ring[opp_idx]
        if captured > 0:
            ring[6] += captured + 1
            ring[last] = 0
            ring[opp_idx] = 0

    sy = ring[0] + ring[1] + ring[2] + ring[3] + ring[4] + ring[5]
    so = ring[7] + ring[8] + ring[9] + ring[10] + ring[11] + ring[12]

    if sy == 0 or so == 0:
        you_store = ring[6] + (sy if so == 0 else 0)
        opp_store += (so if sy == 0 else 0)
        you2 = (0, 0, 0, 0, 0, 0, you_store)
        opp2 = (0, 0, 0, 0, 0, 0, opp_store)
        return you2, opp2, False, True

    you2 = (ring[0], ring[1], ring[2], ring[3], ring[4], ring[5], ring[6])
    opp2 = (ring[7], ring[8], ring[9], ring[10], ring[11], ring[12], opp_store)
    return you2, opp2, extra, False


def move_priority(you: Tuple[int, ...], opp: Tuple[int, ...], i: int, tt_move: int) -> int:
    s = you[i]
    last = (i + s) % 13
    q, r = divmod(s, 13)

    score = 0

    if i == tt_move:
        score += 1000000

    if last == 6:
        score += 10000

    # Rough store gain
    dist_to_store = 6 - i
    store_gain = q + (1 if r >= dist_to_store else 0)
    score += 50 * store_gain

    # Capture potential
    if 0 <= last < 6:
        init_after = 0 if last == i else you[last]
        final_count = init_after + q + (1 if r > 0 else 0)
        if final_count == 1 and opp[5 - last] > 0:
            score += 500 + 10 * opp[5 - last]

    score += 5 * i
    score += s
    return score


def search(you: Tuple[int, ...], opp: Tuple[int, ...], depth: int, alpha: int, beta: int):
    global NODE_COUNTER, DEADLINE, TT

    NODE_COUNTER += 1
    if (NODE_COUNTER & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    sy = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
    so = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]

    if sy == 0 or so == 0:
        return terminal_value(you, opp, sy, so), -1

    if depth == 0:
        return heuristic_value(you, opp, sy, so), -1

    key = (you, opp)
    tt_move = -1
    orig_alpha = alpha
    orig_beta = beta

    entry = TT.get(key)
    if entry is not None:
        tt_depth, tt_score, tt_flag, tt_move = entry
        if tt_depth >= depth:
            if tt_flag == 0:
                return tt_score, tt_move
            elif tt_flag == 1:
                if tt_score > alpha:
                    alpha = tt_score
            else:
                if tt_score < beta:
                    beta = tt_score
            if alpha >= beta:
                return tt_score, tt_move

    legal = [i for i in range(6) if you[i] > 0]
    legal.sort(key=lambda m: move_priority(you, opp, m, tt_move), reverse=True)

    best_move = legal[0]
    best_score = -INF

    for move in legal:
        you2, opp2, extra, terminal = apply_move(you, opp, move)

        if terminal:
            score = terminal_value(you2, opp2, 0, 0)
        elif extra:
            score, _ = search(you2, opp2, depth - 1, alpha, beta)
        else:
            score, _ = search(opp2, you2, depth - 1, -beta, -alpha)
            score = -score

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    flag = 0
    if best_score <= orig_alpha:
        flag = 2
    elif best_score >= orig_beta:
        flag = 1

    TT[key] = (depth, best_score, flag, best_move)
    return best_score, best_move


def policy(you: List[int], opponent: List[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    yt = tuple(int(x) for x in you)
    ot = tuple(int(x) for x in opponent)

    # Keep table bounded across many calls
    if len(TT) > 300000:
        TT.clear()

    # Good default / opening choice
    best_move = legal[0]
    if yt == (4, 4, 4, 4, 4, 4, 0) and ot == (4, 4, 4, 4, 4, 4, 0):
        best_move = 2

    entry = TT.get((yt, ot))
    if entry is not None and entry[3] in legal:
        best_move = entry[3]

    global DEADLINE, NODE_COUNTER
    start = time.perf_counter()
    DEADLINE = start + 0.92

    total_seeds = sum(yt[:6]) + sum(ot[:6])
    if total_seeds <= 14:
        max_depth = 30
    elif total_seeds <= 24:
        max_depth = 20
    else:
        max_depth = 14

    guess = 0

    for depth in range(1, max_depth + 1):
        try:
            NODE_COUNTER = 0

            if depth >= 4:
                window = 300 + 40 * depth
                alpha = guess - window
                beta = guess + window
                score, move = search(yt, ot, depth, alpha, beta)
                if score <= alpha or score >= beta:
                    score, move = search(yt, ot, depth, -INF, INF)
            else:
                score, move = search(yt, ot, depth, -INF, INF)

            if move in legal:
                best_move = move
            guess = score

            # If search found a proven terminal result, often enough to stop.
            if abs(score) >= WIN and (total_seeds <= 18 or depth >= 8):
                break

        except SearchTimeout:
            break

    if best_move not in legal:
        return legal[0]
    return best_move
