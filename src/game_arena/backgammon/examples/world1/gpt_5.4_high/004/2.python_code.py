
from typing import Dict, List, Any

# Unordered dice outcomes with standard probabilities.
# If doubles ever appear in this arena, this code treats them as "two moves"
# for lookahead/evaluation purposes; the policy API itself only supports up to two moves.
_ROLLS = [((a, b), (1.0 if a == b else 2.0) / 36.0) for a in range(1, 7) for b in range(a, 7)]


def _make_pos(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
        "dice": list(state.get("dice", [])),
    }


def _clone(pos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "my_pts": pos["my_pts"][:],
        "opp_pts": pos["opp_pts"][:],
        "my_bar": pos["my_bar"],
        "opp_bar": pos["opp_bar"],
        "my_off": pos["my_off"],
        "opp_off": pos["opp_off"],
        "dice": list(pos.get("dice", [])),
    }


def _mirror(pos: Dict[str, Any]) -> Dict[str, Any]:
    # Convert to opponent-to-move perspective, reusing the same move logic.
    return {
        "my_pts": [pos["opp_pts"][23 - i] for i in range(24)],
        "opp_pts": [pos["my_pts"][23 - i] for i in range(24)],
        "my_bar": pos["opp_bar"],
        "opp_bar": pos["my_bar"],
        "my_off": pos["opp_off"],
        "opp_off": pos["my_off"],
        "dice": list(pos.get("dice", [])),
    }


def _tok(src: Any) -> str:
    if src == "B" or src == "P":
        return src
    return "A" + str(src)


def _all_in_home(pos: Dict[str, Any]) -> bool:
    if pos["my_bar"] > 0:
        return False
    pts = pos["my_pts"]
    for i in range(6, 24):
        if pts[i] > 0:
            return False
    return True


