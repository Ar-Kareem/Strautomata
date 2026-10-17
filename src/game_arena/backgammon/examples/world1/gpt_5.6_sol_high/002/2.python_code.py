
from functools import lru_cache


# Position format:
# (
#   tuple(my_points), tuple(opponent_points),
#   my_bar, opponent_bar, my_off, opponent_off
# )


def _make_position(state):
    return (
        tuple(int(x) for x in state["my_pts"]),
        tuple(int(x) for x in state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )


def _move_options(pos, player, die):
    """Return all (source, resulting_position) pairs for one die.

    player == 0 moves from 23 toward 0.
    player == 1 moves from 0 toward 23.
    source == -1 denotes the bar.
    """
    if die < 1 or die > 6:
        return ()

    my_t, opp_t, my_bar, opp_bar, my_off, opp_off = pos
    results = []

    if player == 0:
        own = my_t
        enemy = opp_t
        own_bar = my_bar

        if own_bar:
            destination = 24 - die
            if enemy[destination] >= 2:
                return ()

            my = list(my_t)
            opp = list(opp_t)
            new_my_bar = my_bar - 1
            new_opp_bar = opp_bar

            if opp[destination] == 1:
                opp[destination] = 0
                new_opp_bar += 1

            my[destination] += 1
            results.append((
                -1,
                (
                    tuple(my), tuple(opp),
                    new_my_bar, new_opp_bar,
                    my_off, opp_off,
                ),
            ))
            return tuple(results)

        all_in_home = not any(own[6:])

        for source, count in enumerate(own):
            if count == 0:
                continue

            destination = source - die

            if destination >= 0:
                if enemy[destination] >= 2:
                    continue

                my = list(my_t)
                opp = list(opp_t)
                new_opp_bar = opp_bar

                my[source] -= 1
                if opp[destination] == 1:
                    opp[destination] = 0
                    new_opp_bar += 1
                my[destination] += 1

                results.append((
                    source,
                    (
                        tuple(my), tuple(opp),
                        my_bar, new_opp_bar,
                        my_off, opp_off,
                    ),
                ))
            else:
                if not all_in_home:
                    continue

                distance = source + 1
                if die < distance:
                    continue

                # Oversized dice may bear off only the farthest checker.
                if die > distance and any(own[source + 1:6]):
                    continue

                my = list(my_t)
                my[source] -= 1
                results.append((
                    source,
                    (
                        tuple(my), opp_t,
                        my_bar, opp_bar,
                        my_off + 1, opp_off,
                    ),
                ))

    else:
        own = opp_t
        enemy = my_t
        own_bar = opp_bar

        if own_bar:
            destination = die - 1
            if enemy[destination] >= 2:
                return ()

            my = list(my_t)
            opp = list(opp_t)
            new_my_bar = my_bar
            new_opp_bar = opp_bar - 1

            if my[destination] == 1:
                my[destination] = 0
                new_my_bar += 1

            opp[destination] += 1
            results.append((
                -1,
                (
                    tuple(my), tuple(opp),
                    new_my_bar, new_opp_bar,
                    my_off, opp_off,
                ),
            ))
            return tuple(results)

        all_in_home = not any(own[:18])

        for source, count in enumerate(own):
            if count == 0:
                continue

            destination = source + die

            if destination <= 23:
                if enemy[destination] >= 2:
                    continue

                my = list(my_t)
                opp = list(opp_t)
                new_my_bar = my_bar

                opp[source] -= 1
                if my[destination] == 1:
                    my[destination] = 0
                    new_my_bar += 1
                opp[destination] += 1

                results.append((
                    source,
                    (
                        tuple(my), tuple(opp),
                        new_my_bar, opp_bar,
                        my_off, opp_off,
                    ),
                ))
            else:
                if not all_in_home:
                    continue

                distance = 24 - source
                if die < distance:
                    continue

                if die > distance and any(own[18:source]):
                    continue

                opp = list(opp_t)
                opp[source] -= 1
                results.append((
                    source,
                    (
                        my_t, tuple(opp),
                        my_bar, opp_bar,
                        my_off, opp_off + 1,
                    ),
                ))

    return tuple(results)


def _legal_records(pos, player, dice):
    """Return (order, sources, resulting_position) for all legal turns."""
    dice = tuple(int(d) for d in dice if 1 <= int(d) <= 6)

    if not dice:
        return (("H", (), pos),)

    if len(dice) == 1:
        moves = _move_options(pos, player, dice[0])
        if not moves:
            return (("H", (), pos),)
        return tuple(("H", (source,), nxt) for source, nxt in moves)

    high = max(dice[0], dice[1])
    low = min(dice[0], dice[1])

    if high == low:
        complete = []
        for source1, pos1 in _move_options(pos, player, high):
            for source2, pos2 in _move_options(pos1, player, high):
                complete.append(("H", (source1, source2), pos2))

        if complete:
            return tuple(complete)

        singles = _move_options(pos, player, high)
        if singles:
            return tuple(("H", (source,), nxt) for source, nxt in singles)

        return (("H", (), pos),)

    complete = []

    for source1, pos1 in _move_options(pos, player, high):
        for source2, pos2 in _move_options(pos1, player, low):
            complete.append(("H", (source1, source2), pos2))

    for source1, pos1 in _move_options(pos, player, low):
        for source2, pos2 in _move_options(pos1, player, high):
            complete.append(("L", (source1, source2), pos2))

    # Both dice must be used whenever any ordering permits it.
    if complete:
        return tuple(complete)

    # If only one die can be used, the higher die is compulsory when possible.
    high_moves = _move_options(pos, player, high)
    if high_moves:
        return tuple(("H", (source,), nxt) for source, nxt in high_moves)

    low_moves = _move_options(pos, player, low)
    if low_moves:
        return tuple(("L", (source,), nxt) for source, nxt in low_moves)

    return (("H", (), pos),)


@lru_cache(maxsize=50000)
def _turn_positions(pos, player, die1, die2):
    records = _legal_records(pos, player, (die1, die2))
    unique = {}
    for _, _, result in records:
        unique[result] = None
    return tuple(unique.keys())


def _longest_prime(points):
    best = 0
    current = 0
    for count in points:
        if count >= 2:
            current += 1
            if current > best:
                best = current
        else:
            current = 0
    return best


def _side_structure(points, enemy_bar):
    home_weights = (0.4, 0.8, 1.4, 2.1, 3.2, 2.7)
    anchor_weights = (2.4, 3.0, 2.8, 2.1, 1.4, 0.8)

    value = 0.0
    home_made = 0
    home_quality = 0.0

    for index, count in enumerate(points):
        if count >= 2:
            if index <= 5:
                point_value = home_weights[index]
                home_made += 1
                home_quality += point_value
            elif index <= 11:
                point_value = 1.65
            elif index <= 17:
                point_value = 1.25
            else:
                point_value = anchor_weights[index - 18]

            value += point_value

        # Large stacks reduce flexibility.
        if count > 3:
            value -= 0.45 * (count - 3)
            if index <= 1:
                value -= 0.30 * (count - 3)

        # Unprotected builders retain some value but are less safe.
        if count == 1:
            value -= 0.18

    prime = _longest_prime(points)
    if prime >= 3:
        value += 1.35 * prime * prime

    if enemy_bar:
        value += enemy_bar * (
            0.80 * home_quality + 0.90 * home_made * home_made
        )

    return value


def _exposure(victim, attacker, attacker_bar):
    """Approximate direct one-die hitting chances against victim blots.

    Coordinates are relative to a victim moving downward. The attacker
    therefore moves upward in these coordinates.
    """
    danger = 0.0

    for point, count in enumerate(victim):
        if count != 1:
            continue

        possible_dice = 0.0
        for die in range(1, 7):
            source = point - die
            can_hit = source >= 0 and attacker[source] > 0

            if attacker_bar and point == die - 1:
                can_hit = True

            if can_hit:
                possible_dice += 1.0

        # Blots in the home board are particularly costly when hit.
        if point <= 5:
            possible_dice *= 1.10

        danger += possible_dice

    return danger


def _race_wastage(points):
    waste = 0.0
    for point, count in enumerate(points[:6]):
        if count > 2:
            waste += (count - 2) * (0.18 + 0.06 * (5 - point))
    return waste


@lru_cache(maxsize=120000)
def _evaluate(pos):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos

    if my_off >= 15:
        return 1000000.0 + 1000.0 * (15 - opp_off)
    if opp_off >= 15:
        return -1000000.0 - 1000.0 * (15 - my_off)

    my_pips = my_bar * 25 + sum((i + 1) * n for i, n in enumerate(my))
    opp_pips = opp_bar * 25 + sum((24 - i) * n for i, n in enumerate(opp))
    pip_advantage = opp_pips - my_pips

    my_points = [i for i, n in enumerate(my) if n]
    opp_points = [i for i, n in enumerate(opp) if n]

    if my_bar or opp_bar:
        contact = True
    elif my_points and opp_points:
        contact = max(my_points) > min(opp_points)
    else:
        contact = False

    off_advantage = my_off - opp_off

    if not contact:
        my_waste = _race_wastage(my)
        opp_relative = tuple(reversed(opp))
        opp_waste = _race_wastage(opp_relative)

        return (
            1.18 * pip_advantage
            + 2.0 * off_advantage
            + 1.4 * (opp_waste - my_waste)
        )

    opp_relative = tuple(reversed(opp))
    my_relative_for_opp = tuple(reversed(my))

    my_structure = _side_structure(my, opp_bar)
    opp_structure = _side_structure(opp_relative, my_bar)

    my_danger = _exposure(my, opp, opp_bar)
    opp_danger = _exposure(
        opp_relative,
        my_relative_for_opp,
        my_bar,
    )

    return (
        0.86 * pip_advantage
        + 2.2 * off_advantage
        + 4.5 * (opp_bar - my_bar)
        + (my_structure - opp_structure)
        + 2.05 * (opp_danger - my_danger)
    )


def _format_action(order, sources):
    tokens = []
    for source in sources[:2]:
        if source == -1:
            tokens.append("B")
        else:
            tokens.append("A" + str(source))

    while len(tokens) < 2:
        tokens.append("P")

    return order + ":" + tokens[0] + "," + tokens[1]


def _opponent_reply_value(pos):
    total = 0.0

    for low in range(1, 7):
        for high in range(low, 7):
            probability = 1 if low == high else 2
            replies = _turn_positions(pos, 1, low, high)

            # The opponent selects the reply least favorable to us.
            worst_reply = min(_evaluate(reply) for reply in replies)
            total += probability * worst_reply

    return total / 36.0


def policy(state: dict) -> str:
    pos = _make_position(state)
    dice = tuple(int(d) for d in state.get("dice", ()) if 1 <= int(d) <= 6)

    records = _legal_records(pos, 0, dice)

    # Different legal encodings can transpose to the same board. Keep one
    # legal action for each distinct result.
    candidates_by_position = {}
    for order, sources, result in records:
        if result not in candidates_by_position:
            candidates_by_position[result] = _format_action(order, sources)

    candidates = [
        (result, action)
        for result, action in candidates_by_position.items()
    ]

    if not candidates:
        return "H:P,P"

    if len(candidates) == 1:
        return candidates[0][1]

    # First use the static evaluator to reduce unusually large move sets.
    candidates.sort(key=lambda item: _evaluate(item[0]), reverse=True)
    search_candidates = candidates[:28]

    best_action = search_candidates[0][1]
    best_value = float("-inf")
    best_static = float("-inf")

    for result, action in search_candidates:
        static_value = _evaluate(result)

        if result[4] >= 15:
            reply_value = static_value
        else:
            reply_value = _opponent_reply_value(result)

        if (
            reply_value > best_value
            or (
                reply_value == best_value
                and static_value > best_static
            )
        ):
            best_value = reply_value
            best_static = static_value
            best_action = action

    return best_action
