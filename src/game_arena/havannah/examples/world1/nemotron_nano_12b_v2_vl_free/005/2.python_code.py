
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_size = 15
    me_set = set(me)
    opp_set = set(opp)
    
    possible_moves = [
        (i, j) for i in range(board_size) for j in range(board_size)
        if valid_mask[i][j] and (i, j) not in me_set and (i, j) not in opp_set
    ]

    if not possible_moves:
        raise RuntimeError("No valid moves found. Game over.")

    # Precompute neighbors for all possible moves
    directions = [
        (-1, 0), (1, 0),    # Up and Down
        (0, -1), (0, 1),    # Left and Right
        (-1, -1), (-1, 1)   # Upper-Left and Upper-Right
    ]
    neighbors_map = {}
    for (x, y) in possible_moves:
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                neighbors.append((nx, ny))
        neighbors_map[(x, y)] = neighbors

    best = possible_moves[0]
    best_score = -float('inf')

    for move in possible_moves:
        i, j = move
        neighbors = neighbors_map[move]

        # Count adjacent friend and foe stones
        friend_adjacency = sum(1 for (x, y) in neighbors if (x, y) in me_set)
        foe_adjacency = sum(1 for (x, y) in neighbors if (x, y) in opp_set)

        # Positional score: closer to center = higher score
        dx = abs(i - 7)
        dy = abs(j - 7)
        center_distance = dx + dy
        positional_score = max(20 - center_distance * 2, 0)

        # Total score: more emphasis on connecting to friend stones and center
        score = friend_adjacency * 5 - foe_adjacency * 2 + positional_score

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
