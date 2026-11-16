
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Find all hits and unknown cells
    hits = set()
    unknown = set()
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.add((r, c))
            elif board[r][c] == 0:
                unknown.add((r, c))
    
    # Target mode: if we have hits, focus around them
    if hits:
        targets = {}  # maps position to priority score
        
        for r, c in hits:
            # Check if this hit is part of a line
            for dr, dc in [(0, 1), (1, 0)]:  # right and down
                line_hits = [(r, c)]
                
                # Extend forward
                nr, nc = r + dr, c + dc
                while 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    line_hits.append((nr, nc))
                    nr += dr
                    nc += dc
                
                # Extend backward
                nr, nc = r - dr, c - dc
                while 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    line_hits.append((nr, nc))
                    nr -= dr
                    nc -= dc
                
                # If we have a line of 2+ hits, prioritize endpoints
                if len(line_hits) >= 2:
                    line_hits.sort()
                    min_r, min_c = line_hits[0]
                    max_r, max_c = line_hits[-1]
                    
                    # Check endpoints
                    for nr, nc in [(min_r - dr, min_c - dc), (max_r + dr, max_c + dc)]:
                        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                            score = len(line_hits) * 10  # High priority for continuing lines
                            targets[(nr, nc)] = max(targets.get((nr, nc), 0), score)
        
        # Add orthogonal neighbors of isolated hits (lower priority)
        for r, c in hits:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    if (nr, nc) not in targets:
                        targets[(nr, nc)] = 1
        
        if targets:
            best_target = max(targets.keys(), key=lambda pos: targets[pos])
            return best_target
    
    # Hunt mode: use checkerboard pattern for efficiency
    # Checkerboard ensures we hit all ships (smallest is length 2)
    checkerboard = [(r, c) for r, c in unknown if (r + c) % 2 == 0]
    
    if checkerboard:
        return random.choice(checkerboard)
    
    # Fallback: any unknown cell
    if unknown:
        return random.choice(list(unknown))
    
    # Should never reach here in valid game
    return (0, 0)
