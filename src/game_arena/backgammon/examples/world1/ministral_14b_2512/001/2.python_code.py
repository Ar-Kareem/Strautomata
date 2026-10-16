
import numpy as np
from typing import List, Dict

def policy(state: Dict) -> str:
    """
    Generates a legal move for the current state in Backgammon.
    Follows aggressive yet strategic heuristics while respecting game rules.
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # If bearing off is allowed, prioritize it (greedy strategy)
    if my_off < 15 and all(my_pts[i] == 0 for i in range(18, 24)):
        # Find all checkers in home board (A0..A5 = 18..23)
        home_checkers = [i for i in range(18, 24) if my_pts[i] > 0]
        if not home_checkers:
            return "H:P,P"  # No checkers left (shouldn't happen per rules)

        # Sort checkers by distance from A0 (ascending)
        home_checkers_sorted = sorted(home_checkers, key=lambda x: x - 18)

        # Try to bear off with higher die first
        moves = []
        for die in sorted(dice, reverse=True):
            if die == 0:
                continue  # No die to play
            # Find the farthest checker that can be moved to A0
            for pt in home_checkers_sorted:
                if my_pts[pt] > 0 and (pt - die) >= 18 and my_pts[pt - die] == 0:
                    moves.append(pt)
                    break
            if len(moves) == 2:
                break

        if len(moves) == 1:
            return "H:" + str(moves[0]) + "," + str(moves[0])  # Use higher die twice
        elif len(moves) == 2:
            return "H:" + str(moves[0]) + "," + str(moves[1])
        else:
            return "H:P,P"  # No bearing off possible (shouldn't happen if all in home)

    # If checkers are on the bar, move them first (lower die if possible)
    if my_bar > 0:
        # Possible re-entry points (1-6, but opponent's checkers block)
        possible_reentries = [i for i in range(23, 17, -1) if opp_pts[i] < 2]
        possible_reentries = [i for i in possible_reentries if i - dice[0] >= 0]  # Lower die first

        # Try to use lower die first (if legal)
        if dice[0] in possible_reentries and my_pts[dice[0]] == 0:
            moves = [dice[0]]
            if len(dice) == 2 and dice[1] in possible_reentries and my_pts[dice[1]] == 0:
                moves.append(dice[1])
            else:
                # If only one die can be used, try higher die next
                if dice[1] in possible_reentries and my_pts[dice[1]] == 0:
                    moves.append(dice[1])
                else:
                    # Fallback: use lower die and then highest possible
                    moves.append(dice[0])
                    if len(dice) == 2:
                        moves.append(max([d for d in dice if d in possible_reentries and my_pts[d] == 0], default=dice[0]))
        else:
            # No legal re-entry with lower die; try higher die first
            moves = [max(dice)] if len(dice) == 1 else [dice[1], dice[0]]  # Higher die first

        # Filter moves to only valid re-entries
        valid_moves = []
        for die in moves:
            if die in possible_reentries and my_pts[die] == 0:
                valid_moves.append(die)
            else:
                # If no re-entry possible, try moving to non-blocked points
                for i in range(23, 17, -1):
                    if my_pts[i] > 0 and (i - die) >= 0 and opp_pts[i - die] < 2:
                        valid_moves.append(i)
                        break
                if len(valid_moves) == 2:
                    break

        if len(valid_moves) == 1:
            return "H:" + str(valid_moves[0]) + "," + str(valid_moves[0])
        elif len(valid_moves) == 2:
            return "H:" + str(valid_moves[0]) + "," + str(valid_moves[1])
        else:
            return "H:P,P"  # No legal moves (shouldn't happen)

    # If no bar checkers, find all possible moves (both dice)
    possible_moves = []
    for die in dice:
        if die == 0:
            continue
        # Try to move from highest point first (aggressive)
        for pt in range(23, -1, -1):
            if my_pts[pt] > 0 and (pt - die) >= 0 and opp_pts[pt - die] < 2:
                possible_moves.append((pt, die))
                break

    if not possible_moves:
        return "H:P,P"  # No legal moves

    # If only one die can be played, use higher die first
    if len(possible_moves) == 1:
        return "H:" + str(possible_moves[0][0]) + "," + str(possible_moves[0][0])

    # If both dice can be played, decide strategy:
    # 1. Attack opponent's blots (single checkers)
    # 2. Build prime near opponent's home board
    # 3. Avoid weak anchors (single checkers deep in opponent's territory)
    die1, die2 = possible_moves[0][1], possible_moves[1][1]
    pt1, pt2 = possible_moves[0][0], possible_moves[1][0]

    # Heuristic 1: Prefer moves that hit opponent's blots (single checkers)
    hit_blot1 = opp_pts[pt1 - die1] == 1
    hit_blot2 = opp_pts[pt2 - die2] == 1

    if hit_blot1 and hit_blot2:
        # Both moves hit blots; choose the one that hits deeper (closer to opponent's home)
        return "H:" + str(pt1) + "," + str(pt2) if (pt1 - die1) > (pt2 - die2) else "H:" + str(pt2) + "," + str(pt1)
    elif hit_blot1:
        return "H:" + str(pt1) + "," + str(pt1)  # Use higher die first to hit blot
    elif hit_blot2:
        return "H:" + str(pt2) + "," + str(pt2)  # Use higher die first to hit blot
    else:
        # Heuristic 2: Build prime near opponent's home board (points 0-5)
        # Prefer moves that land on points 0-5 (if opponent has checkers there)
        target_zone = range(0, 6)
        lands_in_target1 = (pt1 - die1) in target_zone
        lands_in_target2 = (pt2 - die2) in target_zone

        if lands_in_target1 and lands_in_target2:
            # Both moves land in target; prefer the one that builds a stronger prime
            # (e.g., moves that create a 2-checker point in opponent's home)
            return "H:" + str(pt1) + "," + str(pt2) if (pt1 - die1) == (pt2 - die2) else \
                   "H:" + str(pt1) + "," + str(pt1) if opp_pts[pt1 - die1] == 1 else \
                   "H:" + str(pt2) + "," + str(pt2)
        elif lands_in_target1:
            return "H:" + str(pt1) + "," + str(pt1)  # Use higher die to land in target
        elif lands_in_target2:
            return "H:" + str(pt2) + "," + str(pt2)  # Use higher die to land in target
        else:
            # Heuristic 3: Avoid leaving single checkers deep in opponent's territory
            # Prefer moves that don't leave a blot in points 0-12
            leaves_blot1 = (my_pts[pt1 - die1] == 1 and (pt1 - die1) in range(0, 13))
            leaves_blot2 = (my_pts[pt2 - die2] == 1 and (pt2 - die2) in range(0, 13))

            if leaves_blot1 and not leaves_blot2:
                return "H:" + str(pt2) + "," + str(pt2)  # Use higher die to avoid blot
            elif leaves_blot2 and not leaves_blot1:
                return "H:" + str(pt1) + "," + str(pt1)  # Use higher die to avoid blot
            else:
                # Default: use higher die first (engine enforces this)
                return "H:" + str(pt1) + "," + str(pt2)

