
from typing import Dict, List, Tuple, Union

Source = Union[int, str]
Position = Dict[str, object]
Candidate = Tuple[str, Position]

_WIN_SCORE = 100000.0


def _copy_position(state: dict) -> Position:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def _all_in_home(pos: Position) -> bool:
    if pos["my_bar"]:
        return False
    pts = pos["my_pts"]
    return not any(pts[6:])


def _legal_sources(pos: Position, die: int) -> List[Source]:
    my_pts = pos["my_pts"]
    opp_pts = pos["opp_pts"]

    if pos["my_bar"] > 0:
        destination = 24 - die
        if 0 <= destination < 24 and opp_pts[destination] < 2:
            return ["B"]
        return []

    can_bear_off = _all_in_home(pos)
    result: List[Source] = []

    for source in range(24):
        if my_pts[source] <= 0:
            continue

        destination = source - die
        if destination >= 0:
            if opp_pts[destination] < 2:
                result.append(source)
            continue

        if not can_bear_off:
            continue

        # Exact bearing off is always legal. An oversized die may bear off
        # the checker farthest from the player's home edge.
        if die == source + 1:
            result.append(source)
        elif die > source + 1 and not any(my_pts[source + 1:]):
            result.append(source)

    return result


def _apply_move(pos: Position, source: Source, die: int) -> Position:
    nxt: Position = {
        "my_pts": list(pos["my_pts"]),
        "opp_pts": list(pos["opp_pts"]),
        "my_bar": pos["my_bar"],
        "opp_bar": pos["opp_bar"],
        "my_off": pos["my_off"],
        "opp_off": pos["opp_off"],
    }

    if source == "B":
        nxt["my_bar"] -= 1
        destination = 24 - die
    else:
        source_index = int(source)
        nxt["my_pts"][source_index] -= 1
        destination = source_index - die

    if destination < 0:
        nxt["my_off"] += 1
        return nxt

    if nxt["opp_pts"][destination] == 1:
        nxt["opp_pts"][destination] = 0
        nxt["opp_bar"] += 1

    nxt["my_pts"][destination] += 1
    return nxt


def _source_token(source: Source) -> str:
    if source == "B":
        return "B"
    return "A" + str(int(source))


def _format_sequence(sequence: List[Tuple[int, Source]], high_die: int) -> str:
    if not sequence:
        return "H:P,P"

    first_die, first_source = sequence[0]
    order = "H" if first_die == high_die else "L"

    first_token = _source_token(first_source)
    if len(sequence) == 1:
        return order + ":" + first_token + ",P"

    second_token = _source_token(sequence[1][1])
    return order + ":" + first_token + "," + second_token


def _generate_candidates(pos: Position, dice: List[int]) -> List[Candidate]:
    dice = [int(d) for d in dice if 1 <= int(d) <= 6]

    if not dice:
        return [("H:P,P", pos)]

    if len(dice) == 1:
        die = dice[0]
        sources = _legal_sources(pos, die)
        if not sources:
            return [("H:P,P", pos)]

        candidates: List[Candidate] = []
        for source in sources:
            action = "H:" + _source_token(source) + ",P"
            candidates.append((action, _apply_move(pos, source, die)))
        return candidates

    die_a, die_b = dice[0], dice[1]
    high_die = max(die_a, die_b)
    low_die = min(die_a, die_b)

    if high_die == low_die:
        orders = [(high_die, low_die)]
    else:
        orders = [(high_die, low_die), (low_die, high_die)]

    full_moves: List[Candidate] = []
    seen_actions = set()

    for first_die, second_die in orders:
        for first_source in _legal_sources(pos, first_die):
            after_first = _apply_move(pos, first_source, first_die)
            for second_source in _legal_sources(after_first, second_die):
                sequence = [
                    (first_die, first_source),
                    (second_die, second_source),
                ]
                action = _format_sequence(sequence, high_die)
                if action not in seen_actions:
                    seen_actions.add(action)
                    after_second = _apply_move(
                        after_first, second_source, second_die
                    )
                    full_moves.append((action, after_second))

    # If any sequence can use both dice, using both is mandatory.
    if full_moves:
        return full_moves

    # Otherwise, the higher die is mandatory whenever it can be played.
    high_sources = _legal_sources(pos, high_die)
    if high_sources:
        candidates = []
        for source in high_sources:
            sequence = [(high_die, source)]
            action = _format_sequence(sequence, high_die)
            candidates.append((action, _apply_move(pos, source, high_die)))
        return candidates

    low_sources = _legal_sources(pos, low_die)
    if low_sources:
        candidates = []
        for source in low_sources:
            sequence = [(low_die, source)]
            action = _format_sequence(sequence, high_die)
            candidates.append((action, _apply_move(pos, source, low_die)))
        return candidates

    return [("H:P,P", pos)]


def _swap_perspective(pos: Position) -> Position:
    return {
        "my_pts": list(reversed(pos["opp_pts"])),
        "opp_pts": list(reversed(pos["my_pts"])),
        "my_bar": pos["opp_bar"],
        "opp_bar": pos["my_bar"],
        "my_off": pos["opp_off"],
        "opp_off": pos["my_off"],
    }


def _has_contact(pos: Position) -> bool:
    if pos["my_bar"] or pos["opp_bar"]:
        return True

    my_active = [i for i, n in enumerate(pos["my_pts"]) if n]
    opp_active = [i for i, n in enumerate(pos["opp_pts"]) if n]

    if not my_active or not opp_active:
        return False

    # Once every checker of the descending player is below every checker
    # of the ascending player, the checkers have passed one another.
    return not (max(my_active) < min(opp_active))


