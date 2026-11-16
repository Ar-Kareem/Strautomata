
import numpy as np
from typing import List, Tuple, Dict, Optional

def policy(state: dict) -> str:
    # Extract state components
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'])  # sorted low to high
    if len(dice) == 0:
        return "H:P,P"  # No dice - should not happen, but safe fallback

    # Helper: Check if all my checkers are in home board (points 0-5)
    def all_in_home_board():
        return np.sum(my_pts[6:]) == 0

    # Helper: Check if a point is hitable (opponent has exactly 1 checker)
    def is_vulnerable(point):
        return opp_pts[point] == 1

    # Helper: Check if a point is blocked (opponent has >=2 checkers)
    def is_blocked(point):
        return opp_pts[point] >= 2

    # Helper: Check if a point is occupied by me (any number > 0)
    def is_mine(point):
        return my_pts[point] > 0

    # Helper: Compute score for a move or board position
    def evaluate_board():
        score = 0
        # Prioritize bearing off
        if all_in_home_board():
            score += 1000 * (my_off / 15)  # score based on progress

        # Penalize blots (single checkers vulnerable to hit)
        blots = np.sum((my_pts == 1) & (opp_pts < 2))
        score -= blots * 50

        # Reward safe points (2+ checkers)
        safe_points = np.sum(my_pts >= 2)
        score += safe_points * 10

        # Reward control of key points (midboard points 6-17)
        control_mid = np.sum(my_pts[6:18]) * 0.5
        score += control_mid

        # Reward points near home board (points 18-23) as stepping stones
        near_home = np.sum(my_pts[18:24])
        score += near_home * 0.3

        # Penalize checkers on bar
        if my_bar > 0:
            score -= 100  # big penalty for being on bar

        # Bonus for building primes (consecutive points with >=2 checkers)
        primes = 0
        for i in range(18):  # check for primes from 0 to 17, max prime length 6
            if my_pts[i] >= 2:
                streak = 1
                for j in range(i + 1, min(i + 6, 24)):
                    if my_pts[j] >= 2:
                        streak += 1
                    else:
                        break
                if streak >= 4:  # a prime of 4 or more
                    primes += 1
        score += primes * 75

        return score

    # Generate all possible move sequences given dice
    def get_legal_moves(all_dice):
        moves = []
        # Case 1: Checkers on bar, must use dice to re-enter
        if my_bar > 0:
            for i, die in enumerate(all_dice):
                # Re-entry is to point (24 - die) in absolute indexing
                entry_point = 24 - die
                if entry_point > 23:
                    entry_point = entry_point - 24
                # Must be not blocked by opponent
                if not is_blocked(entry_point):
                    # Can take one move
                    moves.append([(entry_point, die)])  # single move: bar -> entry_point
                    # If second die exists, try second re-entry
                    if len(all_dice) > 1 and i == 0:  # first die used
                        second_die = all_dice[1]
                        second_entry = 24 - second_die
                        if second_entry > 23:
                            second_entry = second_entry - 24
                        if not is_blocked(second_entry):
                            moves.append([(entry_point, die), (second_entry, second_die)])
            # Also consider if only one move possible, even with two dice, if second re-entry blocked
            for i, die in enumerate(all_dice):
                entry_point = 24 - die
                if entry_point > 23:
                    entry_point = entry_point - 24
                if not is_blocked(entry_point):
                    # Only play one, leave the other unused
                    moves.append([(entry_point, die)])

        else:
            # No checkers on bar; explore moves from existing points
            # Generate all legal single moves
            single_moves = []
            for point in range(24):
                if my_pts[point] == 0:
                    continue
                for die in all_dice:
                    dest = point - die
                    # Bear off if possible?
                    if dest < 0 and all_in_home_board():
                        # Check if point is within home board (point <= 5)
                        if point <= 5:
                            single_moves.append((point, die, 'bear_off'))  # special flag
                    else:
                        if dest >= 0 and not is_blocked(dest):
                            single_moves.append((point, die, 'move'))

            # Now generate all combinations of two moves (considering dice order)
            # Since dice are ordered, we consider both H and L orders if possible
            for first in single_moves:
                point1, die1, type1 = first
                # State after first move
                my_pts_temp = my_pts.copy()
                if type1 == 'bear_off':
                    my_pts_temp[point1] -= 1
                else:
                    dest1 = point1 - die1
                    my_pts_temp[point1] -= 1
                    my_pts_temp[dest1] += 1

                # Can we make a second move?
                second_moves = []
                for point in range(24):
                    if my_pts_temp[point] == 0:
                        continue
                    for die in all_dice:
                        if die == die1:  # we already used one die equal to die1
                            # We need to use the other die
                            other_die = all_dice[1] if die1 == all_dice[0] else all_dice[0]
                            if other_die == die1:  # same die?
                                continue  # don't use same die twice
                            dest = point - other_die
                            if dest < 0 and all_in_home_board():
                                if point <= 5:
                                    second_moves.append((point, other_die, 'bear_off'))
                            else:
                                if dest >= 0 and not is_blocked(dest):
                                    second_moves.append((point, other_die, 'move'))

                # Also check if second move is the same die, if doubles
                if len(all_dice) == 2 and all_dice[0] == all_dice[1]:
                    # Try using the same die again
                    for point in range(24):
                        if my_pts_temp[point] == 0:
                            continue
                        dest = point - die1
                        if dest < 0 and all_in_home_board():
                            if point <= 5:
                                second_moves.append((point, die1, 'bear_off'))
                        else:
                            if dest >= 0 and not is_blocked(dest):
                                second_moves.append((point, die1, 'move'))

                # Combine
                for second in second_moves:
                    moves.append([first, second])

            # Also allow using only one die (if cannot use both) if forced by rules
            # Check if we have only one legal move
            if len(single_moves) > 0 and len(moves) == 0:
                for m in single_moves:
                    moves.append([m])

            # If there's an option to use the higher die first or lower die first
            # We'll generate both H and L orderings later by evaluating dic order

        return moves

    # Get all legal move sequences
    all_possible_moves = get_legal_moves(dice)

    # If non-legal move generated? Fallback if none
    if len(all_possible_moves) == 0:
        return "H:P,P"
    
    # If no moves, pass
    if len(all_possible_moves) == 1 and len(all_possible_moves[0]) == 0:
        return "H:P,P"

    # Now, evaluate each possible move sequence with heuristic, and choose the best
    best_score = float('-inf')
    best_move = "H:P,P"
    best_dice_order = "H"  # default

    for move_seq in all_possible_moves:
        # Convert to string representation
        move_rep = []
        die_used = []
        for move in move_seq:
            point, die, move_type = move
            if move_type == 'bear_off':
                move_rep.append("P")  # bear off is represented as pass (engine handles it)
            else:
                move_rep.append(f"A{point}")
            die_used.append(die)
        
        # For single move: we need to consider which die was used first
        # We try to optimize order: try using higher die first if possible (H), then L
        # But only if move representation has 1 or 2 moves
        is_two_move = len(move_seq) == 2
        if is_two_move:
            # Try H: higher die first
            dice_high_low = sorted(dice, reverse=True)  # high to low
            die1, die2 = dice_high_low[0], dice_high_low[1]
            # Check if we used die1 then die2 in our sequence
            if die_used[0] == die1 and die_used[1] == die2:
                order = "H"
            elif die_used[0] == die2 and die_used[1] == die1:
                order = "L"
            else:
                # We can try reordering our moves
                # But we must preserve legality. Try both orders.
                # Evaluate both
                for ord in ["H", "L"]:
                    dice_order = [die1, die2] if ord == "H" else [die2, die1]
                    # Check if this ordering is achievable with our move set
                    if sorted(die_used) == sorted(dice_order):  # same dice used
                        move_str = f"{ord}:{move_rep[0]},{move_rep[1]}"
                        # Simulate the move on a temp state to evaluate
                        temp_my_pts = my_pts.copy()
                        temp_my_bar = my_bar
                        for i, (point, die, mtype) in enumerate(move_seq):
                            if mtype == 'bear_off':
                                temp_my_pts[point] -= 1
                            else:
                                temp_my_pts[point] -= 1
                                temp_my_pts[point - die] += 1
                        temp_my_off = my_off + sum(1 for m in move_seq if m[2] == 'bear_off')
                        # Evaluate the resulting board
                        score = evaluate_board()
                        if score > best_score:
                            best_score = score
                            best_move = move_str
        else:
            # Single move
            die_used = die_used[0]
            order_choices = ["H", "L"] if len(dice) == 2 else ["H"]
            for order in order_choices:
                move_str = f"{order}:{move_rep[0]},P"
                # Simulate move
                temp_my_pts = my_pts.copy()
                point, die, mtype = move_seq[0]
                if mtype == 'bear_off':
                    temp_my_pts[point] -= 1
                else:
                    temp_my_pts[point] -= 1
                    temp_my_pts[point - die] += 1
                temp_my_off = my_off + (1 if mtype == 'bear_off' else 0)
                score = evaluate_board()
                if score > best_score:
                    best_score = score
                    best_move = move_str

    # If no move was chosen? Fallback
    if best_move == "H:P,P" and len(all_possible_moves) > 0:
        # Fallback: take the first move
        first_move = all_possible_moves[0]
        move_rep = []
        for move in first_move:
            point, die, mtype = move
            if mtype == 'bear_off':
                move_rep.append("P")
            else:
                move_rep.append(f"A{point}")
        if len(first_move) == 1:
            best_move = f"H:{move_rep[0]},P"
        else:
            best_move = f"H:{move_rep[0]},{move_rep[1]}"

    # Validate: This must be a legal move representation
    # Format check: must be "H/L:A0..A23|B|P,A0..A23|B|P"
    # We assume best_move is correctly formatted now
    return best_move
