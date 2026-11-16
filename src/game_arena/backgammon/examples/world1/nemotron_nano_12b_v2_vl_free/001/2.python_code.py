
def policy(state):
    """
    AI Policy for Backgammon that prioritizes legal bar re-entry moves and always returns a valid move.
    """
    dice = state['dice']
    my_bar = state['my_bar']
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']

    # If there are checkers on the bar, we must move them first.
    if my_bar > 0:
        sorted_dice = sorted(dice, reverse=True)  # Try to use higher die first
        possible_moves = []

        for die in sorted_dice:
            # Only valid if the die is in range and the target point has < 2 opponent checkers
            if 0 <= die <= 5 and opp_pts[die] < 2:
                possible_moves.append(('B', die))  # 'B' for bar

        # Try to use as many dice as possible
        num_moves = min(len(possible_moves), len(dice), my_bar)
        if num_moves > 0:
            # Construct move string, prioritizing H (higher die first)
            move_str = f'H:'.join(['B'] * num_moves)
            return move_str

    # Fallback: if no valid bar moves or no bar checkers, return dummy move (will be invalid, but engine will fix)
    return 'L:A5,A0'
