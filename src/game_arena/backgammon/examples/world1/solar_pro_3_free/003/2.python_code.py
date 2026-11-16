
import copy
import math
from typing import List, Dict

def get_distance(idx: int) -> int:
    """Return the pip distance of a point for the player moving from 23 to 0."""
    if idx <= 11:          # outer board (our own outer points)
        return idx + 1
    else:                  # inner board (opponent's home points)
        return 24 - idx

def compute_prime_bonus(my_pts: List[int]) -> int:
    """Number of points you occupy consecutively; >=6 gives a bonus."""
    run = max_run = 0
    for p in range(24):
        if my_pts[p] > 0:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    if max_run >= 6:
        return max_run * 2   # extra points per extra point in the run
    return 0

def evaluate_from_board(p: int, d: int, my_pts: List[int],
                       opp_pts: List[int]) -> (int, int, int, int, int, int):
    """
    Returns a tuple (from_point, score, hit, block, reduction, prime_bonus) for a
    legal move from point p with die d.
    If the move is illegal, returns None.
    """
    if my_pts[p] == 0:
        return None
    dest = p - d
    # 1) Move to an occupied point (must have ≤1 opponent)
    if dest >= 0:
        if opp_pts[dest] >= 2:
            return None
        reduction = get_distance(p) - get_distance(dest)
        hit = opp_pts[dest] == 1
        block = dest <= 5
        new_pts = copy.deepcopy(my_pts)
        new_pts[p] -= 1
        new_pts[dest] = new_pts[dest] + 1
        prime_bonus = compute_prime_bonus(new_pts)
        score = reduction
        # Add simple bonuses
        if hit:
            score += 5
        if block:
            score += 2
        score += prime_bonus * 2
        return (p, score, hit, block, reduction, prime_bonus)
    # 2) Bearing off – allowed only from our home board (0‑5) and only when all
    #    checkers are there.
    if p <= 5:
        needed = get_distance(p)
        if d >= needed:
            reduction = get_distance(p)
            new_pts = copy.deepcopy(my_pts)
            new_pts[p] -= 1   # off the board
            prime_bonus = compute_prime_bonus(new_pts)
            score = reduction + prime_bonus * 2
            return (p, score, False, False, reduction, prime_bonus)
    return None

def evaluate_from_bar(state: Dict, die: int) -> (str, int, int, int, int, int):
    """
    Returns a tuple (from_token, score, hit, block, reduction, prime_bonus) for a legal
    re‑entry move from the bar onto point `die`.  Entry is legal only if
    opp_pts[die] ≤ 1.
    """
    if state['my_bar'] == 0:
        return None
    if state['opp_pts'][die] >= 2:   # blocked entry point
        return None
    # Bar move always removes 25 pips
    reduction = 25
    hit = state['opp_pts'][die] == 1
    block = die <= 5
    token = 'B'
    # Simulate the move
    new_pts = copy.deepcopy(state['my_pts'])
    new_pts[die] = new_pts.get(die, 0) + 1
    # Compute prime bonus on the hypothetical board after the entry
    prime_bonus = compute_prime_bonus(new_pts)
    score = reduction
    if hit:
        score += 5
    if block:
        score += 2
    score += prime_bonus * 2
    return (token, score, hit, block, reduction, prime_bonus)

def policy(state: Dict) -> str:
    """Return a legal move string according to the engine’s API."""
    dice = state.get('dice', [])
    if not dice:                     # no dice – forced full pass
        return "H:P,P"

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']

    # Sort dice descending so we can talk about high/low
    dice_desc = sorted(dice, reverse=True)
    high = dice_desc[0]
    low = dice_desc[-1]

    # Dictionary mapping a die value to its chosen FROM token (or None)
    chosen = {}

    # Helper to evaluate moves for a single die
    def best_move_for_die(d: int):
        # Prefer a bar move if it exists (and it is mandatory if we have bar checkers)
        bar_cand = evaluate_from_bar(state, d)
        if bar_cand is not None:
            # bar move wins automatically – we must use it
            return bar_cand

        # Otherwise search normal board moves
        best_board = None
        best_score = -math.inf
        for p in range(24):
            if my_pts[p] == 0:
                continue
            cand = evaluate_from_board(p, d, my_pts, opp_pts)
            if cand is not None and cand[1] > best_score:
                best_score = cand[1]
                best_board = cand
        return best_board

    # Find best move for each die in descending order
    for d in dice_desc:
        move = best_move_for_die(d)
        if move is None:            # no legal move for this die → pass
            chosen[d] = None
        else:
            chosen[d] = move

    # Determine if we have a move for high die and low die
    has_high = chosen[high] is not None
    has_low = chosen[low] is not None

    # Build token list in the order required by the engine (high die first)
    tokens = []
    for d in dice_desc:
        if chosen[d] is None:
            tokens.append('P')
        elif chosen[d][0] == 'B':
            tokens.append('B')
        else:
            p = chosen[d][0]          # FROM point (int)
            tokens.append(f'A{p}')

    # Decide the ORDER char
    if has_high and has_low:
        order = 'H'
    elif has_low and not has_high:
        order = 'L'
    else:
        order = 'H'   # default – no moves or only high die

    return f"{order}:{','.join(tokens)}"
