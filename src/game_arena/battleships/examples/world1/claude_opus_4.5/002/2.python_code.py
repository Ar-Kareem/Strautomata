
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    ships = [5, 4, 3, 3, 2]
    
    # Find hits and potential targets
    hits = set()
    unknown = []
    for r in range(10):
        for c in range(10):
            if board[r, c] == 1:
                hits.add((r, c))
            elif board[r, c] == 0:
                unknown.append((r, c))
    
    if not unknown:
        # Shouldn't happen, but fallback
        return (0, 0)
    
    # Calculate probability density for each cell
    prob = np.zeros((10, 10), dtype=float)
    
    for ship_len in ships:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - ship_len + 1):
                valid = True
                hit_count = 0
                unknown_count = 0
                for i in range(ship_len):
                    if board[r, c + i] == -1:
                        valid = False
                        break
                    elif board[r, c + i] == 1:
                        hit_count += 1
                    else:
                        unknown_count += 1
                
                if valid and unknown_count > 0:
                    # Weight placements that include hits much higher
                    weight = 1.0
                    if hit_count > 0:
                        weight = 100.0 * (hit_count ** 2)
                    
                    for i in range(ship_len):
                        if board[r, c + i] == 0:
                            prob[r, c + i] += weight
        
        # Vertical placements
        for r in range(10 - ship_len + 1):
            for c in range(10):
                valid = True
                hit_count = 0
                unknown_count = 0
                for i in range(ship_len):
                    if board[r + i, c] == -1:
                        valid = False
                        break
                    elif board[r + i, c] == 1:
                        hit_count += 1
                    else:
                        unknown_count += 1
                
                if valid and unknown_count > 0:
                    weight = 1.0
                    if hit_count > 0:
                        weight = 100.0 * (hit_count ** 2)
                    
                    for i in range(ship_len):
                        if board[r + i, c] == 0:
                            prob[r + i, c] += weight
    
    # Find cells adjacent to hits (for prioritization)
    adjacent_to_hit = set()
    for r, c in hits:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr, nc] == 0:
                adjacent_to_hit.add((nr, nc))
    
    # If we have hits and adjacent unknowns, prioritize those
    if hits and adjacent_to_hit:
        best = None
        best_prob = -1
        for r, c in adjacent_to_hit:
            if prob[r, c] > best_prob:
                best_prob = prob[r, c]
                best = (r, c)
        if best:
            return best
    
    # Otherwise, choose the cell with highest probability
    # Add small bias for center cells in hunt mode (ships more likely there)
    if not hits:
        for r in range(10):
            for c in range(10):
                if board[r, c] == 0:
                    # Slight center bias
                    center_dist = abs(r - 4.5) + abs(c - 4.5)
                    prob[r, c] += 0.1 * (9 - center_dist)
                    # Checkerboard pattern preference for hunting
                    if (r + c) % 2 == 0:
                        prob[r, c] += 0.5
    
    best = None
    best_prob = -1
    for r in range(10):
        for c in range(10):
            if board[r, c] == 0 and prob[r, c] > best_prob:
                best_prob = prob[r, c]
                best = (r, c)
    
    if best:
        return best
    
    # Fallback: return first unknown
    return unknown[0]
