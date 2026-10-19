
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Find all hits
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # TARGET MODE: If we have hits, try to sink those ships
    if hits:
        # Look for hits that form a line (2+ in a row)
        for r, c in hits:
            # Check horizontal line
            for dc in [-1, 1]:
                if 0 <= c + dc < 10 and board[r][c + dc] == 1:
                    # Found horizontal pair, extend the line
                    for direction in [-1, 1]:
                        scan_c = c
                        # Find the end of the hit sequence
                        while 0 <= scan_c < 10 and board[r][scan_c] == 1:
                            scan_c += direction
                        # Fire at the next cell if it's unfired
                        if 0 <= scan_c < 10 and board[r][scan_c] == 0:
                            return (r, scan_c)
            
            # Check vertical line
            for dr in [-1, 1]:
                if 0 <= r + dr < 10 and board[r + dr][c] == 1:
                    # Found vertical pair, extend the line
                    for direction in [-1, 1]:
                        scan_r = r
                        # Find the end of the hit sequence
                        while 0 <= scan_r < 10 and board[scan_r][c] == 1:
                            scan_r += direction
                        # Fire at the next cell if it's unfired
                        if 0 <= scan_r < 10 and board[scan_r][c] == 0:
                            return (scan_r, c)
        
        # No line found, target adjacent cells of any hit
        for r, c in hits:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # HUNT MODE: Use probability density to find ships
    ship_lengths = [5, 4, 3, 3, 2]
    prob = [[0 for _ in range(10)] for _ in range(10)]
    
    # Calculate probability for each unfired cell
    for length in ship_lengths:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                can_fit = True
                for i in range(length):
                    if board[r][c + i] != 0:  # Already fired here
                        can_fit = False
                        break
                if can_fit:
                    for i in range(length):
                        prob[r][c + i] += 1
        
        # Vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                can_fit = True
                for i in range(length):
                    if board[r + i][c] != 0:  # Already fired here
                        can_fit = False
                        break
                if can_fit:
                    for i in range(length):
                        prob[r + i][c] += 1
    
    # Find unfired cells with maximum probability
    best_cells = []
    max_prob = -1
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:  # Unfired
                if prob[r][c] > max_prob:
                    max_prob = prob[r][c]
                    best_cells = [(r, c)]
                elif prob[r][c] == max_prob:
                    best_cells.append((r, c))
    
    if best_cells:
        # Prefer checkerboard parity for efficiency
        checkerboard = [(r, c) for r, c in best_cells if (r + c) % 2 == 0]
        if checkerboard:
            return random.choice(checkerboard)
        return random.choice(best_cells)
    
    # Fallback: find any unfired cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
