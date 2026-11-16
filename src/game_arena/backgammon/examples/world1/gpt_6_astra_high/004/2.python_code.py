
import math
import time
from functools import lru_cache

BAR = 24
PASS = 25

_HOME_WEIGHTS = (1.4, 2.4, 3.5, 4.7, 5.7, 4.6)
_OUTER_WEIGHTS = (4.5, 3.6, 2.5, 1.7, 1.0, 0.7)
_ANCHOR_WEIGHTS = (6.2, 7.4, 7.0, 5.2, 3.8, 2.5)
_PRIME_WEIGHTS = (0.0, 0.0, 1.5, 4.5, 10.0, 22.0, 40.0)
_DIRECT_PROB = tuple((12 * k - k * k) / 36.0 for k in range(7))

_DIE_MASK = [0] * 7
_PAIR_MASK = [[0] * 7 for _ in range(7)]
for _a in range(1, 7):
    for _b in range(1, 7):
        _bit = 1 << ((_a - 1) * 6 + _b - 1)
        _rev = 1 << ((_b - 1) * 6 + _a - 1)
        _DIE_MASK[_a] |= _bit
        _DIE_MASK[_b] |= _bit
        _PAIR_MASK[_a][_b] = _bit | _rev

_ROLLS = (
    (6, 1), (5, 2), (4, 3), (6, 6), (1, 1),
    (5, 4), (6, 3), (2, 2), (4, 1), (5, 5),
    (3, 2), (6, 4), (4, 4), (3, 1), (6, 2),
    (5, 1), (3, 3), (5, 3), (6, 5), (4, 2),
    (2, 1),
)


def _single_moves(p, die):
    m, o, mb, ob, mo, oo = p
    if mb:
        target = 24 - die
        return [(BAR, target)] if o[target] < 2 else []

    highest = -1
    for i in range(23, -1, -1):
        if m[i]:
            highest = i
            break

    result = []
    home = highest <= 5
    for i, count in enumerate(m):
        if not count:
            continue
        target = i - die
        if target >= 0:
            if o[target] < 2:
                result.append((i, target))
        elif home and (target == -1 or i == highest):
            result.append((i, -1))
    return result


def _step(p, move):
    m, o, mb, ob, mo, oo = p
    source, target = move
    a = list(m)

    if source == BAR:
        mb -= 1
    else:
        a[source] -= 1

    if target < 0:
        mo += 1
    else:
        a[target] += 1
        if o[target] == 1:
            b = list(o)
            b[target] = 0
            o = tuple(b)
            ob += 1

    return tuple(a), o, mb, ob, mo, oo


def _legal_turns(p, dice):
    """Return (order, first source, second source, resulting position)."""
    if not dice:
        return [("H", PASS, PASS, p)]

    if len(dice) == 1:
        moves = _single_moves(p, dice[0])
        if not moves:
            return [("H", PASS, PASS, p)]
        return [("H", mv[0], PASS, _step(p, mv)) for mv in moves]

    high, low = max(dice), min(dice)
    orders = [("H", high, low)]
    if high != low:
        orders.append(("L", low, high))

    two = []
    one = []
    for order, first_die, second_die in orders:
        for mv1 in _single_moves(p, first_die):
            p1 = _step(p, mv1)
            seconds = _single_moves(p1, second_die)
            if seconds:
                for mv2 in seconds:
                    two.append((order, mv1[0], mv2[0], _step(p1, mv2)))
            else:
                one.append((order, mv1[0], PASS, p1))

    if two:
        return two
    if one:
        high_plays = [x for x in one if x[0] == "H"]
        return high_plays if high_plays else one
    return [("H", PASS, PASS, p)]


def _encode(turn):
    def token(source):
        if source == BAR:
            return "B"
        if source == PASS:
            return "P"
        return "A" + str(source)

    return turn[0] + ":" + token(turn[1]) + "," + token(turn[2])


def _reverse(p):
    m, o, mb, ob, mo, oo = p
    return o[::-1], m[::-1], ob, mb, oo, mo


