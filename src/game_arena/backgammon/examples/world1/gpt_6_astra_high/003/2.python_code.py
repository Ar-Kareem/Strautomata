
import time
import math
from functools import lru_cache

# This arena encodes at most two checker moves, including on doubles.
_ROLLS = [(a, b, 1 if a == b else 2)
          for a in range(1, 7) for b in range(a, 7)]

_SEARCH_ROLLS = [
    (3, 4), (1, 1), (5, 6), (2, 5), (1, 6), (4, 4),
    (1, 2), (3, 6), (2, 2), (1, 4), (4, 6), (3, 3),
    (2, 4), (1, 5), (6, 6), (2, 3), (3, 5), (5, 5),
    (1, 3), (2, 6), (4, 5)
]

_DIE_MASK = [0] * 7
_PAIR_MASK = [[0] * 7 for _ in range(7)]
for _a in range(1, 7):
    for _b in range(1, 7):
        _bit = 1 << ((_a - 1) * 6 + _b - 1)
        _DIE_MASK[_a] |= _bit
        _DIE_MASK[_b] |= _bit
        _PAIR_MASK[_a][_b] |= _bit
        _PAIR_MASK[_b][_a] |= _bit

_ENTRY_PROB = [[0.0] * 64 for _ in range(64)]
for _e in range(64):
    for _s in range(64):
        _count = 0
        for _a in range(6):
            for _b in range(6):
                if (((_e >> _a) & 1 and (_s >> _b) & 1) or
                        ((_e >> _b) & 1 and (_s >> _a) & 1)):
                    _count += 1
        _ENTRY_PROB[_e][_s] = _count / 36.0

_POINT_VALUE = (
    5, 7, 8, 10, 11, 11, 8, 7, 6, 5, 4, 3,
    3, 3, 3, 3, 4, 5, 12, 14, 12, 10, 8, 6
)
_RUN_VALUE = (0, 0, 2.5, 8, 17, 32, 55)
_WASTE = (2.5, 2.083333, 1.763889, 1.557870, 1.484182, 1.564879)


# Board: (our points, their points, our bar, their bar, our off, their off).
# In every internally oriented board, "our" checkers move downward.
def _flip(board):
    p, q, bar, obar, off, ooff = board
    return q[::-1], p[::-1], obar, bar, ooff, off


def _starts(board, die):
    p, q, bar, obar, off, ooff = board
    if bar:
        return [-1] if q[24 - die] < 2 else []

    highest = -1
    for i in range(23, -1, -1):
        if p[i]:
            highest = i
            break

    result = []
    home = highest < 6
    for i, n in enumerate(p):
        if not n:
            continue
        dest = i - die
        if dest >= 0:
            if q[dest] < 2:
                result.append(i)
        elif home and (i == die - 1 or i == highest):
            result.append(i)
    return result


def _apply(board, source, die):
    p, q, bar, obar, off, ooff = board
    pp = list(p)
    if source == -1:
        bar -= 1
        dest = 24 - die
    else:
        pp[source] -= 1
        dest = source - die

    if dest < 0:
        off += 1
    else:
        if q[dest] == 1:
            qq = list(q)
            qq[dest] = 0
            q = tuple(qq)
            obar += 1
        pp[dest] += 1

    return tuple(pp), q, bar, obar, off, ooff


def _turn(board, dice):
    """Map distinct legal resulting boards to one legal action encoding."""
    if not dice:
        return {board: ("H", -2, -2)}

    if len(dice) == 1:
        orders = [("H", dice[0], 0)]
    else:
        lo, hi = min(dice), max(dice)
        orders = [("H", hi, lo)]
        if lo != hi:
            orders.append(("L", lo, hi))

    result = {}
    best_count = -1
    best_sum = -1

    for order, first, second in orders:
        # A playable die can always be encoded first. This avoids
        # unnecessary leading-pass representations.
        for src1 in _starts(board, first):
            middle = _apply(board, src1, first)
            starts2 = _starts(middle, second) if second else []
            if not starts2:
                starts2 = [-2]

            for src2 in starts2:
                count = 1 + (src2 != -2)
                used_sum = first + (second if src2 != -2 else 0)

                if count < best_count:
                    continue
                if count == best_count and used_sum < best_sum:
                    continue

                final = (middle if src2 == -2 else
                         _apply(middle, src2, second))

                if count > best_count or used_sum > best_sum:
                    result.clear()
                    best_count, best_sum = count, used_sum

                if final not in result:
                    result[final] = (order, src1, src2)

    return result or {board: ("H", -2, -2)}


