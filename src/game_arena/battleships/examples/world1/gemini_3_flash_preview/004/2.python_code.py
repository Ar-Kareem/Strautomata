
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship AI policy.
    0: Unknown, -1: Miss, 1: Hit
    """
    size = 10
    
    def get_neighbors(r, c):
        res = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                res.append((nr, nc))
        return res

    # 1. Target Mode: Identify hits that need follow-up
    hits = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 1]
    
    target_candidates = {} # {(r, c): weight}
    
    for r, c in hits:
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == 0:
                # Basic weight
                weight = 1
                
                # Boost weight if this cell aligns with another hit (suggests direction)
                dr, dc = nr - r, nc - c
                # Check opposite side
                opp_r, opp_c = r - dr, c - dc
                if 0 <= opp_r < size and 0 <= opp_c < size:
                    if board[opp_r][opp_c] == 1:
                        weight += 2
                
                target_candidates[(nr, nc)] = target_candidates.get((nr, nc), 0) + weight

    if target_candidates:
        # Pick the best target (highest weight)
        best_weight = max(target_candidates.values())
        best_cells = [cell for cell, w in target_candidates.items() if w == best_weight]
        return random.choice(best_cells)

    # 2. Hunt Mode: Heatmap simulation
    # Identify empty spots
    empty_cells = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    ship_lengths = [5, 4, 3, 3, 2] # Default fleet
    
    heatmap = [[0 for _ in range(size)] for _ in range(size)]
    
    for length in ship_lengths:
        # Horizontal
        for r in range(size):
            for c in range(size - length + 1):
                segment = [board[r][c + i] for i in range(length)]
                if all(cell >= 0 for cell in segment): # No misses in segment
                    for i in range(length):
                        heatmap[r][c + i] += 1
        # Vertical
        for r in range(size - length + 1):
            for c in range(size):
                segment = [board[r + i][c] for i in range(length)]
                if all(cell >= 0 for cell in segment):
                    for i in range(length):
                        heatmap[r + i][c] += 1

    # Filter heatmap for only empty cells and apply parity
    # Parity helps find ships faster by skipping cells in a checkerboard
    max_val = -1
    best_hunt_targets = []
    
    for r, c in empty_cells:
        # Increase weight for parity (even sum of coords) to find ships efficiently
        val = heatmap[r][c]
        if (r + c) % 2 == 0:
            val += 1
            
        if val > max_val:
            max_val = val
            best_hunt_targets = [(r, c)]
        elif val == max_val:
            best_hunt_targets.append((r, c))

    if best_hunt_targets:
        return random.choice(best_hunt_targets)

    # Fallback (should not be reached if empty_cells exists)
    return random.choice(empty_cells)

