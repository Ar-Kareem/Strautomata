
import time

# ---------- Public API ----------

def policy(state: dict) -> str:
    start_time = time.perf_counter()
    try:
        board = _board_from_state(state)
        dice = _dice_from_state(state)
        actions = _legal_actions_from_board(board, dice)

        if not actions:
            return "H:P,P"
        if len(actions) == 1:
            return actions[0][0]

        legal_strings = {a for a, _ in actions}
        book = _opening_book_move(board, dice, legal_strings)
        if book is not None:
            return book

        scored = []
        for action, after in actions:
            s = _static_eval(after) + _tiny_tiebreak(action)
            scored.append((s, action, after))
        scored.sort(key=lambda x: x[0], reverse=True)

        # In contact positions, inspect likely opponent replies for the best static moves.
        contact = _has_contact(board[0], board[1], board[2], board[3])
        if contact and len(scored) > 1:
            deadline = start_time + 0.88
            top_n = 18 if len(scored) <= 80 else 14
            top_n = min(top_n, len(scored))

            best_final = None
            best_action = scored[0][1]
            any_deep = False

            for stat_score, action, after in scored[:top_n]:
                if time.perf_counter() > deadline:
                    break
                future = _expected_after_opponent(after, deadline)
                final_score = 0.42 * stat_score + 0.58 * future + _tiny_tiebreak(action)
                if best_final is None or final_score > best_final:
                    best_final = final_score
                    best_action = action
                    any_deep = True

            if any_deep:
                return best_action

        return scored[0][1]

    except Exception:
        # Emergency fallback: still try to use the legal generator.
        try:
            board = _board_from_state(state)
            dice = _dice_from_state(state)
            actions = _legal_actions_from_board(board, dice)
            if actions:
                return actions[0][0]
        except Exception:
            pass
        return "H:P,P"


# ---------- Constants / opening book ----------

_ROLLS = []
for _a in range(1, 7):
    for _b in range(_a, 7):
        _ROLLS.append((_a, _b, (1.0 / 36.0) if _a == _b else (2.0 / 36.0)))

_START_MY = [0] * 24
_START_MY[23] = 2
_START_MY[12] = 5
_START_MY[7] = 3
_START_MY[5] = 5

_START_OPP = [0] * 24
_START_OPP[0] = 2
_START_OPP[11] = 5
_START_OPP[16] = 3
_START_OPP[18] = 5

# Conservative verified first-roll choices for the standard initial layout.
_OPENING_BOOK = {
    (6, 5): "H:A23,A17",
    (6, 4): "H:A23,A17",
    (6, 3): "H:A23,A12",
    (6, 2): "H:A23,A12",
    (6, 1): "H:A12,A7",
    (5, 4): "H:A12,A23",
    (5, 3): "H:A7,A5",
    (5, 2): "H:A12,A12",
    (5, 1): "H:A12,A23",
    (4, 3): "H:A12,A12",
    (4, 2): "H:A7,A5",
    (4, 1): "H:A12,A23",
    (3, 2): "H:A23,A12",
    (3, 1): "H:A7,A5",
    (2, 1): "H:A12,A23",
}


# ---------- State normalization ----------

def _board_from_state(state):
    my = _list24(state.get("my_pts", [0] * 24))
    opp = _list24(state.get("opp_pts", [0] * 24))
    return (
        my,
        opp,
        max(0, int(state.get("my_bar", 0))),
        max(0, int(state.get("opp_bar", 0))),
        max(0, int(state.get("my_off", 0))),
        max(0, int(state.get("opp_off", 0))),
    )


def _list24(x):
    try:
        y = list(x)
    except Exception:
        y = []
    out = []
    for i in range(24):
        try:
            v = int(y[i])
        except Exception:
            v = 0
        out.append(v if v > 0 else 0)
    return out


def _dice_from_state(state):
    raw = state.get("dice", [])
    try:
        raw = list(raw)
    except Exception:
        raw = []
    dice = []
    for x in raw[:2]:
        try:
            d = int(x)
        except Exception:
            continue
        if 1 <= d <= 6:
            dice.append(d)
    return dice


# ---------- Legal move generation ----------

