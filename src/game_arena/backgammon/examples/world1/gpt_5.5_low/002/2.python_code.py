
from typing import List, Tuple, Dict, Any
import math

def policy(state: dict) -> str:
    """
    Backgammon policy.

    Returns a compact legal move string:
        <ORDER>:<FROM1>,<FROM2>
    where ORDER is H or L and FROM tokens are A0..A23, B, or P.
    """

    dice = list(state.get("dice", []))
    if not dice:
        return "H:P,P"

    # Normalize to at most two dice as described by arena.
    if len(dice) == 1:
        high = low = dice[0]
    else:
        high = max(dice[0], dice[1])
        low = min(dice[0], dice[1])

    legal_actions = _generate_legal_actions(state, high, low, len(dice))

    if not legal_actions:
        return "H:P,P"

    best_action = None
    best_score = -10**18

    for action in legal_actions:
        order, starts, resulting_state = action
        score = _evaluate(resulting_state)

        # Small tactical tie-breakers.
        # Prefer actually moving more checkers, then high die first if equal.
        moved = sum(1 for s in starts if s != "P")
        score += moved * 0.001
        if order == "H":
            score += 0.0001

        if score > best_score:
            best_score = score
            best_action = action

    order, starts, _ = best_action
    while len(starts) < 2:
        starts.append("P")
    return f"{order}:{starts[0]},{starts[1]}"


def _copy_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state.get("my_bar", 0)),
        "opp_bar": int(state.get("opp_bar", 0)),
        "my_off": int(state.get("my_off", 0)),
        "opp_off": int(state.get("opp_off", 0)),
        "dice": list(state.get("dice", [])),
    }


def _all_in_home(s: Dict[str, Any]) -> bool:
    # We bear off toward below point 0; home board is A0..A5.
    if s["my_bar"] > 0:
        return False
    for i in range(6, 24):
        if s["my_pts"][i] > 0:
            return False
    return True


def _can_bear_from(s: Dict[str, Any], idx: int, die: int) -> bool:
    dest = idx - die
    if dest >= 0:
        return False
    if not _all_in_home(s):
        return False
    # Exact bear-off is legal.
    if die == idx + 1:
        return True
    # Oversized die may bear off from the highest occupied point only.
    if die > idx + 1:
        for j in range(idx + 1, 6):
            if s["my_pts"][j] > 0:
                return False
        return True
    return False


