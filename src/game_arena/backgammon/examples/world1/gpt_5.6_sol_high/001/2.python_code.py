
# Backgammon policy: legal move generation plus one-roll opponent lookahead.

WIN_SCORE = 100000000.0


def _copy_position(state):
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def _position_key(pos):
    return (
        tuple(pos["my_pts"]),
        tuple(pos["opp_pts"]),
        pos["my_bar"],
        pos["opp_bar"],
        pos["my_off"],
        pos["opp_off"],
    )


def _can_bear_off(pos):
    if pos["my_bar"] != 0:
        return False
    return not any(pos["my_pts"][6:])


def _move_options(pos, die):
    """Return legal (start_token, resulting_position) moves for one die."""
    if die < 1 or die > 6:
        return []

    my_pts = pos["my_pts"]
    opp_pts = pos["opp_pts"]
    result = []

    # Checkers on the bar have absolute priority.
    if pos["my_bar"] > 0:
        destination = 24 - die
        if opp_pts[destination] < 2:
            nxt = _copy_position(pos)
            nxt["my_bar"] -= 1

            if nxt["opp_pts"][destination] == 1:
                nxt["opp_pts"][destination] = 0
                nxt["opp_bar"] += 1

            nxt["my_pts"][destination] += 1
            result.append(("B", nxt))
        return result

    bearing = _can_bear_off(pos)

    for start in range(24):
        if my_pts[start] == 0:
            continue

        destination = start - die

        if destination >= 0:
            if opp_pts[destination] >= 2:
                continue

            nxt = _copy_position(pos)
            nxt["my_pts"][start] -= 1

            if nxt["opp_pts"][destination] == 1:
                nxt["opp_pts"][destination] = 0
                nxt["opp_bar"] += 1

            nxt["my_pts"][destination] += 1
            result.append(("A" + str(start), nxt))
            continue

        if not bearing:
            continue

        exact = die == start + 1
        oversized = (
            die > start + 1
            and not any(my_pts[j] for j in range(start + 1, 24))
        )

        if exact or oversized:
            nxt = _copy_position(pos)
            nxt["my_pts"][start] -= 1
            nxt["my_off"] += 1
            result.append(("A" + str(start), nxt))

    return result


def _deduplicate(candidates):
    seen = set()
    answer = []
    for action, pos in candidates:
        key = _position_key(pos)
        if key not in seen:
            seen.add(key)
            answer.append((action, pos))
    return answer


def _generate_turns(pos, dice):
    """
    Generate all turns that satisfy:
      * both dice must be used if possible;
      * otherwise the higher die must be used when possible.
    """
    dice = [int(d) for d in dice if 1 <= int(d) <= 6]

    if not dice:
        return [("H:P,P", _copy_position(pos))]

    if len(dice) == 1:
        options = _move_options(pos, dice[0])
        if not options:
            return [("H:P,P", _copy_position(pos))]
        return _deduplicate([
            ("H:" + token + ",P", nxt) for token, nxt in options
        ])

    high = max(dice[0], dice[1])
    low = min(dice[0], dice[1])

    full_turns = []

    # High die first.
    for first_token, after_first in _move_options(pos, high):
        for second_token, after_second in _move_options(after_first, low):
            action = "H:" + first_token + "," + second_token
            full_turns.append((action, after_second))

    # Low die first. For doubles this is the same ordering.
    if high != low:
        for first_token, after_first in _move_options(pos, low):
            for second_token, after_second in _move_options(after_first, high):
                action = "L:" + first_token + "," + second_token
                full_turns.append((action, after_second))

    if full_turns:
        return _deduplicate(full_turns)

    # If only one die can be played, the high die is compulsory whenever
    # it is playable from the original position.
    high_options = _move_options(pos, high)
    if high_options:
        return _deduplicate([
            ("H:" + token + ",P", nxt) for token, nxt in high_options
        ])

    if high != low:
        low_options = _move_options(pos, low)
        if low_options:
            return _deduplicate([
                ("L:" + token + ",P", nxt) for token, nxt in low_options
            ])

    return [("H:P,P", _copy_position(pos))]


def _flip_position(pos):
    """Convert a position to the opponent's descending-point perspective."""
    return {
        "my_pts": list(reversed(pos["opp_pts"])),
        "opp_pts": list(reversed(pos["my_pts"])),
        "my_bar": pos["opp_bar"],
        "opp_bar": pos["my_bar"],
        "my_off": pos["opp_off"],
        "opp_off": pos["my_off"],
    }


def _pip_count(points, bar):
    return 25 * bar + sum((i + 1) * n for i, n in enumerate(points))


_POINT_VALUES = (
    3.8, 5.3, 6.1, 6.0, 5.6, 6.5,
    5.4, 4.1, 3.5, 3.1, 3.0, 3.5,
    4.8, 2.8, 2.6, 2.5, 2.6, 3.0,
    4.5, 5.0, 4.1, 3.2, 2.1, 1.2,
)


def _side_quality(points):
    score = 0.0

    for i, count in enumerate(points):
        if count >= 2:
            score += _POINT_VALUES[i]

        # Builders are mildly useful; isolated blots are mildly undesirable.
        if count == 1:
            score -= 0.55
        elif count == 3:
            score += 0.35
        elif count > 3:
            score -= 0.65 * (count - 3)

    # Reward consecutive made points, especially primes.
    run = 0
    for i in range(24):
        if points[i] >= 2:
            run += 1
        else:
            if run >= 2:
                score += 0.75 * (run - 1) * (run - 1)
                if run >= 4:
                    score += 2.0 * (run - 3)
            run = 0

    if run >= 2:
        score += 0.75 * (run - 1) * (run - 1)
        if run >= 4:
            score += 2.0 * (run - 3)

    # Strong home-board primes are particularly valuable.
    home_run = 0
    for i in range(6):
        if points[i] >= 2:
            home_run += 1
        else:
            if home_run >= 3:
                score += 1.25 * (home_run - 2) ** 2
            home_run = 0
    if home_run >= 3:
        score += 1.25 * (home_run - 2) ** 2

    return score