def _encode(action):
    order, first, second = action

    def token(x):
        if x == -1:
            return "B"
        if x == -2:
            return "P"
        return "A" + str(x)

    return order + ":" + token(first) + "," + token(second)


def _contact(board):
    p, q, bar, obar, off, ooff = board
    if bar or obar:
        return True
    high = next((i for i in range(23, -1, -1) if p[i]), -1)
    low = next((i for i in range(24) if q[i]), 24)
    return high >= low


def _race_cost(p):
    result = 0.0
    highest = 0
    for i, n in enumerate(p):
        if n:
            highest = i
            result += n * (i + 1 + (_WASTE[i] if i < 6 else 1.65))
            if 2 <= i < 6 and n > 3:
                result += 0.055 * (n - 3) ** 2 * (i + 1) / 6.0
    return result + 0.10 * highest


def _structure(p, q, bar, obar, off, pip, pip_difference):
    enemy_home = sum(n >= 2 for n in q[18:24])
    own_home = sum(n >= 2 for n in p[:6])
    score = -0.55 * pip + 2.0 * off
    score -= bar * (7.0 + 2.8 * enemy_home)

    qblock = 0
    for i, n in enumerate(q):
        if n >= 2:
            qblock |= 1 << i

    anchor_factor = max(0.65, min(1.45, 1.0 + pip_difference / 110.0))
    behind = obar
    run = 0
    run_behind = 0

    for i, n in enumerate(p):
        if n >= 2:
            if i < 12:
                usefulness = 0.35 + 0.65 * min(1.0, behind / 2.0)
                score += _POINT_VALUE[i] * usefulness
            elif i >= 18:
                score += _POINT_VALUE[i] * anchor_factor
            else:
                score += _POINT_VALUE[i] * (0.5 if not behind else 1.0)

            if i < 13:
                if not run:
                    run_behind = behind
                run += 1
            elif run:
                score += _RUN_VALUE[min(run, 6)] * (
                    0.15 + 0.85 * min(1.0, run_behind / 2.0))
                run = 0
        else:
            if run:
                score += _RUN_VALUE[min(run, 6)] * (
                    0.15 + 0.85 * min(1.0, run_behind / 2.0))
                run = 0
            if n == 1 and 1 <= i <= 5:
                score += 0.5

        if n > 2:
            extra = n - 2
            score -= 0.60 * extra * math.sqrt(extra)
            if i >= 18:
                score -= 1.8 * extra
            elif 6 <= i <= 12 and n == 3:
                score += 0.5

        if n and i >= 6:
            blocked = ((qblock >> (i - 6)) & 63).bit_count()
            if blocked >= 4:
                score -= 0.9 * min(n, 3) * (blocked - 3) ** 2

        behind += q[i]

    if run:
        score += _RUN_VALUE[min(run, 6)] * (
            0.15 + 0.85 * min(1.0, run_behind / 2.0))

    trapped_home = obar + sum(q[:6])
    score += 0.45 * own_home * own_home * (
        0.45 + 0.55 * min(1.0, trapped_home / 2.0))
    return score


