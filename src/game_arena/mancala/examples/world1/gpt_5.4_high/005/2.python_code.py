
import time

INF = 10**18
TERMINAL_SCALE = 100000
TIME_LIMIT = 0.90

TT = {}         # exact results for fully searched nodes: (you, opp, depth) -> (score, best_move)
BEST_HINT = {}  # principal variation / move-order hint: (you, opp) -> best_move

DEADLINE = 0.0
NODES = 0


class Timeout(Exception):
    pass


def house_sum(a):
    return a[0] + a[1] + a[2] + a[3] + a[4] + a[5]


def terminal_score(you, opp):
    sy = house_sum(you)
    so = house_sum(opp)
    # If terminal, remaining house seeds are swept into stores.
    final_diff = (you[6] + sy) - (opp[6] + so)
    return final_diff * TERMINAL_SCALE


def capture_gain(you, opp, move, seeds=None, last_pos=None):
    if seeds is None:
        seeds = you[move]
    if seeds <= 0:
        return 0

    if last_pos is None:
        last_pos = (move + seeds) % 13

    if last_pos >= 6:
        return 0

    # Distance from source to first visit of last_pos in the sow cycle.
    dist = (last_pos - move) % 13
    if dist == 0:
        dist = 13

    # Number of times this house was visited before the final seed.
    if seeds - 1 < dist:
        earlier_visits = 0
    else:
        earlier_visits = 1 + (seeds - 1 - dist) // 13

    pre_drop = (0 if last_pos == move else you[last_pos]) + earlier_visits

    if pre_drop == 0 and opp[5 - last_pos] > 0:
        return 1 + opp[5 - last_pos]
    return 0


def tactical_stats(you, opp):
    extra_turns = 0
    best_capture = 0
    moves = 0

    for m in range(6):
        s = you[m]
        if s <= 0:
            continue
        moves += 1
        r = (m + s) % 13
        if r == 6:
            extra_turns += 1
        elif r < 6:
            cap = capture_gain(you, opp, m, s, r)
            if cap > best_capture:
                best_capture = cap

    return extra_turns, best_capture, moves


def evaluate(you, opp):
    sy = house_sum(you)
    so = house_sum(opp)

    if sy == 0 or so == 0:
        return terminal_score(you, opp)

    store_diff = you[6] - opp[6]
    seed_diff = sy - so

    pos_diff = (
        1 * (you[0] - opp[0]) +
        2 * (you[1] - opp[1]) +
        3 * (you[2] - opp[2]) +
        4 * (you[3] - opp[3]) +
        6 * (you[4] - opp[4]) +
        8 * (you[5] - opp[5])
    )

    self_empty = (
        (you[0] == 0) + (you[1] == 0) + (you[2] == 0) +
        (you[3] == 0) + (you[4] == 0) + (you[5] == 0)
    )
    opp_empty = (
        (opp[0] == 0) + (opp[1] == 0) + (opp[2] == 0) +
        (opp[3] == 0) + (opp[4] == 0) + (opp[5] == 0)
    )

    extra_self, cap_self, moves_self = tactical_stats(you, opp)
    extra_opp, cap_opp, moves_opp = tactical_stats(opp, you)

    remaining = sy + so
    seed_weight = 4 if remaining > 24 else (8 if remaining > 12 else 14)
    store_weight = 180 if remaining > 12 else 220

    return (
        store_weight * store_diff +
        seed_weight * seed_diff +
        2 * pos_diff +
        6 * (opp_empty - self_empty) +
        24 * (extra_self - extra_opp) +
        10 * (cap_self - cap_opp) +
        3 * (moves_self - moves_opp)
    )


def apply_move(you, opp, move):
    y = list(you)
    o = list(opp)

    seeds = y[move]
    y[move] = 0

    side = 0  # 0 = your side, 1 = opponent side
    pos = move
    last_side = 0
    last_pos = move

    while seeds > 0:
        pos += 1

        if side == 0:
            if pos == 6:
                y[6] += 1
                seeds -= 1
                last_side = 0
                last_pos = 6
                if seeds == 0:
                    break
                side = 1
                pos = -1
            else:
                y[pos] += 1
                seeds -= 1
                last_side = 0
                last_pos = pos
        else:
            if pos == 6:
                side = 0
                pos = -1
                continue
            o[pos] += 1
            seeds -= 1
            last_side = 1
            last_pos = pos

    same_turn = (last_side == 0 and last_pos == 6)

    # Capture
    if last_side == 0 and 0 <= last_pos <= 5 and y[last_pos] == 1 and o[5 - last_pos] > 0:
        y[6] += 1 + o[5 - last_pos]
        y[last_pos] = 0
        o[5 - last_pos] = 0

    sy = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    so = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]

    terminal = False
    if sy == 0 or so == 0:
        y[6] += sy
        o[6] += so
        y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0
        o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0
        same_turn = False
        terminal = True

    return tuple(y), tuple(o), same_turn, terminal


