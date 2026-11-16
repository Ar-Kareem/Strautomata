import random

def policy(board):
    # Check for existing hits to guide targeting
    hits = []
    for row in range(10):
        for col in range(10):
            if board[row][col] == 1:
                hits.append((row, col))
    
    # If there are hits, use them to find ship direction
    if hits:
        candidates = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
        
        for (r, c) in hits:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                # Check adjacent cell in this direction
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    # Extend in the same direction to find next cell
                    nnr, nnc = nr + dr, nc + dc
                    if 0 <= nnr < 10 and 0 <= nnc < 10 and board[nnr][nnc] == 0:
                        candidates.append((nnr, nnc))
        
        # If candidates exist, choose the one with most adjacent unknowns
        if candidates:
            best_candidate = None
            best_adjacent = -1
            for (r, c) in candidates:
                adjacent_unknowns = 0
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        adjacent_unknowns += 1
                if adjacent_unknowns > best_adjacent:
                    best_adjacent = adjacent_unknowns
                    best_candidate = (r, c)
            return best_candidate
        
        # If no candidates from hits, choose random unknown cell
        unknown_cells = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
        if unknown_cells:
            return random.choice(unknown_cells)
        else:
            return (0, 0)
    
    # No hits: choose random unknown cell
    unknown_cells = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    if unknown_cells:
        return random.choice(unknown_cells)
    else:
        return (0, 0)