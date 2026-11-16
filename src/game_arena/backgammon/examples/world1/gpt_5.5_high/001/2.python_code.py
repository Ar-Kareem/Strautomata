
import time

# Unordered rolls with exact 36-roll weights.
_ROLLS = []
for _a in range(1, 7):
    for _b in range(_a, 7):
        _ROLLS.append(([_a, _b], (1.0 if _a == _b else 2.0) / 36.0))


def policy(state: dict) -> str:
    """Return a legal compact backgammon move string."""
    start = time.perf_counter()
    deadline = start + 0.82

    try:
        pos = _pos_from_state(state)
        dice = _dice_from_state(state)
        records = _generate_legal_records(pos, dice)

        if not records:
            return "H:P,P"
        if len(records) == 1:
            return records[0][0]

        scored = []
        for action, rpos, used in records:
            val = _evaluate_pos(rpos)
            val += 0.001 * _action_preference(action)
            scored.append((val, action, rpos, used))

        scored.sort(key=lambda x: x[0], reverse=True)
        immediate_best = scored[0][1]

        # Shallow exact opponent-roll lookahead for the best immediate candidates.
        n = len(scored)
        if n > 100:
            topn = 5
        elif n > 45:
            topn = 7
        else:
            topn = 10
        topn = min(topn, n)

        best_action = immediate_best
        best_final = -10**100
        looked = False

        for imm, action, rpos, used in scored[:topn]:
            if time.perf_counter() > deadline:
                break
            exp = _opponent_expectation(rpos, deadline)
            if exp is None:
                break
            looked = True
            final_val = 0.42 * imm + 0.58 * exp + 0.001 * _action_preference(action)
            if final_val > best_final:
                best_final = final_val
                best_action = action

        return best_action if looked else immediate_best

    except Exception:
        # Last-resort safe fallback. In normal arena states the generator above
        # should always succeed and return a legal action.
        try:
            pos = _pos_from_state(state)
            dice = _dice_from_state(state)
            recs = _generate_legal_records(pos, dice)
            if recs:
                return recs[0][0]
        except Exception:
            pass
        return "H:P,P"


def _pos_from_state(state):
    my = _fix_points(state.get("my_pts", [0] * 24))
    opp = _fix_points(state.get("opp_pts", [0] * 24))
    return (
        my,
        opp,
        max(0, int(state.get("my_bar", 0))),
        max(0, int(state.get("opp_bar", 0))),
        max(0, int(state.get("my_off", 0))),
        max(0, int(state.get("opp_off", 0))),
    )


def _fix_points(x):
    y = list(x) if x is not None else []
    if len(y) < 24:
        y += [0] * (24 - len(y))
    y = y[:24]
    out = []
    for v in y:
        iv = int(v)
        out.append(iv if iv > 0 else 0)
    return out


def _dice_from_state(state):
    ds = []
    for x in state.get("dice", []):
        d = int(x)
        if 1 <= d <= 6:
            ds.append(d)
        if len(ds) >= 2:
            break
    return ds


def _all_home(my, my_bar):
    return my_bar == 0 and not any(my[i] for i in range(6, 24))


def _legal_sources(pos, die):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos

    if die < 1 or die > 6:
        return []

    # Bar checkers must enter first.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            return ["B"]
        return []

    sources = []
    home = _all_home(my, my_bar)

    for p in range(24):
        if my[p] <= 0:
            continue

        dest = p - die
        if dest >= 0:
            if opp[dest] < 2:
                sources.append("A" + str(p))
        else:
            # Bearing off: exact die, or oversized die from the highest occupied point.
            if home:
                if die == p + 1:
                    sources.append("A" + str(p))
                elif die > p + 1 and sum(my[p + 1:]) == 0:
                    sources.append("A" + str(p))

    return sources


def _apply_source(pos, source, die):
    if source == "P":
        return pos

    my, opp, my_bar, opp_bar, my_off, opp_off = pos
    my = my[:]
    opp = opp[:]

    if source == "B":
        my_bar -= 1
        dest = 24 - die
    else:
        p = int(source[1:])
        my[p] -= 1
        dest = p - die

    if dest < 0:
        my_off += 1
    else:
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1

    return (my, opp, my_bar, opp_bar, my_off, opp_off)


