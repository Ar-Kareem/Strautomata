
import time
import heapq
from functools import lru_cache


# The action interface uses two moves, including on doubles.
_PASS = -1
_BAR = 24

_DIE_MASK = [0] * 7
_PAIR_MASK = [[0] * 7 for _ in range(7)]
for _a in range(1, 7):
    for _b in range(1, 7):
        _bit = 1 << ((_a - 1) * 6 + _b - 1)
        _DIE_MASK[_a] |= _bit
        _DIE_MASK[_b] |= _bit
        _PAIR_MASK[_a][_b] |= _bit
        _PAIR_MASK[_b][_a] |= _bit

_SPLITS = [[] for _ in range(13)]
for _distance in range(2, 13):
    for _a in range(1, 7):
        _b = _distance - _a
        if 1 <= _b <= 6:
            _SPLITS[_distance].append((_a, _PAIR_MASK[_a][_b]))

_POINT_VALUES = (
    1.6, 2.2, 3.2, 4.1, 4.7, 4.8,
    3.8, 3.0, 2.3, 1.8, 1.4, 1.1,
    0.9, 0.75, 0.6, 0.5, 0.4, 0.3,
)
_ANCHOR_VALUES = (3.7, 3.7, 3.0, 2.2, 1.4, 0.9)
_PRIME_VALUES = (0.0, 0.0, 0.3, 1.2, 3.4, 6.5, 11.5)

_WASTE = tuple(3.5 * (7.0 / 6.0) ** i - (i + 1)
               for i in range(6))

_INITIAL_MY = tuple(
    5 if i in (5, 12) else 3 if i == 7 else 2 if i == 23 else 0
    for i in range(24)
)
_INITIAL_OPP = _INITIAL_MY[::-1]

_OPENINGS = {
    (1, 2): ("H", 12, 5),
    (1, 3): ("H", 7, 5),
    (1, 4): ("H", 12, 23),
    (1, 5): ("H", 12, 23),
    (1, 6): ("H", 12, 7),
    (2, 3): ("H", 23, 12),
    (2, 4): ("H", 7, 5),
    (2, 5): ("H", 12, 23),
    (2, 6): ("H", 23, 12),
    (3, 4): ("H", 12, 23),
    (3, 5): ("H", 7, 5),
    (3, 6): ("H", 23, 12),
    (4, 5): ("H", 12, 23),
    (4, 6): ("H", 23, 12),
    (5, 6): ("H", 23, 17),
}

# Balanced ordering makes an interrupted search reasonably representative.
_ROLLS = (
    (1, 6), (3, 4), (2, 5), (1, 1), (6, 6),
    (2, 3), (4, 5), (1, 3), (4, 6), (2, 2),
    (5, 5), (1, 5), (2, 6), (1, 2), (5, 6),
    (3, 3), (4, 4), (1, 4), (3, 6), (2, 4), (3, 5),
)


def _format(action):
    order, first, second = action

    def token(source):
        if source == _PASS:
            return "P"
        if source == _BAR:
            return "B"
        return "A" + str(source)

    return order + ":" + token(first) + "," + token(second)


def _flip(board):
    m, o, mb, ob, mf, of = board
    return o[::-1], m[::-1], ob, mb, of, mf


def _steps(board, die):
    """All legal single-die moves, without optional passes."""
    m, o, mb, ob, mf, of = board

    if mb:
        destination = 24 - die
        if o[destination] >= 2:
            return []

        nm = list(m)
        nm[destination] += 1
        no = o
        nob = ob
        if o[destination] == 1:
            no = list(o)
            no[destination] = 0
            no = tuple(no)
            nob += 1

        return [((tuple(nm), no, mb - 1, nob, mf, of), _BAR)]

    farthest = -1
    for i in range(23, -1, -1):
        if m[i]:
            farthest = i
            break

    if farthest < 0:
        return []

    home = farthest <= 5
    result = []

    for source, count in enumerate(m):
        if not count:
            continue

        destination = source - die
        if destination < 0:
            if not home:
                continue
            if die != source + 1 and source != farthest:
                continue

            nm = list(m)
            nm[source] -= 1
            result.append(((tuple(nm), o, 0, ob, mf + 1, of), source))
            continue

        if o[destination] >= 2:
            continue

        nm = list(m)
        nm[source] -= 1
        nm[destination] += 1

        no = o
        nob = ob
        if o[destination] == 1:
            no = list(o)
            no[destination] = 0
            no = tuple(no)
            nob += 1

        result.append(((tuple(nm), no, 0, nob, mf, of), source))

    return result