def _legal_single_sources(pos: Dict[str, Any], die: int) -> List[Any]:
    my_pts = pos["my_pts"]
    opp_pts = pos["opp_pts"]

    # Must enter from bar first.
    if pos["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ["B"]
        return []

    sources = []
    can_bear = _all_in_home(pos)

    for i in range(24):
        if my_pts[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                sources.append(i)
        else:
            if not can_bear:
                continue
            # Exact bear-off.
            if die == i + 1:
                sources.append(i)
            # Oversized die: only from highest occupied point.
            elif die > i + 1:
                higher_occupied = False
                for j in range(i + 1, 6):
                    if my_pts[j] > 0:
                        higher_occupied = True
                        break
                if not higher_occupied:
                    sources.append(i)

    return sources


def _apply_move(pos: Dict[str, Any], src: Any, die: int) -> Dict[str, Any]:
    new_pos = _clone(pos)
    my_pts = new_pos["my_pts"]
    opp_pts = new_pos["opp_pts"]

    if src == "B":
        new_pos["my_bar"] -= 1
        dest = 24 - die
    else:
        my_pts[src] -= 1
        dest = src - die

    if dest >= 0:
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            new_pos["opp_bar"] += 1
        my_pts[dest] += 1
    else:
        new_pos["my_off"] += 1

    return new_pos


def _ordered_actions(pos: Dict[str, Any], die1: int, die2: int, order_char: str) -> List[Dict[str, Any]]:
    actions = []
    first_sources = _legal_single_sources(pos, die1)

    for s1 in first_sources:
        pos1 = _apply_move(pos, s1, die1)
        second_sources = _legal_single_sources(pos1, die2)

        if second_sources:
            for s2 in second_sources:
                pos2 = _apply_move(pos1, s2, die2)
                actions.append({
                    "move": f"{order_char}:{_tok(s1)},{_tok(s2)}",
                    "after": pos2,
                    "both": True,
                })
        else:
            actions.append({
                "move": f"{order_char}:{_tok(s1)},P",
                "after": pos1,
                "both": False,
            })

    return actions


def _generate_actions(pos: Dict[str, Any]) -> List[Dict[str, Any]]:
    dice = list(pos.get("dice", []))

    if len(dice) == 0:
        return [{"move": "H:P,P", "after": _clone(pos), "both": False}]

    if len(dice) == 1:
        d = dice[0]
        srcs = _legal_single_sources(pos, d)
        if not srcs:
            return [{"move": "H:P,P", "after": _clone(pos), "both": False}]
        return [{
            "move": f"H:{_tok(s)},P",
            "after": _apply_move(pos, s, d),
            "both": False,
        } for s in srcs]

    high = max(dice)
    low = min(dice)

    seqs = _ordered_actions(pos, high, low, "H")
    if high != low:
        seqs.extend(_ordered_actions(pos, low, high, "L"))

    # If any legal way uses both dice, only those are legal.
    both = [a for a in seqs if a["both"]]
    if both:
        return both

    # Otherwise, if only one die can be played, must play the higher die when possible.
    high_srcs = _legal_single_sources(pos, high)
    if high_srcs:
        return [{
            "move": f"H:{_tok(s)},P",
            "after": _apply_move(pos, s, high),
            "both": False,
        } for s in high_srcs]

    low_srcs = _legal_single_sources(pos, low)
    if low_srcs:
        return [{
            "move": f"L:{_tok(s)},P",
            "after": _apply_move(pos, s, low),
            "both": False,
        } for s in low_srcs]

    return [{"move": "H:P,P", "after": _clone(pos), "both": False}]


def _pip_count(pos: Dict[str, Any]) -> int:
    total = 25 * pos["my_bar"]
    pts = pos["my_pts"]
    for i in range(24):
        total += (i + 1) * pts[i]
    return total


def _has_contact(pos: Dict[str, Any]) -> bool:
    if pos["my_bar"] > 0 or pos["opp_bar"] > 0:
        return True

    max_my = -1
    min_opp = 24

    for i in range(24):
        if pos["my_pts"][i] > 0:
            max_my = i
        if pos["opp_pts"][i] > 0 and min_opp == 24:
            min_opp = i

    if max_my == -1 or min_opp == 24:
        return False

    return max_my >= min_opp


def _prime_stats(pts: List[int]) -> (int, int):
    longest = 0
    cur = 0
    sq = 0
    for n in pts:
        if n >= 2:
            cur += 1
        else:
            if cur >= 2:
                sq += cur * cur
            if cur > longest:
                longest = cur
            cur = 0
    if cur >= 2:
        sq += cur * cur
    if cur > longest:
        longest = cur
    return longest, sq


def _direct_shot_values_count(i: int, opp_pts: List[int], opp_bar: int) -> int:
    seen = [False] * 7  # indices 1..6 used

    # Opponent entering from bar (their entry is our 0..5).
    if opp_bar > 0 and 0 <= i <= 5:
        seen[i + 1] = True

    # Direct single-die shots from the board: opponent moves increasing.
    for d in range(1, 7):
        j = i - d
        if 0 <= j < 24 and opp_pts[j] > 0:
            seen[d] = True

    cnt = 0
    for d in range(1, 7):
        if seen[d]:
            cnt += 1
    return cnt


def _side_score(pos: Dict[str, Any], contact: bool) -> float:
    my_pts = pos["my_pts"]
    opp_pts = pos["opp_pts"]

    score = 0.0

    # Progress.
    score += 130.0 * pos["my_off"]
    score -= (2.4 if not contact else 1.1) * _pip_count(pos)

    # Bar status.
    score -= 38.0 * pos["my_bar"]
    score += 26.0 * pos["opp_bar"]

    # Made points / anchors / home board strength.
    home_closed = 0
    for i, n in enumerate(my_pts):
        if n >= 2:
            if i <= 5:
                score += 6.0
                home_closed += 1
            elif i <= 11:
                score += 4.8
            elif i <= 17:
                score += 3.4
            else:
                score += 4.0 if contact else 1.8
            if i in (4, 5, 6, 7):
                score += 1.2

    if pos["opp_bar"] > 0:
        score += 8.0 * home_closed * pos["opp_bar"]
        if home_closed == 6:
            score += 25.0 * pos["opp_bar"]

    # Prime strength.
    longest, prime_sq = _prime_stats(my_pts)
    score += 1.6 * prime_sq + 2.2 * longest
    if contact and longest >= 4:
        score += 4.0 * (longest - 3)

    # Escaped checkers.
    if contact:
        min_opp = 24
        for i in range(24):
            if opp_pts[i] > 0:
                min_opp = i
                break
        if min_opp < 24:
            escaped = 0
            for i in range(min_opp):
                escaped += my_pts[i]
            score += 1.0 * escaped

    # Blots and direct shot risk.
    blot_count = 0
    risk_total = 0.0
    for i, n in enumerate(my_pts):
        if n == 1:
            blot_count += 1
            k = _direct_shot_values_count(i, opp_pts, pos["opp_bar"])
            if k > 0:
                p_hit = 1.0 - ((6 - k) * (6 - k)) / 36.0
                severity = 6.0 + 0.35 * i
                risk_total += p_hit * severity

    score -= (1.5 if contact else 0.2) * blot_count
    score -= (6.0 if contact else 2.0) * risk_total

    # Stacks: too many checkers on one point wastes flexibility.
    stack_pen = 0.0
    for i, n in enumerate(my_pts):
        if n > 3:
            stack_pen += (n - 3) * (1.0 + 0.08 * max(0, i - 5))
    score -= (1.4 if contact else 0.8) * stack_pen

    return score


def _static_score(pos: Dict[str, Any]) -> float:
    contact = _has_contact(pos)
    mir = _mirror(pos)
    return _side_score(pos, contact) - _side_score(mir, contact)


def _expected_after_opp(pos: Dict[str, Any]) -> float:
    # Expected value from our perspective after opponent gets a roll and plays best.
    mir = _mirror(pos)
    total = 0.0

    for (a, b), prob in _ROLLS:
        st = {
            "my_pts": mir["my_pts"][:],
            "opp_pts": mir["opp_pts"][:],
            "my_bar": mir["my_bar"],
            "opp_bar": mir["opp_bar"],
            "my_off": mir["my_off"],
            "opp_off": mir["opp_off"],
            "dice": [a, b],
        }
        opp_actions = _generate_actions(st)

        best_opp = None
        for act in opp_actions:
            sc = _static_score(act["after"])
            if best_opp is None or sc > best_opp:
                best_opp = sc

        # Negate because best_opp is from opponent-to-move perspective.
        total += prob * (-best_opp)

    return total


def policy(state: dict) -> str:
    pos = _make_pos(state)
    actions = _generate_actions(pos)

    if not actions:
        return "H:P,P"
    if len(actions) == 1:
        return actions[0]["move"]

    for act in actions:
        act["base"] = _static_score(act["after"])
        act["final"] = act["base"]

    # Tactical lookahead in contact positions.
    if _has_contact(pos) or pos["my_bar"] > 0 or pos["opp_bar"] > 0:
        ranked = sorted(actions, key=lambda a: (-a["base"], a["move"]))
        topn = 6 if len(actions) <= 6 else 4
        try:
            for act in ranked[:topn]:
                exp_sc = _expected_after_opp(act["after"])
                act["final"] = 0.65 * act["base"] + 0.35 * exp_sc
        except Exception:
            # If anything goes wrong in lookahead, keep the static scores.
            pass

    best = actions[0]
    for act in actions[1:]:
        if act["final"] > best["final"] + 1e-12:
            best = act
        elif abs(act["final"] - best["final"]) <= 1e-12 and act["move"] < best["move"]:
            best = act

    return best["move"]
