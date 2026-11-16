import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship AI policy.
    0: Unknown, -1: Miss, 1: Hit.
    Grid: 10x10.
    """
    size = 10
    hits = []
    for r in range(size):
        for c in range(size):
            if board[r][c] == 1:
                hits.append((r, c))

    # Target Mode: If there's at least one hit, try to sink the ship
    target_candidates = []
    if hits:
        for r, c in hits:
            # Check neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0:
                    # Heuristic: Check if this neighbor continues a line of hits
                    weight = 1
                    # Look in the opposite direction
                    pr, pc = r - dr, c - dc
                    if 0 <= pr < size and 0 <= pc < size and board[pr][pc] == 1:
                        weight += 2 # Higher priority for following a line
                    
                    target_candidates.append((weight, (nr, nc)))
        
        if target_candidates:
            # Sort by weight descending
            target_candidates.sort(key=lambda x: x[0], reverse=True)
            # Return the best candidate (or random if weights equal)
            best_weight = target_candidates[0][0]
            top_choices = [pos for w, pos in target_candidates if w == best_weight]
            return random.choice(top_choices)

    # Hunt Mode: Fire at unknown squares using parity (checkerboard)
    # Since the smallest ship is size 2, checking every other square is efficient.
    parity_cells = []
    other_cells = []
    
    for r in range(size):
        for c in range(size):
            if board[r][c] == 0:
                # Use parity to narrow search
                if (r + c) % 2 == 0:
                    parity_cells.append((r, c))
                else:
                    other_cells.append((r, c))

    # Prefer cells in the parity group
    hunt_pool = parity_cells if parity_cells else other_cells
    
    # Simple density heuristic: favor cells with more unknown neighbors
    best_hunt_cell = None
    max_neighbors = -1
    
    # Shuffle to avoid predictable patterns
    random.shuffle(hunt_pool)
    
    for r, c in hunt_pool:
        unknown_neighbors = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0:
                unknown_neighbors += 1
        
        if unknown_neighbors > max_neighbors:
            max_neighbors = unknown_neighbors
            best_hunt_cell = (r, c)
            
    return best_hunt_cell if best_hunt_cell else random.choice(hunt_pool)
