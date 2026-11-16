
import random
import time


# A board is:
# (our_points, their_points, our_bar, their_bar, our_off, their_off)
_PASS = -2
_BAR = -1

_HOME_VALUE = (1.7, 2.7, 4.2, 6.0, 7.5, 5.5)
_ANCHOR_VALUE = (5.8, 5.5, 4.2, 3.4, 2.6, 2.0)
_ENTRY_DELAY = (0.0, 0.5, 1.5, 3.5, 7.0, 16.0, 44.0)
_PRIME_VALUE = (0.0, 0.0, 1.5, 4.0, 10.0, 22.0, 45.0)
_WASTE = (2.5, 1.9, 1.4, 1.0, 0.7, 0.5)

# Diverse early rolls make an interrupted search less biased.
_SEARCH_ROLLS = (
    (1, 6), (2, 4), (3, 5), (1, 1), (4, 6), (2, 3),
    (5, 5), (1, 3), (2, 6), (3, 4), (6, 6), (1, 5),
    (2, 2), (4, 5), (3, 6), (1, 2), (4, 4), (2, 5),
    (3, 3), (1, 4), (5, 6),
)


class _OutOfTime(Exception):
    pass


def _format_action(action):
    order, first, second = action

    def token(source):
        if source == _PASS:
            return "P"
        if source == _BAR:
            return "B"
        return "A" + str(source)

    return order + ":" + token(first) + "," + token(second)


def _single_moves(board, die):
    """All legal single-die moves, without adding a pass."""
    p, q, bar, enemy_bar, off, enemy_off = board
    result = []

    if bar:
        destination = 24 - die
        if q[destination] >= 2:
            return result

        pp = list(p)
        pp[destination] += 1
        if q[destination] == 1:
            qq = list(q)
            qq[destination] = 0
            next_q = tuple(qq)
            next_enemy_bar = enemy_bar + 1
        else:
            next_q = q
            next_enemy_bar = enemy_bar

        result.append((
            _BAR,
            (tuple(pp), next_q, bar - 1, next_enemy_bar, off, enemy_off)
        ))
        return result

    highest = -1
    for i in range(23, -1, -1):
        if p[i]:
            highest = i
            break

    if highest < 0:
        return result

    can_bear_off = highest < 6

    for source, count in enumerate(p):
        if not count:
            continue

        destination = source - die
        if destination < 0:
            if not can_bear_off:
                continue
            if destination != -1 and source != highest:
                continue

            pp = list(p)
            pp[source] -= 1
            result.append((
                source,
                (tuple(pp), q, bar, enemy_bar, off + 1, enemy_off)
            ))
            continue

        if q[destination] >= 2:
            continue

        pp = list(p)
        pp[source] -= 1
        pp[destination] += 1

        if q[destination] == 1:
            qq = list(q)
            qq[destination] = 0
            next_q = tuple(qq)
            next_enemy_bar = enemy_bar + 1
        else:
            next_q = q
            next_enemy_bar = enemy_bar

        result.append((
            source,
            (tuple(pp), next_q, bar, next_enemy_bar, off, enemy_off)
        ))

    return result


def _legal_turns(board, dice):
    """
    Map distinct legal resulting boards to representative actions.
    The supplied game encodes at most two moves, including on doubles.
    """
    if not dice:
        return {board: ("H", _PASS, _PASS)}

    if len(dice) == 1:
        moves = _single_moves(board, dice[0])
        if not moves:
            return {board: ("H", _PASS, _PASS)}
        return {
            next_board: ("H", source, _PASS)
            for source, next_board in moves
        }

    low, high = min(dice), max(dice)
    orders = [("H", high, low)]
    if low != high:
        orders.append(("L", low, high))

    best_requirement = (-1, -1)
    results = {}

    for order, first_die, second_die in orders:
        first_moves = _single_moves(board, first_die)
        if not first_moves:
            first_moves = [(_PASS, board)]

        for first_source, intermediate in first_moves:
            second_moves = _single_moves(intermediate, second_die)
            if not second_moves:
                second_moves = [(_PASS, intermediate)]

            for second_source, final_board in second_moves:
                used = int(first_source != _PASS) + int(second_source != _PASS)
                if used == 1:
                    used_die = (
                        first_die if first_source != _PASS else second_die
                    )
                else:
                    used_die = 0

                requirement = (used, used_die)
                if requirement < best_requirement:
                    continue
                if requirement > best_requirement:
                    best_requirement = requirement
                    results.clear()

                action = (order, first_source, second_source)
                previous = results.get(final_board)
                if previous is None:
                    results[final_board] = action
                elif previous[1] == _PASS and first_source != _PASS:
                    # Prefer an actual move followed by a pass.
                    results[final_board] = action

    return results


def _reverse_board(board):
    p, q, bar, enemy_bar, off, enemy_off = board
    return (
        q[::-1], p[::-1], enemy_bar, bar, enemy_off, off
    )


def _is_race(board):
    p, q, bar, enemy_bar, _, _ = board
    if bar or enemy_bar:
        return False

    highest = max((i for i, n in enumerate(p) if n), default=-1)
    lowest_enemy = next((i for i, n in enumerate(q) if n), 24)
    return highest < lowest_enemy


