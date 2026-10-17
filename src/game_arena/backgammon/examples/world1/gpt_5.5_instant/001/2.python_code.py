
# Backgammon policy for the arena API.
# Implements: policy(state: dict) -> str

from functools import lru_cache
import math
import random

def _dest_from(src, die):
    """Our checkers move from 23 down to 0. Bar enters at 24-die."""
    if src == -1:  # bar
        return 24 - die
    return src - die

def _all_in_home(my_pts, my_bar):
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True

def _can_bear_off_from(my_pts, src, die):
    """Assumes all in home and src in 0..5."""
    dest = src - die
    if dest < 0:
        # Exact bearoff always allowed. Overshoot allowed only from highest occupied point.
        if dest == -1:
            return True
        for j in range(src + 1, 6):
            if my_pts[j] > 0:
                return False
        return True
    return False

def _legal_single_moves(pos, die):
    """
    Returns list of from tokens internally:
      -1 = bar, 0..23 = board point.
    """
    my_pts, opp_pts, my_bar, my_off = pos
    moves = []

    if my_bar > 0:
        d = _dest_from(-1, die)
        if 0 <= d <= 23 and opp_pts[d] < 2:
            moves.append(-1)
        return moves

    home = _all_in_home(my_pts, my_bar)

    for src in range(24):
        if my_pts[src] <= 0:
            continue
        dest = _dest_from(src, die)

        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append(src)
        else:
            if home and src <= 5 and _can_bear_off_from(my_pts, src, die):
                moves.append(src)

    return moves

def _apply_single(pos, src, die):
    my_pts, opp_pts, my_bar, my_off = pos
    my_pts = list(my_pts)
    opp_pts = list(opp_pts)
    my_bar = int(my_bar)
    my_off = int(my_off)

    if src == -1:
        my_bar -= 1
    else:
        my_pts[src] -= 1

    dest = _dest_from(src, die)

    if dest < 0:
        my_off += 1
    else:
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            # Opponent bar is not needed for our future legal generation except evaluation.
            # It is tracked separately outside in simulation wrapper.
            hit = 1
        else:
            hit = 0
        my_pts[dest] += 1
        return (my_pts, opp_pts, my_bar, my_off), hit

    return (my_pts, opp_pts, my_bar, my_off), 0

def _token(src):
    if src == -1:
        return "B"
    if src is None:
        return "P"
    return "A%d" % src

def _simulate_action(state, order_char, first_die, second_die, first_src, second_src):
    my_pts = list(state["my_pts"])
    opp_pts = list(state["opp_pts"])
    my_bar = int(state["my_bar"])
    my_off = int(state["my_off"])
    opp_bar = int(state.get("opp_bar", 0))

    pos = (my_pts, opp_pts, my_bar, my_off)
    hits = 0

    if first_src is not None:
        pos, h = _apply_single(pos, first_src, first_die)
        hits += h
        opp_bar += h

    if second_src is not None:
        pos, h = _apply_single(pos, second_src, second_die)
        hits += h
        opp_bar += h

    return {
        "my_pts": pos[0],
        "opp_pts": pos[1],
        "my_bar": pos[2],
        "my_off": pos[3],
        "opp_bar": opp_bar,
        "opp_off": int(state.get("opp_off", 0)),
        "hits": hits,
        "move_count": (1 if first_src is not None else 0) + (1 if second_src is not None else 0),
    }

def _generate_for_order(state, order_char, dice_order):
    d1, d2 = dice_order
    base = (
        list(state["my_pts"]),
        list(state["opp_pts"]),
        int(state["my_bar"]),
        int(state["my_off"]),
    )

    firsts = _legal_single_moves(base, d1)

    actions = []
    if firsts:
        for s1 in firsts:
            pos1, _ = _apply_single(base, s1, d1)
            seconds = _legal_single_moves(pos1, d2)
            if seconds:
                for s2 in seconds:
                    actions.append((order_char, d1, d2, s1, s2))
            else:
                actions.append((order_char, d1, d2, s1, None))
    else:
        seconds = _legal_single_moves(base, d2)
        if seconds:
            for s2 in seconds:
                actions.append((order_char, d1, d2, None, s2))
        else:
            actions.append((order_char, d1, d2, None, None))

    return actions

