
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship strategy using probabilistic targeting and hunt/target modes.
    """
    # Convert to numpy array for convenience
    b = np.array(board, dtype=int)
    
    # SHIP_LENGTHS: sizes of all ships that we need to sink
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    SIZE = 10
    
    # ---------- Helper functions ----------
    def is_valid(r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE
    
    # Check if a ship of given length can be placed at (r,c) horizontally
    def can_place_horiz(r, c, length):
        if c + length > SIZE:
            return False
        for j in range(length):
            # must not be a miss or a hit on a different ship (hit of same ship allowed)
            if b[r][c+j] == -1:
                return False
            # if it's a hit here, we still allow placement (it means part of ship)
        return True
    
    # Check if a ship of given length can be placed at (r,c) vertically
    def can_place_vert(r, c, length):
        if r + length > SIZE:
            return False
        for i in range(length):
            if b[r+i][c] == -1:
                return False
        return True
    
    # ---------- Identify hits and adjacent cells ----------
    # We need to find all '1' cells to possibly target neighbors
    hit_cells = np.argwhere(b == 1)  # list of [r, c]
    
    # If there are hits, we attempt to target mode first
    if len(hit_cells) > 0:
        # For each hit cell, look at its 4 orthogonal neighbors
        target_candidates = set()
        for r, c in hit_cells:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if is_valid(nr, nc) and b[nr][nc] == 0:
                    target_candidates.add((nr, nc))
        
        if target_candidates:
            # In target mode, choose the most promising candidate
            # Score based on:
            # - Part of a possible ship given the local pattern
            # - Adjacent hits that form a line
            
            # Detect line direction of adjacent hits for this candidate
            best_cell = None
            best_score = -1
            
            for (nr, nc) in target_candidates:
                score = 0
                # Check how many adjacent hits there are (connectedness)
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    adj_r, adj_c = nr+dr, nc+dc
                    if is_valid(adj_r, adj_c) and b[adj_r][adj_c] == 1:
                        score += 2
                # Prefer cells that extend an existing line of hits
                # Check if there are two hits in a row along some axis passing through this cell
                # horizontal
                h_count = 0
                if is_valid(nr, nc-1) and b[nr][nc-1] == 1:
                    h_count += 1
                if is_valid(nr, nc+1) and b[nr][nc+1] == 1:
                    h_count += 1
                # vertical
                v_count = 0
                if is_valid(nr-1, nc) and b[nr-1][nc] == 1:
                    v_count += 1
                if is_valid(nr+1, nc) and b[nr+1][nc] == 1:
                    v_count += 1
                score += max(h_count, v_count) * 3
                
                if score > best_score:
                    best_score = score
                    best_cell = (nr, nc)
            
            return best_cell
    
    # ---------- Hunt mode: probabilistic targeting ----------
    # Find all remaining unknown cells
    unknown_cells = np.argwhere(b == 0)
    
    # If none (shouldn't happen), return (0,0)
    if len(unknown_cells) == 0:
        return (0, 0)
    
    # Determine remaining ships using hits count and pattern
    # We don't know exact remaining ships, so we treat all as still possible for simplicity
    # Better approach: estimate remaining ship lengths from unmatched hits
    # For simplicity, we'll assume all ships are still possible and count probability from each
    
    # Probability map
    prob_map = np.zeros((SIZE, SIZE), dtype=float)
    
    # For each ship length, for each possible placement, add weight to each covered unknown cell
    for length in SHIP_LENGTHS:
        for r in range(SIZE):
            for c in range(SIZE):
                if can_place_horiz(r, c, length):
                    for j in range(length):
                        if b[r][c+j] == 0:
                            prob_map[r][c+j] += 1.0
                if can_place_vert(r, c, length):
                    for i in range(length):
                        if b[r+i][c] == 0:
                            prob_map[r+i][c] += 1.0
    
    # Normalize or not? Not needed, we just take max probability
    # Find the maximum probability cell among unknown cells
    max_prob = -1.0
    best_move = None
    for r, c in unknown_cells:
        if prob_map[r][c] > max_prob:
            max_prob = prob_map[r][c]
            best_move = (int(r), int(c))
        elif prob_map[r][c] == max_prob:
            # Tie-break by preferring center-ish cells (heuristic)
            if best_move is None:
                best_move = (int(r), int(c))
            else:
                dist_old = (best_move[0]-4.5)**2 + (best_move[1]-4.5)**2
                dist_new = (r-4.5)**2 + (c-4.5)**2
                if dist_new < dist_old:
                    best_move = (int(r), int(c))
    
    # Fallback (should not happen)
    if best_move is None:
        for r in range(SIZE):
            for c in range(SIZE):
                if b[r][c] == 0:
                    return (r, c)
    
    return best_move
