
import numpy as np

def policy(state):
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    my_off = state['my_off']
    my_off_total = sum(my_pts[18:24])  # Checkers in home board (A0-A5)
    dice = state['dice']

    # If bearing off is possible, prioritize scoring
    if my_off < 15 and my_off_total == 0 and all(my_pts[0:6] == 0):
        # Sort dice in descending order
        dice_sorted = sorted(dice, reverse=True)
        # Try to bear off from highest point first
        for d in dice_sorted:
            # Find the highest point in home board with >= d checkers
            for p in range(5, -1, -1):
                if my_pts[p] >= d:
                    # Bear off from point p (absolute index = p)
                    if len(dice_sorted) == 2:
                        return f"H:A{p},A{p+1-d}" if d == dice_sorted[0] else f"L:A{p},A{p+1-d}"
                    else:
                        return f"H:A{p}" if d == dice_sorted[0] else f"L:A{p}"
        return "H:P,P"  # No valid bearing-off moves (shouldn't happen if dice are valid)

    # If any checkers are on the bar, move them first
    if my_bar > 0:
        # Sort dice in ascending order (lower die first)
        dice_sorted = sorted(dice)
        moves = []
        for d in dice_sorted:
            # Find the first valid entry point (not occupied by 2+ opponent checkers)
            for p in range(23, -1, -1):
                if opp_pts[p] < 2 and my_pts[p] == 0:
                    moves.append(f"A{p}")
                    break
            else:
                # No valid entry point for this die, pass
                moves.append("P")
        # If only one die is valid, ensure higher die is played first
        if len(moves) == 1 and len(dice) == 2:
            return f"H:{moves[0]},P"
        else:
            return f"{'H' if len(dice) == 1 else 'L'}:{moves[0]},{moves[1]}"

    # If no bar checkers, prioritize moving into home board (A0-A5)
    # Sort dice in descending order (higher die first)
    dice_sorted = sorted(dice, reverse=True)
    moves = []
    for d in dice_sorted:
        # Try to move checkers forward (toward opponent's home board)
        # Prefer points closer to home board (A0-A5)
        for p in range(23, 5, -1):
            if my_pts[p] > 0:
                dest = p - d
                if dest >= 0 and opp_pts[dest] < 2:
                    moves.append(f"A{p}")
                    break
        else:
            # If no forward move, try to move into home board (A0-A5)
            for p in range(5, -1, -1):
                if my_pts[p] > 0:
                    dest = p + d  # Moving toward home board (A0-A5)
                    if dest < 24 and opp_pts[dest] < 2:
                        moves.append(f"A{p}")
                        break
            else:
                # No valid moves, pass
                moves.append("P")

    # If both dice can be played, enforce "play both" rule
    if len(moves) == 2:
        return f"H:{moves[0]},{moves[1]}"
    elif len(moves) == 1 and len(dice) == 2:
        # Only one die is valid, play the higher die first
        return f"H:{moves[0]},P"
    else:
        return f"H:P,P"  # No legal moves (full pass)
