
def policy(state):
    # Check if there are checkers on the bar that need to be moved first
    if state['my_bar'] > 0:
        # Check both dice for possible moves from the bar
        dice = sorted(state['dice'], reverse=True)  # Sort dice in descending order
        possible_moves = []
        for die in dice:
            if die < 1 or die > 6:
                continue
            destination = die - 1
            if destination < 0 or destination >= 6:
                continue  # Not in opponent's home board
            if state['opp_pts'][destination] <= 1:
                possible_moves.append(die)
        
        # Generate the move string based on possible moves
        if len(possible_moves) >= 2:
            return f"H:B,B"
        elif len(possible_moves) == 1:
            return f"H:B,P"
        else:
            return "P:B,P"
    else:
        # Placeholder for board moves if no checkers are on the bar
        return "H:P,P"
