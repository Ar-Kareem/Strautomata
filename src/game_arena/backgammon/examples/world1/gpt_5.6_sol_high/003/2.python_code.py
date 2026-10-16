
from typing import Dict, List, Tuple


def _copy_state(state: dict) -> dict:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def _state_key(state: dict) -> tuple:
    return (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        state["my_bar"],
        state["opp_bar"],
        state["my_off"],
        state["opp_off"],
    )


def _single_moves(state: dict, die: int) -> List[Tuple[str, dict]]:
    """Generate all legal single-checker moves for the player moving downward."""
    moves = []
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]

    if state["my_bar"] > 0:
        destination = 24 - die
        if 0 <= destination < 24 and opp_pts[destination] < 2:
            nxt = _copy_state(state)
            nxt["my_bar"] -= 1

            if nxt["opp_pts"][destination] == 1:
                nxt["opp_pts"][destination] = 0
                nxt["opp_bar"] += 1

            nxt["my_pts"][destination] += 1
            moves.append(("B", nxt))
        return moves

    can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))

    for source in range(24):
        if my_pts[source] == 0:
            continue

        destination = source - die

        if destination >= 0:
            if opp_pts[destination] >= 2:
                continue

            nxt = _copy_state(state)
            nxt["my_pts"][source] -= 1

            if nxt["opp_pts"][destination] == 1:
                nxt["opp_pts"][destination] = 0
                nxt["opp_bar"] += 1

            nxt["my_pts"][destination] += 1
            moves.append(("A" + str(source), nxt))
            continue

        if not can_bear_off:
            continue

        exact = destination == -1
        oversize = destination < -1 and all(
            my_pts[i] == 0 for i in range(source + 1, 24)
        )

        if exact or oversize:
            nxt = _copy_state(state)
            nxt["my_pts"][source] -= 1
            nxt["my_off"] += 1
            moves.append(("A" + str(source), nxt))

    return moves


def _generate_turn(state: dict, dice: List[int]) -> List[Tuple[str, dict]]:
    """Generate precisely the actions allowed by forced-dice rules."""
    if not dice:
        return [("H:P,P", _copy_state(state))]

    if len(dice) == 1:
        moves = _single_moves(state, int(dice[0]))
        if not moves:
            return [("H:P,P", _copy_state(state))]
        return [
            ("H:" + token + ",P", outcome)
            for token, outcome in moves
        ]

    d1, d2 = int(dice[0]), int(dice[1])
    high = max(d1, d2)
    low = min(d1, d2)

    if high == low:
        orders = [("H", high, low)]
    else:
        orders = [
            ("H", high, low),
            ("L", low, high),
        ]

    full_moves = []

    for order, first_die, second_die in orders:
        first_moves = _single_moves(state, first_die)
        for first_token, first_state in first_moves:
            second_moves = _single_moves(first_state, second_die)
            for second_token, second_state in second_moves:
                action = (
                    order + ":" + first_token + "," + second_token
                )
                full_moves.append((action, second_state))

    if full_moves:
        seen = set()
        unique = []
        for action, outcome in full_moves:
            if action not in seen:
                seen.add(action)
                unique.append((action, outcome))
        return unique

    high_moves = _single_moves(state, high)
    if high_moves:
        return [
            ("H:" + token + ",P", outcome)
            for token, outcome in high_moves
        ]

    if low != high:
        low_moves = _single_moves(state, low)
        if low_moves:
            return [
                ("L:" + token + ",P", outcome)
                for token, outcome in low_moves
            ]

    return [("H:P,P", _copy_state(state))]


_POINT_VALUES = (
    1.5, 3.0, 5.0, 7.0, 10.0, 9.0,
    5.0, 5.5, 4.5, 4.0, 3.0, 3.0,
    5.0, 3.0, 2.8, 2.8, 3.2, 4.0,
    7.0, 10.0, 8.0, 6.0, 4.0, 2.0,
)


def _home_made(points: List[int]) -> int:
    return sum(1 for i in range(6) if points[i] >= 2)


def _structure(points: List[int]) -> float:
    score = 0.0
    made = [points[i] >= 2 for i in range(24)]

    for i, count in enumerate(points):
        if count >= 2:
            score += _POINT_VALUES[i]

        if count > 3:
            score -= 1.15 * (count - 3)
        if count > 5:
            score -= 0.7 * (count - 5)

    run = 0
    for i in range(24):
        if made[i]:
            run += 1
        else:
            if run >= 3:
                score += 1.55 * (run - 2) * (run - 2)
            run = 0

    if run >= 3:
        score += 1.55 * (run - 2) * (run - 2)

    home_points = sum(1 for i in range(6) if made[i])
    score += 0.65 * home_points * home_points

    return score


def _blot_danger(
    own: List[int],
    enemy: List[int],
    enemy_bar: int,
) -> float:
    """
    Estimate direct next-roll exposure of own blots. Coordinates are
    canonical: own checkers move down and enemy checkers move up.
    """
    total = 0.0
    enemy_blockade = sum(
        1 for i in range(18, 24) if enemy[i] >= 2
    )

    for target in range(24):
        if own[target] != 1:
            continue

        direct_dice = set()

        if enemy_bar == 0:
            for die in range(1, 7):
                source = target - die
                if source >= 0 and enemy[source] > 0:
                    direct_dice.add(die)
        elif enemy_bar == 1:
            # Board shots are less immediate while the bar has priority.
            board_dice = set()
            for die in range(1, 7):
                source = target - die
                if source >= 0 and enemy[source] > 0:
                    board_dice.add(die)
            if board_dice:
                k = len(board_dice)
                probability = (36.0 - (6.0 - k) ** 2) / 36.0
                severity = (
                    5.0
                    + 0.48 * (23 - target)
                    + 1.2 * enemy_blockade
                )
                total += 0.23 * probability * severity

        # An enemy checker on the bar enters on canonical points 0..5.
        if enemy_bar > 0 and 0 <= target <= 5:
            direct_dice.add(target + 1)

        if direct_dice:
            k = len(direct_dice)
            probability = (36.0 - (6.0 - k) ** 2) / 36.0
            severity = (
                5.5
                + 0.52 * (23 - target)
                + 1.25 * enemy_blockade
            )
            total += probability * severity

    return total


