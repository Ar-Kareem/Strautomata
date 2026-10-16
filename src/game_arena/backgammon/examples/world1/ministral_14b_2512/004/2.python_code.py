
import numpy as np
from typing import List, Dict

def policy(state: Dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # If bearing off is allowed, use a bearing-off strategy
    if can_bear_off(my_pts, opp_pts):
        return bear_off(my_pts, opp_pts, dice)

    # If checkers are on the bar, move them first (highest die first)
    if my_bar > 0:
        return move_from_bar(my_pts, opp_pts, my_bar, dice)

    # Otherwise, use positional/aggressive play
    return aggressive_move(my_pts, opp_pts, dice)

def can_bear_off(my_pts: List[int], opp_pts: List[int]) -> bool:
    # All my checkers must be in home board (A0..A5, which is points 18..23)
    return all(p == 0 for p in my_pts[:18])

def bear_off(my_pts: List[int], opp_pts: List[int], dice: List[int]) -> str:
    # Prioritize high-value checkers (6-pointers first)
    home_points = my_pts[18:]  # A0..A5 (indices 18..23)
    home_points = np.array(home_points)

    # Sort checkers by value (highest first)
    checker_values = np.array([6, 5, 4, 3, 2, 1]) * home_points
    checker_values_flat = checker_values.flatten()
    checker_values_flat = checker_values_flat[checker_values_flat > 0]

    if len(checker_values_flat) == 0:
        return "H:P,P"  # No checkers left (edge case)

    # Sort indices of checkers by their value (descending)
    checker_indices = np.argsort(-checker_values_flat)
    top_checkers = np.where(home_points > 0)[0][checker_indices]

    # Try to bear off highest-value checkers first
    moves = []
    for die in sorted(dice, reverse=True):
        if len(moves) >= 2:
            break
        for idx in top_checkers:
            point = 18 + idx
            if my_pts[point] > 0 and (point - die) >= 18:  # Can bear off
                moves.append(point)
                break
        else:
            # If no bearing off possible, try safe moves (e.g., into home board)
            for idx in range(18, 24):
                if my_pts[idx] > 0 and (idx - die) >= 18:
                    moves.append(idx)
                    break
            else:
                # If no bearing off or safe move, try any legal move
                for idx in range(23, -1, -1):
                    if my_pts[idx] > 0 and (idx - die) >= 0 and opp_pts[idx - die] < 2:
                        moves.append(idx)
                        break

    # If only one die can be played, use the higher die first
    if len(moves) == 1:
        return "H:" + moves[0].__str__() + ",P"
    elif len(moves) == 2:
        return "H:" + moves[0].__str__() + "," + moves[1].__str__()
    else:
        return "H:P,P"  # No legal moves (edge case)

def move_from_bar(my_pts: List[int], opp_pts: List[int], my_bar: int, dice: List[int]) -> str:
    # Sort dice in descending order
    dice_sorted = sorted(dice, reverse=True)

    # Try to move highest die first (as required)
    moves = []
    for die in dice_sorted:
        if len(moves) >= 2:
            break
        # Find the first legal point to move into (no 2+ opp checkers)
        for idx in range(23, -1, -1):
            dest = idx - die
            if dest >= 0 and opp_pts[dest] < 2 and my_pts[idx] > 0:
                moves.append(idx)
                break
        else:
            # If no legal move with this die, try next (but prioritize higher die)
            pass

    # If no moves found (unlikely due to rules), try any legal re-entry
    if len(moves) == 0:
        for die in dice_sorted:
            for idx in range(23, -1, -1):
                dest = idx - die
                if dest >= 0 and opp_pts[dest] < 2:
                    moves.append(idx)
                    break
            if len(moves) > 0:
                break

    # If only one die can be played, use the higher die first
    if len(moves) == 1:
        return "H:" + moves[0].__str__() + ",P"
    elif len(moves) == 2:
        return "H:" + moves[0].__str__() + "," + moves[1].__str__()
    else:
        return "H:P,P"  # No legal moves (edge case)

def aggressive_move(my_pts: List[int], opp_pts: List[int], dice: List[int]) -> str:
    dice_sorted = sorted(dice, reverse=True)
    moves = []

    # Try to hit opponent's blots (single checkers) in their prime (0..5)
    for die in dice_sorted:
        if len(moves) >= 2:
            break
        for idx in range(23, -1, -1):
            dest = idx - die
            if dest >= 0 and opp_pts[dest] == 1 and my_pts[idx] > 0:
                moves.append(idx)
                break
        else:
            # If no hits possible, try to move into opponent's prime (defense)
            for idx in range(23, -1, -1):
                dest = idx - die
                if dest >= 0 and dest <= 5 and opp_pts[dest] < 2 and my_pts[idx] > 0:
                    moves.append(idx)
                    break
            else:
                # If no prime-related moves, try to consolidate (move into home board)
                for idx in range(23, -1, -1):
                    dest = idx - die
                    if dest >= 18 and my_pts[idx] > 0:  # Home board
                        moves.append(idx)
                        break
                else:
                    # If no consolidation possible, try any legal move (higher die first)
                    for idx in range(23, -1, -1):
                        if my_pts[idx] > 0 and opp_pts[idx - die] < 2:
                            moves.append(idx)
                            break

    # If only one die can be played, use the higher die first
    if len(moves) == 1:
        return "H:" + moves[0].__str__() + ",P"
    elif len(moves) == 2:
        return "H:" + moves[0].__str__() + "," + moves[1].__str__()
    else:
        return "H:P,P"  # No legal moves (edge case)
