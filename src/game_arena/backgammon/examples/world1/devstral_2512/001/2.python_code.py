
import random

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # If no dice rolled, pass
    if not dice:
        return "H:P,P"

    # If only one die, duplicate it
    if len(dice) == 1:
        dice = [dice[0], dice[0]]

    # Sort dice to determine order
    dice_sorted = sorted(dice, reverse=True)
    higher_die = dice_sorted[0]
    lower_die = dice_sorted[1]

    # Check if we have checkers on the bar
    if my_bar > 0:
        # Try to enter from bar with higher die first
        entry_point = 23 - higher_die
        if entry_point >= 0 and opp_pts[entry_point] < 2:
            # Try to use both dice
            second_entry = 23 - lower_die
            if second_entry >= 0 and opp_pts[second_entry] < 2:
                return f"H:B,B"
            else:
                return f"H:B,P"
        else:
            # Try with lower die
            entry_point = 23 - lower_die
            if entry_point >= 0 and opp_pts[entry_point] < 2:
                return f"L:B,P"
            else:
                return "H:P,P"

    # Check if we can bear off
    home_board = my_pts[:6]
    if all(x == 0 for x in my_pts[6:]):
        # Try to bear off with both dice
        possible_moves = []
        for i in range(6):
            if home_board[i] > 0:
                if i + 1 == higher_die:
                    possible_moves.append((i, higher_die))
                if i + 1 == lower_die:
                    possible_moves.append((i, lower_die))

        # Try to use both dice
        if len(possible_moves) >= 2:
            # Find two different points
            first_move = None
            second_move = None
            for move in possible_moves:
                if move[1] == higher_die and first_move is None:
                    first_move = move[0]
                elif move[1] == lower_die and second_move is None:
                    second_move = move[0]

            if first_move is not None and second_move is not None:
                return f"H:A{first_move},A{second_move}"

        # Try to use one die
        if possible_moves:
            move = possible_moves[0]
            if move[1] == higher_die:
                return f"H:A{move[0]},P"
            else:
                return f"L:A{move[0]},P"

    # General movement strategy
    # Find all possible moves
    possible_moves = []
    for i in range(24):
        if my_pts[i] > 0:
            # Check higher die move
            dest = i - higher_die
            if dest >= 0 and opp_pts[dest] < 2:
                possible_moves.append((i, higher_die, dest))
            # Check lower die move
            dest = i - lower_die
            if dest >= 0 and opp_pts[dest] < 2:
                possible_moves.append((i, lower_die, dest))

    # Try to use both dice
    if len(possible_moves) >= 2:
        # Find two different moves
        first_move = None
        second_move = None
        for move in possible_moves:
            if move[1] == higher_die and first_move is None:
                first_move = move[0]
            elif move[1] == lower_die and second_move is None:
                second_move = move[0]

        if first_move is not None and second_move is not None:
            return f"H:A{first_move},A{second_move}"

    # Try to use one die
    if possible_moves:
        move = possible_moves[0]
        if move[1] == higher_die:
            return f"H:A{move[0]},P"
        else:
            return f"L:A{move[0]},P"

    # No legal moves
    return "H:P,P"