def _race_wastage(points):
    """Approximate future dice wastage caused by deep stacks."""
    waste = 0.0
    for i in range(6):
        extra = max(0, points[i] - 2)
        waste += extra * max(0.0, 2.5 - 0.35 * i)

    # A very large stack on the ace or two point is especially inflexible.
    waste += 0.8 * max(0, points[0] - 3)
    waste += 0.4 * max(0, points[1] - 3)
    return waste


def _vulnerability(victim, attacker, attacker_bar):
    """
    Approximate immediate direct-shot danger to the victim's blots.
    Coordinates are from the victim's descending perspective, so the
    attacker moves upward.
    """
    danger = 0.0

    for point, count in enumerate(victim):
        if count != 1:
            continue

        hitting_dice = set()

        if attacker_bar > 0:
            if point < 6:
                hitting_dice.add(point + 1)
        else:
            lower = max(0, point - 6)
            for source in range(lower, point):
                if attacker[source] > 0:
                    distance = point - source
                    if 1 <= distance <= 6:
                        hitting_dice.add(distance)

        if not hitting_dice:
            continue

        misses_per_die = 6 - len(hitting_dice)
        hit_probability = 1.0 - (misses_per_die / 6.0) ** 2
        setback = 24 - point
        danger += hit_probability * (2.5 + 0.32 * setback)

    return danger


def _has_contact(my_pts, opp_pts, my_bar, opp_bar):
    if my_bar or opp_bar:
        return True

    my_occupied = [i for i, n in enumerate(my_pts) if n]
    opp_occupied = [i for i, n in enumerate(opp_pts) if n]

    if not my_occupied or not opp_occupied:
        return False

    # Once every friendly checker is below every enemy checker, the sides
    # can no longer hit one another.
    return max(my_occupied) >= min(opp_occupied)


def _evaluate(pos):
    if pos["my_off"] >= 15:
        return WIN_SCORE
    if pos["opp_off"] >= 15:
        return -WIN_SCORE

    my_pts = pos["my_pts"]
    opp_actual = pos["opp_pts"]
    opp_pts = list(reversed(opp_actual))

    my_pips = _pip_count(my_pts, pos["my_bar"])
    opp_pips = _pip_count(opp_pts, pos["opp_bar"])

    score = 1.18 * (opp_pips - my_pips)
    score += 9.0 * (pos["my_off"] - pos["opp_off"])
    score += 9.0 * (pos["opp_bar"] - pos["my_bar"])

    contact = _has_contact(
        my_pts, opp_actual, pos["my_bar"], pos["opp_bar"]
    )

    my_quality = _side_quality(my_pts)
    opp_quality = _side_quality(opp_pts)

    if contact:
        score += my_quality - opp_quality

        my_danger = _vulnerability(
            my_pts, opp_actual, pos["opp_bar"]
        )
        opp_danger = _vulnerability(
            opp_pts, list(reversed(my_pts)), pos["my_bar"]
        )
        score += 0.9 * (opp_danger - my_danger)
    else:
        # In a pure race, structure matters mainly through dice efficiency.
        score += 0.16 * (my_quality - opp_quality)
        score += 1.3 * (
            _race_wastage(opp_pts) - _race_wastage(my_pts)
        )

    my_home_points = sum(1 for i in range(6) if my_pts[i] >= 2)
    opp_home_points = sum(1 for i in range(6) if opp_pts[i] >= 2)

    score += 2.3 * (
        my_home_points * pos["opp_bar"]
        - opp_home_points * pos["my_bar"]
    )

    return score


_ROLLS = [
    ((a, b), 1 if a == b else 2)
    for a in range(1, 7)
    for b in range(a, 7)
]


def _reply_value(pos):
    """Expected value after the opponent chooses its best move for each roll."""
    if pos["my_off"] >= 15:
        return WIN_SCORE
    if pos["opp_off"] >= 15:
        return -WIN_SCORE

    opponent_position = _flip_position(pos)
    total = 0.0

    for dice, weight in _ROLLS:
        replies = _generate_turns(opponent_position, dice)
        best_for_opponent = -WIN_SCORE * 2.0

        for _, reply in replies:
            value = _evaluate(reply)
            if value > best_for_opponent:
                best_for_opponent = value

        total += weight * (-best_for_opponent)

    return total / 36.0


def policy(state: dict) -> str:
    position = _copy_position(state)
    candidates = _generate_turns(position, state.get("dice", []))

    if len(candidates) == 1:
        return candidates[0][0]

    # Static ordering limits worst-case work while retaining all normal
    # backgammon positions' serious alternatives.
    ranked = [
        (_evaluate(result), action, result)
        for action, result in candidates
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)

    if len(ranked) > 48:
        ranked = ranked[:48]

    best_action = ranked[0][1]
    best_score = -WIN_SCORE * 3.0

    for static_value, action, result in ranked:
        if result["my_off"] >= 15:
            combined = WIN_SCORE
        else:
            combined = _reply_value(result) + 0.08 * static_value

        if combined > best_score:
            best_score = combined
            best_action = action

    return best_action
