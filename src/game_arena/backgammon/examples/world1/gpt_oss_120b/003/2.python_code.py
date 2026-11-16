
import copy
from typing import List, Tuple, Dict

def possible_starts(state: Dict) -> List[str]:
    """Return a list of tokens where we can move a checker from."""
    if state['my_bar'] > 0:
        return ['B']
    starts = []
    for i, cnt in enumerate(state['my_pts']):
        if cnt > 0:
            starts.append(f'A{i}')
    return starts

def dest_index(start: str, die: int) -> Tuple[int, bool]:
    """
    Return destination index and a flag indicating bearing off.
    For a normal move the index is between 0 and 23.
    For bearing off the index is -1 and the flag is True.
    """
    if start == 'B':
        # entering from the bar: points 24-die .. 23 (0‑based)
        return 24 - die, False
    idx = int(start[1:])
    target = idx - die
    if target >= 0:
        return target, False
    # possible bearing off
    return -1, True

def can_bear_off(state: Dict, start_idx: int, die: int) -> bool:
    """Check if bearing off from start_idx with die is legal."""
    # All checkers must be in home board (points 0‑5)
    if any(state['my_pts'][i] > 0 for i in range(6, 24)):
        return False
    # Exact bear off
    if start_idx == die - 1:
        return True
    # Overshoot bear off – allowed only if no higher occupied points
    for higher in range(start_idx + 1, 6):
        if state['my_pts'][higher] > 0:
            return False
    return True

def move_possible(state: Dict, start: str, die: int) -> bool:
    """Return True if a checker can be moved from `start` using `die`."""
    if start == 'B':
        dest, off = dest_index(start, die)
        # entering from bar never bears off
        if off:
            return False
        # destination must not be blocked by 2+ opponent checkers
        return state['opp_pts'][dest] <= 1
    else:
        idx = int(start[1:])
        if state['my_pts'][idx] == 0:
            return False
        dest, off = dest_index(start, die)
        if off:
            return can_bear_off(state, idx, die)
        # normal move: destination must be free or contain at most one opponent checker
        return state['opp_pts'][dest] <= 1

def apply_move_once(state: Dict, start: str, die: int) -> Dict:
    """Return a new state after moving one checker from `start` with `die`."""
    new_state = {
        'my_pts': state['my_pts'][:],
        'opp_pts': state['opp_pts'][:],
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
        'dice': state['dice']  # unchanged, not needed after move
    }

    if start == 'B':
        new_state['my_bar'] -= 1
        dest, _ = dest_index(start, die)
        # hit?
        if new_state['opp_pts'][dest] == 1:
            new_state['opp_pts'][dest] = 0
            new_state['opp_bar'] += 1
        new_state['my_pts'][dest] += 1
        return new_state

    idx = int(start[1:])
    new_state['my_pts'][idx] -= 1

    dest, off = dest_index(start, die)
    if off:
        # bearing off
        new_state['my_off'] += 1
        return new_state

    # normal move
    if new_state['opp_pts'][dest] == 1:
        # hit opponent blot
        new_state['opp_pts'][dest] = 0
        new_state['opp_bar'] += 1
    new_state['my_pts'][dest] += 1
    return new_state

def evaluate(after: Dict, before: Dict) -> float:
    """Simple heuristic score for the board after the move."""
    score = 0.0
    # borne off gain
    score += (after['my_off'] - before['my_off']) * 10.0
    # hits
    score += (after['opp_bar'] - before['opp_bar']) * 5.0
    # blots penalty
    blots = sum(1 for c in after['my_pts'] if c == 1)
    score -= blots * 1.0
    # advancement (lower total distance is better)
    total_distance = sum(i * c for i, c in enumerate(after['my_pts']))
    score -= total_distance * 0.01
    return score

def generate_all_moves(state: Dict) -> List[Tuple[str, str, str, Dict]]:
    """Return a list of legal moves as (order, from1, from2, resulting_state)."""
    dice = state['dice']
    if not dice:
        return [("H", "P", "P", state)]

    if len(dice) == 1:
        d = dice[0]
        moves = []
        for s in possible_starts(state):
            if move_possible(state, s, d):
                ns = apply_move_once(state, s, d)
                moves.append(("H", s, "P", ns))
        if not moves:
            moves.append(("H", "P", "P", state))
        return moves

    d1, d2 = dice
    higher = max(d1, d2)
    lower = min(d1, d2)

    raw_moves = []
    # Try both orderings
    for order_char, first_die, second_die in [("H", higher, lower), ("L", lower, higher)]:
        for s1 in possible_starts(state):
            if not move_possible(state, s1, first_die):
                continue
            state1 = apply_move_once(state, s1, first_die)
            second_possible = False
            for s2 in possible_starts(state1):
                if not move_possible(state1, s2, second_die):
                    continue
                second_possible = True
                state2 = apply_move_once(state1, s2, second_die)
                raw_moves.append((order_char, s1, s2, state2))
            if not second_possible:
                # only one die could be played with this ordering
                raw_moves.append((order_char, s1, "P", state1))

    # Determine if any move uses both dice
    any_both = any(m[2] != "P" for m in raw_moves)

    if any_both:
        # Must play both dice, discard single‑die moves
        legal = [m for m in raw_moves if m[2] != "P"]
    else:
        # Only one die can be played. Must use the higher die if it is playable.
        higher_playable = any(move_possible(state, s, higher) for s in possible_starts(state))
        legal = []
        for order_char, s1, s2, ns in raw_moves:
            if higher_playable:
                if order_char != "H" or s2 != "P":
                    continue
                legal.append((order_char, s1, s2, ns))
            else:
                if order_char != "L" or s2 != "P":
                    continue
                legal.append((order_char, s1, s2, ns))

    if not legal:
        return [("H", "P", "P", state)]
    return legal

def policy(state: dict) -> str:
    """
    Choose the best legal move according to a simple heuristic.
    Returns a string in the required format.
    """
    candidates = generate_all_moves(state)
    best_move = None
    best_score = -1e9

    for order, f1, f2, after_state in candidates:
        sc = evaluate(after_state, state)
        if sc > best_score:
            best_score = sc
            best_move = (order, f1, f2)

    order, frm1, frm2 = best_move
    return f"{order}:{frm1},{frm2}"
