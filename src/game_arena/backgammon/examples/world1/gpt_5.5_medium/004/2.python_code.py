
# Backgammon policy for the required arena API.
# The player to move always travels from A23 down to A0.

def policy(state: dict) -> str:
    dice = list(state.get("dice", []))
    board = _board_from_state(state)

    if len(dice) == 0:
        return "H:P,P"

    if len(dice) == 1:
        d = int(dice[0])
        starts = _legal_starts(board, d)
        if not starts:
            return "H:P,P"

        best_score = None
        best_start = starts[0]
        for s in starts:
            b2 = _apply_move(board, d, s)
            sc = _evaluate(b2)
            if best_score is None or sc > best_score:
                best_score = sc
                best_start = s
        return "H:%s,P" % _fmt(best_start)

    # The API supplies at most two dice.  H/L are interpreted by value.
    d1, d2 = int(dice[0]), int(dice[1])
    hi, lo = (d1, d2) if d1 >= d2 else (d2, d1)

    candidates = []

    # H means higher die first, then lower die.
    for s1, s2, b, used in _generate_order(board, hi, lo):
        candidates.append(("H", s1, s2, b, used))

    # L means lower die first, then higher die.  For doubles this is duplicate.
    if hi != lo:
        for s1, s2, b, used in _generate_order(board, lo, hi):
            candidates.append(("L", s1, s2, b, used))

    if not candidates:
        return "H:P,P"

    # Enforce maximum dice usage.
    max_used = max(len(c[4]) for c in candidates)
    candidates = [c for c in candidates if len(c[4]) == max_used]

    # If only one die can be played, the higher die must be played if possible.
    if max_used == 1 and hi != lo:
        high_candidates = [c for c in candidates if hi in c[4]]
        if high_candidates:
            candidates = high_candidates

    best = candidates[0]
    best_score = _evaluate(best[3])

    for c in candidates[1:]:
        sc = _evaluate(c[3])
        if sc > best_score:
            best_score = sc
            best = c

    order, s1, s2, _b, _used = best
    return "%s:%s,%s" % (order, _fmt(s1), _fmt(s2))


def _board_from_state(state):
    my = list(state.get("my_pts", [0] * 24))
    opp = list(state.get("opp_pts", [0] * 24))
    if len(my) < 24:
        my += [0] * (24 - len(my))
    if len(opp) < 24:
        opp += [0] * (24 - len(opp))
    return (
        my[:24],
        opp[:24],
        int(state.get("my_bar", 0)),
        int(state.get("opp_bar", 0)),
        int(state.get("my_off", 0)),
        int(state.get("opp_off", 0)),
    )


def _fmt(start):
    if start == "B" or start == "P":
        return start
    return "A%d" % int(start)


def _all_my_in_home(my, my_bar):
    return my_bar == 0 and sum(my[6:24]) == 0


def _can_bear_off_from(my, my_bar, point, die):
    if not _all_my_in_home(my, my_bar):
        return False
    # Exact bear-off.
    if die == point + 1:
        return True
    # Oversized die may bear off only the farthest remaining checker.
    if die > point + 1 and sum(my[point + 1:6]) == 0:
        return True
    return False