def _generate_legal_records(pos, dice):
    """Return [(action, resulting_pos, dice_used), ...], filtered by dice rules."""
    dice = [int(d) for d in dice if 1 <= int(d) <= 6]

    if len(dice) == 0:
        return [("H:P,P", pos, 0)]

    if len(dice) == 1:
        d = dice[0]
        srcs = _legal_sources(pos, d)
        if not srcs:
            return [("H:P,P", pos, 0)]
        out = []
        for s in srcs:
            out.append(("H:" + s + ",P", _apply_source(pos, s, d), 1))
        return out

    hi = max(dice[0], dice[1])
    lo = min(dice[0], dice[1])

    orders = [("H", hi, lo)]
    if hi != lo:
        orders.append(("L", lo, hi))

    raw = []

    for order, d1, d2 in orders:
        srcs1 = _legal_sources(pos, d1)
        if not srcs1:
            srcs1 = ["P"]

        for s1 in srcs1:
            pos1 = pos if s1 == "P" else _apply_source(pos, s1, d1)

            srcs2 = _legal_sources(pos1, d2)
            if not srcs2:
                srcs2 = ["P"]

            for s2 in srcs2:
                pos2 = pos1 if s2 == "P" else _apply_source(pos1, s2, d2)
                used = (1 if s1 != "P" else 0) + (1 if s2 != "P" else 0)

                if hi == lo:
                    high_used = used > 0
                    low_used = used > 0
                elif order == "H":
                    high_used = s1 != "P"
                    low_used = s2 != "P"
                else:
                    low_used = s1 != "P"
                    high_used = s2 != "P"

                action = order + ":" + s1 + "," + s2
                raw.append((action, pos2, used, high_used, low_used))

    if not raw:
        return [("H:P,P", pos, 0)]

    max_used = max(r[2] for r in raw)

    if max_used == 0:
        return [("H:P,P", pos, 0)]

    if max_used == 2:
        filt = [r for r in raw if r[2] == 2]
    else:
        one_die = [r for r in raw if r[2] == 1]
        if hi != lo and any(r[3] for r in one_die):
            filt = [r for r in one_die if r[3]]
        else:
            filt = one_die

    seen = set()
    out = []
    for action, rpos, used, hu, lu in filt:
        if action not in seen:
            seen.add(action)
            out.append((action, rpos, used))

    return out if out else [("H:P,P", pos, 0)]


def _pip_counts(pos):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos
    my_pip = my_bar * 25
    opp_pip = opp_bar * 25

    for i in range(24):
        my_pip += my[i] * (i + 1)
        opp_pip += opp[i] * (24 - i)

    return my_pip, opp_pip


def _has_contact(my, opp, my_bar, opp_bar):
    if my_bar > 0 or opp_bar > 0:
        return True

    max_my = -1
    min_opp = 24

    for i in range(24):
        if my[i] > 0:
            max_my = i
        if opp[i] > 0 and i < min_opp:
            min_opp = i

    return max_my > min_opp


def _home_made_count(my):
    return sum(1 for i in range(6) if my[i] >= 2)


def _home_structure_score(my):
    # A made five/six/four point is much stronger than a made ace point.
    weights = [1.5, 2.5, 4.2, 6.6, 9.5, 8.0]
    s = 0.0
    for i in range(6):
        if my[i] >= 2:
            s += weights[i]
    return s


def _structure_score(my, opp, contact, all_home):
    s = 0.0

    if not all_home:
        for p in range(6, 24):
            c = my[p]
            if c < 2:
                continue

            if p == 6:
                b = 10.5
            elif p == 7:
                b = 5.5
            elif 8 <= p <= 11:
                b = 3.0
            elif p == 12:
                b = 5.0
            elif 13 <= p <= 17:
                b = 1.5
            else:
                # Anchors in opponent's home board. Lower index is more advanced.
                anchor_weights = {
                    18: 10.0,
                    19: 8.0,
                    20: 6.0,
                    21: 4.2,
                    22: 3.0,
                    23: 2.0,
                }
                b = anchor_weights.get(p, 0.0)

            s += b if contact else 0.15 * b

    # Prime/consecutive made-point value.
    run = 0
    start = 0
    for p in range(25):
        made = p < 24 and my[p] >= 2
        if made:
            if run == 0:
                start = p
            run += 1
        else:
            if run >= 2:
                end = p - 1
                useful = contact and any(opp[q] > 0 for q in range(0, end))
                mult = 1.65 if useful else 0.25
                s += mult * run * run
            run = 0

    return s


def _stack_penalty(my, all_home):
    pen = 0.0
    for p, c in enumerate(my):
        if c <= 0:
            continue

        if c > 5:
            pen += (c - 5) * 4.0 + (c - 5) * (c - 5)

        if all_home:
            if c > 4:
                pen += (c - 4) * 0.8
        else:
            # Some stacks are natural early-game points; others are inflexible.
            if c > 3 and p not in (5, 6, 12, 23):
                pen += (c - 3) * 1.3

    return pen