def _is_race(p):
    m, o, mb, ob, mo, oo = p
    if mb or ob:
        return False
    last = next((i for i in range(23, -1, -1) if m[i]), -1)
    first_enemy = next((i for i in range(24) if o[i]), 24)
    return last < first_enemy


def _race_cost(m, bar=0):
    n = sum(m) + bar
    if not n:
        return 0.0
    pip = 25 * bar + sum((i + 1) * v for i, v in enumerate(m))
    waste = (
        2.5 * max(0, m[0] - 1)
        + 1.7 * max(0, m[1] - 1)
        + 0.9 * max(0, m[2] - 2)
        + 0.4 * max(0, m[3] - 3)
    )
    return max(pip + 7.0 + waste, 3.5 * n + 3.5)


def _attack_probability(m, o, enemy_bar, target):
    """Roll probability of an available direct or two-step hit."""
    mask = 0

    if enemy_bar >= 2:
        return 11.0 / 36.0 if target < 6 else 0.0

    if enemy_bar == 1:
        if target < 6:
            mask |= _DIE_MASK[target + 1]

        for entry_die in range(1, 7):
            entry = entry_die - 1
            if m[entry] >= 2:
                continue

            second = target - entry
            if 1 <= second <= 6:
                mask |= _PAIR_MASK[entry_die][second]

            for second in range(1, min(6, target) + 1):
                if o[target - second]:
                    mask |= _PAIR_MASK[entry_die][second]

        return mask.bit_count() / 36.0

    for die in range(1, min(6, target) + 1):
        if o[target - die]:
            mask |= _DIE_MASK[die]

    for distance in range(2, min(12, target) + 1):
        source = target - distance
        if not o[source]:
            continue
        for first in range(max(1, distance - 6), min(6, distance - 1) + 1):
            if m[source + first] < 2:
                mask |= _PAIR_MASK[first][distance - first]

    return mask.bit_count() / 36.0


def _prime_bonus(length, trapped, start):
    if length < 2 or not trapped:
        return 0.0
    value = _PRIME_WEIGHTS[min(length, 6)]
    if length > 6:
        value += 2.0 * (length - 6)
    value *= min(1.15, 0.55 + 0.20 * trapped)
    if start >= 12:
        value *= 0.65
    return value


def _side_features(m, o, bar, enemy_bar, off, enemy_home, detailed):
    pip = 25 * bar
    score = 1.3 * off
    risk = 0.0

    enemy_occ = 0
    enemy_blocks = 0
    for i, n in enumerate(o):
        if n:
            enemy_occ |= 1 << i
        if n >= 2:
            enemy_blocks |= 1 << i

    own_home = sum(m[i] >= 2 for i in range(6))
    entry_delay = 2.0 + 4.0 * enemy_home / (6.5 - enemy_home)
    score -= bar * entry_delay

    behind = enemy_bar
    run = 0
    run_start = 0
    run_trapped = 0
    deep_count = 0

    for i, n in enumerate(m):
        pip += (i + 1) * n

        if n >= 2:
            if not run:
                run_start = i
                run_trapped = behind
            run += 1

            if i < 6:
                score += _HOME_WEIGHTS[i]
            elif i < 12:
                if behind:
                    score += _OUTER_WEIGHTS[i - 6] * min(1.15, 0.7 + 0.15 * behind)
            elif i < 18:
                if behind:
                    score += 0.7
            else:
                score += _ANCHOR_WEIGHTS[i - 18]

            if n == 3 and 4 <= i <= 11:
                score += 0.3
        else:
            if run:
                score += _prime_bonus(run, run_trapped, run_start)
                run = 0

        if n:
            excess = max(0, n - 3)
            score -= (0.22 if i < 6 else 0.34) * excess * excess

            width = min(6, i)
            lower_mask = (1 << width) - 1
            shift = max(0, i - 6)
            blocked = ((enemy_blocks >> shift) & lower_mask).bit_count()
            score -= 0.48 * min(n, 2) * blocked

            if i >= 18:
                deep_count += n
                score -= n * (0.7 + 0.15 * (i - 17))
                if n == 1 and enemy_home >= 3:
                    score -= 1.0
            elif 6 <= i <= 11 and own_home < 4:
                score += 0.25 * min(n, 3)

            if n == 1:
                if detailed or enemy_bar:
                    probability = _attack_probability(m, o, enemy_bar, i)
                else:
                    direct = ((enemy_occ >> shift) & lower_mask).bit_count()
                    probability = _DIRECT_PROB[direct]

                risk += probability * (24 - i + entry_delay + 1.0)

        behind += o[i]

    if run:
        score += _prime_bonus(run, run_trapped, run_start)

    score -= 1.8 * max(0, deep_count - 2)
    score -= 0.55 * max(0, m[0] - 1)
    score -= 0.25 * max(0, m[1] - 2)
    return score - pip, risk, pip


