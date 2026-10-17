
# Backgammon policy for the arena.
# The player using this policy always moves from point 23 down to point 0.

def policy(state: dict) -> str:
    try:
        actions = _legal_actions(state)
        if not actions:
            return "H:P,P"

        best_action = actions[0]["action"]
        best_score = None

        for a in actions:
            score = _evaluate(a["board"])
            # Tiny deterministic tie-breaks: prefer using more pips/off progress already
            # reflected in eval, then prefer non-pass moves.
            score += 0.01 * a["used_count"]
            if best_score is None or score > best_score:
                best_score = score
                best_action = a["action"]

        return best_action
    except Exception:
        # Valid arena states should not reach this. Kept as a last-resort string.
        return "H:P,P"


def _copy_board(state):
    return {
        "my_pts": list(state.get("my_pts", [0] * 24)),
        "opp_pts": list(state.get("opp_pts", [0] * 24)),
        "my_bar": int(state.get("my_bar", 0)),
        "opp_bar": int(state.get("opp_bar", 0)),
        "my_off": int(state.get("my_off", 0)),
        "opp_off": int(state.get("opp_off", 0)),
    }


def _all_in_home(b):
    return b["my_bar"] == 0 and sum(b["my_pts"][6:24]) == 0


def _can_bear_off_from(b, point, die):
    if not _all_in_home(b):
        return False
    dest = point - die
    if dest >= 0:
        return False
    # Exact bear-off.
    if die == point + 1:
        return True
    # Oversized die may bear off only from the highest occupied point.
    if die > point + 1:
        for j in range(point + 1, 6):
            if b["my_pts"][j] > 0:
                return False
        return True
    return False


def _apply_move(b, from_token, die):
    nb = {
        "my_pts": b["my_pts"][:],
        "opp_pts": b["opp_pts"][:],
        "my_bar": b["my_bar"],
        "opp_bar": b["opp_bar"],
        "my_off": b["my_off"],
        "opp_off": b["opp_off"],
    }

    if from_token == "B":
        if nb["my_bar"] <= 0:
            return None
        dest = 24 - die
        if dest < 0 or dest > 23:
            return None
        if nb["opp_pts"][dest] >= 2:
            return None
        nb["my_bar"] -= 1
        if nb["opp_pts"][dest] == 1:
            nb["opp_pts"][dest] = 0
            nb["opp_bar"] += 1
        nb["my_pts"][dest] += 1
        return nb

    if not from_token.startswith("A"):
        return None

    try:
        src = int(from_token[1:])
    except Exception:
        return None

    if src < 0 or src > 23 or nb["my_pts"][src] <= 0:
        return None

    # If we have men on the bar, no point checker may be moved.
    if nb["my_bar"] > 0:
        return None

    dest = src - die
    nb["my_pts"][src] -= 1

    if dest >= 0:
        if nb["opp_pts"][dest] >= 2:
            return None
        if nb["opp_pts"][dest] == 1:
            nb["opp_pts"][dest] = 0
            nb["opp_bar"] += 1
        nb["my_pts"][dest] += 1
        return nb

    # Bearing off.
    # Re-check on the original board, before removing the checker.
    if not _can_bear_off_from(b, src, die):
        return None
    nb["my_off"] += 1
    return nb


def _legal_single_die_moves(b, die):
    moves = []

    # Bar has absolute priority.
    if b["my_bar"] > 0:
        token = "B"
        nb = _apply_move(b, token, die)
        if nb is not None:
            moves.append((token, nb))
        return moves

    for i in range(24):
        if b["my_pts"][i] <= 0:
            continue
        token = "A" + str(i)
        nb = _apply_move(b, token, die)
        if nb is not None:
            moves.append((token, nb))

    return moves


def _legal_actions(state):
    dice = list(state.get("dice", []))
    dice = [int(d) for d in dice if int(d) > 0]

    start = _copy_board(state)

    if len(dice) == 0:
        return [{"action": "H:P,P", "board": start, "used_count": 0, "used_dice": []}]

    if len(dice) == 1:
        d = dice[0]
        opts = _legal_single_die_moves(start, d)
        if not opts:
            return [{"action": "H:P,P", "board": start, "used_count": 0, "used_dice": []}]
        res = []
        for frm, nb in opts:
            res.append({
                "action": "H:%s,P" % frm,
                "board": nb,
                "used_count": 1,
                "used_dice": [d],
            })
        return res

    # Arena format supports two encoded checker moves.
    hi = max(dice[0], dice[1])
    lo = min(dice[0], dice[1])

    orders = [("H", [hi, lo])]
    if hi != lo:
        orders.append(("L", [lo, hi]))

    sequences = []

    for order_char, ordered_dice in orders:
        d1, d2 = ordered_dice

        first_opts = _legal_single_die_moves(start, d1)
        if not first_opts:
            first_opts = [("P", start)]

        for f1, b1 in first_opts:
            used1 = [] if f1 == "P" else [d1]

            second_opts = _legal_single_die_moves(b1, d2)
            if not second_opts:
                second_opts = [("P", b1)]

            for f2, b2 in second_opts:
                used = used1[:] if f1 != "P" else []
                if f2 != "P":
                    used.append(d2)
                sequences.append({
                    "action": "%s:%s,%s" % (order_char, f1, f2),
                    "board": b2,
                    "used_count": len(used),
                    "used_dice": used,
                })

    if not sequences:
        return [{"action": "H:P,P", "board": start, "used_count": 0, "used_dice": []}]

    # Must play the maximum possible number of dice.
    max_used = max(s["used_count"] for s in sequences)
    sequences = [s for s in sequences if s["used_count"] == max_used]

    # If only one die can be played, the higher die must be played if possible.
    if max_used == 1 and hi > lo:
        high_sequences = [s for s in sequences if s["used_dice"] and s["used_dice"][0] == hi]
        if high_sequences:
            sequences = high_sequences

    return sequences


