
import numpy as np

def policy(state: dict) -> str:
    my_bar = state['my_bar']
    dice = state['dice']

    # Handle bar checkers first
    if my_bar > 0:
        possible_bar_moves = []
        for die in dice:
            dest = 24 - die
            if 0 <= dest < 24 and state['opp_pts'][dest] < 2:
                possible_bar_moves.append(die)
        if possible_bar_moves:
            possible_bar_moves_sorted = sorted(possible_bar_moves, reverse=True)
            if len(possible_bar_moves) == 1:
                return "H:B,P"
            else:
                return "H:B,B"
        else:
            return "H:P,P"

    # Check if bearing off is possible
    all_home = True
    for i in range(6, 24):
        if state['my_pts'][i] > 0:
            all_home = False
            break
    if all_home:
        bearing_moves = []
        for die in dice:
            for i in range(5, -1, -1):
                if state['my_pts'][i] > 0 and i <= die:
                    bearing_moves.append((die, i))
                    break
        if bearing_moves:
            if len(bearing_moves) == 1:
                die, from_point = bearing_moves[0]
                return f"H:A{from_point},P"
            else:
                die1, from1 = bearing_moves[0]
                die2, from2 = bearing_moves[1]
                if die1 > die2:
                    return f"H:A{from1},A{from2}"
                else:
                    return f"H:A{from2},A{from1}"

    # Normal moves: find furthest checker for each die
    possible_moves = []
    for die in dice:
        for i in range(23, -1, -1):
            if state['my_pts'][i] > 0:
                dest = i - die
                if 0 <= dest < 24 and state['opp_pts'][dest] < 2:
                    possible_moves.append((die, i))
                    break
    if not possible_moves:
        return "H:P,P"
    elif len(possible_moves) == 1:
        die, from_point = possible_moves[0]
        return f"H:A{from_point},P"
    else:
        die1, from1 = possible_moves[0]
        die2, from2 = possible_moves[1]
        if die1 > die2:
            return f"H:A{from1},A{from2}"
        else:
            return f"H:A{from2},A{from1}"