def _blot_penalty(my, opp, opp_bar, contact):
    if not contact and opp_bar == 0:
        return 0.0

    pen = 0.0
    board_mult = 0.35 if opp_bar > 0 else 1.0

    for p in range(24):
        if my[p] != 1:
            continue

        loss = 24 - p
        risk = 0.0

        # Opponent checker on bar can hit blots in our home board on entry.
        if opp_bar > 0 and p <= 5:
            risk += 3.2 + min(2, opp_bar - 1) * 1.0

        # Direct shots.
        for d in range(1, 7):
            q = p - d
            if q >= 0 and opp[q] > 0:
                risk += board_mult * (1.4 + 0.35 * min(opp[q], 3))

        # Two-dice indirect shots, approximate but useful for move ordering.
        if opp_bar == 0:
            for a in range(1, 7):
                for b in range(1, 7):
                    q = p - a - b
                    if q >= 0 and opp[q] > 0:
                        inter1 = q + a
                        inter2 = q + b
                        if my[inter1] < 2 or my[inter2] < 2:
                            risk += 0.035

        # Blots backed up by our checkers are a little less costly.
        protect = 0
        for d in range(1, 7):
            q = p + d
            if q < 24 and my[q] > 0:
                protect += min(my[q], 2)
        if protect:
            risk /= (1.0 + 0.08 * protect)

        pen += risk * (2.0 + 0.50 * loss)

    return pen


def _opp_blot_bonus(my, opp, my_bar, contact):
    if not contact and my_bar == 0:
        return 0.0

    bonus = 0.0
    board_mult = 0.35 if my_bar > 0 else 1.0

    for p in range(24):
        if opp[p] != 1:
            continue

        gain = p + 1
        chance = 0.0

        # Our bar entry can hit opponent blots on their home-board points.
        if my_bar > 0 and p >= 18:
            d = 24 - p
            if 1 <= d <= 6:
                chance += 1.8

        # Direct shots from our board checkers.
        for d in range(1, 7):
            q = p + d
            if q < 24 and my[q] > 0:
                chance += board_mult * (1.2 + 0.3 * min(my[q], 3))

        # Indirect shots.
        if my_bar == 0:
            for a in range(1, 7):
                for b in range(1, 7):
                    q = p + a + b
                    if q < 24 and my[q] > 0:
                        inter1 = q - a
                        inter2 = q - b
                        if opp[inter1] < 2 or opp[inter2] < 2:
                            chance += 0.03

        bonus += chance * (1.4 + 0.25 * gain)

    return bonus


def _evaluate_pos(pos):
    my, opp, my_bar, opp_bar, my_off, opp_off = pos

    if my_off >= 15:
        return 100000000.0
    if opp_off >= 15:
        return -100000000.0

    my_pip, opp_pip = _pip_counts(pos)
    contact = _has_contact(my, opp, my_bar, opp_bar)
    all_home = _all_home(my, my_bar)

    if contact:
        score = (opp_pip - my_pip) * 1.08
        score += (my_off - opp_off) * 120.0
    else:
        # In a pure race, pip count dominates.
        score = (opp_pip - my_pip) * 2.0
        score += (my_off - opp_off) * 140.0

    home_count = _home_made_count(my)
    home_score = _home_structure_score(my)

    score += opp_bar * (42.0 + 9.0 * home_count)

    opp_entry_blocks = sum(1 for i in range(18, 24) if opp[i] >= 2)
    score -= my_bar * (70.0 + 7.0 * opp_entry_blocks)

    if contact:
        score += home_score
        if opp_bar > 0:
            score += 0.85 * home_score + 10.0 * home_count
        score += _structure_score(my, opp, contact, all_home)
        score -= _blot_penalty(my, opp, opp_bar, contact)
        score += 0.55 * _opp_blot_bonus(my, opp, my_bar, contact)
    else:
        score += 0.15 * home_score
        score += _structure_score(my, opp, contact, all_home)

    score -= _stack_penalty(my, all_home)

    if all_home:
        score += 15.0
        highest = -1
        for i in range(6):
            if my[i] > 0:
                highest = i
        if highest >= 0:
            score -= 0.35 * highest

    return score


def _flip_pos(pos):
    """Convert absolute board to opponent perspective, where mover again goes 23->0."""
    my, opp, my_bar, opp_bar, my_off, opp_off = pos
    return (
        [opp[23 - i] for i in range(24)],
        [my[23 - i] for i in range(24)],
        opp_bar,
        my_bar,
        opp_off,
        my_off,
    )


def _best_side_value(pos, dice):
    recs = _generate_legal_records(pos, dice)
    best = -10**100
    for action, rpos, used in recs:
        v = _evaluate_pos(rpos)
        if v > best:
            best = v
    return best


def _opponent_expectation(pos, deadline):
    """Expected value for us after opponent rolls and chooses its best reply."""
    opp_pos = _flip_pos(pos)
    total = 0.0

    for dice, wt in _ROLLS:
        if time.perf_counter() > deadline:
            return None
        # Opponent maximizes its own evaluation; from our perspective negate it.
        total += wt * (-_best_side_value(opp_pos, dice))

    return total


def _action_preference(action):
    # Tiny deterministic tie-breaker: prefer actually moving before passing.
    try:
        order, body = action.split(":")
        a, b = body.split(",")
        pref = 0.0
        if a != "P":
            pref += 2.0
        if b != "P":
            pref += 1.0
        if order == "H":
            pref += 0.1
        return pref
    except Exception:
        return 0.0
