
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = sorted(state['dice'])  # Sort dice to easily differentiate between high and low
    die1, die2 = (dice[1], dice[0]) if len(dice) > 1 else (dice[0], 0)

    def can_move(start, die):
        if 0 <= start - die < 24 and opp_pts[start - die] < 2:
            return True
        return False
    
    # If there are checkers on the bar, we must move them first
    if my_bar > 0:
        return f'H:B,P' if die1 > 0 else 'L:B,P'

    # List possible moves
    possible_moves = []
    
    # Check for moves using the higher die, then lower die
    for i in range(24):
        if my_pts[i] > 0:  # We have checkers on this point
            if can_move(i, die1):
                possible_moves.append(f'H:A{i},{f"A{i - die2}" if can_move(i, die2) else "P"}')
            if can_move(i, die2):
                possible_moves.append(f'L:A{i},{f"A{i - die1}" if can_move(i, die1) else "P"}')

    # Make a decision based on possible moves or a pass
    if possible_moves:
        return possible_moves[0]  # Return the first valid move

    # If no valid moves found, return pass
    return 'H:P,P'
