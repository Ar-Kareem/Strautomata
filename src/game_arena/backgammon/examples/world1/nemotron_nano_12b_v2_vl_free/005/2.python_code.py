
def policy(state):
    my_pts = state['my_pts']
    my_bar = state['my_bar']
    opp_pts = state['opp_pts']
    dice = state['dice']

    def valid_home_reentry(dest):
        """Check if a die allows re-entry into the opponent's home (18-23)."""
        return 18 <= dest <= 23 and opp_pts[dest] <= 1

    def reentry_moves():
        """Return all valid re-entry points using the dice."""
        moves = []
        for die in [dice[0], dice[1]]:
            dest = 24 - die  # Entering from the bar to the opponent's home
            if valid_home_reentry(dest):
                moves.append(dest)
        return moves

    def bar_move(d):  # Returns 'B,A{point}'
        return f'B,A{d}' if 18 <= (24 - d) <= 23 else None

    def home_move(d, pt):
        """Try to move a checker from point `pt` forward by d spaces."""
        if pt < 0 or pt >= 24 or my_pts[pt] == 0:
            return None
        dest = pt - d
        if dest < 0:
            return None
        if opp_pts[dest] < 2 and not (bar > 0 and pt >= 18):
            return pt
        return None

    # Helper to generate a move from a point using a die
    def generate_move(pt, die):
        if pt < 0 or pt >= 24 or my_pts[pt] == 0:
            return None
        dest = pt - die
        if dest < 0:
            return None
        if dest == -1:  # bar to home
            return 'B'
        if 6 <= dest <= 17:
            return f'A{pt}'
        if 0 <= dest <= 5:
            return 'H:B,P'  # if bearing off is allowed
        return None

    # Case 1: Re-entry required
    if my_bar > 0:
        valid_entries = reentry_moves()
        if len(valid_entries) >= 2:
            # Two re-entries possible, must return both
            dests = [24 - dice[0], 24 - dice[1]]
            return f'H:B,A{dests[0]},B,A{dests[1]}'
        elif len(valid_entries) == 1:
            # Only one valid re-entry
            return f'H:B,A{valid_entries[0]}'
        else:
            return 'H:P,P'  # No valid move, engine must handle

    # Case 2: Bearing off (if all checkers are in the home board)
    if all(p == 0 for p in opp_pts[6:24]) and all(my_pts[6:] == 0):
        # Try to bear off
        results = []
        for d1, d2 in [(dice[0], dice[1]), (dice[1], dice[0])]:
            if my_pts[0] > 0 and d1 == 6:
                results.append('H:A0,P')
            if my_pts[0] > 0 and d2 == 6:
                results.append('L:A0,P')
            # Add other bearing off logic as needed
        return results[0] if results else 'H:P,P'

    # Case 3: General move
    # Try to build a prime or move toward home
    return 'H:A11,A10'  # Placeholder for actual logic
