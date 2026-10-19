
def policy(state, role):
    """
    Policy for the Stanford GameMaster game "cbnk" (checkers on a barrel board).
    Returns a legal move string for the given role (black or red).
    """

    # ----------------------------------------------------------------------
    # Helper: wrap a coordinate from 1..8 to the same range (barrel board)
    def wrap_y(y):
        return ((y - 1) % 8) + 1

    # ----------------------------------------------------------------------
    # Parse the state: collect positions of black and red pieces
    black_positions = []
    red_positions = []
    for fact in state:
        if fact[0] == "location":
            x = int(fact[1])
            y = int(fact[2])
            color = fact[3]
            if color == "black":
                black_positions.append((x, y))
            else:
                red_positions.append((x, y))

    # Determine own and opponent pieces
    if role == "black":
        own_positions = black_positions
        opp_positions = red_positions
    else:
        own_positions = red_positions
        opp_positions = black_positions

    # Sets for fast membership tests
    own_set = set(own_positions)
    opp_set = set(opp_positions)
    occupied = own_set | opp_set

    # Forward direction: +1 for black, -1 for red
    sign = 1 if role == "black" else -1

    # ----------------------------------------------------------------------
    # Generate captures (jumps)
    captures = []
    for x, y in own_positions:
        for dx in (-1, 1):
            jumped_x = x + dx
            # Horizontal boundaries must be respected
            if not (1 <= jumped_x <= 8):
                continue
            jumped_y = wrap_y(y + sign)
            # The jumped square must contain an opponent piece
            if (jumped_x, jumped_y) not in opp_set:
                continue
            landing_x = x + 2 * dx
            if not (1 <= landing_x <= 8):
                continue
            landing_y = wrap_y(y + 2 * sign)
            # Landing square must be empty
            if (landing_x, landing_y) in occupied:
                continue
            captures.append((x, y, jumped_x, jumped_y, landing_x, landing_y))

    # If any captures exist, select the best one
    if captures:
        # Heuristic: capture the opponent piece that is most advanced.
        # For black prefer higher y, for red prefer lower y.
        if role == "black":
            captures.sort(key=lambda m: m[3], reverse=True)  # sort by jumped_y descending
        else:
            captures.sort(key=lambda m: m[3])  # sort by jumped_y ascending
        best = captures[0]
        x1, y1, x2, y2, x3, y3 = best
        return f"jump({x1},{y1},{x2},{y2},{x3},{y3})"

    # ----------------------------------------------------------------------
    # Generate step moves
    steps = []
    for x, y in own_positions:
        for dx in (-1, 1):
            new_x = x + dx
            if not (1 <= new_x <= 8):
                continue
            new_y = wrap_y(y + sign)
            if (new_x, new_y) in occupied:
                continue
            steps.append((x, y, new_x, new_y))

    if not steps:
        # No legal moves at all
        return "noop"

    # Heuristic: move the piece that gets closest to the opponent's back‑rank.
    # Distance to opponent's back‑rank: for black it's (8 - new_y),
    # for red it's (new_y - 1). Smaller distance is better.
    if role == "black":
        steps.sort(key=lambda m: 8 - m[3])   # lower distance for black
    else:
        steps.sort(key=lambda m: m[3] - 1)    # lower distance for red

    best_step = steps[0]
    x1, y1, x2, y2 = best_step
    return f"move({x1},{y1},{x2},{y2})"
