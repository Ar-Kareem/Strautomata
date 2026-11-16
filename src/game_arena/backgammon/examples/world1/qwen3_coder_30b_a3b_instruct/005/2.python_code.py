
import random
import numpy as np

def policy(state):
    # Parse state information
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)  # Sort dice in descending order
    
    # Determine if we can bear off
    can_bear_off = True
    for i in range(18):  # Points 18-23 (our home board)
        if my_pts[i] > 0:
            can_bear_off = False
            break

    # Simple evaluation function (returns a score for a move, higher is better)
    def evaluate_move(move_str):
        score = 0
        # Prefer hits
        for i in range(len(move_str)):
            if move_str[i] == ',':
                break
        # Simplistic check: move to hit is better
        # In a full implementation, compute hits explicitly
        # For now, we use a very simple heuristic
        return score

    # Generate all possible legal moves - basic implementation
    # In reality, one would generate all possible move sequences, but that requires more complex logic
    # To simplify: if bar checkers, re-enter first. For other moves, try random valid moves.
    
    # If we have checkers on the bar, we must move them first
    if my_bar > 0:
        # Try to re-enter
        from_point = 'B'
        # Try to use the highest die to re-enter (but we need to make sure we can re-enter in that point)
        # The reentry point for a die "n" is 24 - n  (i is 0-based, so it's 23 - (die - 1))
        entry_point = 24 - dice[0] if dice else 0
        if entry_point < 24 and entry_point >= 0:
            # This assumes valid entry point
            # But since we're only checking if there's a checker on the bar, just return first valid move
            if dice[0] == 6:
                return 'H:B,A18'  # Example valid move
            elif dice[0] == 5:
                return 'H:B,A19'  # Example valid move
            else:
                return f'H:B,A{24 - dice[0]}'
        else:
            # If no reentry point is available (shouldn't happen in normal play)
            # Just pass
            return 'H:P,P'

    # Otherwise, generate legal moves using basic principles
    # This implementation focuses on providing a working solution rather than a fully optimized one
    # Check bearing off conditions
    # For simplicity, we'll just return a valid move, focusing on being correct rather than optimal
    
    # If bearing off is allowed, try to do so
    if can_bear_off and my_off < 15:
        if dice[0] == 1:
            for i in range(18, 24):
                if my_pts[i] > 0:
                    return 'H:A{},P'.format(i)
        elif dice[0] == 2:
            for i in range(18, 24):
                if my_pts[i] > 0:
                    return 'H:A{},P'.format(i)
        elif dice[0] == 3:
            for i in range(18, 24):
                if my_pts[i] > 0:
                    return 'H:A{},P'.format(i)
        elif dice[0] == 4:
            for i in range(18, 24):
                if my_pts[i] > 0:
                    return 'H:A{},P'.format(i)
        elif dice[0] == 5:
            for i in range(18, 24):
                if my_pts[i] > 0:
                    return 'H:A{},P'.format(i)
        elif dice[0] == 6:
            for i in range(18, 24):
                if my_pts[i] > 0:
                    return 'H:A{},P'.format(i)

    # If only 1 checker on the bar, try to re-enter and then make a move
    # If we're not at the bar, and we can make a move:
    # Find a point with a checker to move
    from_point1 = None
    from_point2 = None
    
    move_order = 'H'  # Default to higher die first
    
    # Try to find the best first move for non-bar checkers
    # This is a simple approach - in a real policy, one would do more advanced board evaluation
    
    # If there are no checkers on the bar, we move existing checkers
    if my_bar == 0:
        # Try to find a move with the highest die first
        # Simplified version
        for i in range(24):
            if my_pts[i] > 0 and not (i + dice[0] > 23 and dice[0] != 6):
                # Check that there's a valid destination for dice[0]
                dest = i - dice[0]
                if dest >= 0 and dest < 24:
                    if not (opp_pts[dest] >= 2):  # Not blocked by enemy 2 or more checkers
                        if from_point1 is None:
                            from_point1 = i
                        elif from_point2 is None:
                            if i != from_point1:
                                from_point2 = i
                                break
    
    if from_point1 is not None:
        if from_point2 is not None:
            return f'{move_order}:A{from_point1},A{from_point2}'
        else:
            return f'{move_order}:A{from_point1},P'
    else:
        # Return simple pass if cannot make move
        return 'H:P,P'
