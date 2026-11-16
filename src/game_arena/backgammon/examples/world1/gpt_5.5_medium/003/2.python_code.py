
# Backgammon policy for the arena.
# The player using this policy always moves from point 23 down to point 0.

def policy(state: dict) -> str:
    """
    Return a legal move string in the format '<ORDER>:<FROM1>,<FROM2>'.
    """
    try:
        candidates = _legal_candidates(state)
        if not candidates:
            return "H:P,P"

        best_action = candidates[0][0]
        best_score = -10**100

        for action, pos, moves, order in candidates:
            try:
                score = _evaluate(pos)
            except Exception:
                score = 0.0

            # Tiny deterministic tie-breaker: prefer non-pass, then lexical stability.
            if moves > 0:
                score += 0.001 * moves
            score += _tiny_tiebreak(action)

            if score > best_score:
                best_score = score
                best_action = action

        return best_action
    except Exception:
        # This should only be reached on malformed input. The arena states are valid.
        return "H:P,P"


# ---------------------------------------------------------------------
# Legal move generation
# ---------------------------------------------------------------------

def _initial_pos(state):
    return (
        list(state.get("my_pts", [0] * 24)),
        list(state.get("opp_pts", [0] * 24)),
        int(state.get("my_bar", 0)),
        int(state.get("opp_bar", 0)),
        int(state.get("my_off", 0)),
        int(state.get("opp_off", 0)),
    )


def _token(start):
    if start == "B":
        return "B"
    if start == "P" or start is None:
        return "P"
    return "A" + str(int(start))


def _action(order, s1=None, s2=None):
    return order + ":" + _token(s1) + "," + _token(s2)


def _legal_candidates(state):
    dice = state.get("dice", [])
    dice = [int(d) for d in dice if 1 <= int(d) <= 6]
    pos = _initial_pos(state)

    if len(dice) == 0:
        return [("H:P,P", pos, 0, "H")]

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_starts(pos, d)
        if not starts:
            return [("H:P,P", pos, 0, "H")]

        out = []
        for s in starts:
            p1 = _simulate_move(pos, s, d)
            if p1 is not None:
                out.append((_action("H", s, None), p1, 1, "H"))
        return out if out else [("H:P,P", pos, 0, "H")]

    # The API supports at most two checker moves.
    d0, d1 = dice[0], dice[1]
    high, low = max(d0, d1), min(d0, d1)

    if high == low:
        orders = [("H", high, low)]
    else:
        orders = [("H", high, low), ("L", low, high)]

    candidates = []

    for order, first_die, second_die in orders:
        first_starts = _legal_starts(pos, first_die)

        for s1 in first_starts:
            p1 = _simulate_move(pos, s1, first_die)
            if p1 is None:
                continue

            second_starts = _legal_starts(p1, second_die)
            if second_starts:
                for s2 in second_starts:
                    p2 = _simulate_move(p1, s2, second_die)
                    if p2 is not None:
                        candidates.append((_action(order, s1, s2), p2, 2, order))
            else:
                candidates.append((_action(order, s1, None), p1, 1, order))

    if not candidates:
        return [("H:P,P", pos, 0, "H")]

    # Rule: if both dice can be played, both must be played.
    max_moves = max(c[2] for c in candidates)
    candidates = [c for c in candidates if c[2] == max_moves]

    # Rule: if only one die can be played, the higher die must be played when possible.
    if max_moves == 1 and high > low:
        high_candidates = [c for c in candidates if c[3] == "H"]
        if high_candidates:
            candidates = high_candidates

    return candidates


def _legal_starts(pos, die):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos

    if my_bar > 0:
        return ["B"] if _simulate_move(pos, "B", die) is not None else []

    starts = []
    for i in range(24):
        if my[i] > 0 and _simulate_move(pos, i, die) is not None:
            starts.append(i)
    return starts


def _simulate_move(pos, start, die):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos

    if start == "B":
        if my_bar <= 0:
            return None

        dest = 24 - die
        if dest < 0 or dest > 23:
            return None
        if opp[dest] >= 2:
            return None

        nmy = my[:]
        nopp = opp[:]
        n_my_bar = my_bar - 1
        n_opp_bar = opp_bar

        if nopp[dest] == 1:
            nopp[dest] = 0
            n_opp_bar += 1

        nmy[dest] += 1
        return (nmy, nopp, n_my_bar, n_opp_bar, my_off, opp_off)

    if not isinstance(start, int):
        return None
    if start < 0 or start > 23:
        return None
    if my_bar > 0:
        return None
    if my[start] <= 0:
        return None

    dest = start - die

    # Normal board move.
    if dest >= 0:
        if opp[dest] >= 2:
            return None

        nmy = my[:]
        nopp = opp[:]
        n_opp_bar = opp_bar

        nmy[start] -= 1

        if nopp[dest] == 1:
            nopp[dest] = 0
            n_opp_bar += 1

        nmy[dest] += 1
        return (nmy, nopp, my_bar, n_opp_bar, my_off, opp_off)

    # Bearing off.
    if not _all_my_checkers_home(my, my_bar):
        return None

    # Exact bear-off, or overshoot from the highest occupied home point.
    exact = (die == start + 1)
    overshoot = (die > start + 1 and not any(my[j] > 0 for j in range(start + 1, 6)))

    if not (exact or overshoot):
        return None

    nmy = my[:]
    nmy[start] -= 1
    return (nmy, opp[:], my_bar, opp_bar, my_off + 1, opp_off)


def _all_my_checkers_home(my, my_bar):
    return my_bar == 0 and sum(my[6:24]) == 0