def _legal_actions_from_board(board, dice):
    dice = [d for d in dice if 1 <= int(d) <= 6]
    if len(dice) == 0:
        return [("H:P,P", board)]

    if len(dice) == 1:
        d = int(dice[0])
        moves = _legal_sources(board, d)
        if not moves:
            return [("H:P,P", board)]
        return [("H:%s,P" % _src_token(src), _apply_move(board, src, d)) for src in moves]

    d0, d1 = int(dice[0]), int(dice[1])
    high, low = (d0, d1) if d0 >= d1 else (d1, d0)

    # First enumerate all ways to play both dice. If any exist, they are mandatory.
    actions = []
    orders = [("H", high, low)]
    if low != high:
        orders.append(("L", low, high))

    for order, first_die, second_die in orders:
        first_sources = _legal_sources(board, first_die)
        for s1 in first_sources:
            b1 = _apply_move(board, s1, first_die)
            second_sources = _legal_sources(b1, second_die)
            for s2 in second_sources:
                b2 = _apply_move(b1, s2, second_die)
                actions.append(("%s:%s,%s" % (order, _src_token(s1), _src_token(s2)), b2))

    if actions:
        return _dedup_actions(actions)

    # If only one die can be played, the higher die must be used if possible.
    high_sources = _legal_sources(board, high)
    if high_sources:
        return [("H:%s,P" % _src_token(src), _apply_move(board, src, high))
                for src in high_sources]

    low_sources = _legal_sources(board, low)
    if low_sources:
        order = "H" if high == low else "L"
        return [("%s:%s,P" % (order, _src_token(src)), _apply_move(board, src, low))
                for src in low_sources]

    return [("H:P,P", board)]


def _dedup_actions(actions):
    seen = set()
    out = []
    for a, b in actions:
        if a not in seen:
            seen.add(a)
            out.append((a, b))
    return out


