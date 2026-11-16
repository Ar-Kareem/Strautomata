
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = state['dice']
    
    # Prioritize bar moves if any checkers are on the bar
    if my_bar > 0:
        sorted_dice = sorted(dice, reverse=True)
        moves = []
        for die in sorted_dice:
            for point in range(24):
                if opp_pts[point] < 2:  # Valid destination (not blocked)
                    if die <= point:    # Valid move from bar
                        moves.append((die, point))
                        break
        if len(moves) >= 2:
            return f'H:{moves[0][1]},{moves[1][1]}'
        elif len(moves) == 1:
            return f'H:{moves[0][1]},P'
        else:
            return 'H:P,P'
    
    # Check if all my checkers are in the home board (A0-A5)
    total_my = sum(my_pts)
    home_sum = sum(my_pts[:6])
    if home_sum == total_my:
        sorted_dice = sorted(dice, reverse=True)
        moves = []
        for die in sorted_dice:
            if die <= 5:  # Can bear off
                for point in range(5, -1, -1):  # Check home board points from highest to lowest
                    if my_pts[point] > 0:
                        moves.append((die, point))
                        break
        if len(moves) >= 2:
            return f'H:{moves[0][1]},{moves[1][1]}'
        elif len(moves) == 1:
            return f'H:{moves[0][1]},P'
        else:
            return 'H:P,P'
    
    # Move from home board or outer board if no bar or bearing off
    sorted_dice = sorted(dice, reverse=True)
    moves = []
    for die in sorted_dice:
        for point in range(24):
            if my_pts[point] > 0:
                # Skip if moving would land on a blocked point
                if opp_pts[point - die] >= 2:
                    continue
                moves.append((die, point))
                break
    if len(moves) >= 2:
        return f'H:{moves[0][1]},{moves[1][1]}'
    elif len(moves) == 1:
        return f'H:{moves[0][1]},P'
    else:
        return 'H:P,P'
