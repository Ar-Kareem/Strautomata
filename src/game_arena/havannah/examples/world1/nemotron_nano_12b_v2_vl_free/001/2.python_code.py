
def policy(me, opp, valid_mask):
    import math

    # Convert to sets for O(1) lookups
    me_set = set(me)
    opp_set = set(opp)
    n = 15

    # Generate all valid moves
    valid_moves = []
    for r in range(n):
        for c in range(n):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))

    if not valid_moves:
        raise RuntimeError("No valid moves")

    # Define neighbor directions for hexagonal grid
    dirs = [
        (-1, 0), (1, 0),   # Up and Down (same column)
        (0, -1), (0, 1),   # Left and Right (same row)
        (-1, -1), (-1, 1)  # Upper-left and Upper-right
    ]

    best_move = None
    max_score = -math.inf

    for (r, c) in valid_moves:
        adj_me = 0
        adj_opp = 0

        # Check all adjacent cells
        for dr, dc in dirs:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < n and 0 <= nc < n:
                if (nr, nc) in me_set:
                    adj_me += 1
                elif (nr, nc) in opp_set:
                    adj_opp += 1

        # Calculate distance penalty to the center (7.5, 7.5)
        distance_penalty = (r - 7.5)**2 + (c - 7.5)**2

        # Heuristic weights
        score = (adj_me * 5) - (adj_opp * 3) - (distance_penalty * 0.1)

        # Update best move if current score is higher
        if score > max_score or (score == max_score and (r, c) == (7, 7)):
            max_score = score
            best_move = (r, c)

    return best_move
