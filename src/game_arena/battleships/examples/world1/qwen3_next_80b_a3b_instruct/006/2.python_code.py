
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy for efficiency
    board = np.array(board)
    n = 10
    unknown = (board == 0)
    hits = (board == 1)
    misses = (board == -1)
    
    # Track which ships are still alive (by total hit count)
    # Standard ships: [5, 4, 3, 3, 2]
    total_ship_cells = 5 + 4 + 3 + 3 + 2
    total_hits = np.sum(hits)
    remaining_ships = []
    remaining_counts = [5, 4, 3, 3, 2]
    # Deduce which ships are still alive by comparing total hits to expected ship lengths
    # We assume we haven't sunk any ship yet unless we've hit exactly its length
    for length in remaining_counts:
        # If we have hit 'length' cells of a ship of this length, it's sunk
        # But we don't know which hit belongs to which ship, so we estimate based on total
        # We'll just keep track of total remaining ship length and use it for probability
        pass  # We'll use total_hits to infer remaining ship count implicitly
    
    # If no hits yet, use checkerboard pattern for initial search
    if total_hits == 0:
        # Checkerboard: only shoot on (row+col) % 2 == 0 cells to maximize coverage
        # This ensures we'll hit any ship >=2 in at least one cell quickly
        candidates = []
        for i in range(n):
            for j in range(n):
                if unknown[i, j]:
                    if (i + j) % 2 == 0:
                        candidates.append((i, j))
        if candidates:
            return candidates[0]  # Return first available in order
        else:
            # Fallback: use any unknown (shouldn't happen)
            for i in range(n):
                for j in range(n):
                    if unknown[i, j]:
                        return (i, j)
    
    # Find all hit cells
    hit_cells = list(zip(*np.where(hits)))
    
    # Look for potential ship orientation from existing hits
    # For each hit, check neighbors for continuation
    for r, c in hit_cells:
        # Check 4 directions for another hit to determine orientation
        directions = [(-1, 0), (1, 0), (0, 1), (0, -1)]  # up, down, right, left
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr, nc] == 1:
                # Found a connected hit! Now try to extend along this line
                # Determine direction vector
                # Try to extend in both directions along this line
                hit_line = [(r, c), (nr, nc)]
                # Extend in the direction of (dr, dc)
                r1, c1 = nr + dr, nc + dc
                while 0 <= r1 < n and 0 <= c1 < n and board[r1, c1] == 1:
                    hit_line.append((r1, c1))
                    r1 += dr
                    c1 += dc
                # Extend in opposite direction
                r2, c2 = r - dr, c - dc
                while 0 <= r2 < n and 0 <= c2 < n and board[r2, c2] == 1:
                    hit_line.append((r2, c2))
                    r2 -= dr
                    c2 -= dc
                
                # Now we have a line of hits. Try to fire at ends
                start_r, start_c = hit_line[0]
                end_r, end_c = hit_line[-1]
                # Try the cell before the start
                r_prev, c_prev = start_r - dr, start_c - dc
                if 0 <= r_prev < n and 0 <= c_prev < n and unknown[r_prev, c_prev]:
                    return (r_prev, c_prev)
                # Try the cell after the end
                r_next, c_next = end_r + dr, end_c + dc
                if 0 <= r_next < n and 0 <= c_next < n and unknown[r_next, c_next]:
                    return (r_next, c_next)
                # If no clear extension, then try adjacent perpendicular to break symmetry
                # But we want to prioritize extending first
                
                # If we've already found a line, we'll stick to it, because sinking is priority
    
    # If no line is fully determined or we have isolated hits, use probability map
    
    # Compute probability map for all unknown cells
    # We'll calculate for each unknown cell: how many possible placements of remaining ships can cover it
    ship_lengths = [5, 4, 3, 3, 2]
    hit_count = total_hits
    # Estimate remaining ships: remove sunk ships (those with full hit count)
    # But since we don't know which hit belongs to which ship, we assume all are still alive until full hit
    remaining_ships = ship_lengths[:]  # Copy
    
    # We'll simulate all possible ship placements for each ship and count coverage
    # But this is expensive - let's optimize by precomputing possible placements for each ship length
    # And cache based on current hits and misses
    
    # We'll compute a simple heuristic: for each unknown cell, count how many ships of each length
    # can still be placed such that they cover this cell (without overlapping misses or known hits)
    
    prob_map = np.zeros((n, n), dtype=float)
    
    # For each remaining ship length, count possible placements that include each cell
    for length in remaining_ships:
        # Skip if this ship is likely sunk? We don't know. Assume alive.
        # For each possible placement of a ship of this length
        for r in range(n):
            for c in range(n):
                # Try horizontal placement
                if c + length <= n:
                    valid = True
                    for dc in range(length):
                        if board[r, c + dc] == -1:  # Miss means placement invalid
                            valid = False
                            break
                    if valid:
                        # Check if this placement overlaps any known hit? That's allowed!
                        # We can place ship over known hits without conflict
                        for dc in range(length):
                            if unknown[r, c + dc]:
                                prob_map[r, c + dc] += 1.0 / length  # Weight by how many cells it covers
                # Try vertical placement
                if r + length <= n:
                    valid = True
                    for dr in range(length):
                        if board[r + dr, c] == -1:
                            valid = False
                            break
                    if valid:
                        for dr in range(length):
                            if unknown[r + dr, c]:
                                prob_map[r + dr, c] += 1.0 / length
    
    # Also give extra weight to cells near multiple hits (if partial hit pattern present)
    # We'll use a simple heuristic: if a cell is adjacent to a hit, give it bonus
    # But we already have the hit-line detection above, so this is fallback
    
    # Find the unknown cell with maximum probability
    max_prob = -1
    best_cell = None
    for i in range(n):
        for j in range(n):
            if unknown[i, j]:
                if prob_map[i, j] > max_prob:
                    max_prob = prob_map[i, j]
                    best_cell = (i, j)
                # If tie, prefer higher row+col? No, we want randomness but deterministic
                # We'll pick first max, which is deterministic and fine
    
    if best_cell is not None:
        return best_cell
    
    # Fallback: if we still haven't found a move (shouldn't happen with unknown cells)
    # Use checkerboard on leftmost possible
    for i in range(n):
        for j in range(n):
            if unknown[i, j]:
                return (i, j)
    
    # This should never be reached
    return (0, 0)