def _side_features(p, q, bar, enemy_bar, off, pip_weight):
    pip = 25 * bar
    waste = 1.7 * bar
    position = 4.0 * off
    danger = 0.0

    enemy_home = sum(q[i] >= 2 for i in range(18, 24))
    entry_delay = _ENTRY_DELAY[enemy_home]
    position -= bar * (5.0 + entry_delay)
    position -= 1.5 * bar * max(0, bar - 1)

    enemy_deep = enemy_bar + sum(q[:6])
    home_factor = 1.0 if enemy_deep else 0.72

    own_home_points = 0
    enemies_before = enemy_bar
    run_length = 0
    run_victims = 0
    run_start = 0

    for i in range(25):
        count = p[i] if i < 24 else 0

        if count >= 2:
            if not run_length:
                run_start = i
                run_victims = enemies_before
            run_length += 1
        elif run_length:
            if run_length >= 2:
                bonus = _PRIME_VALUE[min(run_length, 6)]
                if run_victims:
                    factor = 0.6 + 0.2 * min(run_victims, 3)
                    position += bonus * factor
                elif run_start < 6:
                    position += 0.15 * bonus
            run_length = 0

        if i == 24:
            break

        enemies_before += q[i]
        if not count:
            continue

        pip += count * (i + 1)
        if i < 6:
            waste += count * _WASTE[i]
        else:
            waste += count * (1.5 + 0.12 * (i // 6))

        if i >= 18:
            position -= count * (1.8 + 0.30 * (i - 18))
        elif i >= 12:
            position -= 0.25 * count

        if count >= 2:
            if i < 6:
                own_home_points += 1
                position += _HOME_VALUE[i] * home_factor
            elif i == 6:
                position += 5.5
            elif i == 7:
                position += 4.0
            elif i == 8:
                position += 3.0
            elif i <= 11:
                position += 2.2
            elif i < 18:
                position += 1.3
            else:
                position += _ANCHOR_VALUE[i - 18]
                position += 0.5 * max(0, enemy_home - 2)

            extra = count - 2
            if extra:
                if i < 6:
                    position -= 0.45 * extra + 0.22 * extra * extra
                elif i >= 18:
                    position -= 0.9 * extra + 0.12 * extra * extra
                else:
                    position -= 0.25 * extra + 0.08 * extra * extra

        elif count == 1:
            # Probability of at least one direct hitting die.
            shots = 0
            for die in range(1, min(6, i) + 1):
                if q[i - die]:
                    shots += 1

            board_shot_probability = shots * (12.0 - shots) / 36.0

            if enemy_bar == 0:
                hit_probability = board_shot_probability
            else:
                entry_shot = 11.0 / 36.0 if i < 6 else 0.0
                if enemy_bar == 1:
                    open_entries = 6 - sum(p[j] >= 2 for j in range(6))
                    other_shot = (
                        0.55 * board_shot_probability * open_entries / 6.0
                    )
                    hit_probability = (
                        entry_shot + (1.0 - entry_shot) * other_shot
                    )
                else:
                    hit_probability = entry_shot

            hit_cost = (
                pip_weight * (24 - i) + 4.0 + 0.8 * entry_delay
            )
            danger += hit_probability * hit_cost

    if own_home_points >= 4:
        position += (0.0, 0.0, 0.0, 0.0, 1.0, 4.0, 10.0)[own_home_points]

    return pip, waste, position, danger


def _evaluate(board):
    """Value for the represented player, who has just moved."""
    p, q, bar, enemy_bar, off, enemy_off = board
    ours_left = sum(p) + bar
    theirs_left = sum(q) + enemy_bar

    if ours_left == 0:
        return 10000.0
    if theirs_left == 0:
        return -10000.0

    highest = max((i for i, n in enumerate(p) if n), default=-1)
    lowest_enemy = next((i for i, n in enumerate(q) if n), 24)

    if bar or enemy_bar:
        contact = 1.0
    elif highest < lowest_enemy:
        contact = 0.0
    else:
        involved = sum(p[lowest_enemy:]) + sum(q[:highest + 1])
        contact = min(1.0, involved / 8.0)

    pip_weight = 0.38 + 0.62 * (1.0 - contact)
    a = _side_features(p, q, bar, enemy_bar, off, pip_weight)
    b = _side_features(
        q[::-1], p[::-1], enemy_bar, bar, enemy_off, pip_weight
    )

    return (
        pip_weight * (b[0] - a[0])
        + (1.0 - contact) * (b[1] - a[1])
        + contact * (a[2] - b[2])
        - contact * (0.85 * a[3] - 0.28 * b[3])
    )


def _race_cost(points):
    total = 0.0
    for i, count in enumerate(points):
        if count:
            waste = _WASTE[i] if i < 6 else 1.5 + 0.12 * (i // 6)
            total += count * (i + 1 + waste)
    return total


def _dice_stream(rng, length=80):
    result = []
    for _ in range(length):
        a = rng.randint(1, 6)
        b = rng.randint(1, 6)
        result.append((a, b) if a >= b else (b, a))
    return result


def _race_finish(points, rolls):
    """
    Fast race rollout. Exact bearoffs are preferred; otherwise advance
    the rearmost checker, reducing crossovers and avoiding stranded men.
    """
    p = list(points)
    remaining = sum(p)
    if not remaining:
        return 0

    highest = 23
    while not p[highest]:
        highest -= 1

    turn = 0
    for dice in rolls:
        turn += 1
        for die in dice:
            if highest < 6 and p[die - 1]:
                source = die - 1
                destination = -1
            elif highest < die:
                source = highest
                destination = -1
            else:
                source = highest
                destination = source - die

            p[source] -= 1
            if destination < 0:
                remaining -= 1
                if not remaining:
                    return turn
            else:
                p[destination] += 1

            while highest >= 0 and not p[highest]:
                highest -= 1

    # Extremely long races are rare; retain a sensible continuation.
    return turn + max(1, int(_race_cost(p) / 7.0 + 0.5))


def _race_choice(legal, original_board, deadline, seed):
    candidates = sorted(
        legal.items(), key=lambda item: _race_cost(item[0][0])
    )[:12]

    if len(candidates) == 1:
        return candidates[0][1]

    rng = random.Random(seed)
    opponent_points = original_board[1][::-1]
    opponent_finishes = []

    # Estimate the opponent's finish-time distribution first.
    for sample in range(128):
        if sample >= 32 and time.perf_counter() >= deadline - 0.15:
            break
        opponent_finishes.append(
            _race_finish(opponent_points, _dice_stream(rng))
        )

    largest = max(opponent_finishes) + 2
    survival = [
        sum(finish > t for finish in opponent_finishes)
        / len(opponent_finishes)
        for t in range(largest + 1)
    ]

    scores = [0.0] * len(candidates)
    completed = 0

    for _ in range(256):
        if time.perf_counter() >= deadline:
            break

        # Common random numbers make candidate comparisons much quieter.
        rolls = _dice_stream(rng)
        additions = []
        for board, _action in candidates:
            finish = _race_finish(board[0], rolls)
            win_probability = survival[finish] if finish <= largest else 0.0
            additions.append(win_probability - 0.0001 * finish)

        for i, value in enumerate(additions):
            scores[i] += value
        completed += 1

    if not completed:
        return candidates[0][1]

    best = max(range(len(candidates)), key=lambda i: scores[i])
    return candidates[best][1]


def policy(state: dict) -> str:
    start = time.perf_counter()
    deadline = start + 0.86

    dice = tuple(state["dice"])
    if not dice:
        return "H:P,P"

    board = (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )

    legal = _legal_turns(board, dice)
    fallback_action = next(iter(legal.values()))

    if len(legal) == 1:
        return _format_action(fallback_action)

    for result, action in legal.items():
        if result[2] == 0 and not any(result[0]):
            return _format_action(action)

    # Nothing below this point can invalidate the retained legal fallback.
    try:
        if _is_race(board):
            seed = (
                7193
                + sum(
                    (i + 1) * (board[0][i] + 3 * board[1][i])
                    for i in range(24)
                )
                + 97 * sum(dice)
                + 503 * board[4]
            )
            action = _race_choice(legal, board, deadline, seed)
            return _format_action(action)

        cache = {}

        def value(position):
            cached = cache.get(position)
            if cached is None:
                cached = _evaluate(position)
                cache[position] = cached
            return cached

        ranked = [
            (value(result), result, action)
            for result, action in legal.items()
        ]
        ranked.sort(key=lambda item: item[0], reverse=True)
        candidates = ranked[:8]
        fallback_action = candidates[0][2]

        sums = [0.0] * len(candidates)
        total_weight = 0.0
        evaluations = 0

        try:
            for low, high in _SEARCH_ROLLS:
                if time.perf_counter() >= deadline:
                    break

                roll_values = []
                weight = 1.0 if low == high else 2.0

                # Commit a roll only after every candidate has been searched.
                for _initial, result, _action in candidates:
                    if time.perf_counter() >= deadline:
                        raise _OutOfTime

                    opponent_board = _reverse_board(result)
                    replies = _legal_turns(opponent_board, (low, high))
                    opponent_best = -float("inf")

                    for reply in replies:
                        opponent_best = max(opponent_best, value(reply))
                        evaluations += 1
                        if evaluations % 64 == 0:
                            if time.perf_counter() >= deadline:
                                raise _OutOfTime

                    roll_values.append(-opponent_best)

                for i, score in enumerate(roll_values):
                    sums[i] += weight * score
                total_weight += weight

        except _OutOfTime:
            pass

        if total_weight:
            # Use a stronger static prior when only a few rolls completed.
            search_weight = 0.85 * total_weight / (total_weight + 3.0)
            best_score = -float("inf")

            for i, (initial, _result, action) in enumerate(candidates):
                score = (
                    (1.0 - search_weight) * initial
                    + search_weight * sums[i] / total_weight
                )
                if score > best_score:
                    best_score = score
                    fallback_action = action

    except Exception:
        # Evaluation/search failure must never produce an illegal action.
        pass

    return _format_action(fallback_action)