def _exact_shots(p, q, target, enemy_bar):
    mask = 0
    if not enemy_bar:
        for origin in range(max(0, target - 12), target):
            if not q[origin]:
                continue
            distance = target - origin
            if distance <= 6:
                mask |= _DIE_MASK[distance]
            for first in range(max(1, distance - 6), min(6, distance - 1) + 1):
                if p[origin + first] < 2:
                    mask |= _PAIR_MASK[first][distance - first]
        return mask

    if target < 6:
        mask |= _DIE_MASK[target + 1]

    if enemy_bar == 1:
        for entry in range(1, 7):
            if p[entry - 1] >= 2:
                continue
            remaining = target - (entry - 1)
            if 1 <= remaining <= 6:
                mask |= _PAIR_MASK[entry][remaining]
            for die in range(1, 7):
                origin = target - die
                if origin >= 0 and q[origin]:
                    mask |= _PAIR_MASK[entry][die]
    return mask


def _danger(p, q, enemy_bar, exact=False):
    enemy_home = sum(n >= 2 for n in q[18:24])
    delay = 7.0 + 2.8 * enemy_home
    blots = [i for i, n in enumerate(p) if n == 1]
    if not blots:
        return 0.0

    if exact:
        shots = []
        for x in blots:
            mask = _exact_shots(p, q, x, enemy_bar)
            if mask:
                loss = 0.55 * (24 - x) + delay
                shots.append((loss, mask))
        shots.sort(reverse=True)
        covered = 0
        value = 0.0
        for loss, mask in shots:
            fresh = mask & ~covered
            overlap = mask & covered
            value += loss * (fresh.bit_count() + 0.20 * overlap.bit_count())
            covered |= mask
        return value / 36.0

    occupied = 0
    for i, n in enumerate(q):
        if n:
            occupied |= 1 << i

    entry_mask = 0
    if enemy_bar:
        for i in range(6):
            if p[i] < 2:
                entry_mask |= 1 << i

    total = 0.0
    for x in blots:
        width = min(x, 6)
        near = (occupied >> max(0, x - 6)) & ((1 << width) - 1)
        k = near.bit_count()

        if not enemy_bar:
            probability = 1.0 - ((6 - k) / 6.0) ** 2
            far_count = 0
            if x >= 7:
                width2 = min(6, x - 6)
                far_count = ((occupied >> max(0, x - 12)) &
                             ((1 << width2) - 1)).bit_count()
            indirect = min(0.32, 0.07 * far_count + 0.02 * k)
            probability += (1.0 - probability) * indirect
        else:
            probability = 11.0 / 36.0 if x < 6 else 0.0
            if enemy_bar == 1:
                shot_dice = 0
                for die in range(1, 7):
                    origin = x - die
                    if origin >= 0 and q[origin]:
                        shot_dice |= 1 << (die - 1)
                other = _ENTRY_PROB[entry_mask][shot_dice]
                if 1 <= x < 12:
                    ways = 0
                    for entry in range(1, 7):
                        remaining = x - entry + 1
                        if (entry_mask & (1 << (entry - 1)) and
                                1 <= remaining <= 6):
                            ways += 1
                    other = min(1.0, other + ways / 36.0)
                probability += (1.0 - probability) * other

        total += probability * (0.55 * (24 - x) + delay)

    return 0.85 * total


def _evaluate(board, exact=False):
    """Value to the oriented player who has just completed a turn."""
    p, q, bar, obar, off, ooff = board
    if off >= 15:
        return 1000.0
    if ooff >= 15:
        return -1000.0

    if not _contact(board):
        return 0.55 * (_race_cost(q[::-1]) - _race_cost(p))

    pip = 25 * bar + sum((i + 1) * n for i, n in enumerate(p))
    opip = 25 * obar + sum((24 - i) * n for i, n in enumerate(q))
    rp, rq = q[::-1], p[::-1]

    score = _structure(p, q, bar, obar, off, pip, pip - opip)
    score -= _structure(rp, rq, obar, bar, ooff, opip, opip - pip)

    # Their roll is next: our exposures matter more than their exposures.
    score -= 0.85 * _danger(p, q, obar, exact)
    score += 0.20 * _danger(rp, rq, bar, exact)
    return score


