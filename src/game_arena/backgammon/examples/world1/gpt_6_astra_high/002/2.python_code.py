
import math
import time
from functools import lru_cache


# The action interface uses at most two dice, including for doubles.
_PASS = -2
_BAR = -1
_CLOCK = time.perf_counter


class _TimeUp(Exception):
    pass


# Bit masks over the 36 equally likely ordered rolls.
_DIE_MASK = [0] * 7
_PAIR_MASK = [[0] * 7 for _ in range(7)]
for _a in range(1, 7):
    for _b in range(1, 7):
        _bit = 1 << ((_a - 1) * 6 + _b - 1)
        _DIE_MASK[_a] |= _bit
        _DIE_MASK[_b] |= _bit
        _PAIR_MASK[_a][_b] |= _bit
        _PAIR_MASK[_b][_a] |= _bit

_DIRECT = []
_INDIRECT = []
for _i in range(24):
    _DIRECT.append([
        (_i - d, _DIE_MASK[d], d)
        for d in range(1, 7) if _i >= d
    ])
    _INDIRECT.append([
        (_i - a - b, _i - b, _i - a, _PAIR_MASK[a][b])
        for a in range(1, 7)
        for b in range(a, 7)
        if _i >= a + b
    ])

_HOME_VALUE = (1.2, 2.4, 3.8, 5.0, 5.8, 4.8)
_POINT_VALUE = (
    0, 0, 0, 0, 0, 0,
    2.8, 2.4, 1.8, 1.3, 1.0, 0.8,
    0.9, 0.8, 0.8, 1.0, 1.2, 1.5,
    5.0, 6.0, 4.5, 3.5, 2.5, 2.0
)
_STACK_COST = tuple(
    0.65 * max(0, n - 3) ** 1.35 for n in range(31)
)
_ESCAPE_COST = (0.0, 0.10, 0.30, 0.65, 1.2, 2.1, 3.8)
_PRIME_VALUE = (0.0, 0.0, 1.2, 4.4, 10.0, 20.0, 34.0)

# An interleaved roll order gives reasonably balanced partial searches.
_ROLLS = (
    (1, 2), (3, 4), (5, 6), (1, 6), (2, 5),
    (3, 3), (1, 4), (2, 3), (3, 6), (4, 5),
    (5, 5), (2, 6), (1, 5), (2, 4), (3, 5),
    (1, 1), (1, 3), (4, 6), (2, 2), (4, 4), (6, 6)
)


def _legal_sources(pos, die):
    m, o, mb, ob, mf, of = pos
    if mb:
        return [_BAR] if o[24 - die] < 2 else []

    highest = -1
    for i in range(23, -1, -1):
        if m[i]:
            highest = i
            break

    if highest < 0:
        return []

    home = highest < 6
    result = []
    for i, count in enumerate(m):
        if not count:
            continue
        dest = i - die
        if dest >= 0:
            if o[dest] < 2:
                result.append(i)
        elif home and (i == die - 1 or i == highest):
            result.append(i)
    return result


def _apply(pos, src, die):
    if src == _PASS:
        return pos

    m, o, mb, ob, mf, of = pos
    nm = list(m)
    if src == _BAR:
        mb -= 1
        dest = 24 - die
    else:
        nm[src] -= 1
        dest = src - die

    if dest < 0:
        mf += 1
    else:
        if o[dest] == 1:
            no = list(o)
            no[dest] = 0
            o = tuple(no)
            ob += 1
        nm[dest] += 1

    return tuple(nm), o, mb, ob, mf, of


def _successors(pos, dice):
    """Return distinct legal final positions and their action encodings."""
    if not dice:
        return {pos: ("H", _PASS, _PASS)}

    hi, lo = max(dice), min(dice)
    if len(dice) == 1:
        orders = ((hi, None, "H"),)
    elif hi == lo:
        orders = ((hi, lo, "H"),)
    else:
        orders = ((hi, lo, "H"), (lo, hi, "L"))

    result = {}
    best_requirement = (-1, -1)

    for d1, d2, order in orders:
        first = _legal_sources(pos, d1)
        if not first:
            first = (_PASS,)

        for s1 in first:
            middle = _apply(pos, s1, d1)
            second = _legal_sources(middle, d2) if d2 is not None else []
            if not second:
                second = (_PASS,)

            for s2 in second:
                end = _apply(middle, s2, d2)
                used = int(s1 != _PASS) + int(s2 != _PASS)
                high_used = (
                    (s1 != _PASS and d1 == hi) or
                    (s2 != _PASS and d2 == hi)
                )
                requirement = (used, int(high_used) if used == 1 else 0)

                if requirement < best_requirement:
                    continue
                if requirement > best_requirement:
                    best_requirement = requirement
                    result.clear()

                action = (order, s1, s2)
                old = result.get(end)
                # Prefer the natural encoding with the played move first.
                if old is None or (old[1] == _PASS and s1 != _PASS):
                    result[end] = action

    return result


def _format_action(action):
    order, first, second = action

    def token(src):
        if src == _PASS:
            return "P"
        if src == _BAR:
            return "B"
        return "A" + str(src)

    return order + ":" + token(first) + "," + token(second)


