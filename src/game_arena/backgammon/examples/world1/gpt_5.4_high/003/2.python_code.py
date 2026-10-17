
from math import inf

# Unique unordered dice outcomes with standard 36-roll weights.
ROLLS = [(a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7)]

# Probability that at least one of two dice shows one of n distinct hitting numbers.
SHOT_PROB = [0.0] + [1.0 - ((6 - n) * (6 - n)) / 36.0 for n in range(1, 7)]


def _board_from_state(state):
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def _copy_board(board):
    return {
        "my_pts": board["my_pts"][:],
        "opp_pts": board["opp_pts"][:],
        "my_bar": board["my_bar"],
        "opp_bar": board["opp_bar"],
        "my_off": board["my_off"],
        "opp_off": board["opp_off"],
    }


def _flip_board(board):
    # Convert absolute board to the opponent-relative view (and vice versa).
    return {
        "my_pts": list(reversed(board["opp_pts"])),
        "opp_pts": list(reversed(board["my_pts"])),
        "my_bar": board["opp_bar"],
        "opp_bar": board["my_bar"],
        "my_off": board["opp_off"],
        "opp_off": board["my_off"],
    }


def _all_in_home(board):
    return board["my_bar"] == 0 and sum(board["my_pts"][6:]) == 0


def _token(src):
    return "B" if src == "B" else f"A{src}"


def _apply_move(board, src, die):
    # src is either "B" or an integer 0..23.
    if not (1 <= die <= 6):
        return None

    if board["my_bar"] > 0 and src != "B":
        return None

    newb = _copy_board(board)

    if src == "B":
        if newb["my_bar"] <= 0:
            return None
        dest = 24 - die  # 1->23, 6->18
        if newb["opp_pts"][dest] >= 2:
            return None
        newb["my_bar"] -= 1
        if newb["opp_pts"][dest] == 1:
            newb["opp_pts"][dest] = 0
            newb["opp_bar"] += 1
        newb["my_pts"][dest] += 1
        return newb

    if not (0 <= src <= 23):
        return None
    if newb["my_pts"][src] <= 0:
        return None

    dest = src - die
    if dest >= 0:
        if newb["opp_pts"][dest] >= 2:
            return None
        newb["my_pts"][src] -= 1
        if newb["opp_pts"][dest] == 1:
            newb["opp_pts"][dest] = 0
            newb["opp_bar"] += 1
        newb["my_pts"][dest] += 1
        return newb

    # Bearing off
    if not _all_in_home(newb):
        return None
    if src > 5:
        return None

    exact = (src == die - 1)
    oversize = (src < die - 1 and sum(newb["my_pts"][src + 1:6]) == 0)
    if not (exact or oversize):
        return None

    newb["my_pts"][src] -= 1
    newb["my_off"] += 1
    return newb


def _single_die_moves(board, die):
    moves = []
    if not (1 <= die <= 6):
        return moves

    if board["my_bar"] > 0:
        nb = _apply_move(board, "B", die)
        if nb is not None:
            moves.append(("B", nb))
        return moves

    for src in range(24):
        if board["my_pts"][src] > 0:
            nb = _apply_move(board, src, die)
            if nb is not None:
                moves.append((src, nb))
    return moves


def _generate_actions(board, dice):
    dice = list(dice)

    if len(dice) == 0:
        return [("H:P,P", _copy_board(board))]

    if len(dice) == 1:
        d = dice[0]
        one = _single_die_moves(board, d)
        if not one:
            return [("H:P,P", _copy_board(board))]
        return [(f"H:{_token(src)},P", nb) for src, nb in one]

    d1, d2 = dice[0], dice[1]
    hi, lo = (d1, d2) if d1 >= d2 else (d2, d1)

    seen = set()
    two_move_actions = []

    orders = [("H", hi, lo)] if hi == lo else [("H", hi, lo), ("L", lo, hi)]

    for label, first_die, second_die in orders:
        first_moves = _single_die_moves(board, first_die)
        for src1, b1 in first_moves:
            second_moves = _single_die_moves(b1, second_die)
            for src2, b2 in second_moves:
                act = f"{label}:{_token(src1)},{_token(src2)}"
                if act not in seen:
                    seen.add(act)
                    two_move_actions.append((act, b2))

    if two_move_actions:
        return two_move_actions

    # If only one die can be played, must play the higher die when possible.
    high_moves = _single_die_moves(board, hi)
    if high_moves:
        out = []
        for src, nb in high_moves:
            act = f"H:{_token(src)},P"
            if act not in seen:
                seen.add(act)
                out.append((act, nb))
        return out

    low_moves = _single_die_moves(board, lo)
    if low_moves:
        label = "H" if hi == lo else "L"
        out = []
        for src, nb in low_moves:
            act = f"{label}:{_token(src)},P"
            if act not in seen:
                seen.add(act)
                out.append((act, nb))
        return out

    return [("H:P,P", _copy_board(board))]


