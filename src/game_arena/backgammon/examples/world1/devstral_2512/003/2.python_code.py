
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    higher_die = dice[0] if len(dice) > 0 else 0
    lower_die = dice[1] if len(dice) > 1 else 0

    # Helper function to check if a point is safe (not blocked by opponent)
    def is_safe(point):
        return opp_pts[point] < 2

    # Helper function to generate all possible moves from a given point
    def get_possible_moves(from_point, die):
        moves = []
        if from_point == 'B':
            # Re-entering from bar: can enter on opponent's home board (points 0-5)
            for i in range(6):
                if is_safe(i) and (i + 1) == die:
                    moves.append(('B', i))
        else:
            # Moving from a point
            from_idx = int(from_point[1:])
            to_idx = from_idx - die
            if to_idx >= 0 and is_safe(to_idx):
                moves.append((from_point, to_idx))
        return moves

    # Helper function to check if all checkers are in home board
    def all_in_home():
        for i in range(6, 24):
            if my_pts[i] > 0:
                return False
        return True

    # Helper function to generate bearing off moves
    def get_bearing_off_moves(die):
        moves = []
        if all_in_home():
            # Find the highest point with checkers that can be borne off
            for i in range(5, -1, -1):
                if my_pts[i] > 0 and (i + 1) <= die:
                    moves.append(('A' + str(i), 'off'))
                    break
        return moves

    # Generate all possible moves
    possible_moves = []

    # Case 1: Checkers on bar
    if my_bar > 0:
        for die in [higher_die, lower_die]:
            moves = get_possible_moves('B', die)
            for move in moves:
                possible_moves.append((move[0], move[1], die))
        # If no moves from bar, must pass
        if not possible_moves:
            return "H:P,P"
    else:
        # Case 2: No checkers on bar
        # Check for bearing off
        if all_in_home():
            for die in [higher_die, lower_die]:
                moves = get_bearing_off_moves(die)
                for move in moves:
                    possible_moves.append((move[0], 'off', die))
            # If no bearing off moves, look for regular moves
            if not possible_moves:
                for i in range(24):
                    if my_pts[i] > 0:
                        for die in [higher_die, lower_die]:
                            moves = get_possible_moves('A' + str(i), die)
                            for move in moves:
                                possible_moves.append((move[0], move[1], die))
        else:
            # Regular moves
            for i in range(24):
                if my_pts[i] > 0:
                    for die in [higher_die, lower_die]:
                        moves = get_possible_moves('A' + str(i), die)
                        for move in moves:
                            possible_moves.append((move[0], move[1], die))

    # If no moves found, pass
    if not possible_moves:
        return "H:P,P"

    # Select the best move based on strategy
    # Priority: 1. Hit opponent's blot, 2. Safe move, 3. Build point
    best_move = None
    best_score = -1

    for move in possible_moves:
        from_point, to_point, die = move
        score = 0

        # Check if this move hits an opponent's blot
        if to_point != 'off' and opp_pts[to_point] == 1:
            score += 10  # High priority for hitting

        # Check if this move is safe (not leaving a blot)
        if to_point != 'off':
            # After moving, check if the from point is safe
            from_idx = int(from_point[1:]) if from_point != 'B' else -1
            if from_idx != -1 and my_pts[from_idx] - 1 < 2 and opp_pts[from_idx] >= 1:
                score -= 5  # Penalty for leaving a blot

        # Check if this move builds a new point
        if to_point != 'off':
            if my_pts[to_point] == 1:
                score += 3  # Building a point is good

        # Check if this move bears off a checker
        if to_point == 'off':
            score += 2  # Bearing off is good

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    # If no move found (shouldn't happen), pass
    if not best_move:
        return "H:P,P"

    # Determine the order (H or L)
    from1, to1, die1 = best_move
    remaining_dice = [d for d in dice if d != die1]

    # Find a second move if possible
    from2 = 'P'
    if remaining_dice:
        # Try to find a second move with the remaining die
        second_die = remaining_dice[0]
        if my_bar > 0:
            moves = get_possible_moves('B', second_die)
            if moves:
                from2 = 'B'
        else:
            for i in range(24):
                if my_pts[i] > 0:
                    moves = get_possible_moves('A' + str(i), second_die)
                    if moves:
                        from2 = 'A' + str(i)
                        break

    # Determine order
    if die1 == higher_die:
        order = 'H'
    else:
        order = 'L'

    return f"{order}:{from1},{from2}"
