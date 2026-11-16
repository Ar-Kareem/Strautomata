
import numpy as np

def policy(board):
    """
    Battleship AI using parity search with probability weighting and efficient targeting.
    Strategy: 
    1. If hits exist, try to extend lines or target neighbors
    2. Otherwise, use parity-based probabilistic search
    """
    board = np.array(board, dtype=int)
    N = 10
    ships = [5, 4, 3, 3, 2]
    
    # Helper to check bounds
    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N
    
    # Phase 1: Target around hits
    hits = np.argwhere(board == 1)
    
    if len(hits) > 0:
        # First, try to extend any lines of hits
        for r, c in hits:
            # Check horizontal line (both directions)
            line_length = 1
            left = c - 1
            right = c + 1
            
            # Count left
            while left >= 0 and board[r, left] == 1:
                line_length += 1
                left -= 1
            # Count right
            while right < N and board[r, right] == 1:
                line_length += 1
                right += 1
            
            # If line has multiple hits, try to extend
            if line_length > 1:
                if left >= 0 and board[r, left] == 0:
                    return (r, left)
                if right < N and board[r, right] == 0:
                    return (r, right)
            
            # Check vertical line (both directions)
            line_length = 1
            top = r - 1
            bottom = r + 1
            
            # Count up
            while top >= 0 and board[top, c] == 1:
                line_length += 1
                top -= 1
            # Count down
            while bottom < N and board[bottom, c] == 1:
                line_length += 1
                bottom += 1
            
            # If line has multiple hits, try to extend
            if line_length > 1:
                if top >= 0 and board[top, c] == 0:
                    return (top, c)
                if bottom < N and board[bottom, c] == 0:
                    return (bottom, c)
        
        # If no extendable lines, target neighbors of isolated hits
        for r, c in hits:
            for nr, nc in [(r-1,c), (r+1,c), (r,c-1), (r,c+1)]:
                if in_bounds(nr, nc) and board[nr, nc] == 0:
                    return (nr, nc)
    
    # Phase 2: Probabilistic parity search
    prob = np.zeros((N, N))
    
    # Count possible ship placements for each cell
    for length in ships:
        # Horizontal placements
        for r in range(N):
            for c in range(N - length + 1):
                if np.all(board[r, c:c+length] >= 0):
                    prob[r, c:c+length] += 1
        
        # Vertical placements
        for r in range(N - length + 1):
            for c in range(N):
                if np.all(board[r:r+length, c] >= 0):
                    prob[r:r+length, c] += 1
    
    # Mask to unknown cells only
    prob *= (board == 0)
    
    # Checkerboard pattern for initial search efficiency
    parity = (np.arange(N)[:, None] + np.arange(N)[None, :]) % 2
    
    # Select best cell
    if prob.max() > 0:
        max_val = prob.max()
        candidates = np.argwhere(prob == max_val)
        
        # Among max probability cells, prefer parity cells
        for r, c in candidates:
            if parity[r, c] == 0:
                return (r, c)
        
        return tuple(candidates[0])
    
    # Final fallback: checkerboard pattern
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0 and parity[r, c] == 0:
                return (r, c)
    
    # Absolute fallback
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                return (r, c)
    
    return (0, 0)
