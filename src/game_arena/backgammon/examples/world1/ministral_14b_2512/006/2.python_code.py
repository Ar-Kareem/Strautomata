
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # If no dice, must pass
    if not dice:
        return "H:P,P"

    # If any checkers on the bar, must move them first
    if my_bar > 0:
        # Try to move from bar using lower die first (if possible)
        lower_die = dice[0] if len(die) == 1 else min(dice)
        higher_die = max(dice)

        # Find all possible bar moves (avoiding points with 2+ opponent checkers)
        possible_bar_moves = []
        for die in [lower_die, higher_die]:
            dest = die - 1  # Bar moves enter at die-1 (0-based)
            if opp_pts[dest] < 2:
                possible_bar_moves.append(die)

        # If only one die can be played, use the higher one
        if len(possible_bar_moves) == 1:
            return f"H:B" if possible_bar_moves[0] == higher_die else f"L:B"
        elif len(possible_bar_moves) == 2:
            # Play both dice: lower first, then higher
            return f"L:B,B" if lower_die in possible_bar_moves and higher_die in possible_bar_moves else f"H:B,B"
        else:
            # No legal bar moves (e.g., both dice land on points with 2+ opponent checkers)
            return "H:P,P"  # Should not happen per legal-move constraints

    # If all checkers are in home board (A0-A5), bear off
    if all(my_pts[0:6] == 0) and all(my_pts[18:24] == 0):
        if len(dice) == 1:
            die = dice[0]
            # Find highest possible checker to move off
            for pt in range(5, -1, -1):
                if my_pts[pt] > 0:
                    return f"H:A{pt}" if die >= pt + 1 else "H:P,P"
            return "H:P,P"
        else:
            die1, die2 = sorted(dice, reverse=True)
            # Bear off highest possible checkers first
            moves = []
            for die in [die1, die2]:
                for pt in range(5, -1, -1):
                    if my_pts[pt] > 0 and die >= pt + 1:
                        moves.append(f"A{pt}")
                        my_pts[pt] -= 1
                        break
            if len(moves) == 2:
                return f"H:{moves[0]},{moves[1]}"
            elif len(moves) == 1:
                return f"H:{moves[0]},P"
            else:
                return "H:P,P"

    # If opponent has blots in home board (A0-A5), attack them aggressively
    opp_home_blots = [pt for pt in range(0, 6) if opp_pts[pt] == 1]
    if opp_home_blots:
        # Try to hit opponent's blots with higher die first
        if len(dice) == 1:
            die = dice[0]
            for pt in range(0, 6):
                if my_pts[pt] > 0 and die == pt + 1 and opp_pts[pt] == 1:
                    return f"H:A{pt}"
            # If no direct hit, move forward safely
            for pt in range(5, -1, -1):
                if my_pts[pt] > 0 and die == pt + 1 and opp_pts[pt + 1] < 2:
                    return f"H:A{pt}"
            # If no safe move, play lower die (but engine enforces higher die first)
            return "H:P,P"
        else:
            die1, die2 = sorted(dice, reverse=True)
            moves = []
            # First try higher die
            for pt in range(0, 6):
                if my_pts[pt] > 0 and die1 == pt + 1 and opp_pts[pt] == 1:
                    moves.append(f"A{pt}")
                    break
            # If no hit, move forward safely
            if len(moves) == 0:
                for pt in range(5, -1, -1):
                    if my_pts[pt] > 0 and die1 == pt + 1 and opp_pts[pt + 1] < 2:
                        moves.append(f"A{pt}")
                        break
            # Second die
            if len(moves) < 2:
                for pt in range(0, 6):
                    if my_pts[pt] > 0 and die2 == pt + 1 and opp_pts[pt] == 1:
                        moves.append(f"A{pt}")
                        break
            if len(moves) < 2:
                for pt in range(5, -1, -1):
                    if my_pts[pt] > 0 and die2 == pt + 1 and opp_pts[pt + 1] < 2:
                        moves.append(f"A{pt}")
                        break
            # If both dice can be played, return them
            if len(moves) == 2:
                return f"H:{moves[0]},{moves[1]}"
            elif len(moves) == 1:
                return f"H:{moves[0]},P"
            else:
                # No legal moves (should not happen per constraints)
                return "H:P,P"

    # General strategy: move forward safely, avoid opponent's heavy points
    if len(dice) == 1:
        die = dice[0]
        # Prefer moving checkers forward (toward A0-A5)
        for pt in range(23, 5, -1):  # Start from outer board (A18-A23)
            if my_pts[pt] > 0 and die == pt + 1 and opp_pts[pt + 1] < 2:
                return f"H:A{pt}"
        # If no forward move, try backward (but less preferred)
        for pt in range(5, 23):
            if my_pts[pt] > 0 and die == pt + 1 and opp_pts[pt + 1] < 2:
                return f"H:A{pt}"
        # If no safe move, pass (but engine enforces higher die first)
        return "H:P,P"
    else:
        die1, die2 = sorted(dice, reverse=True)
        moves = []
        # First die: move forward safely
        for pt in range(23, 5, -1):
            if my_pts[pt] > 0 and die1 == pt + 1 and opp_pts[pt + 1] < 2:
                moves.append(f"A{pt}")
                break
        # Second die: move forward safely
        if len(moves) < 2:
            for pt in range(23, 5, -1):
                if my_pts[pt] > 0 and die2 == pt + 1 and opp_pts[pt + 1] < 2:
                    moves.append(f"A{pt}")
                    break
        # If both dice can be played, return them
        if len(moves) == 2:
            return f"H:{moves[0]},{moves[1]}"
        elif len(moves) == 1:
            return f"H:{moves[0]},P"
        else:
            # No legal moves (should not happen per constraints)
            return "H:P,P"
