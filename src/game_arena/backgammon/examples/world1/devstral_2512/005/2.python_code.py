
import random
from typing import List, Tuple, Dict, Optional

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = state['dice']

    # If no dice rolled (shouldn't happen in normal play), pass
    if not dice:
        return "H:P,P"

    # If only one die, we must use it (with H order)
    if len(dice) == 1:
        return handle_single_die(state, dice[0])

    # Sort dice to determine order
    dice_sorted = sorted(dice, reverse=True)
    high_die = dice_sorted[0]
    low_die = dice_sorted[1]

    # Check if we have checkers on bar - must move them first
    if my_bar > 0:
        return handle_bar_moves(state, high_die, low_die)

    # Generate all possible moves
    possible_moves = generate_possible_moves(state, high_die, low_die)

    if not possible_moves:
        return "H:P,P"

    # Evaluate and select best move
    best_move = evaluate_moves(state, possible_moves, high_die, low_die)

    return best_move

def handle_single_die(state: dict, die: int) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']

    # If on bar, try to enter
    if my_bar > 0:
        # Try to enter from bar (opponent's home board is 0-5)
        for point in range(6):
            if opp_pts[point] < 2:  # Can enter if not blocked
                return f"H:B,A{point}"

        # If can't enter, must pass
        return "H:P,P"

    # Find all possible moves with this die
    possible_starts = []
    for start in range(24):
        if my_pts[start] > 0:
            end = start - die
            if end < 0:
                # Bearing off case
                if all(p == 0 for p in my_pts[end+1:]):
                    possible_starts.append(start)
            elif end >= 0 and opp_pts[end] < 2:
                possible_starts.append(start)

    if not possible_starts:
        return "H:P,P"

    # Choose the move that gets us closest to bearing off
    # Prefer moves that hit opponent's blots
    best_start = None
    best_score = -float('inf')

    for start in possible_starts:
        end = start - die
        score = 0

        # Bonus for hitting opponent
        if end >= 0 and opp_pts[end] == 1:
            score += 100

        # Bonus for moving toward home board
        score += (23 - start)

        # Bonus for bearing off
        if end < 0:
            score += 1000

        if score > best_score:
            best_score = score
            best_start = start

    return f"H:A{best_start},P"

def handle_bar_moves(state: dict, high_die: int, low_die: int) -> str:
    opp_pts = state['opp_pts']

    # Try to enter with both dice
    possible_entries = []
    for die in [high_die, low_die]:
        # Opponent's home board is 0-5
        entry_point = die - 1
        if entry_point < 6 and opp_pts[entry_point] < 2:
            possible_entries.append(die)

    if not possible_entries:
        return "H:P,P"

    # If only one die can enter
    if len(possible_entries) == 1:
        die = possible_entries[0]
        entry_point = die - 1
        if die == high_die:
            return f"H:B,P"
        else:
            return f"L:B,P"

    # Both dice can enter - choose order
    # Prefer higher die first if it gives better position
    high_entry = high_die - 1
    low_entry = low_die - 1

    # Evaluate which order is better
    # Prefer the one that gets us closer to our home board (higher point number)
    if high_entry > low_entry:
        return f"H:B,B"
    else:
        return f"L:B,B"

def generate_possible_moves(state: dict, high_die: int, low_die: int) -> List[Tuple[str, int, int]]:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    moves = []

    # Check all possible combinations of moves
    for start1 in range(24):
        if my_pts[start1] == 0:
            continue

        end1 = start1 - high_die
        # Check if move1 is valid
        if end1 < 0:
            # Bearing off case
            if not all(p == 0 for p in my_pts[end1+1:]):
                continue
        elif opp_pts[end1] >= 2:
            continue

        # Now check second move
        for start2 in range(24):
            if start2 == start1 and my_pts[start1] == 1:
                continue  # Can't move same checker twice unless it's the only one

            if my_pts[start2] == 0:
                continue

            end2 = start2 - low_die
            # Check if move2 is valid
            if end2 < 0:
                # Bearing off case
                if not all(p == 0 for p in my_pts[end2+1:]):
                    continue
            elif opp_pts[end2] >= 2:
                continue

            # Both moves are valid
            moves.append((start1, start2))

    return moves

def evaluate_moves(state: dict, possible_moves: List[Tuple[int, int]], high_die: int, low_die: int) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']

    best_move = None
    best_score = -float('inf')

    for start1, start2 in possible_moves:
        # Calculate scores for both possible orders
        # First try H order (high die first)
        score_h = evaluate_move_order(state, start1, start2, high_die, low_die, True)
        # Then try L order (low die first)
        score_l = evaluate_move_order(state, start2, start1, low_die, high_die, False)

        # Choose the better order
        if score_h >= score_l:
            current_score = score_h
            order = 'H'
            from1, from2 = start1, start2
        else:
            current_score = score_l
            order = 'L'
            from1, from2 = start2, start1

        if current_score > best_score:
            best_score = current_score
            best_move = f"{order}:A{from1},A{from2}"

    return best_move if best_move else "H:P,P"

def evaluate_move_order(state: dict, start1: int, start2: int, die1: int, die2: int, is_h_order: bool) -> float:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    score = 0.0

    # Evaluate first move
    end1 = start1 - die1
    # Bonus for hitting opponent
    if end1 >= 0 and opp_pts[end1] == 1:
        score += 100
    # Bonus for bearing off
    if end1 < 0:
        score += 1000
    # Bonus for moving toward home board
    score += (23 - start1) * 0.1

    # Evaluate second move
    end2 = start2 - die2
    # Bonus for hitting opponent
    if end2 >= 0 and opp_pts[end2] == 1:
        score += 100
    # Bonus for bearing off
    if end2 < 0:
        score += 1000
    # Bonus for moving toward home board
    score += (23 - start2) * 0.1

    # Bonus for building primes (consecutive points)
    if end1 >= 0 and end2 >= 0:
        if abs(end1 - end2) == 1:
            score += 50

    # Small bonus for using both dice (better pip reduction)
    score += 10

    return score