def _blot_exposure(index: int, enemy: List[int], enemy_bar: int) -> float:
    # Convert this point into the opponent's descending coordinate system.
    target = 23 - index
    exposure = 0.0

    if enemy_bar:
        if 18 <= target <= 23:
            exposure += 1.25
        return exposure

    for source in range(target + 1, 24):
        if enemy[source] <= 0:
            continue

        distance = source - target
        if distance <= 6:
            exposure += 1.0 + 0.12 * min(enemy[source] - 1, 2)
        elif distance <= 12:
            # Approximate combination-shot danger.
            combinations = 6 - abs(7 - distance)
            exposure += 0.07 * max(1, combinations)

    return min(exposure, 2.8)


def _side_feature(
    checkers: List[int],
    enemy: List[int],
    bar: int,
    enemy_bar: int,
    off: int,
    contact: bool,
) -> float:
    score = 1.7 * off - 3.8 * bar

    home_weights = (0.8, 1.8, 2.8, 3.7, 4.4, 3.5)
    anchor_weights = {
        18: 4.0,
        19: 4.2,
        20: 3.4,
        21: 2.5,
        22: 1.7,
        23: 1.0,
    }

    home_factor = 1.0 if contact else 0.25
    made = [n >= 2 for n in checkers]
    made_home = 0

    for i, count in enumerate(checkers):
        if count >= 2:
            if i < 6:
                score += home_factor * home_weights[i]
                made_home += 1
            elif i < 18:
                score += 1.05 if contact else 0.20
            elif contact:
                score += anchor_weights[i]

        if count > 3:
            score -= 0.18 * (count - 3)
        if count > 5:
            score -= 0.55 * (count - 5)

        if count == 1 and contact:
            exposure = _blot_exposure(i, enemy, enemy_bar)
            score -= 0.45 + 1.35 * exposure

    if contact and enemy_bar:
        score += enemy_bar * made_home * 1.45
        if made_home >= 5:
            score += enemy_bar * 4.0

    # Reward consecutive made points, especially real primes.
    run = 0
    for i in range(24):
        if made[i]:
            run += 1
        else:
            if run >= 3:
                score += (run - 2) * (run - 2) * (1.7 if contact else 0.35)
            run = 0
    if run >= 3:
        score += (run - 2) * (run - 2) * (1.7 if contact else 0.35)

    # Builders near useful points have modest value if not badly exposed.
    if contact:
        for i in range(1, 18):
            if checkers[i] == 1:
                nearby = 0
                for distance in range(1, 7):
                    destination = i - distance
                    if destination >= 0 and enemy[23 - destination] < 2:
                        nearby += 1
                score += min(nearby, 3) * 0.10

    return score


def _evaluate(pos: Position) -> float:
    if pos["my_off"] >= 15:
        return _WIN_SCORE
    if pos["opp_off"] >= 15:
        return -_WIN_SCORE

    my_pts = pos["my_pts"]
    # Opponent checkers in their own descending coordinate system.
    opp_canonical = list(reversed(pos["opp_pts"]))

    my_pips = 25 * pos["my_bar"]
    opp_pips = 25 * pos["opp_bar"]

    for i in range(24):
        my_pips += (i + 1) * my_pts[i]
        opp_pips += (i + 1) * opp_canonical[i]

    contact = _has_contact(pos)
    pip_weight = 0.98 if contact else 1.42
    score = pip_weight * (opp_pips - my_pips)

    my_feature = _side_feature(
        my_pts,
        opp_canonical,
        pos["my_bar"],
        pos["opp_bar"],
        pos["my_off"],
        contact,
    )
    opp_feature = _side_feature(
        opp_canonical,
        my_pts,
        pos["opp_bar"],
        pos["my_bar"],
        pos["opp_off"],
        contact,
    )

    return score + my_feature - opp_feature


def _expected_after_opponent(pos: Position) -> float:
    opponent_position = _swap_perspective(pos)
    weighted_total = 0.0

    for low in range(1, 7):
        for high in range(low, 7):
            weight = 1 if low == high else 2
            opponent_candidates = _generate_candidates(
                opponent_position, [low, high]
            )

            best_opponent_value = -float("inf")
            for _, resulting_position in opponent_candidates:
                value = _evaluate(resulting_position)
                if value > best_opponent_value:
                    best_opponent_value = value
                    if value >= _WIN_SCORE:
                        break

            # Evaluation is antisymmetric under perspective swapping.
            weighted_total += weight * (-best_opponent_value)

    return weighted_total / 36.0


def policy(state: dict) -> str:
    position = _copy_position(state)
    dice = list(state.get("dice", []))
    candidates = _generate_candidates(position, dice)

    if len(candidates) == 1:
        return candidates[0][0]

    immediate = []
    for action, resulting_position in candidates:
        score = _evaluate(resulting_position)
        immediate.append((score, action, resulting_position))

    immediate.sort(key=lambda item: item[0], reverse=True)

    # Any move which bears off the final checker wins immediately.
    if immediate and immediate[0][0] >= _WIN_SCORE:
        return immediate[0][1]

    # Limit the expensive chance-node search in unusually high-branching
    # positions while retaining a broad set of plausible moves.
    search_candidates = immediate[:30]

    best_action = search_candidates[0][1]
    best_score = -float("inf")

    for immediate_score, action, resulting_position in search_candidates:
        future_score = _expected_after_opponent(resulting_position)

        # The small immediate component stabilizes choices among nearly
        # identical expected outcomes.
        total_score = 0.94 * future_score + 0.06 * immediate_score

        if total_score > best_score:
            best_score = total_score
            best_action = action

    return best_action