def _generate_legal_actions(state):
    dice = list(state.get("dice", []))
    if len(dice) == 0:
        return [("H", 0, 0, None, None)]
    if len(dice) == 1:
        d = dice[0]
        acts = []
        base = (
            list(state["my_pts"]),
            list(state["opp_pts"]),
            int(state["my_bar"]),
            int(state["my_off"]),
        )
        moves = _legal_single_moves(base, d)
        if moves:
            for s in moves:
                acts.append(("H", d, 0, s, None))
        else:
            acts.append(("H", d, 0, None, None))
        return acts

    a, b = dice[0], dice[1]
    hi, lo = max(a, b), min(a, b)

    # This engine format supports up to two checker moves. For doubles, use two dice as well.
    if hi == lo:
        acts = _generate_for_order(state, "H", (hi, lo))
    else:
        acts = _generate_for_order(state, "H", (hi, lo)) + _generate_for_order(state, "L", (lo, hi))

    # Enforce "use maximum dice; if only one die, higher die when possible" rule.
    max_count = -1
    for act in acts:
        cnt = (1 if act[3] is not None else 0) + (1 if act[4] is not None else 0)
        if cnt > max_count:
            max_count = cnt

    acts = [a for a in acts if ((1 if a[3] is not None else 0) + (1 if a[4] is not None else 0)) == max_count]

    if max_count == 1 and hi != lo:
        # If only one die can be played, higher die must be played when possible.
        high_play = []
        for act in acts:
            oc, d1, d2, s1, s2 = act
            played_die = d1 if s1 is not None else d2 if s2 is not None else None
            if played_die == hi:
                high_play.append(act)
        if high_play:
            acts = high_play

    return acts or [("H", 0, 0, None, None)]

def _pip_count_my(my_pts, my_bar):
    # Distance to bear off is index+1; bar is treated as 25 pips.
    return sum((i + 1) * my_pts[i] for i in range(24)) + 25 * my_bar

def _pip_count_opp(opp_pts, opp_bar):
    # Opponent moves 0->23, distance to bearoff is 24-index.
    return sum((24 - i) * opp_pts[i] for i in range(24)) + 25 * opp_bar

def _evaluate(sim):
    my_pts = sim["my_pts"]
    opp_pts = sim["opp_pts"]
    my_bar = sim["my_bar"]
    opp_bar = sim["opp_bar"]
    my_off = sim["my_off"]
    opp_off = sim["opp_off"]

    my_pip = _pip_count_my(my_pts, my_bar)
    opp_pip = _pip_count_opp(opp_pts, opp_bar)

    score = 0.0

    # Race and borne-off checkers.
    score += (opp_pip - my_pip) * 1.15
    score += my_off * 18.0
    score -= opp_off * 12.0
    score -= my_bar * 35.0
    score += opp_bar * 22.0
    score += sim.get("hits", 0) * 18.0

    # Home-board strength: made points in 0..5 matter a lot for containing hit checkers.
    for i in range(6):
        if my_pts[i] >= 2:
            score += 10.0 + (5 - i) * 1.5
        elif my_pts[i] == 1:
            score -= 3.0 + (5 - i) * 0.7

    # Made points and blots over the whole board.
    for i in range(24):
        m = my_pts[i]
        o = opp_pts[i]

        if m >= 2:
            score += 4.0
            # Advanced anchors / blocking points.
            if i >= 18:
                score += 5.0
            if 6 <= i <= 17:
                score += 2.0
        elif m == 1:
            # Blot danger: opponent checkers behind can often hit.
            danger = 0.0
            for d in range(1, 7):
                j = i - d  # opponent moves upward, so opponent at lower index can hit us
                if 0 <= j < 24 and o_at_least(opp_pts, j):
                    danger += 1.0
            score -= 5.0 + 1.3 * danger

        # Opponent blots are good targets/weaknesses.
        if o == 1:
            score += 1.8

    # Prefer compactness and avoid tall stacks.
    occupied = [i for i, c in enumerate(my_pts) if c > 0]
    if occupied:
        score -= (max(occupied) - min(occupied)) * 0.45

    for i, c in enumerate(my_pts):
        if c >= 4:
            score -= (c - 3) * 1.8
        if c >= 6:
            score -= (c - 5) * 2.5

    # Bearing off mode: very strongly favor taking checkers off.
    if _all_in_home(my_pts, my_bar):
        score += my_off * 25.0
        for i in range(6):
            score -= my_pts[i] * (i + 1) * 0.9

    return score

def o_at_least(pts, idx):
    return pts[idx] > 0

def _action_to_string(act):
    oc, d1, d2, s1, s2 = act
    return "%s:%s,%s" % (oc, _token(s1), _token(s2))

def policy(state: dict) -> str:
    try:
        actions = _generate_legal_actions(state)
        best = None
        best_score = -10**18

        for act in actions:
            sim = _simulate_action(state, act[0], act[1], act[2], act[3], act[4])
            sc = _evaluate(sim)

            # Small deterministic tie-breakers: prefer using both dice, then bearing off/hitting.
            sc += 0.001 * sim.get("move_count", 0)
            sc += 0.0001 * sim.get("hits", 0)

            if sc > best_score:
                best_score = sc
                best = act

        if best is None:
            return "H:P,P"
        return _action_to_string(best)
    except Exception:
        # Safety fallback. This is legal when no moves exist; if moves exist, generation should
        # normally prevent this path. Avoid raising at all costs.
        return "H:P,P"