def _equity(advantage, scale):
    # The small rational term preserves distinctions in very lopsided games.
    return (
        99.0 * math.erf(advantage / (1.4142135623730951 * scale))
        + advantage / (abs(advantage) + scale)
    )


def _evaluate(p, detailed=False):
    """Value to the player who has just completed the encoded turn."""
    m, o, mb, ob, mo, oo = p
    if not mb and not any(m):
        return 100.0
    if not ob and not any(o):
        return -100.0

    if _is_race(p):
        my_pip = sum((i + 1) * n for i, n in enumerate(m))
        enemy_pip = sum((24 - i) * n for i, n in enumerate(o))
        advantage = _race_cost(o[::-1]) - _race_cost(m) - 3.5
        return _equity(advantage, 4.0 + 0.055 * (my_pip + enemy_pip))

    my_home = sum(m[i] >= 2 for i in range(6))
    enemy_home = sum(o[i] >= 2 for i in range(18, 24))

    mine, my_risk, my_pip = _side_features(
        m, o, mb, ob, mo, enemy_home, detailed
    )
    theirs, enemy_risk, enemy_pip = _side_features(
        o[::-1], m[::-1], ob, mb, oo, my_home, detailed
    )

    advantage = mine - theirs - 0.90 * my_risk + 0.30 * enemy_risk - 3.0
    return _equity(advantage, 10.0 + 0.060 * (my_pip + enemy_pip))


@lru_cache(maxsize=20000)
def _home_next(code, die):
    """Legal single-die bear-off successors, using six packed counters."""
    if code == 0:
        return (0,)

    result = []
    for i in range(die, 6):
        if (code >> (4 * i)) & 15:
            result.append(code - (1 << (4 * i)) + (1 << (4 * (i - die))))

    exact = die - 1
    if (code >> (4 * exact)) & 15:
        result.append(code - (1 << (4 * exact)))
    else:
        highest = (code.bit_length() - 1) // 4
        if highest < exact:
            result.append(code - (1 << (4 * highest)))

    return tuple(result)


@lru_cache(maxsize=4000)
def _bearoff_stats(code):
    """
    Exact expected turns under expectation-optimal two-die play.
    Also return survival probabilities P(turns remaining > k).
    """
    if code == 0:
        return 0.0, ()

    expectation = 1.0
    survival = [1.0]

    for d1 in range(1, 7):
        for d2 in range(d1, 7):
            best_e = float("inf")
            best_s = ()

            for c1 in _home_next(code, d1):
                for c2 in _home_next(c1, d2):
                    e, s = _bearoff_stats(c2)
                    if e < best_e:
                        best_e, best_s = e, s

            if d1 != d2:
                for c1 in _home_next(code, d2):
                    for c2 in _home_next(c1, d1):
                        e, s = _bearoff_stats(c2)
                        if e < best_e:
                            best_e, best_s = e, s

            weight = (1.0 if d1 == d2 else 2.0) / 36.0
            expectation += weight * best_e

            required = len(best_s) + 1
            if len(survival) < required:
                survival.extend([0.0] * (required - len(survival)))
            for k, probability in enumerate(best_s):
                survival[k + 1] += weight * probability

    return expectation, tuple(survival)


def _home_code(points):
    return sum(points[i] << (4 * i) for i in range(6))


