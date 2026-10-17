
def policy(board):
    # Collect all possible moves: cells that are 0 (unknown)
    possibles = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
    
    # Find all hits (1s) to check if we need targeting mode
    hits = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]
    
    if hits:
        # Target mode: collect adjacent cells to hits that are 0
        candidates = []
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, down, left, right
        for i, j in hits:
            for di, dj in dirs:
                ni, nj = i + di, j + dj
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                    if (ni, nj) not in candidates:  # Avoid duplicates
                        candidates.append((ni, nj))
        if candidates:
            # Select the first candidate (priorities expansion around hits)
            return candidates[0]
    
    # Hunt mode: default to even parity checkerboard, sorted for systematic scanning
    # Prefer (i+j) % 2 == 0, but fall back to any remaining cells
    hunter_targets = [p for p in possibles if (p[0] + p[1]) % 2 == 0]
    if hunter_targets:
        hunter_targets.sort()  # Lexical order: top-left to bottom-right
        return hunter_targets[0]
    else:
        # Only odd parity or limited cells left; pick first possible
        return possibles[0]