def _pip_counts_abs(board):
    my_pip = 25 * board["my_bar"]
    opp_pip = 25 * board["opp_bar"]
    for i in range(24):
        my_pip += (i + 1) * board["my_pts"][i]
        opp_pip += (24 - i) * board["opp_pts"][i]
    return my_pip, opp_pip


def _is_race_abs(board):
    if board["my_bar"] > 0 or board["opp_bar"] > 0:
        return False

    my_max = -1
    for i in range(23, -1, -1):
        if board["my_pts"][i] > 0:
            my_max = i
            break

    opp_min = 24
    for i in range(24):
        if board["opp_pts"][i] > 0:
            opp_min = i
            break

    return my_max < opp_min


def _count_made(pts, start, end):
    c = 0
    for i in range(start, end):
        if pts[i] >= 2:
            c += 1
    return c


def _count_occ(pts, start, end):
    c = 0
    for i in range(start, end):
        if pts[i] > 0:
            c += 1
    return c


def _count_blots(pts):
    return sum(1 for x in pts if x == 1)


def _prime_strength(pts):
    run = 0
    total = 0
    for x in pts:
        if x >= 2:
            run += 1
        else:
            if run >= 2:
                total += run * run
            run = 0
    if run >= 2:
        total += run * run
    return total


def _stack_penalty_my(pts):
    # Extra checkers on one point create wastage/flexibility issues.
    return sum((i + 1) * max(0, n - 3) for i, n in enumerate(pts))


def _stack_penalty_opp(pts):
    return sum((24 - i) * max(0, n - 3) for i, n in enumerate(pts))


def _my_blot_exposure_abs(board):
    # Our blots that opponent can hit directly next turn.
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    opp_bar = board["opp_bar"]

    total = 0.0
    for b in range(24):
        if my_pts[b] != 1:
            continue

        nums = [False] * 7
        if opp_bar > 0 and 0 <= b <= 5:
            nums[b + 1] = True

        for d in range(1, 7):
            src = b - d
            if src >= 0 and opp_pts[src] > 0:
                nums[d] = True

        n = sum(1 for d in range(1, 7) if nums[d])
        if n:
            # Getting hit near home is especially painful.
            cost = 1.0 + (23 - b) / 12.0
            total += SHOT_PROB[n] * cost

    return total


def _opp_blot_exposure_abs(board):
    # Opponent blots that we can hit directly next turn.
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    my_bar = board["my_bar"]

    total = 0.0
    for b in range(24):
        if opp_pts[b] != 1:
            continue

        nums = [False] * 7
        if my_bar > 0 and 18 <= b <= 23:
            d = 24 - b
            if 1 <= d <= 6:
                nums[d] = True

        for d in range(1, 7):
            src = b + d
            if src <= 23 and my_pts[src] > 0:
                nums[d] = True

        n = sum(1 for d in range(1, 7) if nums[d])
        if n:
            # Hitting an advanced opponent blot is especially valuable.
            cost = 1.0 + b / 12.0
            total += SHOT_PROB[n] * cost

    return total