def ordered_children(you, opp, hint_move=None):
    items = []
    base_store = you[6]

    for m in range(6):
        s = you[m]
        if s <= 0:
            continue

        ny, no, same, term = apply_move(you, opp, m)

        pri = 0
        if hint_move == m:
            pri += 10_000_000

        if term:
            pri += 2_000_000 + 50_000 * (ny[6] - no[6])

        if same:
            pri += 1_000_000

        store_gain = ny[6] - base_store
        pri += 20_000 * store_gain

        r = (m + s) % 13
        pri += 2_000 * capture_gain(you, opp, m, s, r)

        # Slight bias toward pits nearer the store.
        pri += m

        items.append((pri, m, ny, no, same, term))

    items.sort(key=lambda x: x[0], reverse=True)
    return items


def check_time():
    global NODES
    NODES += 1
    if (NODES & 127) == 0 and time.perf_counter() >= DEADLINE:
        raise Timeout


def negamax(you, opp, depth, alpha, beta):
    check_time()

    sy = house_sum(you)
    so = house_sum(opp)

    if sy == 0 or so == 0:
        return terminal_score(you, opp), None

    if depth <= 0:
        return evaluate(you, opp), None

    key = (you, opp, depth)
    cached = TT.get(key)
    if cached is not None:
        return cached

    hint = BEST_HINT.get((you, opp))
    children = ordered_children(you, opp, hint)
    if not children:
        # Should not happen in valid nonterminal calls, but stay safe.
        return evaluate(you, opp), None

    best_score = -INF
    best_move = children[0][1]
    cutoff = False

    for _, m, ny, no, same, term in children:
        if term:
            score = terminal_score(ny, no)
        elif same:
            score, _ = negamax(ny, no, depth, alpha, beta)
        else:
            child_score, _ = negamax(no, ny, depth - 1, -beta, -alpha)
            score = -child_score

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

        if alpha >= beta:
            cutoff = True
            break

    BEST_HINT[(you, opp)] = best_move

    result = (best_score, best_move)
    if not cutoff:
        TT[key] = result

    return result


def quick_move(you, opp):
    hint = BEST_HINT.get((you, opp))
    children = ordered_children(you, opp, hint)
    if not children:
        return 0

    best_move = children[0][1]
    best_score = -INF

    for _, m, ny, no, same, term in children:
        if term:
            score = terminal_score(ny, no)
        elif same:
            score = evaluate(ny, no) + 60
        else:
            score = -evaluate(no, ny)

        if score > best_score:
            best_score = score
            best_move = m

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global DEADLINE, NODES

    yt = tuple(int(x) for x in you)
    ot = tuple(int(x) for x in opponent)

    legal = [i for i in range(6) if yt[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    # Prevent unbounded memory growth across many calls/games.
    if len(TT) > 300000 or len(BEST_HINT) > 300000:
        TT.clear()
        BEST_HINT.clear()

    DEADLINE = time.perf_counter() + TIME_LIMIT
    NODES = 0

    best_move = quick_move(yt, ot)
    if yt[best_move] <= 0:
        best_move = legal[0]
    BEST_HINT[(yt, ot)] = best_move

    remaining = house_sum(yt) + house_sum(ot)
    if remaining <= 14:
        hard_cap = 24
    elif remaining <= 24:
        hard_cap = 18
    else:
        hard_cap = 14

    depth = 1
    while depth <= hard_cap:
        if time.perf_counter() >= DEADLINE:
            break
        try:
            score, move = negamax(yt, ot, depth, -INF, INF)
            if move is not None and yt[move] > 0:
                best_move = move
            # If we have an overwhelmingly terminal-like score, deeper search is less urgent.
            # Still continue while time allows.
        except Timeout:
            break
        depth += 1

    if yt[best_move] > 0:
        return best_move

    return legal[0]