@lru_cache(maxsize=None)
def _bear_steps(position, die):
    highest = next((i for i in range(5, -1, -1) if position[i]), -1)
    if highest < 0:
        return (position,)

    outcomes = set()
    for i, count in enumerate(position):
        if not count:
            continue
        dest = i - die
        if dest < 0 and i != die - 1 and i != highest:
            continue
        after = list(position)
        after[i] -= 1
        if dest >= 0:
            after[dest] += 1
        outcomes.add(tuple(after))
    return tuple(outcomes)


@lru_cache(maxsize=None)
def _bear_time(position):
    if not any(position):
        return 0.0

    expectation = 0.0
    for a, b, weight in _ROLLS:
        outcomes = set()
        for middle in _bear_steps(position, a):
            outcomes.update(_bear_steps(middle, b))
        if a != b:
            for middle in _bear_steps(position, b):
                outcomes.update(_bear_steps(middle, a))
        best = min(_bear_time(after) for after in outcomes)
        expectation += weight * best
    return 1.0 + expectation / 36.0


class _SearchTimeout(Exception):
    pass


def policy(state: dict) -> str:
    started = time.perf_counter()
    deadline = started + 0.87

    board = (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )
    dice = tuple(state["dice"])
    legal = _turn(board, dice)

    if len(legal) == 1:
        return _encode(next(iter(legal.values())))

    for after, action in legal.items():
        if after[4] >= 15:
            return _encode(action)

    # In a pure race the opponent cannot alter our checker placement.
    if not _contact(board):
        if not any(board[0][6:]) and sum(board[0]) <= 4:
            best = min(
                legal,
                key=lambda b: (_bear_time(b[0][:6]), _race_cost(b[0]))
            )
        else:
            best = min(legal, key=lambda b: _race_cost(b[0]))
        return _encode(legal[best])

    cache = {}

    def quick(b):
        value = cache.get(b)
        if value is None:
            value = _evaluate(b, False)
            cache[b] = value
        return value

    ranked = sorted(legal, key=quick, reverse=True)
    finalists = [(b, _evaluate(b, True)) for b in ranked[:14]]
    finalists.sort(key=lambda item: item[1], reverse=True)

    # Preserve multiple strategic alternatives for the opponent-roll search.
    cutoff = finalists[0][1] - 18.0
    finalists = [item for item in finalists if item[1] >= cutoff][:5]
    if len(finalists) == 1:
        return _encode(legal[finalists[0][0]])

    baseline_best = finalists[0][0]
    oriented = [_flip(b) for b, value in finalists]
    totals = [0.0] * len(finalists)
    total_weight = 0
    completed = 0
    evaluations = 0

    # Complete the same roll for every candidate before using its results.
    # Consequently an interrupted search never compares unequal samples.
    for a, b in _SEARCH_ROLLS:
        if time.perf_counter() >= deadline:
            break
        round_values = []
        try:
            for enemy_board in oriented:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout
                replies = _turn(enemy_board, (a, b))
                enemy_best = -float("inf")
                for reply in replies:
                    value = quick(reply)
                    if value > enemy_best:
                        enemy_best = value
                    evaluations += 1
                    if evaluations % 32 == 0:
                        if time.perf_counter() >= deadline:
                            raise _SearchTimeout
                round_values.append(-enemy_best)
        except _SearchTimeout:
            break

        weight = 1 if a == b else 2
        for i, value in enumerate(round_values):
            totals[i] += weight * value
        total_weight += weight
        completed += 1

    if completed < 3:
        return _encode(legal[baseline_best])

    # Retaining a small static component reduces noise from partial roll sets
    # and counters the shallow search's positional horizon effects.
    best_index = max(
        range(len(finalists)),
        key=lambda i: (
            0.82 * totals[i] / total_weight + 0.18 * finalists[i][1],
            finalists[i][1],
        )
    )
    return _encode(legal[finalists[best_index][0]])
