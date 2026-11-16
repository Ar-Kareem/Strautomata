
from typing import Dict, List, Tuple, Optional


State = Dict[str, object]
ActionResult = Tuple[str, State, Tuple[int, ...]]


def _clone_state(state: State) -> State:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
        "dice": list(state.get("dice", [])),
    }


def _state_key(state: State) -> Tuple:
    return (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )


def _all_home(state: State) -> bool:
    if int(state["my_bar"]) != 0:
        return False
    pts = state["my_pts"]
    return not any(pts[i] for i in range(6, 24))


def _legal_sources(state: State, die: int) -> List[Optional[int]]:
    """
    A source of None denotes the bar. Integer sources denote board points.
    """
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]

    if int(state["my_bar"]) > 0:
        destination = 24 - die
        if 0 <= destination < 24 and opp_pts[destination] < 2:
            return [None]
        return []

    can_bear_off = _all_home(state)
    sources: List[Optional[int]] = []

    for source in range(24):
        if my_pts[source] <= 0:
            continue

        destination = source - die

        if destination >= 0:
            if opp_pts[destination] < 2:
                sources.append(source)
            continue

        if not can_bear_off:
            continue

        # Exact bear-off or an oversize die from the highest occupied point.
        if die == source + 1:
            sources.append(source)
        elif die > source + 1:
            if not any(my_pts[j] for j in range(source + 1, 24)):
                sources.append(source)

    return sources


def _apply_move(state: State, source: Optional[int], die: int) -> State:
    result = _clone_state(state)
    my_pts = result["my_pts"]
    opp_pts = result["opp_pts"]

    if source is None:
        result["my_bar"] = int(result["my_bar"]) - 1
        destination = 24 - die
    else:
        my_pts[source] -= 1
        destination = source - die

    if destination < 0:
        result["my_off"] = int(result["my_off"]) + 1
        return result

    if opp_pts[destination] == 1:
        opp_pts[destination] = 0
        result["opp_bar"] = int(result["opp_bar"]) + 1

    my_pts[destination] += 1
    return result


def _source_token(source: Optional[int]) -> str:
    return "B" if source is None else "A" + str(source)


def _generate_actions(state: State, dice: List[int]) -> List[ActionResult]:
    dice = [int(d) for d in dice if 1 <= int(d) <= 6]

    if not dice:
        return [("H:P,P", _clone_state(state), tuple())]

    if len(dice) == 1:
        die = dice[0]
        sources = _legal_sources(state, die)
        if not sources:
            return [("H:P,P", _clone_state(state), tuple())]

        results: List[ActionResult] = []
        for source in sources:
            after = _apply_move(state, source, die)
            action = "H:" + _source_token(source) + ",P"
            results.append((action, after, (die,)))
        return results

    d1, d2 = dice[0], dice[1]
    high = max(d1, d2)
    low = min(d1, d2)

    if high == low:
        orders = [("H", high, low)]
    else:
        orders = [("H", high, low), ("L", low, high)]

    generated: List[ActionResult] = []

    for order_name, first_die, second_die in orders:
        first_sources = _legal_sources(state, first_die)

        if first_sources:
            first_branches = [
                (_apply_move(state, source, first_die),
                 _source_token(source),
                 (first_die,))
                for source in first_sources
            ]
        else:
            first_branches = [(_clone_state(state), "P", tuple())]

        for after_first, first_token, used_first in first_branches:
            second_sources = _legal_sources(after_first, second_die)

            if second_sources:
                for source in second_sources:
                    after_second = _apply_move(after_first, source, second_die)
                    action = (
                        order_name + ":" + first_token + ","
                        + _source_token(source)
                    )
                    generated.append(
                        (action, after_second, used_first + (second_die,))
                    )
            else:
                action = order_name + ":" + first_token + ",P"
                generated.append((action, after_first, used_first))

    if not generated:
        return [("H:P,P", _clone_state(state), tuple())]

    # Backgammon requires the maximum possible number of dice to be used.
    maximum_used = max(len(entry[2]) for entry in generated)
    generated = [
        entry for entry in generated if len(entry[2]) == maximum_used
    ]

    # If only one die can be used, the higher die is mandatory when possible.
    if high != low and maximum_used == 1:
        high_moves = [
            entry for entry in generated if high in entry[2]
        ]
        if high_moves:
            generated = high_moves

    # Remove identical action encodings.
    unique: Dict[str, ActionResult] = {}
    for entry in generated:
        if entry[0] not in unique:
            unique[entry[0]] = entry

    return list(unique.values())