def _is_race(state: dict) -> bool:
    if state["my_bar"] or state["opp_bar"]:
        return False

    my_positions = [
        i for i, count in enumerate(state["my_pts"]) if count
    ]
    opp_positions = [
        i for i, count in enumerate(state["opp_pts"]) if count
    ]

    if not my_positions or not opp_positions:
        return True

    return max(my_positions) < min(opp_positions)


def _race_cost(points: List[int], bar: int) -> float:
    pip_count = 25 * bar
    onboard = 0

    for i, count in enumerate(points):
        pip_count += (i + 1) * count
        onboard += count

    congestion = 0.0
    for i in range(6):
        if points[i] > 2:
            congestion += 1.1 * (points[i] - 2)

    return pip_count + 1.75 * onboard + congestion


def _evaluate(state: dict) -> float:
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = state["my_bar"]
    opp_bar = state["opp_bar"]
    my_off = state["my_off"]
    opp_off = state["opp_off"]

    my_remaining = sum(my_pts) + my_bar
    opp_remaining = sum(opp_pts) + opp_bar

    if my_remaining == 0 and my_off > 0:
        return 100000.0 + 100.0 * my_off - opp_off
    if opp_remaining == 0 and opp_off > 0:
        return -100000.0 - 100.0 * opp_off + my_off

    opp_canonical = list(reversed(opp_pts))
    my_reversed = list(reversed(my_pts))

    if _is_race(state):
        my_cost = _race_cost(my_pts, my_bar)
        opp_cost = _race_cost(opp_canonical, opp_bar)
        return (
            1.28 * (opp_cost - my_cost)
            + 2.2 * (my_off - opp_off)
        )

    my_pips = 25 * my_bar + sum(
        (i + 1) * count for i, count in enumerate(my_pts)
    )
    opp_pips = 25 * opp_bar + sum(
        (i + 1) * count
        for i, count in enumerate(opp_canonical)
    )

    score = 0.72 * (opp_pips - my_pips)
    score += 5.0 * (my_off - opp_off)

    my_structure = _structure(my_pts)
    opp_structure = _structure(opp_canonical)
    score += my_structure - opp_structure

    my_home = _home_made(my_pts)
    opp_home = _home_made(opp_canonical)

    score += 27.0 * (opp_bar - my_bar)
    score += 4.1 * (
        opp_bar * my_home - my_bar * opp_home
    )
    score += 3.0 * (
        opp_bar * opp_bar - my_bar * my_bar
    )

    my_danger = _blot_danger(my_pts, opp_pts, opp_bar)
    opp_danger = _blot_danger(
        opp_canonical, my_reversed, my_bar
    )
    score += opp_danger - my_danger

    return score


def _opponent_view(state: dict) -> dict:
    return {
        "my_pts": list(reversed(state["opp_pts"])),
        "opp_pts": list(reversed(state["my_pts"])),
        "my_bar": state["opp_bar"],
        "opp_bar": state["my_bar"],
        "my_off": state["opp_off"],
        "opp_off": state["my_off"],
    }


_ROLLS = [
    (a, b, 1 if a == b else 2)
    for a in range(1, 7)
    for b in range(a, 7)
]


def _expected_after_reply(state: dict) -> Tuple[float, float]:
    opponent_state = _opponent_view(state)

    weighted_value = 0.0
    worst_value = float("inf")

    for die1, die2, weight in _ROLLS:
        replies = _generate_turn(opponent_state, [die1, die2])

        best_opponent_score = -float("inf")
        seen_outcomes = set()

        for _, reply_state in replies:
            key = _state_key(reply_state)
            if key in seen_outcomes:
                continue
            seen_outcomes.add(key)

            value = _evaluate(reply_state)
            if value > best_opponent_score:
                best_opponent_score = value

        our_value = -best_opponent_score
        weighted_value += weight * our_value

        if our_value < worst_value:
            worst_value = our_value

    return weighted_value / 36.0, worst_value


def policy(state: Dict) -> str:
    dice = list(state.get("dice", []))
    root = _copy_state(state)
    moves = _generate_turn(root, dice)

    if len(moves) == 1:
        return moves[0][0]

    # Equivalent board outcomes need only one legal representative action.
    unique = {}
    for action, outcome in moves:
        key = _state_key(outcome)
        if key not in unique:
            unique[key] = (action, outcome)

    candidates = list(unique.values())

    # Immediately take any move that bears off the final checker.
    for action, outcome in candidates:
        if (
            sum(outcome["my_pts"]) == 0
            and outcome["my_bar"] == 0
            and outcome["my_off"] > 0
        ):
            return action

    ranked = [
        (_evaluate(outcome), action, outcome)
        for action, outcome in candidates
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)

    # This bound preserves tactical depth under the execution-time limit.
    if len(ranked) > 32:
        ranked = ranked[:32]

    best_action = ranked[0][1]
    best_score = -float("inf")

    for immediate, action, outcome in ranked:
        expected, worst = _expected_after_reply(outcome)

        # Mostly maximize expectation, with small amounts of positional
        # persistence and protection against catastrophic tactical rolls.
        score = (
            0.86 * expected
            + 0.14 * immediate
            + 0.035 * (worst - expected)
        )

        if score > best_score:
            best_score = score
            best_action = action

    return best_action
