
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy for easier handling, though list works fine
    board = np.array(board)
    
    # Find all hits
    hits = np.argwhere(board == 1).tolist()
    
    if hits:
        # Targeting mode: Find unshot adjacent cells
        targets = set()
        for hi, hj in hits:
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = hi + di, hj + dj
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                    targets.add((ni, nj))
        if targets:
            # Select the first in sorted order for consistency
            target_list = sorted(list(targets))
            return tuple(target_list[0])
    
    # Hunting mode: All unshot cells
    candidates = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
    
    # Prioritize even parity (checkerboard)
    parity_candidates = [c for c in candidates if (c[0] + c[1]) % 2 == 0]
    if parity_candidates:
        parity_candidates.sort()  # Row-major order
        return tuple(parity_candidates[0])
    
    # Fallback to any unshot cell
    candidates.sort()
    return tuple(candidates[0])