def _pip_count(pts: List[int], bar: int) -> int:
    return 25 * bar + sum((i + 1) * pts[i] for i in range(24))


def _bearoff_wastage(pts: List[int], bar: int) -> float:
    if bar or any(pts[i] for i in range(6, 24)):
        return 0.0

    waste = 0.0
    for i in range(6):
        excess = max(0, pts[i] - 2)
        waste += excess * (6 - i) * 0.28

    occupied = [i for i in range(6) if pts[i]]
    if occupied:
        highest = max(occupied)
        holes = sum(1 for i in range(highest + 1) if pts[i] == 0)
        waste += holes * 0.22

    return waste


def _structure_value(pts: List[int], enemy_bar: int) -> float:
    value = 0.0
    made = [pts[i] >= 2 for i in range(24)]

    strategic = {
        4: 1.15,
        5: 2.35,
        6: 2.05,
        7: 0.75,
        16: 0.65,
        17: 1.45,
        18: 1.05,
        19: 0.50,
    }

    home_points = 0
    for i, count in enumerate(pts):
        if count >= 2:
            value += 1.05
            value += strategic.get(i, 0.0)
            if i < 6:
                value += 0.50
                home_points += 1

        if count > 3:
            # Large stacks are generally inflexible, except that the
            # penalty is mild during the bear-off.
            value -= (count - 3) * (0.30 if i < 6 else 0.58)

    # Reward consecutive made points (primes) super-linearly.
    run = 0
    for i in range(24):
        if made[i]:
            run += 1
        else:
            if run >= 2:
                value += 0.72 * (run - 1) * (run - 1)
            run = 0
    if run >= 2:
        value += 0.72 * (run - 1) * (run - 1)

    value += 0.24 * home_points * home_points

    if enemy_bar:
        value += enemy_bar * (
            0.85 * home_points + 0.20 * home_points * home_points
        )

    return value


def _blot_exposure(
    side_pts: List[int],
    enemy_oriented_pts: List[int],
    enemy_bar: int,
) -> float:
    """
    Estimates direct one-die exposure. side_pts and enemy_oriented_pts are
    each expressed in that side's own descending orientation.
    """
    exposure = 0.0

    for point, count in enumerate(side_pts):
        if count != 1:
            continue

        target_for_enemy = 23 - point
        hitting_dice = set()

        if enemy_bar:
            # A checker entering from the bar can hit only in its entry board.
            if 18 <= target_for_enemy <= 23:
                die = 24 - target_for_enemy
                if 1 <= die <= 6:
                    hitting_dice.add(die)
        else:
            for die in range(1, 7):
                source = target_for_enemy + die
                if source < 24 and enemy_oriented_pts[source] > 0:
                    hitting_dice.add(die)

        k = len(hitting_dice)
        if not k:
            continue

        probability = 1.0 - ((6.0 - k) / 6.0) ** 2
        distance_lost_if_hit = 24 - point
        exposure += probability * (
            2.35 + 0.24 * distance_lost_if_hit
        )

    return exposure


def _is_pure_race(
    my_pts: List[int],
    opp_pts: List[int],
    my_bar: int,
    opp_bar: int,
) -> bool:
    if my_bar or opp_bar:
        return False

    my_positions = [i for i, n in enumerate(my_pts) if n]
    opp_positions = [i for i, n in enumerate(opp_pts) if n]

    if not my_positions or not opp_positions:
        return True

    # My checkers move downward and opposing checkers move upward.
    return max(my_positions) < min(opp_positions)


