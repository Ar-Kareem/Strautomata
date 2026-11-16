
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Helper function to check if a point is within bounds
    def in_bounds(r, c):
        return 1 <= r <= 19 and 1 <= c <= 19
    
    # Helper function to check if a point is occupied
    def is_occupied(r, c):
        return (r, c) in me or (r, c) in opponent
    
    # Helper function to check if a point is empty
    def is_empty(r, c):
        return not is_occupied(r, c)
    
    # Helper function to check if a stone is surrounded (capture)
    def is_surrounded(r, c):
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            if is_occupied(nr, nc):
                continue
            return False
        return True
    
    # Check for capturing moves
    capture_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if not is_empty(r, c):
                continue
            captures = 0
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                if (nr, nc) in opponent:
                    # Check if opponent stone is surrounded
                    if is_surrounded(nr, nc):
                        captures += 1
            if captures > 0:
                capture_moves.append((r, c, captures))
    
    if capture_moves:
        # Choose move with most captures
        return max(capture_moves, key=lambda x: x[2])[0:2]
    
    # Evaluate center control and connectivity
    center_value = lambda r, c: (10 - r)**2 + (10 - c)**2
    move_value = lambda r, c: center_value(r, c) + sum(1 for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)] 
                                                  if is_occupied(r+dr, c+dc))
    
    # Find best move among empty points
    best_move = (0, 0)
    best_score = -float('inf')
    for r in range(1, 20):
        for c in range(1, 20):
            if not is_empty(r, c):
                continue
            # Check if move connects groups
            if any(is_occupied(r+dr, c+dc) for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]):
                score = move_value(r, c)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    return best_move
