
import math
from copy import deepcopy

def policy(state: dict) -> str:
    """
    Backgammon policy.

    The policy generates legal candidate actions, simulates them, evaluates the
    resulting board, and returns the highest-scoring legal move string.
    """

    dice = list(state.get("dice", []))
    if not dice:
        return "H:P,P"

    def clone(st):
        return {
            "my_pts": list(st["my_pts"]),
            "opp_pts": list(st["opp_pts"]),
            "my_bar": int(st["my_bar"]),
            "opp_bar": int(st["opp_bar"]),
            "my_off": int(st["my_off"]),
            "opp_off": int(st["opp_off"]),
            "dice": list(st.get("dice", [])),
        }

    def all_in_home(st):
        if st["my_bar"] > 0:
            return False
        for i in range(6, 24):
            if st["my_pts"][i] > 0:
                return False
        return True

    def can_bear_off_from(st, pt, die):
        if not all_in_home(st):
            return False
        dest = pt - die
        if dest == -1:
            return True
        if dest < -1:
            # Oversized die can bear off only if no checker is farther away.
            for j in range(pt + 1, 6):
                if st["my_pts"][j] > 0:
                    return False
            return True
        return False

    def legal_starts_for_die(st, die):
        starts = []

        # Bar must be entered first.
        if st["my_bar"] > 0:
            dest = 24 - die
            if 0 <= dest <= 23 and st["opp_pts"][dest] < 2:
                starts.append("B")
            return starts

        for pt in range(24):
            if st["my_pts"][pt] <= 0:
                continue
            dest = pt - die
            if dest >= 0:
                if st["opp_pts"][dest] < 2:
                    starts.append("A" + str(pt))
            else:
                if can_bear_off_from(st, pt, die):
                    starts.append("A" + str(pt))

        return starts

    def apply_move(st, start, die):
        ns = clone(st)

        if start == "P":
            return ns

        if start == "B":
            if ns["my_bar"] <= 0:
                return None
            dest = 24 - die
            if not (0 <= dest <= 23):
                return None
            if ns["opp_pts"][dest] >= 2:
                return None

            ns["my_bar"] -= 1
            if ns["opp_pts"][dest] == 1:
                ns["opp_pts"][dest] = 0
                ns["opp_bar"] += 1
            ns["my_pts"][dest] += 1
            return ns

        if not start.startswith("A"):
            return None

        try:
            pt = int(start[1:])
        except Exception:
            return None

        if pt < 0 or pt > 23:
            return None
        if ns["my_pts"][pt] <= 0:
            return None
        if ns["my_bar"] > 0:
            return None

        dest = pt - die
        if dest >= 0:
            if ns["opp_pts"][dest] >= 2:
                return None
            ns["my_pts"][pt] -= 1
            if ns["opp_pts"][dest] == 1:
                ns["opp_pts"][dest] = 0
                ns["opp_bar"] += 1
            ns["my_pts"][dest] += 1
        else:
            if not can_bear_off_from(ns, pt, die):
                return None
            ns["my_pts"][pt] -= 1
            ns["my_off"] += 1

        return ns

    def generate_for_order(order_char, dice_seq):
        results = []

        def rec(st, idx, starts, used):
            if idx >= len(dice_seq):
                padded = list(starts)
                while len(padded) < 2:
                    padded.append("P")
                results.append((order_char + ":" + padded[0] + "," + padded[1], st, used))
                return

            die = dice_seq[idx]
            legal = legal_starts_for_die(st, die)

            if not legal:
                rec(st, idx + 1, starts + ["P"], used)
            else:
                for s in legal:
                    ns = apply_move(st, s, die)
                    if ns is not None:
                        rec(ns, idx + 1, starts + [s], used + 1)

        rec(clone(state), 0, [], 0)
        return results

    # Build candidate move sequences.
    candidates = []

    if len(dice) == 1:
        d = dice[0]
        candidates.extend(generate_for_order("H", [d]))
    else:
        d1, d2 = dice[0], dice[1]
        hi, lo = max(d1, d2), min(d1, d2)
        candidates.extend(generate_for_order("H", [hi, lo]))
        candidates.extend(generate_for_order("L", [lo, hi]))

    if not candidates:
        return "H:P,P"

    # Enforce maximum number of playable dice.
    max_used = max(c[2] for c in candidates)
    candidates = [c for c in candidates if c[2] == max_used]

    # If only one die can be played, higher die must be used if possible.
    if len(dice) >= 2 and max_used == 1:
        hi, lo = max(dice[0], dice[1]), min(dice[0], dice[1])
        high_initial = len(legal_starts_for_die(clone(state), hi)) > 0
        if high_initial:
            filtered = []
            for move, st, used in candidates:
                order = move[0]
                f1, f2 = move.split(":")[1].split(",")
                if order == "H" and f1 != "P":
                    filtered.append((move, st, used))
                elif order == "L" and f2 != "P":
                    filtered.append((move, st, used))
            if filtered:
                candidates = filtered

    def point_made_bonus(my_pts):
        score = 0.0
        for i, n in enumerate(my_pts):
            if n >= 2:
                # Home-board points are especially valuable.
                if i <= 5:
                    score += 7.0
                elif i <= 11:
                    score += 4.0
                else:
                    score += 2.0
        return score

    def blot_exposure_penalty(st):
        penalty = 0.0
        my = st["my_pts"]
        opp = st["opp_pts"]

        for i in range(24):
            if my[i] == 1:
                exposure = 0
                # Opponent moves upward, so checkers below us can hit us.
                for d in range(1, 7):
                    j = i - d
                    if 0 <= j <= 23 and opp[j] > 0:
                        exposure += opp[j]
                # Opponent on bar can enter onto our high points.
                if st["opp_bar"] > 0 and i >= 18:
                    exposure += 2 * st["opp_bar"]

                if exposure:
                    # Blots closer to home are more costly.
                    weight = 1.0 + max(0, 12 - i) / 8.0
                    penalty += exposure * weight

        return penalty

    def hitting_potential_bonus(st):
        bonus = 0.0
        my = st["my_pts"]
        opp = st["opp_pts"]
        for i in range(24):
            if opp[i] == 1:
                attackers = 0
                for d in range(1, 7):
                    j = i + d
                    if 0 <= j <= 23 and my[j] > 0:
                        attackers += my[j]
                bonus += min(attackers, 4) * 0.8
        return bonus

    def home_board_strength(st):
        made = 0
        spare = 0
        for i in range(6):
            if st["my_pts"][i] >= 2:
                made += 1
            if st["my_pts"][i] > 2:
                spare += st["my_pts"][i] - 2
        return 6.0 * made + 0.8 * spare

    def evaluate(st):
        my_pip = st["my_bar"] * 25
        opp_pip = st["opp_bar"] * 25

        for i, n in enumerate(st["my_pts"]):
            my_pip += n * (i + 1)

        for i, n in enumerate(st["opp_pts"]):
            opp_pip += n * (24 - i)

        score = 0.0

        # Race and bear-off priorities.
        score += -1.15 * my_pip
        score += 0.45 * opp_pip
        score += 120.0 * st["my_off"]
        score += -95.0 * st["opp_off"]

        # Bar and hitting.
        score += 28.0 * st["opp_bar"]
        score += -38.0 * st["my_bar"]

        # Structure and safety.
        score += point_made_bonus(st["my_pts"])
        score += home_board_strength(st)
        score += hitting_potential_bonus(st)
        score += -5.0 * blot_exposure_penalty(st)

        # Avoid stacks; prefer flexible distribution.
        for i, n in enumerate(st["my_pts"]):
            if n > 5:
                score -= (n - 5) * 2.5
            if n == 1 and i <= 5:
                score -= 3.0

        # Prefer advanced anchors / made points in opponent board.
        for i in range(18, 24):
            if st["my_pts"][i] >= 2:
                score += 3.0

        return score

    best_move = None
    best_score = -10**100

    for move, st, used in candidates:
        sc = evaluate(st)
        if sc > best_score:
            best_score = sc
            best_move = move

    if best_move:
        return best_move

    return "H:P,P"