def _legal_sources(board, die):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    die = int(die)
    if die < 1 or die > 6:
        return []

    # Bar checkers must enter first.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            return [-1]  # bar
        return []

    all_home = _all_home_points(my, my_bar)
    sources = []

    for i in range(24):
        if my[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp[dest] < 2:
                sources.append(i)
        else:
            if all_home and _can_bear_off_from(my, i, die):
                sources.append(i)

    return sources


def _can_bear_off_from(my, src, die):
    if src < 0 or src > 5:
        return False

    # Exact bear-off.
    if die == src + 1:
        return True

    # Oversized die may bear off only from the highest occupied home point.
    if die > src + 1:
        for j in range(src + 1, 6):
            if my[j] > 0:
                return False
        return True

    return False


def _apply_move(board, src, die):
    my0, opp0, my_bar, opp_bar, my_off, opp_off = board
    my = my0[:]
    opp = opp0[:]
    die = int(die)

    if src == -1:
        # Enter from bar onto opponent's home board.
        my_bar -= 1
        dest = 24 - die
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1
    else:
        i = int(src)
        my[i] -= 1
        dest = i - die
        if dest >= 0:
            if opp[dest] == 1:
                opp[dest] = 0
                opp_bar += 1
            my[dest] += 1
        else:
            my_off += 1

    return (my, opp, my_bar, opp_bar, my_off, opp_off)


def _src_token(src):
    if src == -1:
        return "B"
    if src is None:
        return "P"
    return "A" + str(int(src))


# ---------- Evaluation ----------

def _static_eval(board):
    my, opp, my_bar, opp_bar, my_off, opp_off = board

    if my_off >= 15:
        return 100000.0 + 1000.0 * (15 - opp_off)
    if opp_off >= 15:
        return -100000.0 - 1000.0 * (15 - my_off)

    my_pips = _pip_count_down(my, my_bar)
    opp_pips = _pip_count_up(opp, opp_bar)
    pip_adv = opp_pips - my_pips

    contact = _has_contact(my, opp, my_bar, opp_bar)
    race = not contact

    my_all_home = _all_home_points(my, my_bar)
    opp_rev = opp[::-1]
    my_rev = my[::-1]
    opp_all_home = _all_home_points(opp_rev, opp_bar)

    pip_weight = 3.05 if race else 1.55
    if my_all_home or opp_all_home:
        pip_weight += 0.35

    score = pip_weight * pip_adv

    off_weight = 21.0 if (race or my_all_home or opp_all_home) else 11.0
    score += off_weight * (my_off - opp_off)

    # Bar: being hit is costly; hitting while owning a board is excellent.
    score += 46.0 * opp_bar - 58.0 * my_bar

    my_home_made = _made_count(my, 0, 6)
    opp_home_made = _made_count(opp_rev, 0, 6)

    score += 3.5 * (my_home_made - opp_home_made)
    if opp_bar:
        score += opp_bar * (6.5 * my_home_made + 18.0 * max(0, my_home_made - 3))
        if my_home_made == 6:
            score += 75.0 * opp_bar
    if my_bar:
        score -= my_bar * (6.5 * opp_home_made + 18.0 * max(0, opp_home_made - 3))
        if opp_home_made == 6:
            score -= 75.0 * my_bar

    # Point-making, primes, useful anchors, and stack efficiency.
    score += _structure_score(my) - _structure_score(opp_rev)

    # Blot safety. When ahead, avoid shots; when behind, accept more risk.
    my_blot_penalty = _blot_penalty(my, opp, opp_bar, contact)
    opp_blot_penalty = _blot_penalty(opp_rev, my_rev, my_bar, contact)

    risk_weight = 1.0
    if pip_adv > 20:
        risk_weight = 1.25
    elif pip_adv < -20:
        risk_weight = 0.78
    if race:
        risk_weight = 0.18

    score -= risk_weight * my_blot_penalty

    blot_reward = 0.38
    if pip_adv < -10:
        blot_reward += 0.18
    if race:
        blot_reward = 0.08
    score += blot_reward * opp_blot_penalty

    # Anchors/back-checkers: keep anchors when behind, escape when ahead.
    if contact:
        my_back = sum(my[18:24])
        opp_back = sum(opp[0:6])
        my_anchor = sum(1 for i in range(18, 24) if my[i] >= 2)
        opp_anchor = sum(1 for i in range(0, 6) if opp[i] >= 2)

        if pip_adv > 12:
            score -= 1.25 * my_back
            score += 0.85 * opp_back
            score -= 3.2 * opp_anchor
        elif pip_adv < -12:
            score += 4.8 * my_anchor
            score -= 1.2 * opp_anchor
        else:
            score += 1.7 * my_anchor
            score -= 1.7 * opp_anchor

    # Bearing off and bear-in shape.
    if my_all_home:
        score += 18.0
        score -= _bearoff_shape_penalty(my)
    if opp_all_home:
        score -= 18.0
        score += _bearoff_shape_penalty(opp_rev)

    return score


def _pip_count_down(pts, bar):
    total = 25 * bar
    for i, c in enumerate(pts):
        total += (i + 1) * c
    return total


def _pip_count_up(pts, bar):
    total = 25 * bar
    for i, c in enumerate(pts):
        total += (24 - i) * c
    return total


def _all_home_points(my, my_bar):
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my[i] > 0:
            return False
    return True


def _has_contact(my, opp, my_bar, opp_bar):
    if my_bar > 0 or opp_bar > 0:
        return True

    max_my = -1
    for i in range(23, -1, -1):
        if my[i] > 0:
            max_my = i
            break

    min_opp = 24
    for i in range(24):
        if opp[i] > 0:
            min_opp = i
            break

    if max_my < 0 or min_opp > 23:
        return False
    return max_my > min_opp


def _made_count(pts, lo, hi):
    n = 0
    for i in range(lo, hi):
        if pts[i] >= 2:
            n += 1
    return n


def _structure_score(pts):
    s = 0.0
    made = [False] * 24

    home_extra = [1.0, 1.5, 2.2, 3.0, 4.0, 3.5]

    for i, c in enumerate(pts):
        if c >= 2:
            made[i] = True
            if i <= 5:
                s += 4.4 + home_extra[i]
            elif i <= 11:
                s += 3.5
            elif i <= 17:
                s += 3.0
            else:
                # Defensive anchors. Mid/deep anchors are useful, but not as much as home points.
                if i == 18:
                    s += 4.0
                elif i == 19:
                    s += 4.6
                elif i == 20:
                    s += 3.8
                elif i == 21:
                    s += 2.8
                elif i == 22:
                    s += 2.1
                else:
                    s += 1.4

            if c == 3:
                s += 0.45
            elif c == 4:
                s += 0.15
            elif c >= 6:
                s -= 0.75 * (c - 5) * (c - 4)

        # Very large stacks are inefficient even if the point is valuable.
        if c >= 7:
            s -= 0.55 * (c - 6) * (c - 6)

    # Important outer-board points.
    for i in (6, 7):
        if pts[i] >= 2:
            s += 1.7
    if pts[12] >= 2:
        s += 0.9

    # Reward primes / consecutive made points.
    run = 0
    for i in range(24):
        if made[i]:
            run += 1
        else:
            if run >= 2:
                s += _run_reward(run)
            run = 0
    if run >= 2:
        s += _run_reward(run)

    return s


def _run_reward(n):
    r = 0.85 * n * n
    if n >= 4:
        r += 5.0
    if n >= 5:
        r += 10.0
    if n >= 6:
        r += 18.0
    return r


def _blot_penalty(own, enemy, enemy_bar, contact):
    if not contact and enemy_bar == 0:
        return 0.0

    penalty = 0.0

    for i, c in enumerate(own):
        if c != 1:
            continue

        # Base cost of an exposed single checker.
        p = 1.15

        hit_numbers = set()
        board_attack_numbers = set()

        # Enemy moves upward in these coordinates, so an enemy checker at i-d
        # attacks our blot on i with die d.
        for d in range(1, 7):
            src = i - d
            if src >= 0 and enemy[src] > 0:
                hit_numbers.add(d)
                board_attack_numbers.add(d)

            # Enemy bar enters on points 0..5.
            if enemy_bar > 0 and i == d - 1:
                hit_numbers.add(d)

        if hit_numbers:
            n = len(hit_numbers)
            prob = 1.0 - ((6.0 - n) / 6.0) ** 2

            # A blot close to our bear-off side loses more pips if hit.
            value = 14.0 + 0.58 * (23 - i)

            # If the enemy has a checker on the bar, board-origin shots are less
            # immediate unless they enter first; direct entry hits remain dangerous.
            if enemy_bar > 0 and board_attack_numbers and i > 5:
                prob *= 0.55

            p += value * prob

        if enemy_bar > 0 and i <= 5:
            p += 7.5 * enemy_bar

        # Inner-board blots are costly in bearoff/contact; deep back blots are
        # often acceptable while anchoring or escaping.
        if i <= 5:
            p += 2.0
        elif i >= 18:
            p *= 0.82

        if not contact:
            p *= 0.22

        penalty += p

    return penalty


def _bearoff_shape_penalty(pts):
    pen = 0.0
    for i in range(6):
        c = pts[i]
        if c > 3:
            pen += (c - 3) * (0.65 + 0.12 * i)

    # Gaps below the highest occupied point slightly increase wastage.
    highest = -1
    for i in range(5, -1, -1):
        if pts[i] > 0:
            highest = i
            break
    if highest > 0:
        for i in range(highest):
            if pts[i] == 0:
                pen += 0.35

    return pen


# ---------- Opponent lookahead ----------

def _mirror_board(board):
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    return (opp[::-1], my[::-1], opp_bar, my_bar, opp_off, my_off)


def _expected_after_opponent(board, deadline=None):
    base = _static_eval(board)
    opp_start = _mirror_board(board)

    total = 0.0
    prob_done = 0.0

    for d1, d2, prob in _ROLLS:
        if deadline is not None and time.perf_counter() > deadline:
            break

        opp_actions = _legal_actions_from_board(opp_start, (d1, d2))
        worst_for_us = None

        for _, opp_after in opp_actions:
            if deadline is not None and time.perf_counter() > deadline:
                break
            our_after = _mirror_board(opp_after)
            val = _static_eval(our_after)
            if worst_for_us is None or val < worst_for_us:
                worst_for_us = val

        if worst_for_us is None:
            worst_for_us = base - 3.0

        total += prob * worst_for_us
        prob_done += prob

    if prob_done < 0.999999:
        total += (1.0 - prob_done) * (base - 3.0)

    return total


# ---------- Misc ----------

def _opening_book_move(board, dice, legal_strings):
    if len(dice) != 2:
        return None
    my, opp, my_bar, opp_bar, my_off, opp_off = board
    if my_bar or opp_bar or my_off or opp_off:
        return None
    if my != _START_MY or opp != _START_OPP:
        return None

    high, low = (dice[0], dice[1]) if dice[0] >= dice[1] else (dice[1], dice[0])
    move = _OPENING_BOOK.get((high, low))
    if move in legal_strings:
        return move
    return None


def _tiny_tiebreak(action):
    # Deterministic tiny preference to avoid arbitrary dependence on generation order.
    v = 0
    for i, ch in enumerate(action):
        v += (i + 1) * ord(ch)
    return (v % 997) * 1.0e-7