# ---------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------

def _evaluate(pos):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos

    if my_off >= 15:
        return 1_000_000_000.0
    if opp_off >= 15:
        return -1_000_000_000.0

    my_pip = _my_pips(my, my_bar)
    opp_pip = _opp_pips(opp, opp_bar)

    score = 0.0

    # Race and material progress.
    score += 1200.0 * (my_off - opp_off)
    score += 9.0 * (opp_pip - my_pip)

    # Bar pressure is tactically very important.
    score += 575.0 * opp_bar
    score -= 675.0 * my_bar

    my_home_made = sum(1 for i in range(6) if my[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp[i] >= 2)

    if opp_bar:
        score += 95.0 * my_home_made * opp_bar
        if my_home_made == 6:
            score += 500.0 * opp_bar

    if my_bar:
        score -= 85.0 * opp_home_made * my_bar
        if opp_home_made == 6:
            score -= 500.0 * my_bar

    # Made points, anchors, home-board strength, and stack efficiency.
    for i, c in enumerate(my):
        if c >= 2:
            score += _my_point_bonus(i)
            if c > 3:
                score -= _stack_penalty(i, c)
        elif c == 1:
            score -= _my_blot_penalty(i, my, opp, opp_bar)

    for i, c in enumerate(opp):
        if c >= 2:
            score -= 0.85 * _opp_point_bonus(i)
            if c > 3:
                score += 0.35 * _opp_stack_penalty(i, c)
        elif c == 1:
            score += _opp_blot_reward(i, my, opp, my_bar)

    # Prime strength.
    score += _run_bonus(my)
    score -= 0.85 * _run_bonus(opp)

    # Slight preference for smoother bearoff structures once all checkers are home.
    if _all_my_checkers_home(my, my_bar):
        score += _bearoff_shape_bonus(my)

    return score


def _my_pips(my, my_bar):
    total = my_bar * 25
    for i, c in enumerate(my):
        total += (i + 1) * c
    return total


def _opp_pips(opp, opp_bar):
    total = opp_bar * 25
    for i, c in enumerate(opp):
        total += (24 - i) * c
    return total


def _my_point_bonus(i):
    # Our home board is 0..5. The 6-point, index 5, is especially valuable.
    if 0 <= i <= 5:
        return [45, 55, 70, 88, 108, 130][i]
    if 6 <= i <= 11:
        return 48
    if 12 <= i <= 17:
        return 38
    # Defensive anchors in the opponent home board.
    return 62


def _opp_point_bonus(i):
    # Mirror the board for the opponent.
    mirror_i = 23 - i
    return _my_point_bonus(mirror_i)


def _stack_penalty(i, c):
    extra = c - 3
    if i <= 5:
        return 7.0 * extra
    return 14.0 * extra


def _opp_stack_penalty(i, c):
    extra = c - 3
    if i >= 18:
        return 7.0 * extra
    return 14.0 * extra


def _run_bonus(points):
    bonus = 0.0
    run = 0
    for i in range(24):
        if points[i] >= 2:
            run += 1
        else:
            if run >= 2:
                bonus += 20.0 * run * run
            run = 0
    if run >= 2:
        bonus += 20.0 * run * run
    return bonus


def _my_blot_penalty(i, my, opp, opp_bar):
    penalty = 14.0

    # Blots in the opponent's home board and outer board tend to be dangerous.
    if i >= 18:
        penalty += 32.0
    elif i >= 6:
        penalty += 18.0

    attackers = 0
    direct_numbers = 0

    # Opponent moves upward, so an opposing checker on i-d can directly hit i.
    for d in range(1, 7):
        j = i - d
        if j >= 0 and opp[j] > 0:
            attackers += min(opp[j], 3)
            direct_numbers += 1

    penalty += 12.0 * attackers + 7.0 * direct_numbers

    # Opponent checkers on the bar enter into our home board, 0..5.
    if opp_bar > 0 and 0 <= i <= 5:
        penalty += 70.0 * opp_bar

    # A blot very deep in our home board is less bad if the opponent has no contact.
    if i <= 2 and opp_bar == 0 and attackers == 0:
        penalty *= 0.55

    return penalty


def _opp_blot_reward(i, my, opp, my_bar):
    reward = 8.0

    attackers = 0
    direct_numbers = 0

    # We move downward, so our checker on i+d can directly hit opponent blot i.
    for d in range(1, 7):
        j = i + d
        if j <= 23 and my[j] > 0:
            attackers += min(my[j], 3)
            direct_numbers += 1

    reward += 7.0 * attackers + 4.0 * direct_numbers

    # From our bar we enter on 18..23 and may hit a blot there.
    if my_bar > 0 and 18 <= i <= 23:
        reward += 35.0

    return reward


def _bearoff_shape_bonus(my):
    # Prefer having checkers closer to bearoff and avoid excessive gaps/stacks.
    bonus = 0.0
    occupied = [i for i in range(6) if my[i] > 0]
    if not occupied:
        return bonus

    highest = max(occupied)
    bonus -= 5.0 * highest

    for i in range(6):
        c = my[i]
        if c == 0:
            continue
        # In bearoff, lower points are closer to scoring.
        bonus += (6 - i) * 3.0 * c
        if c > 4:
            bonus -= (c - 4) * 5.0

    return bonus


def _tiny_tiebreak(action):
    # Stable tiny value in [0, 0.0001), avoiding random imports.
    v = 0
    for ch in action:
        v = (v * 131 + ord(ch)) % 1009
    return v / 1009.0 * 0.0001
