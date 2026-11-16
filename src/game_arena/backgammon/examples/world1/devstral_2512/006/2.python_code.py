
import random

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # If no dice, pass
    if not dice:
        return "H:P,P"

    # If only one die, use it
    if len(dice) == 1:
        die = dice[0]
        # Check if we have checkers on the bar
        if my_bar > 0:
            # Try to enter from bar
            target = 23 - die
            if opp_pts[target] < 2:
                return f"H:B,P"
            else:
                return "H:P,P"
        else:
            # Find a checker to move
            for i in range(24):
                if my_pts[i] > 0:
                    target = i - die
                    if target < 0:
                        # Bearing off
                        if all(p == 0 for p in my_pts[6:]):
                            return f"H:A{i},P"
                    else:
                        if opp_pts[target] < 2:
                            return f"H:A{i},P"
            return "H:P,P"

    # Two dice case
    die1, die2 = sorted(dice)
    higher_die = max(die1, die2)
    lower_die = min(die1, die2)

    # Check if we have checkers on the bar
    if my_bar > 0:
        # Try to enter from bar with both dice
        target1 = 23 - higher_die
        target2 = 23 - lower_die
        if opp_pts[target1] < 2 and opp_pts[target2] < 2:
            return f"H:B,B"
        elif opp_pts[target1] < 2:
            return f"H:B,P"
        elif opp_pts[target2] < 2:
            return f"L:B,P"
        else:
            return "H:P,P"

    # No checkers on bar, try to move checkers
    moves = []
    for i in range(24):
        if my_pts[i] > 0:
            # Try higher die
            target = i - higher_die
            if target < 0:
                if all(p == 0 for p in my_pts[6:]):
                    moves.append((i, higher_die, 'H'))
            else:
                if opp_pts[target] < 2:
                    moves.append((i, higher_die, 'H'))
            # Try lower die
            target = i - lower_die
            if target < 0:
                if all(p == 0 for p in my_pts[6:]):
                    moves.append((i, lower_die, 'L'))
            else:
                if opp_pts[target] < 2:
                    moves.append((i, lower_die, 'L'))

    # If no moves, pass
    if not moves:
        return "H:P,P"

    # Try to use both dice
    used_dice = set()
    first_move = None
    second_move = None
    for move in moves:
        if move[1] not in used_dice:
            if first_move is None:
                first_move = move
                used_dice.add(move[1])
            else:
                second_move = move
                used_dice.add(move[1])
                break

    if first_move and second_move:
        if first_move[2] == 'H':
            return f"H:A{first_move[0]},A{second_move[0]}"
        else:
            return f"L:A{first_move[0]},A{second_move[0]}"
    elif first_move:
        if first_move[2] == 'H':
            return f"H:A{first_move[0]},P"
        else:
            return f"L:A{first_move[0]},P"
    else:
        return "H:P,P"
