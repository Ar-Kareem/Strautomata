
import math
from typing import List, Tuple, Optional

def can_bear_off(my_pts: List[int], my_bar: int) -> bool:
    if my_bar > 0:
        return False
    # home board assumed to be points 18..23
    return all(x == 0 for x in my_pts[:18])

def apply_move(state, from_point, die):
    # state: (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off)
    my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, opp_off0 = state
    my_pts = list(my_pts0)
    opp_pts = list(opp_pts0)
    my_bar = my_bar0
    opp_bar = opp_bar0
    my_off = my_off0
    opp_off = opp_off0

    if from_point == 'B':
        if my_bar <= 0:
            return None
        my_bar -= 1
        dest = die - 1
        start_index = None
    else:
        i = from_point
        if my_pts[i] <= 0:
            return None
        my_pts[i] -= 1
        dest = i + die
        start_index = i

    if dest <= 23:
        if opp_pts[dest] >= 2:
            return None
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
        my_pts[dest] += 1
        return (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off)
    else:
        # Bearing off
        if not can_bear_off(my_pts0, my_bar0):
            return None
        if start_index is None:
            return None
        if start_index < 18:
            return None
        if dest == 24:
            my_off += 1
            return (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off)
        else:
            # dest > 24, allowed only if no checkers on higher points
            for j in range(start_index + 1, 24):
                if my_pts0[j] > 0:
                    return None
            my_off += 1
            return (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off)

def legal_moves_for_die(state, die):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = state
    results = []
    if my_bar > 0:
        from_points = ['B']
    else:
        from_points = [i for i in range(24) if my_pts[i] > 0]
    for fp in from_points:
        new_state = apply_move(state, fp, die)
        if new_state is not None:
            token = 'B' if fp == 'B' else f"A{fp}"
            results.append((token, new_state))
    return results

def sequences_for_order(state, die1, die2, order_char):
    seqs = []
    for fp1, st1 in legal_moves_for_die(state, die1):
        moves2 = legal_moves_for_die(st1, die2)
        if moves2:
            for fp2, st2 in moves2:
                seqs.append((order_char, fp1, fp2, st2))
    return seqs

def evaluate(state, base_state):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = state
    base_my_pts, base_opp_pts, base_my_bar, base_opp_bar, base_my_off, base_opp_off = base_state

    pip = sum((24 - i) * my_pts[i] for i in range(24))
    opp_pip = sum((i + 1) * opp_pts[i] for i in range(24))
    made = sum(1 for i in range(24) if my_pts[i] >= 2)
    blots = sum(1 for i in range(24) if my_pts[i] == 1)
    hit = opp_bar - base_opp_bar

    score = (
        10000 * my_off
        - 500 * my_bar
        + 250 * opp_bar
        - pip
        + 0.1 * opp_pip
        + 20 * made
        - 5 * blots
        + 200 * hit
    )
    return score

def choose_best(candidates, base_state):
    if not candidates:
        return None
    best = None
    best_score = -1e18
    for cand in candidates:
        order, f1, f2, st = cand
        sc = evaluate(st, base_state)
        if sc > best_score:
            best_score = sc
            best = cand
    return best

def policy(state: dict) -> str:
    dice = state.get('dice', [])
    if not dice:
        return "H:P,P"

    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']

    base_state = (my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off)

    if len(dice) == 1:
        die = dice[0]
        moves = legal_moves_for_die(base_state, die)
        if not moves:
            return "H:P,P"
        candidates = [('H', fp, 'P', st) for fp, st in moves]
        best = choose_best(candidates, base_state)
        if best is None:
            return "H:P,P"
        order, f1, f2, _ = best
        return f"{order}:{f1},{f2}"

    d1, d2 = dice[0], dice[1]
    if d1 == d2:
        hi = lo = d1
    else:
        hi = max(d1, d2)
        lo = min(d1, d2)

    candidates = []
    # Try to use both dice if possible
    candidates += sequences_for_order(base_state, hi, lo, 'H')
    if hi != lo:
        candidates += sequences_for_order(base_state, lo, hi, 'L')

    if candidates:
        best = choose_best(candidates, base_state)
        if best is None:
            return "H:P,P"
        order, f1, f2, _ = best
        return f"{order}:{f1},{f2}"

    # If cannot play both dice, play one (higher if possible)
    moves_hi = legal_moves_for_die(base_state, hi)
    moves_lo = legal_moves_for_die(base_state, lo)

    if moves_hi:
        candidates = [('H', fp, 'P', st) for fp, st in moves_hi]
        best = choose_best(candidates, base_state)
        if best is None:
            return "H:P,P"
        order, f1, f2, _ = best
        return f"{order}:{f1},{f2}"
    elif moves_lo:
        order_char = 'L' if hi != lo else 'H'
        candidates = [(order_char, fp, 'P', st) for fp, st in moves_lo]
        best = choose_best(candidates, base_state)
        if best is None:
            return "H:P,P"
        order, f1, f2, _ = best
        return f"{order}:{f1},{f2}"

    return "H:P,P"