def _legal(board, dice):
    """Enumerate complete legal actions and deduplicate resulting positions."""
    if not dice:
        return [(board, ("H", _PASS, _PASS))]

    if len(dice) == 1:
        moves = _steps(board, dice[0])
        if not moves:
            return [(board, ("H", _PASS, _PASS))]
        return [(b, ("H", source, _PASS)) for b, source in moves]

    high = max(dice)
    low = min(dice)
    orders = [("H", high, low)]
    if high != low:
        orders.append(("L", low, high))

    best_rank = (-1, -1)
    result = []
    seen = set()

    for order, first_die, second_die in orders:
        first_moves = _steps(board, first_die)
        if not first_moves:
            first_moves = [(board, _PASS)]

        for middle, first in first_moves:
            second_moves = _steps(middle, second_die)
            if not second_moves:
                second_moves = [(middle, _PASS)]

            for final, second in second_moves:
                # Prefer the equivalent encoding with its actual move first.
                if first == _PASS and second != _PASS:
                    continue

                used = int(first != _PASS) + int(second != _PASS)
                high_used = 0
                if used == 1:
                    actual_die = first_die if first != _PASS else second_die
                    high_used = int(actual_die == high)
                rank = used, high_used

                if rank > best_rank:
                    best_rank = rank
                    result = []
                    seen = set()

                if rank == best_rank and final not in seen:
                    seen.add(final)
                    result.append((final, (order, first, second)))

    return result or [(board, ("H", _PASS, _PASS))]


def _no_contact(board):
    m, o, mb, ob, _, _ = board
    if mb or ob:
        return False

    back = -1
    for i in range(23, -1, -1):
        if m[i]:
            back = i
            break

    front = 24
    for i in range(24):
        if o[i]:
            front = i
            break

    return back < front


@lru_cache(maxsize=20000)
def _bear_steps(counts, die):
    farthest = -1
    for i in range(5, -1, -1):
        if counts[i]:
            farthest = i
            break

    if farthest < 0:
        return (counts,)

    result = []
    for source, n in enumerate(counts):
        if not n:
            continue
        destination = source - die
        if destination < 0 and die != source + 1 and source != farthest:
            continue
        new = list(counts)
        new[source] -= 1
        if destination >= 0:
            new[destination] += 1
        result.append(tuple(new))
    return tuple(result)


@lru_cache(maxsize=4096)
def _bear_time(counts):
    """Optimal expected turns for a small, uncontested home-board position."""
    if not any(counts):
        return 0.0

    expectation = 0.0
    for low in range(1, 7):
        for high in range(low, 7):
            orders = ((high, low),) if high == low else (
                (high, low), (low, high)
            )
            best = float("inf")
            for first, second in orders:
                for middle in _bear_steps(counts, first):
                    for final in _bear_steps(middle, second):
                        value = _bear_time(final)
                        if value < best:
                            best = value
            expectation += best * (1 if high == low else 2)

    return 1.0 + expectation / 36.0