def _static_eval_abs(board):
    # Large terminal scores.
    if board["my_off"] >= 15:
        return 1e9
    if board["opp_off"] >= 15:
        return -1e9

    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    my_pip, opp_pip = _pip_counts_abs(board)
    pip_diff = opp_pip - my_pip
    off_diff = board["my_off"] - board["opp_off"]
    bar_diff = board["opp_bar"] - board["my_bar"]

    race = _is_race_abs(board)

    my_home_made = _count_made(my_pts, 0, 6)
    my_outer_made = _count_made(my_pts, 6, 12)
    my_mid_made = _count_made(my_pts, 12, 18)
    my_anchor_made = _count_made(my_pts, 18, 24)

    opp_anchor_made = _count_made(opp_pts, 0, 6)
    opp_mid_made = _count_made(opp_pts, 6, 12)
    opp_outer_made = _count_made(opp_pts, 12, 18)
    opp_home_made = _count_made(opp_pts, 18, 24)

    home_occ_my = _count_occ(my_pts, 0, 6)
    home_occ_opp = _count_occ(opp_pts, 18, 24)

    my_blots = _count_blots(my_pts)
    opp_blots = _count_blots(opp_pts)

    my_prime = _prime_strength(my_pts)
    opp_prime = _prime_strength(opp_pts)

    my_stack = _stack_penalty_my(my_pts)
    opp_stack = _stack_penalty_opp(opp_pts)

    my_exposure = _my_blot_exposure_abs(board)
    opp_exposure = _opp_blot_exposure_abs(board)

    highest_my = 0
    for i in range(23, -1, -1):
        if my_pts[i] > 0:
            highest_my = i
            break

    lowest_opp = 0
    found_opp = False
    for i in range(24):
        if opp_pts[i] > 0:
            lowest_opp = i
            found_opp = True
            break
    if not found_opp:
        lowest_opp = 0

    score = 0.0

    # Core race / progress terms.
    score += 120.0 * off_diff
    score += 60.0 * bar_diff
    score += (1.65 if race else 0.65) * pip_diff

    # Structure / flexibility.
    score += 0.9 * (opp_stack - my_stack)
    score += 2.8 * (my_prime - opp_prime)

    # Tactical vulnerability / opportunities.
    score += 16.0 * opp_exposure
    score -= 22.0 * my_exposure

    if not race:
        score += 14.0 * (my_home_made - opp_home_made)
        score += 8.0 * (my_outer_made - opp_outer_made)
        score += 5.0 * (my_mid_made - opp_mid_made)
        score += 4.0 * (my_anchor_made - opp_anchor_made)

        score += 3.0 * (opp_blots - my_blots)

        # Escaping our back checkers and keeping theirs back matters in contact.
        score -= 1.0 * highest_my
        score -= 0.8 * lowest_opp

        # Closed board value when someone is on the bar.
        score += 4.0 * (board["opp_bar"] * my_home_made - board["my_bar"] * opp_home_made)
    else:
        # In a pure race, smoother bearoff distribution helps.
        score += 2.0 * (home_occ_my - home_occ_opp)
        score += 0.4 * (my_home_made - opp_home_made)

    return score


def _expected_reply_score_abs(board):
    # Opponent rolls next, and we assume they choose the reply worst for us.
    if board["my_off"] >= 15 or board["opp_off"] >= 15:
        return _static_eval_abs(board)

    opp_rel = _flip_board(board)
    total = 0.0

    for a, b, w in ROLLS:
        actions = _generate_actions(opp_rel, [a, b])
        worst_for_us = None

        for _, resp_rel in actions:
            resp_abs = _flip_board(resp_rel)
            s = _static_eval_abs(resp_abs)
            if worst_for_us is None or s < worst_for_us:
                worst_for_us = s

        if worst_for_us is None:
            worst_for_us = _static_eval_abs(board)

        total += w * worst_for_us

    return total / 36.0


def policy(state):
    try:
        board = _board_from_state(state)
        dice = [int(d) for d in state.get("dice", [])][:2]
        actions = _generate_actions(board, dice)
    except Exception:
        return "H:P,P"

    if not actions:
        return "H:P,P"
    if len(actions) == 1:
        return actions[0][0]

    # First-pass static scoring for all legal moves.
    scored = []
    for act, nb in actions:
        scored.append((_static_eval_abs(nb), act, nb))

    # Immediate win shortcut.
    for st, act, nb in scored:
        if nb["my_off"] >= 15:
            return act

    # Evaluate all if modest branching; otherwise only the best static candidates.
    scored.sort(key=lambda x: (-x[0], x[1]))
    contenders = scored if len(scored) <= 10 else scored[:8]

    best_action = contenders[0][1]
    best_value = -inf
    best_static = -inf

    try:
        for st, act, nb in contenders:
            reply = _expected_reply_score_abs(nb)
            val = 0.20 * st + 0.80 * reply
            if (
                val > best_value + 1e-12
                or (
                    abs(val - best_value) <= 1e-12
                    and (
                        st > best_static + 1e-12
                        or (abs(st - best_static) <= 1e-12 and act < best_action)
                    )
                )
            ):
                best_value = val
                best_static = st
                best_action = act
        return best_action
    except Exception:
        # Safe fallback: best static legal move.
        return scored[0][1]