def _flip(pos):
    m, o, mb, ob, mf, of = pos
    return o[::-1], m[::-1], ob, mb, of, mf


def _is_race(pos):
    m, o, mb, ob, mf, of = pos
    if mb or ob:
        return False
    last_m = next((i for i in range(23, -1, -1) if m[i]), -1)
    first_o = next((i for i in range(24) if o[i]), 24)
    return last_m < first_o


def _race_pips(p):
    pip = sum((i + 1) * n for i, n in enumerate(p))
    count = sum(p)
    waste = (
        2.5 * max(0, p[0] - 1)
        + 1.7 * max(0, p[1] - 1)
        + 1.0 * max(0, p[2] - 3)
        + 0.4 * max(0, p[3] - 4)
    )
    if count >= 6:
        waste += 0.65 * sum(p[i] == 0 for i in (3, 4, 5))
    for i in range(6, 24):
        n = p[i]
        if n:
            waste += 0.16 * n * (i // 6)
            waste += 0.14 * max(0, n - 3) ** 2
    waste += 0.10 * max(0, p[5] - 5) ** 2
    return pip + waste + 0.15 * count


def _bar_cost(home_points):
    k = home_points
    return 5.0 + k + 0.8 * k * k / (6.5 - k)


def _shot_risk(m, o, attacker_bar, entry_cost):
    """Expected blot loss, using direct and legal two-step hitting paths."""
    risk = 0.0
    open_entries = None
    if attacker_bar == 1:
        open_entries = [d for d in range(1, 7) if m[d - 1] < 2]

    for i, n in enumerate(m):
        if n != 1:
            continue

        mask = 0
        if attacker_bar:
            if i < 6:
                mask |= _DIE_MASK[i + 1]

            if attacker_bar == 1:
                # Enter one checker, then hit with a checker already in play.
                for j, direct_mask, d in _DIRECT[i]:
                    if o[j]:
                        for entry in open_entries:
                            mask |= _PAIR_MASK[d][entry]

                # Enter and hit with that same checker.
                total = i + 1
                if 2 <= total <= 12:
                    for a in range(1, 7):
                        b = total - a
                        if a <= b <= 6:
                            if m[a - 1] < 2 or m[b - 1] < 2:
                                mask |= _PAIR_MASK[a][b]
        else:
            for j, direct_mask, d in _DIRECT[i]:
                if o[j]:
                    mask |= direct_mask
            for j, mid1, mid2, pair_mask in _INDIRECT[i]:
                if o[j] and (m[mid1] < 2 or m[mid2] < 2):
                    mask |= pair_mask

        if mask:
            loss = 0.65 * (24 - i) + entry_cost
            risk += mask.bit_count() * loss / 36.0

    return risk


def _prime_bonus(length, trapped, start, gap):
    if length < 2 or trapped <= 0:
        return 0.0
    value = _PRIME_VALUE[min(length, 6)]
    if length > 6:
        value += 2.0 * (length - 6)
    value *= 0.65 + 0.18 * min(trapped, 4)
    if start >= 12:
        value *= 0.55
    if gap > 7:
        value *= 0.75
    return value


def _features(p, q, bar, enemy_bar, off, enemy_home):
    pip = 25 * bar
    value = 1.5 * off - bar * _bar_cost(enemy_home)
    if bar > 1:
        value -= 2.0 * (bar - 1)

    attacking = enemy_bar > 0 or any(q[:12])
    home_factor = 1.0 if attacking else 0.60

    behind = enemy_bar
    last_enemy = -1 if enemy_bar else -100
    run = 0
    trapped = 0
    start = 0
    gap = 0

    for i in range(24):
        n = p[i]
        if n:
            pip += (i + 1) * n
            if i == 0:
                value -= 0.65 * n
            elif i == 1:
                value -= 0.30 * n

            if n >= 2:
                if i < 6:
                    value += _HOME_VALUE[i] * home_factor
                elif i < 18:
                    value += _POINT_VALUE[i] * (1.0 if behind else 0.25)
                elif behind:
                    value += _POINT_VALUE[i] * (0.55 + 0.10 * enemy_home)

                value -= _STACK_COST[min(n, 30)]
                if i < 2 and n > 2:
                    value -= (1.2 if i == 0 else 0.65) * (n - 2)

            if i >= 18 and enemy_home >= 2:
                blocked = 0
                for d in range(1, 7):
                    if q[i - d] >= 2:
                        blocked += 1
                value -= min(n, 3) * _ESCAPE_COST[blocked]

        if n >= 2:
            if run == 0:
                start = i
                trapped = behind
                gap = i - last_enemy
            run += 1
        else:
            if run:
                value += _prime_bonus(run, trapped, start, gap)
                run = 0

        if q[i]:
            behind += q[i]
            last_enemy = i

    if run:
        value += _prime_bonus(run, trapped, start, gap)

    return value - 0.65 * pip


def _evaluate(pos):
    m, o, mb, ob, mf, of = pos
    if mf >= 15:
        return 1000.0
    if of >= 15:
        return -1000.0

    ro = o[::-1]
    if _is_race(pos):
        return (
            0.65 * (_race_pips(ro) - _race_pips(m))
            + 1.5 * (mf - of)
        )

    rm = m[::-1]
    mh = sum(n >= 2 for n in m[:6])
    oh = sum(n >= 2 for n in ro[:6])

    value = _features(m, o, mb, ob, mf, oh)
    value -= _features(ro, rm, ob, mb, of, mh)

    # This is an after-move evaluation: the opponent acts next.
    value -= _shot_risk(m, o, ob, _bar_cost(oh))
    value += 0.22 * _shot_risk(ro, rm, mb, _bar_cost(mh))
    return value


_BEAR_DEADLINE = 0.0
_BEAR_CALLS = 0


@lru_cache(maxsize=120000)
def _bear_dice(t):
    """Optimal expected remaining independent die plays in a home board."""
    global _BEAR_CALLS
    _BEAR_CALLS += 1
    if (_BEAR_CALLS & 255) == 0 and _CLOCK() >= _BEAR_DEADLINE:
        raise _TimeUp

    highest = -1
    for i in range(5, -1, -1):
        if t[i]:
            highest = i
            break
    if highest < 0:
        return 0.0

    total = 0.0
    for die in range(1, 7):
        best = float("inf")
        for i in range(highest + 1):
            if not t[i]:
                continue
            dest = i - die
            if dest < 0 and i != die - 1 and i != highest:
                continue

            child = list(t)
            child[i] -= 1
            if dest >= 0:
                child[dest] += 1
            value = _bear_dice(tuple(child))
            if value < best:
                best = value
        total += best

    return 1.0 + total / 6.0


def _choose_race(pos, successors, deadline):
    global _BEAR_DEADLINE
    m = pos[0]

    fallback = min(
        successors,
        key=lambda p: (_race_pips(p[0]), -p[4], sum(p[0][6:]))
    )

    # Small and moderately sized bear-offs can be solved cheaply.
    if (
        not any(m[6:])
        and sum(m) <= 12
        and sum((i + 1) * n for i, n in enumerate(m[:6])) <= 55
    ):
        _BEAR_DEADLINE = deadline
        try:
            values = {}
            for child in successors:
                values[child] = _bear_dice(child[0][:6])
            return min(
                successors,
                key=lambda p: (values[p], _race_pips(p[0]), -p[4])
            )
        except _TimeUp:
            pass

    return fallback


def policy(state: dict) -> str:
    started = _CLOCK()
    deadline = started + 0.87

    dice = tuple(state["dice"])
    if not dice:
        return "H:P,P"

    pos = (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )

    successors = _successors(pos, dice)
    if not successors:
        # Defensive fallback; valid game states always produce a successor.
        return "H:P,P"

    if len(successors) == 1:
        return _format_action(next(iter(successors.values())))

    for child, action in successors.items():
        if child[4] >= 15:
            return _format_action(action)

    if _is_race(pos):
        chosen = _choose_race(pos, successors, deadline)
        return _format_action(successors[chosen])

    cache = {}

    def evaluate(p):
        value = cache.get(p)
        if value is None:
            value = _evaluate(p)
            cache[p] = value
        return value

    ranked = sorted(
        ((evaluate(child), child) for child in successors),
        key=lambda item: item[0],
        reverse=True
    )
    best_static = ranked[0][0]
    candidates = [
        item for item in ranked[:6]
        if item[0] >= best_static - 12.0
    ]

    if len(candidates) == 1 or _CLOCK() >= deadline:
        return _format_action(successors[ranked[0][1]])

    totals = [0.0] * len(candidates)
    completed_weight = 0
    reflected = [_flip(child) for score, child in candidates]

    # Commit only complete roll rounds, so a timeout never gives one
    # candidate an unfairly different set of sampled opponent rolls.
    try:
        for roll in _ROLLS:
            if _CLOCK() >= deadline:
                break

            round_values = []
            for opponent_pos in reflected:
                if _CLOCK() >= deadline:
                    raise _TimeUp

                replies = _successors(opponent_pos, roll)
                opponent_best = -float("inf")
                for j, reply in enumerate(replies):
                    if (j & 15) == 0 and _CLOCK() >= deadline:
                        raise _TimeUp
                    value = evaluate(reply)
                    if value > opponent_best:
                        opponent_best = value
                    if opponent_best >= 1000.0:
                        break
                round_values.append(-opponent_best)

            weight = 1 if roll[0] == roll[1] else 2
            for i, value in enumerate(round_values):
                totals[i] += weight * value
            completed_weight += weight
    except _TimeUp:
        pass

    if completed_weight:
        fraction = completed_weight / 36.0
        blend = min(0.85, 0.20 + 0.65 * math.sqrt(fraction))
        best_index = max(
            range(len(candidates)),
            key=lambda i: (
                (1.0 - blend) * candidates[i][0]
                + blend * totals[i] / completed_weight
            )
        )
        chosen = candidates[best_index][1]
    else:
        chosen = ranked[0][1]

    return _format_action(successors[chosen])
