
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    n = len(board)
    
    # Find all hit positions
    hits = []
    misses = []
    unknown = []
    
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:
                hits.append((i, j))
            elif board[i][j] == -1:
                misses.append((i, j))
            else:
                unknown.append((i, j))
    
    # If we have no hits, shoot randomly
    if not hits:
        return random.choice(unknown)
    
    # If we have hits, try to complete the ships
    # First, check if we have any ship that can be extended in a straight line
    for hit in hits:
        r, c = hit
        
        # Check horizontal and vertical directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            # Check if we can extend in this direction
            nr, nc = r + dr, c + dc
            
            # Check if the adjacent cell is valid and unknown
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                # Check if extending further in this direction would be consistent
                # with possible ship placements
                extended_r, extended_c = nr + dr, nc + dc
                if 0 <= extended_r < n and 0 <= extended_c < n:
                    # If the cell after the target is a hit, this is likely the right direction
                    if board[extended_r][extended_c] == 1:
                        return (nr, nc)
                # If we have only one hit, try this direction
                elif len(hits) == 1:
                    return (nr, nc)
                
                # If we have a line of hits, continue in that direction
                if len(hits) > 1:
                    # Check if this hit is part of a line
                    for dr2, dc2 in directions:
                        if (dr2, dc2) == (-dr, -dc):  # Skip the opposite direction
                            continue
                        nr2, nc2 = r + dr2, c + dc2
                        if 0 <= nr2 < n and 0 <= nc2 < n and board[nr2][nc2] == 1:
                            # We found another hit in a different direction
                            # This means we should continue in the original direction
                            return (nr, nc)
        
        # If we have multiple hits, try to determine the orientation
        if len(hits) > 1:
            # Try to find hits that are in a line
            for other_hit in hits:
                if other_hit == hit:
                    continue
                or_, oc = other_hit
                
                # Check if they are in the same row or column
                if r == or_:
                    # Same row, try left and right
                    min_c = min(c, oc)
                    max_c = max(c, oc)
                    # Check left
                    if min_c > 0 and board[r][min_c - 1] == 0:
                        return (r, min_c - 1)
                    # Check right
                    if max_c < n - 1 and board[r][max_c + 1] == 0:
                        return (r, max_c + 1)
                elif c == oc:
                    # Same column, try up and down
                    min_r = min(r, or_)
                    max_r = max(r, or_)
                    # Check up
                    if min_r > 0 and board[min_r - 1][c] == 0:
                        return (min_r - 1, c)
                    # Check down
                    if max_r < n - 1 and board[max_r + 1][c] == 0:
                        return (max_r + 1, c)
    
    # If we have hits but no clear direction, try neighbors of hits
    for hit in hits:
        r, c = hit
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                neighbors.append((nr, nc))
        if neighbors:
            return random.choice(neighbors)
    
    # Fallback to random shooting with parity strategy
    # Shoot at cells that are more likely to contain ships (checkerboard pattern)
    parity_positions = []
    for i in range(n):
        for j in range(n):
            if (i + j) % 2 == 0 and board[i][j] == 0:
                parity_positions.append((i, j))
    
    if parity_positions:
        return random.choice(parity_positions)
    
    # If no parity positions, shoot randomly among unknowns
    return random.choice(unknown)