def _race_choice(p, turns):
    m, o, mb, ob, mo, oo = p
    small_home = not any(m[6:]) and sum(m) <= 6

    if not small_home:
        return min(
            turns,
            key=lambda t: (
                _race_cost(t[3][0]),
                -t[3][4],
                sum(i * i * n for i, n in enumerate(t[3][0])),
            ),
        )

    enemy = o[::-1]
    enemy_small = not any(enemy[6:]) and sum(enemy) <= 6
    enemy_stats = _bearoff_stats(_home_code(enemy)) if enemy_small else None

    best = turns[0]
    best_value = -float("inf")
    for turn in turns:
        code = _home_code(turn[3][0])
        if code == 0:
            return turn
        expected, survival = _bearoff_stats(code)

        if enemy_stats is None:
            value = -expected
        else:
            enemy_survival = enemy_stats[1]
            win_probability = 0.0
            for k in range(1, len(survival) + 1):
                before = survival[k - 1]
                after = survival[k] if k < len(survival) else 0.0
                enemy_alive = (
                    enemy_survival[k] if k < len(enemy_survival) else 0.0
                )
                win_probability += (before - after) * enemy_alive
            value = win_probability - 0.00001 * expected

        if value > best_value:
            best_value, best = value, turn
    return best


class _OutOfTime(Exception):
    pass


def _reply_value(p, roll, deadline):
    opponent = _reverse(p)
    replies = _legal_turns(opponent, roll)
    seen = set()
    top = []

    for index, reply in enumerate(replies):
        if index % 16 == 0 and time.perf_counter() >= deadline:
            raise _OutOfTime

        q = reply[3]
        if q in seen:
            continue
        seen.add(q)

        value = _evaluate(q, False)
        if len(top) < 3:
            top.append((value, q))
            top.sort(key=lambda x: x[0], reverse=True)
        elif value > top[-1][0]:
            top[-1] = (value, q)
            top.sort(key=lambda x: x[0], reverse=True)

    if time.perf_counter() >= deadline:
        raise _OutOfTime

    # Recheck the strongest replies with two-die hitting routes included.
    best_opponent = max(_evaluate(q, True) for _, q in top)
    return -best_opponent


def _choose(p, turns, start):
    for turn in turns:
        q = turn[3]
        if not q[2] and not any(q[0]):
            return turn

    if _is_race(p):
        return _race_choice(p, turns)

    ranked = [(_evaluate(turn[3], True), turn) for turn in turns]
    ranked.sort(key=lambda item: item[0], reverse=True)
    shortlist = ranked[:6]
    best = shortlist[0][1]

    if len(shortlist) == 1:
        return best

    deadline = start + 0.86
    totals = [0.0] * len(shortlist)
    total_weight = 0.0

    # Every completed sampling round uses the same roll for every candidate.
    # An interrupted round is discarded, keeping comparisons balanced.
    for roll in _ROLLS:
        if time.perf_counter() >= deadline:
            break

        values = []
        try:
            for static_value, turn in shortlist:
                values.append(_reply_value(turn[3], roll, deadline))
        except _OutOfTime:
            break

        weight = 1.0 if roll[0] == roll[1] else 2.0
        total_weight += weight
        for i, value in enumerate(values):
            totals[i] += weight * value

    if total_weight:
        search_weight = 0.78 * min(1.0, total_weight / 24.0)
        best_index = max(
            range(len(shortlist)),
            key=lambda i: (
                (1.0 - search_weight) * shortlist[i][0]
                + search_weight * totals[i] / total_weight
            ),
        )
        best = shortlist[best_index][1]

    return best


def policy(state: dict) -> str:
    start = time.perf_counter()

    p = (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["opp_bar"]),
        int(state["my_off"]),
        int(state["opp_off"]),
    )
    dice = tuple(int(d) for d in state["dice"])
    generated = _legal_turns(p, dice)

    # Different die orders often reach an identical position.
    unique = {}
    for turn in generated:
        if turn[3] not in unique:
            unique[turn[3]] = turn
    turns = list(unique.values())

    fallback = turns[0]
    if len(turns) == 1:
        return _encode(fallback)

    try:
        selected = _choose(p, turns, start)
    except Exception:
        # Evaluation failure must never turn a legal action into a forfeit.
        selected = fallback

    return _encode(selected)