def _evaluate(state: State) -> float:
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = int(state["my_bar"])
    opp_bar = int(state["opp_bar"])
    my_off = int(state["my_off"])
    opp_off = int(state["opp_off"])

    if my_off >= 15:
        return 1_000_000.0 + 100.0 * (15 - opp_off)
    if opp_off >= 15:
        return -1_000_000.0 - 100.0 * (15 - my_off)

    opp_oriented = list(reversed(opp_pts))

    my_pips = _pip_count(my_pts, my_bar)
    opp_pips = _pip_count(opp_oriented, opp_bar)

    score = float(opp_pips - my_pips)
    score += 3.4 * (my_off - opp_off)
    score += 5.5 * (opp_bar - my_bar)

    if _is_pure_race(my_pts, opp_pts, my_bar, opp_bar):
        my_waste = _bearoff_wastage(my_pts, my_bar)
        opp_waste = _bearoff_wastage(opp_oriented, opp_bar)
        score += opp_waste - my_waste
        return score

    my_structure = _structure_value(my_pts, opp_bar)
    opp_structure = _structure_value(opp_oriented, my_bar)
    score += my_structure - opp_structure

    my_exposure = _blot_exposure(my_pts, opp_oriented, opp_bar)
    opp_exposure = _blot_exposure(opp_oriented, my_pts, my_bar)
    score += opp_exposure - my_exposure

    return score


def _opponent_view(state: State) -> State:
    return {
        "my_pts": list(reversed(state["opp_pts"])),
        "opp_pts": list(reversed(state["my_pts"])),
        "my_bar": int(state["opp_bar"]),
        "opp_bar": int(state["my_bar"]),
        "my_off": int(state["opp_off"]),
        "opp_off": int(state["my_off"]),
        "dice": [],
    }


def _from_opponent_view(state: State) -> State:
    return {
        "my_pts": list(reversed(state["opp_pts"])),
        "opp_pts": list(reversed(state["my_pts"])),
        "my_bar": int(state["opp_bar"]),
        "opp_bar": int(state["my_bar"]),
        "my_off": int(state["opp_off"]),
        "opp_off": int(state["my_off"]),
        "dice": [],
    }


def _expected_after_opponent(state: State) -> float:
    immediate = _evaluate(state)
    if abs(immediate) >= 900_000.0:
        return immediate

    opponent_state = _opponent_view(state)
    weighted_total = 0.0

    for low in range(1, 7):
        for high in range(low, 7):
            weight = 1 if low == high else 2
            replies = _generate_actions(opponent_state, [low, high])

            # The opponent chooses the reply minimizing our evaluation.
            best_for_opponent = float("inf")
            seen_positions = set()

            for _, reply_state, _ in replies:
                key = _state_key(reply_state)
                if key in seen_positions:
                    continue
                seen_positions.add(key)

                original_view = _from_opponent_view(reply_state)
                value = _evaluate(original_view)
                if value < best_for_opponent:
                    best_for_opponent = value

            if best_for_opponent == float("inf"):
                best_for_opponent = immediate

            weighted_total += weight * best_for_opponent

    return weighted_total / 36.0


def policy(state: dict) -> str:
    current = _clone_state(state)
    dice = list(current.get("dice", []))
    actions = _generate_actions(current, dice)

    if not actions:
        return "H:P,P"

    # Equivalent final positions need only one legal encoding.
    unique_positions: Dict[Tuple, Tuple[str, State]] = {}
    for action, result, _ in actions:
        key = _state_key(result)
        if key not in unique_positions:
            unique_positions[key] = (action, result)

    candidates = []
    for action, result in unique_positions.values():
        static_value = _evaluate(result)
        candidates.append((static_value, action, result))

    # Static pruning controls the worst-case branching factor for doubles.
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    search_candidates = candidates[:32]

    best_action = search_candidates[0][1]
    best_value = float("-inf")
    best_static = float("-inf")

    for static_value, action, result in search_candidates:
        lookahead_value = _expected_after_opponent(result)

        # A tiny static component provides stable strategic tie-breaking.
        combined_value = lookahead_value + 0.015 * static_value

        if (
            combined_value > best_value
            or (
                combined_value == best_value
                and static_value > best_static
            )
        ):
            best_value = combined_value
            best_static = static_value
            best_action = action

    return best_action
