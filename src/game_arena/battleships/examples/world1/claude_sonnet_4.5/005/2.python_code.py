
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Find all hits and unknown cells
    hits = []
    unknowns = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r, c))
    
    if not unknowns:
        return (0, 0)  # Shouldn't happen
    
    # Target mode: we have hits to follow up on
    if hits:
        targets = []
        
        # For each hit, check if it's part of an unsunk ship
        for r, c in hits:
            # Check all 4 directions for patterns
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                
                # If adjacent cell is unknown, it's a high-priority target
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    # Check if we have a line of hits in this direction
                    # to prioritize extending known ship segments
                    opposite_hit = False
                    if 0 <= r - dr < 10 and 0 <= c - dc < 10:
                        if board[r - dr][c - dc] == 1:
                            opposite_hit = True
                    
                    # Higher priority if extending a line
                    priority = 2 if opposite_hit else 1
                    targets.append((priority, nr, nc))
        
        if targets:
            # Sort by priority (higher first), then random
            targets.sort(key=lambda x: (-x[0], random.random()))
            return (targets[0][1], targets[0][2])
    
    # Hunt mode: use checkerboard pattern with density
    # Checkerboard pattern is efficient since smallest ship is length 2
    
    # Calculate a simple probability score for each unknown cell
    def score_cell(r, c):
        # Checkerboard pattern (parity matching)
        parity_score = 10 if (r + c) % 2 == 0 else 0
        
        # Prefer center (more possible ship placements)
        center_score = 5 - (abs(r - 4.5) + abs(c - 4.5)) / 2
        
        # Avoid cells adjacent to misses (less likely for long ships)
        miss_penalty = 0
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == -1:
                miss_penalty += 1
        
        return parity_score + center_score - miss_penalty * 0.5
    
    # Score all unknown cells
    scored_unknowns = [(score_cell(r, c), r, c) for r, c in unknowns]
    scored_unknowns.sort(reverse=True)
    
    return (scored_unknowns[0][1], scored_unknowns[0][2])