def _pip_counts(b):
    my_pips = 25 * b["my_bar"]
    opp_pips = 25 * b["opp_bar"]

    for i, c in enumerate(b["my_pts"]):
        if c:
            my_pips += (i + 1) * c

    for i, c in enumerate(b["opp_pts"]):
        if c:
            # Opponent moves from 0 up to 23 and bears off past 23.
            opp_pips += (24 - i) * c

    return my_pips, opp_pips


def _my_made_point_value(i):
    # Our home board is 0..5. Points 18..23 are advanced anchors.
    if 0 <= i <= 5:
        return 10.0 + 1.2 * i
    if 6 <= i <= 11:
        return 7.0
    if 12 <= i <= 17:
        return 5.0
    return 7.5


def _opp_made_point_value(i):
    # Opponent home board is 18..23 from their perspective.
    if 18 <= i <= 23:
        return 10.0 + 1.2 * (23 - i)
    if 12 <= i <= 17:
        return 7.0
    if 6 <= i <= 11:
        return 5.0
    return 7.5


def _my_blot_penalty(b, i):
    opp = b["opp_pts"]
    risk = 0.0

    # Opponent bar enters on 0..5.
    if i <= 5 and b["opp_bar"] > 0:
        risk += 2.5 * min(b["opp_bar"], 3)

    # Direct shots from opponent checkers behind the blot.
    for d in range(1, 7):
        src = i - d
        if src >= 0 and opp[src] > 0:
            risk += 1.0 + 0.25 * min(opp[src] - 1, 4)

    if risk <= 0:
        base = 0.6
    else:
        base = 2.0

    pen = base + 5.2 * risk

    # Blots in our home while opponent is on the bar are especially bad.
    if i <= 5 and b["opp_bar"] > 0:
        pen += 8.0

    # Advanced blots can sometimes be useful as builders/anchors, discount a bit.
    if i >= 18:
        pen *= 0.85

    return pen


def _opp_blot_bonus(b, i):
    my = b["my_pts"]
    chance = 0.0

    # We enter from the bar on 18..23.
    if i >= 18 and b["my_bar"] > 0:
        chance += 2.0 * min(b["my_bar"], 3)

    # Our direct shots come from higher-numbered points.
    for d in range(1, 7):
        src = i + d
        if src <= 23 and my[src] > 0:
            chance += 1.0 + 0.25 * min(my[src] - 1, 4)

    if chance <= 0:
        return 0.5
    return 2.0 + 3.2 * chance


def _prime_score(points):
    total = 0.0
    run = 0
    for i in range(24):
        if points[i] >= 2:
            run += 1
        else:
            if run >= 2:
                total += 1.6 * run * run
            run = 0
    if run >= 2:
        total += 1.6 * run * run
    return total


def _evaluate(b):
    if b["my_off"] >= 15:
        return 1000000.0
    if b["opp_off"] >= 15:
        return -1000000.0

    my_pips, opp_pips = _pip_counts(b)

    score = 0.0

    # Race and bear-off equity.
    score += 120.0 * (b["my_off"] - b["opp_off"])
    score += 3.2 * (opp_pips - my_pips)

    # Bar pressure: hitting is valuable; being hit is costly.
    score += 55.0 * b["opp_bar"]
    score -= 65.0 * b["my_bar"]

    my = b["my_pts"]
    opp = b["opp_pts"]

    my_home_made = 0
    opp_home_made = 0

    for i in range(24):
        c = my[i]
        oc = opp[i]

        if c >= 2:
            val = _my_made_point_value(i)
            score += val
            if i <= 5:
                my_home_made += 1

            # Too many checkers stacked on one point are inefficient,
            # except somewhat less so in the inner board during bear-off.
            if c > 3:
                stack_pen = (c - 3) * (c - 3)
                if i <= 5:
                    stack_pen *= 0.55
                score -= 1.8 * stack_pen

        elif c == 1:
            score -= _my_blot_penalty(b, i)

        if oc >= 2:
            val = _opp_made_point_value(i)
            score -= val
            if i >= 18:
                opp_home_made += 1

            if oc > 3:
                stack_pen = (oc - 3) * (oc - 3)
                if i >= 18:
                    stack_pen *= 0.55
                score += 1.4 * stack_pen

        elif oc == 1:
            score += _opp_blot_bonus(b, i)

    # Primes and compact blocking structures.
    score += _prime_score(my)
    score -= _prime_score(opp)

    # Closed or strong home board when opponent is on the bar.
    if b["opp_bar"] > 0:
        score += b["opp_bar"] * my_home_made * 18.0
        if my_home_made == 6:
            score += 450.0

    # Opponent closed board while we are on the bar is disastrous.
    if b["my_bar"] > 0:
        score -= b["my_bar"] * opp_home_made * 20.0
        if opp_home_made == 6:
            score -= 500.0

    # Bearing-off mode: once all checkers are home, emphasize taking checkers off
    # and smoothing stacks.
    if b["my_bar"] == 0 and sum(my[6:24]) == 0:
        score += 35.0
        for i in range(6):
            score -= 0.25 * i * my[i]

    # Opponent bearing-off containment.
    if b["opp_bar"] == 0 and sum(opp[0:18]) == 0:
        score -= 35.0

    return score