def _race_cost(points, exact=False):
    remaining = sum(points)
    if not remaining:
        return 0.0

    outside = any(points[6:])
    if exact and not outside and remaining <= 6:
        return 7.0 * _bear_time(tuple(points[:6]))

    if points[0] == remaining:
        return 7.0 * ((remaining + 1) // 2)

    pips = 0
    waste = 0.0
    stretch = 0
    for i, n in enumerate(points):
        if n:
            pips += (i + 1) * n
            waste += n * (_WASTE[i] if i < 6 else 1.67)
            if i >= 6:
                stretch += n * (i - 5) ** 2

    return (
        pips
        + 0.72 * waste
        + 0.28 * max(0.0, 3.5 * remaining - pips)
        + 1.75
        + 0.012 * stretch
    )


def _prime_bonus(length, trapped):
    if length < 2 or trapped <= 0:
        return 0.0
    value = _PRIME_VALUES[min(length, 6)]
    if length > 6:
        value += 0.7 * (length - 6)
    return value * (0.75 + 0.25 * min(3, trapped))


def _position_score(points, other, bar, other_bar, off):
    blocked_prefix = [0] * 25
    for i, n in enumerate(other):
        blocked_prefix[i + 1] = blocked_prefix[i] + int(n >= 2)

    enemy_home = blocked_prefix[24] - blocked_prefix[18]
    score = (
        -0.23 * 25 * bar
        + 0.70 * off
        - bar * (3.5 + 0.85 * enemy_home + 0.30 * enemy_home ** 2)
    )

    behind = other_bar
    run = 0
    run_trapped = 0

    for i, n in enumerate(points):
        if n >= 2:
            if i < 6:
                score += _POINT_VALUES[i] * (
                    0.35 + 0.65 * min(1.0, behind / 2.0)
                )
            elif i < 18:
                score += _POINT_VALUES[i] * min(1.0, behind / 2.0)
            else:
                score += _ANCHOR_VALUES[i - 18] * (
                    0.65 + 0.10 * enemy_home
                )

            if run == 0:
                run_trapped = behind
            run += 1
        else:
            score += _prime_bonus(run, run_trapped)
            run = 0
            if n == 1 and 3 <= i <= 11:
                score += 0.15

        if n:
            score -= 0.23 * (i + 1) * n

            if n > 3:
                score -= 0.35 * (n - 3) + 0.35 * max(0, n - 5)
            if i < 3 and n > 2:
                score -= 0.55 * (3 - i) * (n - 2) / 3.0

            if i >= 18:
                score -= 0.09 * (i - 17) * n

            if i >= 6:
                blocked = blocked_prefix[i] - blocked_prefix[max(0, i - 6)]
                if blocked > 2:
                    score -= 0.40 * (blocked - 2) * min(n, 3)

        behind += other[i]

    return score + _prime_bonus(run, run_trapped)


def _hit_penalty(points, other, other_bar, full):
    """Expected exposure, using unions of the 36 ordered dice outcomes."""
    enemy_home = sum(n >= 2 for n in other[18:24])
    bar_cost = 3.5 + 0.85 * enemy_home + 0.30 * enemy_home ** 2
    penalty = 0.0

    for target, n in enumerate(points):
        if n != 1:
            continue

        mask = 0

        if other_bar == 0:
            radius = 12 if full else 6
            for source in range(max(0, target - radius), target):
                if not other[source]:
                    continue

                distance = target - source
                if distance <= 6:
                    mask |= _DIE_MASK[distance]

                if full:
                    for first_die, pair_mask in _SPLITS[distance]:
                        if points[source + first_die] < 2:
                            mask |= pair_mask

        elif other_bar >= 2:
            if target < 6:
                mask = _DIE_MASK[target + 1]

        else:
            if target < 6:
                mask |= _DIE_MASK[target + 1]

            # One bar checker: enter, then move an existing checker,
            # or move the entered checker again.
            for entry_die in range(1, 7):
                if points[entry_die - 1] >= 2:
                    continue

                for source in range(max(0, target - 6), target):
                    if other[source]:
                        mask |= _PAIR_MASK[entry_die][target - source]

                if full:
                    second_die = target + 1 - entry_die
                    if 1 <= second_die <= 6:
                        mask |= _PAIR_MASK[entry_die][second_die]

        if mask:
            cost = bar_cost + 0.23 * (24 - target)
            if target >= 18 and enemy_home <= 3:
                cost *= 0.82
            penalty += mask.bit_count() * cost / 36.0

    return penalty


def _evaluate(board, full):
    m, o, mb, ob, mf, of = board

    if mf >= 15:
        return 10000.0
    if of >= 15:
        return -10000.0

    if _no_contact(board):
        return 0.23 * (_race_cost(o[::-1]) - _race_cost(m))

    rm = m[::-1]
    ro = o[::-1]

    value = (
        _position_score(m, o, mb, ob, mf)
        - _position_score(ro, rm, ob, mb, of)
    )
    value += 0.78 * (
        _hit_penalty(ro, rm, mb, full)
        - _hit_penalty(m, o, ob, full)
    )
    return value


def policy(state: dict) -> str:
    started = time.perf_counter()
    deadline = started + 0.88

    board = (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )
    dice = tuple(state["dice"])
    legal = _legal(board, dice)

    if len(legal) == 1:
        return _format(legal[0][1])

    for final, action in legal:
        if final[4] >= 15:
            return _format(action)

    if (
        len(dice) == 2
        and board[0] == _INITIAL_MY
        and board[1] == _INITIAL_OPP
        and board[2:] == (0, 0, 0, 0)
    ):
        opening = _OPENINGS.get(tuple(sorted(dice)))
        if opening is not None:
            for _, action in legal:
                if action == opening:
                    return _format(action)

    if _no_contact(board):
        best = min(legal, key=lambda item: _race_cost(item[0][0], exact=True))
        return _format(best[1])

    full_cache = {}
    fast_cache = {}

    def evaluate(position, full):
        cache = full_cache if full else fast_cache
        cached = cache.get(position)
        if cached is not None:
            return cached
        value = _evaluate(position, full)
        cache[position] = value
        return value

    ranked = [
        (evaluate(final, True), final, action)
        for final, action in legal
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)

    top_score = ranked[0][0]
    candidates = [
        item for index, item in enumerate(ranked[:8])
        if index < 3 or item[0] >= top_score - 7.0
    ]

    if len(candidates) == 1 or time.perf_counter() >= deadline:
        return _format(candidates[0][2])

    bases = [item[0] for item in candidates]
    opponent_positions = [_flip(item[1]) for item in candidates]
    corrections = [0.0] * len(candidates)

    def opponent_reply(position, roll):
        replies = _legal(position, roll)
        best_heap = []

        for index, (final, _) in enumerate(replies):
            if index % 24 == 0 and time.perf_counter() >= deadline:
                return None

            quick = evaluate(final, False)
            if quick >= 9999.0:
                return -10000.0

            entry = (quick, index, final)
            if len(best_heap) < 4:
                heapq.heappush(best_heap, entry)
            elif quick > best_heap[0][0]:
                heapq.heapreplace(best_heap, entry)

        best = -float("inf")
        for _, _, final in best_heap:
            value = evaluate(final, True)
            if value > best:
                best = value

        return -best

    # Only complete roll groups contribute, so every candidate receives
    # the same search coverage even when the time budget expires.
    for roll in _ROLLS:
        if time.perf_counter() >= deadline:
            break

        values = []
        for position in opponent_positions:
            if time.perf_counter() >= deadline:
                break
            value = opponent_reply(position, roll)
            if value is None:
                break
            values.append(value)

        if len(values) != len(candidates):
            break

        weight = 1 if roll[0] == roll[1] else 2
        reference = values[0]
        base_reference = bases[0]

        for i in range(len(candidates)):
            corrections[i] += weight * (
                (values[i] - reference) - (bases[i] - base_reference)
            )

    best_index = max(
        range(len(candidates)),
        key=lambda i: bases[i] + 0.82 * corrections[i] / 36.0,
    )
    return _format(candidates[best_index][2])
