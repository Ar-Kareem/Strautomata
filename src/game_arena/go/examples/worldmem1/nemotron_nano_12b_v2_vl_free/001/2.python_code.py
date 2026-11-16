
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Combine occupied cells from both players
    occupied = frozenset(me + opponent)
    # Generate all possible empty cells
    possible_moves = []
    for row in range(1, 20):
        for col in range(1, 20):
            if (row, col) not in occupied:
                possible_moves.append((row, col))
    
    # If the board is full, return a pass
    if not possible_moves:
        return (0, 0), memory
    
    # Check if there are any existing own stones
    my_stones = set(me)
    if my_stones:
        # Find moves adjacent to existing stones for expansion
        adjacent_moves = []
        for move in possible_moves:
            r, c = move
            if ((r > 1 and (r - 1, c) in my_stones) or
                (r < 19 and (r + 1, c) in my_stones) or
                (c > 1 and (r, c - 1) in my_stones) or
                (c < 19 and (r, c + 1) in my_stones)):
                adjacent_moves.append(move)
        # Prioritize adjacent moves
        candidates = adjacent_moves
    else:
        # No stones yet: select from all possible moves
        candidates = possible_moves
    
    # Calculate liberties and distance to center for each candidate
    def calculate_liberties(move):
        r, c = move
        lib = 0
        if r > 1 and (r - 1, c) not in occupied: lib += 1
        if r < 19 and (r + 1, c) not in occupied: lib += 1
        if c > 1 and (r, c - 1) not in occupied: lib += 1
        if c < 19 and (r, c + 1) not in occupied: lib += 1
        return lib
    
    move_metrics = []
    for move in candidates:
        r, c = move
        lib = calculate_liberties(move)
        dist = (r - 10) ** 2 + (c - 10) ** 2  # Euclidean distance squared to center
        move_metrics.append((lib, dist, r, c))
    
    # Sort by: liberties descending, distance ascending, row, column
    sorted_moves = sorted(move_metrics, key=lambda x: (-x[0], x[1], x[2], x[3]))
    best_move = (sorted_moves[0][2], sorted_moves[0][3])
    
    # Return the best move and preserve the memory state
    return (best_move, memory)