def _legal_starts_for_die(s: Dict[str, Any], die: int) -> List[str]:
    starts = []

    # Bar has priority.
    if s["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and s["opp_pts"][dest] < 2:
            return ["B"]
        return []

    for i in range(24):
        if s["my_pts"][i] <= 0:
            continue
        dest = i - die
        if dest >= 0:
            if s["opp_pts"][dest] < 2:
                starts.append(f"A{i}")
        else:
            if _can_bear_from(s, i, die):
                starts.append(f"A{i}")

    return starts


def _apply_move(s: Dict[str, Any], start: str, die: int) -> Dict[str, Any]:
    ns = _copy_state(s)

    if start == "P":
        return ns

    if start == "B":
        if ns["my_bar"] <= 0:
            return ns
        ns["my_bar"] -= 1
        dest = 24 - die
    else:
        idx = int(start[1:])
        if ns["my_pts"][idx] <= 0:
            return ns
        ns["my_pts"][idx] -= 1
        dest = idx - die

    if dest < 0:
        ns["my_off"] += 1
    else:
        if ns["opp_pts"][dest] == 1:
            ns["opp_pts"][dest] = 0
            ns["opp_bar"] += 1
        ns["my_pts"][dest] += 1

    return ns


def _seqs_for_order(state: Dict[str, Any], dice_seq: List[int], order_char: str) -> List[Tuple[str, List[str], Dict[str, Any]]]:
    results = []

    def rec(s, k, starts):
        if k >= len(dice_seq):
            results.append((order_char, starts[:], s))
            return

        die = dice_seq[k]
        legal = _legal_starts_for_die(s, die)
        if not legal:
            # Pass this die; the global filtering later keeps only legal max-usage actions.
            rec(s, k + 1, starts + ["P"])
        else:
            for st in legal:
                ns = _apply_move(s, st, die)
                rec(ns, k + 1, starts + [st])

    rec(_copy_state(state), 0, [])
    return results


def _generate_legal_actions(state: Dict[str, Any], high: int, low: int, dice_count: int):
    if dice_count <= 0:
        return []

    if dice_count == 1:
        # Single die: encode as H by convention.
        seqs = _seqs_for_order(state, [high], "H")
        actions = []
        for order, starts, s2 in seqs:
            if len(starts) < 2:
                starts = starts + ["P"] * (2 - len(starts))
            actions.append((order, starts[:2], s2))
        # Prefer non-pass if any.
        max_moved = max(sum(1 for x in a[1] if x != "P") for a in actions)
        return [a for a in actions if sum(1 for x in a[1] if x != "P") == max_moved]

    # Two dice.
    actions = []
    actions.extend(_seqs_for_order(state, [high, low], "H"))
    if low != high:
        actions.extend(_seqs_for_order(state, [low, high], "L"))

    if not actions:
        return []

    # Keep only actions that play the maximum number of dice.
    max_moved = max(sum(1 for x in starts if x != "P") for _, starts, _ in actions)
    actions = [a for a in actions if sum(1 for x in a[1] if x != "P") == max_moved]

    # If only one die can be played, must play the higher die when possible.
    if max_moved == 1 and high != low:
        high_initial = len(_legal_starts_for_die(_copy_state(state), high)) > 0
        if high_initial:
            filtered = []
            for order, starts, s2 in actions:
                if order == "H" and starts[0] != "P":
                    filtered.append((order, starts, s2))
                elif order == "L" and len(starts) > 1 and starts[0] == "P" and starts[1] != "P":
                    # Mostly unreachable with our recursion, but safe.
                    filtered.append((order, starts, s2))
            if filtered:
                actions = filtered

    # Normalize/deduplicate.
    seen = set()
    out = []
    for order, starts, s2 in actions:
        starts = starts + ["P"] * (2 - len(starts))
        starts = starts[:2]
        key = (order, tuple(starts))
        if key not in seen:
            seen.add(key)
            out.append((order, starts, s2))

    return out


def _pip_count_my(s: Dict[str, Any]) -> int:
    return sum((i + 1) * s["my_pts"][i] for i in range(24)) + 25 * s["my_bar"]


def _pip_count_opp(s: Dict[str, Any]) -> int:
    # Opponent moves in the opposite direction, from 0 toward 23/off.
    return sum((24 - i) * s["opp_pts"][i] for i in range(24)) + 25 * s["opp_bar"]


def _made_points_my(s: Dict[str, Any]) -> int:
    return sum(1 for x in s["my_pts"] if x >= 2)


def _made_points_opp(s: Dict[str, Any]) -> int:
    return sum(1 for x in s["opp_pts"] if x >= 2)


def _home_points_my(s: Dict[str, Any]) -> int:
    return sum(1 for i in range(6) if s["my_pts"][i] >= 2)


def _home_points_opp(s: Dict[str, Any]) -> int:
    return sum(1 for i in range(18, 24) if s["opp_pts"][i] >= 2)


def _blot_penalty_my(s: Dict[str, Any]) -> float:
    penalty = 0.0
    opp = s["opp_pts"]
    for i in range(24):
        if s["my_pts"][i] == 1:
            p = 1.0
            # Blots in opponent's attacking/home side are more dangerous.
            if i >= 18:
                p += 1.5
            elif i >= 12:
                p += 0.8

            # If opponent has direct shots within 6 points behind us.
            shots = 0
            for d in range(1, 7):
                j = i - d
                if 0 <= j < 24 and opp[j] > 0:
                    shots += opp[j]
            p += min(shots, 4) * 0.6

            penalty += p
    return penalty


def _blot_reward_opp(s: Dict[str, Any]) -> float:
    reward = 0.0
    my = s["my_pts"]
    for i in range(24):
        if s["opp_pts"][i] == 1:
            r = 1.0
            # Opponent blots in our home board are valuable targets/containment.
            if i <= 5:
                r += 1.5
            elif i <= 11:
                r += 0.7

            shots = 0
            for d in range(1, 7):
                j = i + d
                if 0 <= j < 24 and my[j] > 0:
                    shots += my[j]
            r += min(shots, 4) * 0.35
            reward += r
    return reward


def _stack_penalty(points: List[int]) -> float:
    # Too many checkers stacked on one point is inflexible.
    pen = 0.0
    for c in points:
        if c > 5:
            pen += (c - 5) * 0.7
        if c > 3:
            pen += (c - 3) * 0.15
    return pen


def _evaluate(s: Dict[str, Any]) -> float:
    my_pip = _pip_count_my(s)
    opp_pip = _pip_count_opp(s)

    score = 0.0

    # Race and borne-off material.
    score += (s["my_off"] - s["opp_off"]) * 120.0
    score += (opp_pip - my_pip) * 1.15

    # Bar is tactically huge.
    score += s["opp_bar"] * 35.0
    score -= s["my_bar"] * 45.0

    # Made points and home-board strength.
    score += _made_points_my(s) * 4.0
    score -= _made_points_opp(s) * 3.0
    score += _home_points_my(s) * 5.0
    score -= _home_points_opp(s) * 4.0

    # Blots.
    score -= _blot_penalty_my(s) * 4.2
    score += _blot_reward_opp(s) * 2.0

    # Prefer advanced anchors / checkers not stranded too far back.
    # Since we move downward, low indices are advanced.
    for i, c in enumerate(s["my_pts"]):
        if c >= 2:
            if 18 <= i <= 23:
                score += 1.5  # opponent home anchor
            if 0 <= i <= 5:
                score += 2.0  # our home/off structure
        if c == 1 and i >= 18:
            score -= 2.0

    # Penalize inflexible stacks.
    score -= _stack_penalty(s["my_pts"])

    # Endgame: if all in home, strongly favor bearing off and low pips.
    if _all_in_home(s):
        score += 30.0
        score += s["my_off"] * 20.0
        score -= my_pip * 0.8

    return score
