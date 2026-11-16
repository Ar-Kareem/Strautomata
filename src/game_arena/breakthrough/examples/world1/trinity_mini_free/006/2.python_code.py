
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction
    step = -1 if color == 'b' else 1
    
    # Check for immediate promotion (win condition)
    for (r, c) in me:
        if color == 'w' and r + step == 7:
            return ((r, c), (r + step, c))
        if color == 'b' and r + step == 0:
            return ((r, c), (r + step, c))
    
    # Evaluate all possible moves
    candidates = []
    for (r, c) in me:
        # Check captures
        for dr, dc in [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp:
                # Calculate opponent's distance to home row
                opp_dist = 7 - nr if color == 'w' else nr
                candidates.append((opp_dist, ((r, c), (nr, nc))))
        
        # Check forward moves
        for dr in [-1] if color == 'b' else [1]:
            nr, nc = r + dr, c
            if (nr, nc) not in me and (nr, nc) not in opp:
                # Calculate distance to opponent's home row
                new_dist = 7 - nr if color == 'w' else nr
                candidates.append((new_dist, ((r, c), (nr, nc))))
    
    # Select best move (prioritize captures, then forward moves)
    if candidates:
        candidates.sort(key=lambda x: x[0])  # Sort by distance metric
        return candidates[0][1]
    
    # Fallback: return any valid move if none found (should not occur)
    for (r, c) in me:
        for dr, dc in [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp:
                return ((r, c), (nr, nc))
        for dr in [-1] if color == 'b' else [1]:
            nr, nc = r + dr, c
            if (nr, nc) not in me and (nr, nc) not in opp:
                return ((r, c), (nr, nc))
    return ((0, 0), (0, 0))
