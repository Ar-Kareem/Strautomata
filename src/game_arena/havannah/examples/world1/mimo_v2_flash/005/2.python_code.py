
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    import numpy as np
    
    # Precompute occupied set for fast lookups
    occupied = set(me + opp)
    
    # Define hexagonal neighbors (assuming even-r offset coordinates for the 2D array)
    # In the provided example, (r, c) connects to (r±1, c) and (r±1, c±1).
    # This corresponds to the "odd-r" or "even-r" offset coordinate system depending on parity.
    # For a 2D array representation of a hex grid, we assume rows are slanted.
    # Given the example: (4,1) touches (3,0) and (3,2).
    # This suggests an offset where neighbors depend on row parity.
    # Standard approach for hex grids in 2D arrays:
    # Even rows: (r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c), (r+1, c+1)
    # Odd rows:  (r-1, c-1), (r-1, c), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
    def get_neighbors(r, c):
        neighbors = []
        # Check parity
        if r % 2 == 0:
            # Even row
            potential = [
                (r-1, c), (r-1, c+1),
                (r, c-1), (r, c+1),
                (r+1, c), (r+1, c+1)
            ]
        else:
            # Odd row
            potential = [
                (r-1, c-1), (r-1, c),
                (r, c-1), (r, c+1),
                (r+1, c-1), (r+1, c)
            ]
        for nr, nc in potential:
            if 0 <= nr < 15 and 0 <= nc < 15:
                neighbors.append((nr, nc))
        return neighbors

    # Heuristic weights
    W_CENTER = 5.0
    W_FRIENDLY = 2.0
    W_MOBILITY = 0.5
    W_EDGE = -0.5
    W_THREAT = 10.0
    
    best_score = -float('inf')
    best_move = None
    
    # Find center
    center_r, center_c = 7, 7
    
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in occupied:
                score = 0.0
                
                # 1. Center Control
                dist = max(abs(r - center_r), abs(c - center_c)) # Approximation of distance
                score += W_CENTER * (1.0 / (1.0 + dist))
                
                # 2. Connectivity & Mobility
                neighbors = get_neighbors(r, c)
                friendly_adj = 0
                empty_adj = 0
                opp_adj = 0
                
                for nr, nc in neighbors:
                    if (nr, nc) in occupied:
                        if (nr, nc) in me:
                            friendly_adj += 1
                        else:
                            opp_adj += 1
                    else:
                        # Check if valid within board bounds (get_neighbors does this, but double check valid_mask if needed)
                        # Here we assume neighbors are within bounds.
                        empty_adj += 1
                
                score += W_FRIENDLY * friendly_adj
                score += W_MOBILITY * empty_adj
                
                # 3. Threat Blocking
                # If we are adjacent to opponent, check if this move blocks a potential connection.
                # High penalty if we don't block, but we are evaluating this move as a block.
                # If opp_adj > 0, we are blocking something.
                # We prioritize moves that block opponent connectivity.
                if opp_adj > 0:
                    # Identify if this spot is critical for opponent expansion
                    # A simple heuristic: if neighbor to multiple opponents, it's a good block.
                    # Or if it is between two opponents (requires checking specific geometry).
                    # For now, simply being adjacent to an opponent while maintaining our own connectivity is good.
                    score += W_THREAT * (opp_adj * 0.5)
                    
                    # Aggressive blocking: if an opponent is adjacent, we MUST consider blocking.
                    # If we find a move adjacent to an opponent, we might want to prioritize it highly
                    # to prevent them from closing a ring or bridge.
                    # However, building our own structure is also key.
                    # We add a fixed bonus for blocking opponent expansion paths.
                    score += W_THREAT 

                # 4. Edge Avoidance (unless necessary for blocking or bridge)
                # Corners are (0,0), (0,14), (14,0), (14,14).
                # Edges are row 0, row 14, col 0, col 14.
                if r == 0 or r == 14 or c == 0 or c == 14:
                    # Exception: if this is a corner, it might be part of a bridge strategy later,
                    # but usually better to wait. Currently, we penalize edges slightly.
                    # However, if we are playing a bridge strategy, we might want corners.
                    # Since we don't have explicit strategy, we stick to center dominance.
                    score += W_EDGE

                # Jitter to avoid deterministic loops if scores are identical
                score += (r * 13 + c * 7) % 10 * 0.001

                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # Fallback: if no move found (shouldn't happen if valid_mask has True), return first valid
    if best_move is None:
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c] and (r, c) not in occupied:
                    return (r, c)
                    
    return best_move
