
import numpy as np
import itertools

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    arr = np.array(board, dtype=int)  # shape (3,3,3)
    
    # Generate all winning lines (list of list of (i,j,k) tuples)
    lines = []
    directions = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if not (dx == 0 and dy == 0 and dz == 0)]
    for dx, dy, dz in directions:
        # Determine starting indices range
        start_i_range = range(3) if dx == 0 else (0 if dx == 1 else 2,)
        start_j_range = range(3) if dy == 0 else (0 if dy == 1 else 2,)
        start_k_range = range(3) if dz == 0 else (0 if dz == 1 else 2,)
        for i in start_i_range:
            for j in start_j_range:
                for k in start_k_range:
                    end_i = i + 2 * dx
                    end_j = j + 2 * dy
                    end_k = k + 2 * dz
                    if 0 <= end_i < 3 and 0 <= end_j < 3 and 0 <= end_k < 3:
                        line = [(i, j, k), (i + dx, j + dy, k + dz), (i + 2*dx, j + 2*dy, k + 2*dz)]
                        # Avoid duplicates (some lines may be generated multiple times due to symmetry, but fine)
                        lines.append(line)
    
    # Helper to count pieces in a line
    def line_counts(line):
        counts = {1: 0, -1: 0, 0: 0}
        for (i, j, k) in line:
            val = arr[i, j, k]
            counts[val] += 1
        return counts[1], counts[-1], counts[0]
    
    # 1. Check for winning move
    for line in lines:
        ours, opp, empty = line_counts(line)
        if ours == 2 and empty == 1:
            # Find the empty cell in this line
            for (i, j, k) in line:
                if arr[i, j, k] == 0:
                    return (i, j, k)
    
    # 2. Block opponent's winning move
    for line in lines:
        ours, opp, empty = line_counts(line)
        if opp == 2 and empty == 1:
            for (i, j, k) in line:
                if arr[i, j, k] == 0:
                    return (i, j, k)
    
    # Heuristic evaluation of empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if arr[i, j, k] == 0]
    best_score = -1
    best_move = None
    
    # Precompute lines through each cell (for efficiency)
    lines_through = {cell: [] for cell in empty_cells}
    for line in lines:
        for cell in line:
            if cell in lines_through:
                lines_through[cell].append(line)
    
    for cell in empty_cells:
        score = 0
        # Center bonus
        if cell == (1, 1, 1):
            score += 20
        # Corner bonus (corners are (0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2))
        if sum(1 for coord in cell if coord in (0, 2)) == 3:
            score += 5
        
        for line in lines_through[cell]:
            ours, opp, empty = line_counts(line)
            if opp > 0:
                # opponent already in this line, not promising
                continue
            if ours == 1 and empty == 2:  # cell included, so actually after placing ours, line would have 2 ours
                score += 10
            elif ours == 0 and empty == 3:
                score += 1
        if score > best_score:
            best_score = score
            best_move = cell
    
    # Fallback: first empty cell (should not happen)
    if best_move is None:
        best_move = empty_cells[0]
    return best_move
