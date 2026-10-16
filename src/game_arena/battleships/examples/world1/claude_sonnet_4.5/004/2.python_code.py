
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Targeting policy for Battleship.
    Returns (row, col) to fire at next.
    """
    import random
    
    # Find all hits and their neighbors
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # If we have hits, prioritize targeting around them
    if hits:
        # Find hits that are part of a line (have adjacent hits)
        lines = []
        isolated_hits = []
        
        for r, c in hits:
            adjacent_hits = []
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    adjacent_hits.append((nr, nc))
            
            if adjacent_hits:
                lines.append((r, c, adjacent_hits))
            else:
                isolated_hits.append((r, c))
        
        # Priority 1: Extend known ship lines
        if lines:
            candidates = []
            for r, c, adj in lines:
                # Determine orientation
                for ar, ac in adj:
                    if ar == r:  # Horizontal line
                        # Try extending left and right
                        for dc in [-1, 1]:
                            nc = c + dc
                            while 0 <= nc < 10:
                                if board[r][nc] == 0:
                                    candidates.append((r, nc))
                                    break
                                elif board[r][nc] == -1:
                                    break
                                nc += dc
                    else:  # Vertical line (ac == c)
                        # Try extending up and down
                        for dr in [-1, 1]:
                            nr = r + dr
                            while 0 <= nr < 10:
                                if board[nr][c] == 0:
                                    candidates.append((nr, c))
                                    break
                                elif board[nr][c] == -1:
                                    break
                                nr += dr
            
            if candidates:
                # Remove duplicates and return first
                candidates = list(set(candidates))
                return candidates[0]
        
        # Priority 2: Target adjacent to isolated hits
        candidates = []
        for r, c in isolated_hits:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.append((nr, nc))
        
        if candidates:
            # Remove duplicates
            candidates = list(set(candidates))
            return candidates[0]
    
    # Hunt mode: Use checkerboard pattern
    # Prioritize cells where ships are more likely to fit
    
    # Try parity pattern (row + col) % 2 == 0 first
    parity_0 = []
    parity_1 = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if (r + c) % 2 == 0:
                    parity_0.append((r, c))
                else:
                    parity_1.append((r, c))
    
    # Count how many unknowns we've checked
    total_unknown = len(parity_0) + len(parity_1)
    
    # Use parity 0 first (typically better coverage)
    if parity_0:
        # Prefer center cells early on for better probability
        if total_unknown > 50:
            parity_0.sort(key=lambda pos: abs(pos[0] - 4.5) + abs(pos[1] - 4.5))
        return parity_0[0]
    elif parity_1:
        if total_unknown > 50:
            parity_1.sort(key=lambda pos: abs(pos[0] - 4.5) + abs(pos[1] - 4.5))
        return parity_1[0]
    
    # Fallback: return any unknown cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # Should never reach here in a valid game
    return (0, 0)