def _legal_starts(board, die):
    my, opp, my_bar, _opp_bar, _my_off, _opp_off = board
    starts = []

    if die <= 0:
        return starts

    # Bar checkers must enter before anything else can move.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            starts.append("B")
        return starts

    for i in range(24):
        if my[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp[dest] < 2:
                starts.append(i)
        else:
            if 0 <= i <= 5 and _can_bear_off_from(my, my_bar, i, die):
                starts.append(i)

    return starts


def _apply_move(board, die, start):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    my = my[:]
    opp = opp[:]

    if start == "P":
        return (my, opp, my_bar, opp_bar, my_off, opp_off)

    if start == "B":
        my_bar -= 1
        dest = 24 - die
    else:
        start = int(start)
        my[start] -= 1
        dest = start - die

    if dest < 0:
        my_off += 1
    else:
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1

    return (my, opp, my_bar, opp_bar, my_off, opp_off)


def _generate_order(board, first_die, second_die):
    seqs = []
    first_moves = _legal_starts(board, first_die)

    if first_moves:
        for s1 in first_moves:
            b1 = _apply_move(board, first_die, s1)
            second_moves = _legal_starts(b1, second_die)
            if second_moves:
                for s2 in second_moves:
                    b2 = _apply_move(b1, second_die, s2)
                    seqs.append((s1, s2, b2, (first_die, second_die)))
            else:
                seqs.append((s1, "P", b1, (first_die,)))
    else:
        second_moves = _legal_starts(board, second_die)
        if second_moves:
            for s2 in second_moves:
                b2 = _apply_move(board, second_die, s2)
                seqs.append(("P", s2, b2, (second_die,)))
        else:
            seqs.append(("P", "P", board, ()))

    return seqs


def _pip_count_my(my, my_bar):
    # My checker on point i needs i+1 pips to bear off.
    return sum(my[i] * (i + 1) for i in range(24)) + 25 * my_bar


def _pip_count_opp(opp, opp_bar):
    # Opponent travels upward, so point i is 24-i pips from bearing off.
    return sum(opp[i] * (24 - i) for i in range(24)) + 25 * opp_bar


def _longest_made_run(pts):
    best = 0
    cur = 0
    for c in pts:
        if c >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _my_blot_shots(my, opp, opp_bar):
    total = 0.0

    for i in range(24):
        if my[i] != 1:
            continue

        shots = 0

        if opp_bar > 0:
            # Opponent enters from bar onto A0..A5.
            if 0 <= i <= 5:
                shots += 1
        else:
            # Opponent moves upward, from i-d to i.
            for d in range(1, 7):
                src = i - d
                if src >= 0 and opp[src] > 0:
                    shots += 1

        if shots:
            weight = 1.0
            if i <= 5:
                weight += 0.7       # home-board blots are costly
            if i >= 18:
                weight += 0.3       # advanced blots can be attacked
            total += shots * weight

    return total


def _opp_blot_shots(my, my_bar, opp):
    total = 0.0

    for i in range(24):
        if opp[i] != 1:
            continue

        shots = 0

        if my_bar > 0:
            # I enter from bar onto A23..A18.
            if 18 <= i <= 23:
                shots += 1
        else:
            # I move downward, from i+d to i.
            for d in range(1, 7):
                src = i + d
                if src < 24 and my[src] > 0:
                    shots += 1

        if shots:
            weight = 1.0
            if i >= 18:
                weight += 0.5
            if i <= 5:
                weight += 0.3
            total += shots * weight

    return total


def _evaluate(board):
    my, opp, my_bar, opp_bar, my_off, opp_off = board

    if my_off >= 15:
        return 1_000_000_000.0
    if opp_off >= 15:
        return -1_000_000_000.0

    my_pip = _pip_count_my(my, my_bar)
    opp_pip = _pip_count_opp(opp, opp_bar)

    score = 0.0

    # Race and score progress.
    score += 1000.0 * (my_off - opp_off)
    score += 3.2 * (opp_pip - my_pip)

    # Bar pressure.  Opponent on the bar is very valuable, especially with
    # closed entry points; being on the bar is very bad.
    my_home_made = sum(1 for i in range(6) if my[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp[i] >= 2)

    score += opp_bar * (85.0 + 18.0 * my_home_made)
    score -= my_bar * (110.0 + 18.0 * opp_home_made)

    # Made points, anchors, and board structure.
    for i in range(24):
        c = my[i]
        if c >= 2:
            score += 3.5
            if i <= 5:
                score += 13.0
            elif i >= 18:
                score += 7.0
            else:
                score += 4.0
            if c > 5:
                score -= 2.0 * (c - 5)
        elif c == 1:
            score -= 1.2
            if i <= 5:
                score -= 2.5

        oc = opp[i]
        if oc >= 2:
            score -= 3.0
            if i >= 18:
                score -= 10.0
            elif i <= 5:
                score -= 5.0
        elif oc == 1:
            score += 0.8

    my_run = _longest_made_run(my)
    opp_run = _longest_made_run(opp)
    score += 2.4 * my_run * my_run
    score -= 2.0 * opp_run * opp_run

    # Blot danger and tactical attacking chances.
    score -= 5.2 * _my_blot_shots(my, opp, opp_bar)
    score += 3.0 * _opp_blot_shots(my, my_bar, opp)

    # Penalize inefficient stacks and reward opponent inefficiency.
    score -= 0.9 * sum(max(0, my[i] - 3) for i in range(24))
    score += 0.5 * sum(max(0, opp[i] - 3) for i in range(24))

    # In bearoff/race positions, prioritize removing checkers and reducing pips.
    if sum(my[6:24]) == 0 and my_bar == 0:
        score += 20.0 * my_off
        score -= 0.5 * sum(my[i] * i for i in range(6))

    return score
