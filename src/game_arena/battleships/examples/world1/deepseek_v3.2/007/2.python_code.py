
import itertools

# Precompute all possible ship placements for each ship length
PLACEMENTS = {}
for length in [2, 3, 4, 5]:
    placements = []
    # Horizontal placements
    for r in range(10):
        for c in range(10 - length + 1):
            placements.append([(r, c + i) for i in range(length)])
    # Vertical placements
    for r in range(10 - length + 1):
        for c in range(10):
            placements.append([(r + i, c) for i in range(length)])
    PLACEMENTS[length] = placements

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to list of lists for easier access
    # board is 10x10, values: 0 unknown, -1 miss, 1 hit
    
    # Step 1: Compute probability map from ship placements
    prob = [[0 for _ in range(10)] for _ in range(10)]
    
    # For each ship length, consider all placements
    # Lengths: 5,4,3,3,2 -> treat length 3 twice
    ship_lengths = [5, 4, 3, 3, 2]
    for length in ship_lengths:
        weight = 2 if length == 3 else 1  # two ships of length 3
        for placement in PLACEMENTS[length]:
            valid = True
            for (r, c) in placement:
                if board[r][c] == -1:  # misses cannot be part of a ship
                    valid = False
                    break
            if valid:
                for (r, c) in placement:
                    prob[r][c] += weight
    
    # Step 2: Find hits that have unknown neighbors
    hit_candidates = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                # Check orthogonal neighbors
                neighbors = []
                if r > 0 and board[r-1][c] == 0:
                    neighbors.append((r-1, c))
                if r < 9 and board[r+1][c] == 0:
                    neighbors.append((r+1, c))
                if c > 0 and board[r][c-1] == 0:
                    neighbors.append((r, c-1))
                if c < 9 and board[r][c+1] == 0:
                    neighbors.append((r, c+1))
                if neighbors:
                    hit_candidates.append((r, c))
    
    # If there are hits with unknown neighbors, target those neighbors
    if hit_candidates:
        # Collect all unknown neighbors of these hits
        target_cells = []
        for (r, c) in hit_candidates:
            if r > 0 and board[r-1][c] == 0:
                target_cells.append((r-1, c))
            if r < 9 and board[r+1][c] == 0:
                target_cells.append((r+1, c))
            if c > 0 and board[r][c-1] == 0:
                target_cells.append((r, c-1))
            if c < 9 and board[r][c+1] == 0:
                target_cells.append((r, c+1))
        # Remove duplicates
        target_cells = list(set(target_cells))
        # Choose the target cell with highest probability
        if target_cells:
            best_cell = max(target_cells, key=lambda rc: prob[rc[0]][rc[1]])
            return best_cell
    
    # Step 3: No hits to follow, choose cell with highest probability
    best_prob = -1
    best_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:  # unknown cell
                if prob[r][c] > best_prob:
                    best_prob = prob[r][c]
                    best_cells = [(r, c)]
                elif prob[r][c] == best_prob:
                    best_cells.append((r, c))
    
    # Tie-breaker: choose cell closest to center (prefer middle of board)
    if best_cells:
        center = (4.5, 4.5)  # center of 10x10 board (indices 0-9)
        best_cell = min(best_cells, key=lambda rc: (rc[0]-center[0])**2 + (rc[1]-center[1])**2)
        return best_cell
    
    # Fallback: should never happen, but return first unknown cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)  # no moves left
