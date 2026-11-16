
import math
from copy import deepcopy

def policy(state: dict) -> str:
    dice = state.get("dice", [])
    if not dice:
        return "H:P,P"

    def clone_pos(s):
        return {
            "my_pts": list(s["my_pts"]),
            "opp_pts": list(s["opp_pts"]),
            "my_bar": int(s["my_bar"]),
            "opp_bar": int(s["opp_bar"]),
            "my_off": int(s["my_off"]),
            "opp_off": int(s["opp_off"]),
        }

    def all_home(pos):
        if pos["my_bar"] > 0:
            return False
        for i in range(6, 24):
            if pos["my_pts"][i] > 0:
                return False
        return True

    def blocked(pos, dest):
        return pos["opp_pts"][dest] >= 2

    def legal_starts_for_die(pos, die):
        starts = []

        if pos["my_bar"] > 0:
            dest = 24 - die
            if 0 <= dest <= 23 and not blocked(pos, dest):
                starts.append("B")
            return starts

        home = all_home(pos)

        for f in range(24):
            if pos["my_pts"][f] <= 0:
                continue

            dest = f - die

            if dest >= 0:
                if not blocked(pos, dest):
                    starts.append("A" + str(f))
            else:
                if home:
                    if die == f + 1:
                        starts.append("A" + str(f))
                    elif die > f + 1:
                        higher_exists = False
                        for j in range(f + 1, 6):
                            if pos["my_pts"][j] > 0:
                                higher_exists = True
                                break
                        if not higher_exists:
                            starts.append("A" + str(f))

        return starts

    def apply_move(pos, start, die):
        p = {
            "my_pts": list(pos["my_pts"]),
            "opp_pts": list(pos["opp_pts"]),
            "my_bar": pos["my_bar"],
            "opp_bar": pos["opp_bar"],
            "my_off": pos["my_off"],
            "opp_off": pos["opp_off"],
        }

        if start == "P":
            return p

        if start == "B":
            if p["my_bar"] <= 0:
                return None
            dest = 24 - die
            if dest < 0 or dest > 23 or p["opp_pts"][dest] >= 2:
                return None
            p["my_bar"] -= 1
        else:
            if not start.startswith("A"):
                return None
            try:
                f = int(start[1:])
            except Exception:
                return None
            if f < 0 or f > 23 or p["my_pts"][f] <= 0:
                return None

            dest = f - die
            p["my_pts"][f] -= 1

            if dest < 0:
                if not all_home(pos):
                    return None
                if die == f + 1:
                    p["my_off"] += 1
                    return p
                elif die > f + 1:
                    for j in range(f + 1, 6):
                        if pos["my_pts"][j] > 0:
                            return None
                    p["my_off"] += 1
                    return p
                else:
                    return None

        if start == "B":
            dest = 24 - die
        else:
            f = int(start[1:])
            dest = f - die

        if dest < 0:
            p["my_off"] += 1
            return p

        if p["opp_pts"][dest] == 1:
            p["opp_pts"][dest] = 0
            p["opp_bar"] += 1

        p["my_pts"][dest] += 1
        return p

    def generate_for_order(order, d1, d2):
        res = []
        starts1 = legal_starts_for_die(clone_pos(state), d1)

        if starts1:
            first_options = starts1
        else:
            first_options = ["P"]

        for s1 in first_options:
            pos1 = apply_move(clone_pos(state), s1, d1)
            if pos1 is None:
                continue

            starts2 = legal_starts_for_die(pos1, d2)
            if starts2:
                second_options = starts2
            else:
                second_options = ["P"]

            for s2 in second_options:
                pos2 = apply_move(pos1, s2, d2)
                if pos2 is None:
                    continue
                cnt = (0 if s1 == "P" else 1) + (0 if s2 == "P" else 1)
                res.append((order + ":" + s1 + "," + s2, pos2, cnt, s1, s2))

        return res

    if len(dice) == 1:
        d = dice[0]
        candidates = []
        for order in ("H", "L"):
            starts = legal_starts_for_die(clone_pos(state), d)
            if not starts:
                candidates.append((order + ":P,P", clone_pos(state), 0, "P", "P"))
            else:
                for s in starts:
                    p = apply_move(clone_pos(state), s, d)
                    if p is not None:
                        candidates.append((order + ":" + s + ",P", p, 1, s, "P"))
    else:
        hi = max(dice[0], dice[1])
        lo = min(dice[0], dice[1])

        candidates = []
        candidates.extend(generate_for_order("H", hi, lo))
        candidates.extend(generate_for_order("L", lo, hi))

        if not candidates:
            return "H:P,P"

        maxcnt = max(c[2] for c in candidates)
        candidates = [c for c in candidates if c[2] == maxcnt]

        if maxcnt == 1 and hi != lo:
            initial_hi = legal_starts_for_die(clone_pos(state), hi)
            if initial_hi:
                filtered = []
                for c in candidates:
                    move = c[0]
                    order, rest = move.split(":")
                    a, b = rest.split(",")
                    if order == "H" and a != "P":
                        filtered.append(c)
                    elif order == "L" and b != "P":
                        filtered.append(c)
                if filtered:
                    candidates = filtered

    if not candidates:
        return "H:P,P"

    def pip_my(pos):
        return sum((i + 1) * pos["my_pts"][i] for i in range(24)) + 25 * pos["my_bar"]

    def pip_opp(pos):
        return sum((24 - i) * pos["opp_pts"][i] for i in range(24)) + 25 * pos["opp_bar"]

    def blot_danger(pos, i):
        if pos["my_pts"][i] != 1:
            return 0.0
        danger = 0.0

        for j in range(max(0, i - 6), i):
            if pos["opp_pts"][j] > 0:
                dist = i - j
                danger += pos["opp_pts"][j] * (7 - dist)

        if 18 <= i <= 23 and pos["opp_bar"] > 0:
            entry_die = 24 - i
            if 1 <= entry_die <= 6:
                danger += 8.0 + 2.0 * pos["opp_bar"]

        return danger

    def eval_pos(pos):
        score = 0.0

        score += 120.0 * (pos["my_off"] - pos["opp_off"])
        score += 3.2 * (pip_opp(pos) - pip_my(pos))

        score -= 28.0 * pos["my_bar"]
        score += 24.0 * pos["opp_bar"]

        for i in range(24):
            m = pos["my_pts"][i]
            o = pos["opp_pts"][i]

            if m >= 2:
                if i <= 5:
                    score += 7.0 + 1.0 * m
                elif i >= 18:
                    score += 4.0
                else:
                    score += 3.0

            if m == 1:
                danger = blot_danger(pos, i)
                score -= 2.8 * danger
                if i <= 5:
                    score -= 1.5
                if i >= 18:
                    score -= 2.5

            if o == 1:
                score += 2.0
                if i <= 5:
                    score += 3.0
                if pos["my_bar"] == 0:
                    for j in range(i + 1, min(24, i + 7)):
                        if pos["my_pts"][j] > 0:
                            score += 1.2 * pos["my_pts"][j]

            if o >= 2:
                if i >= 18:
                    score -= 3.0

        if all_home(pos):
            score += 20.0
            score -= 1.5 * sum(i * pos["my_pts"][i] for i in range(6))

        made_home = sum(1 for i in range(6) if pos["my_pts"][i] >= 2)
        score += 6.0 * made_home

        opp_blocked_entry = 0
        if pos["opp_bar"] > 0:
            for die in range(1, 7):
                dest = 24 - die
                if pos["my_pts"][dest] >= 2:
                    opp_blocked_entry += 1
            score += 8.0 * opp_blocked_entry * pos["opp_bar"]

        return score

    best = None
    best_score = -10**18

    for cand in candidates:
        move, pos, cnt, s1, s2 = cand
        sc = eval_pos(pos)

        if cnt == 2:
            sc += 1.0
        if "B" in (s1, s2):
            sc += 1.5

        if sc > best_score:
            best_score = sc
            best = move

    if best is None:
        return "H:P,P"

    return best
