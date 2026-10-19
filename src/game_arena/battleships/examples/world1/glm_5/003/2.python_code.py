
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    rows = 10
    cols = 10
    ships = [5, 4, 3, 3, 2]
    
    # 1. Identify Target Candidates (cells adjacent to hits)
    target_candidates = set()
    hits = []
    
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1:
                hits.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == 0:
                        target_candidates.add((nr, nc))
    
    # If no hits or no neighbors, switch to Hunt Mode (all unknown cells)
    if not target_candidates:
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == 0:
                    target_candidates.add((r, c))
    
    # 2. Calculate Probability Density Map (PDM)
    prob_grid = [[0] * cols for _ in range(rows)]
    
    for ship_len in ships:
        # Check Horizontal Placements
        for r in range(rows):
            for c in range(cols - ship_len + 1):
                hits_covered = 0
                valid = True
                for i in range(ship_len):
                    cell_val = board[r][c+i]
                    if cell_val == -1:
                        valid = False
                        break
                    if cell_val == 1:
                        hits_covered += 1
                
                if valid:
                    # Weight placements to heavily prioritize extending hits
                    weight = 1 + hits_covered * 20
                    for i in range(ship_len):
                        prob_grid[r][c+i] += weight
                        
        # Check Vertical Placements
        for r in range(rows - ship_len + 1):
            for c in range(cols):
                hits_covered = 0
                valid = True
                for i in range(ship_len):
                    cell_val = board[r+i][c]
                    if cell_val == -1:
                        valid = False
                        break
                    if cell_val == 1:
                        hits_covered += 1
                
                if valid:
                    weight = 1 + hits_covered * 20
                    for i in range(ship_len):
                        prob_grid[r+i][c] += weight

    # 3. Select Best Move
    max_prob = -1
    best_moves = []
    
    for r, c in target_candidates:
        p = prob_grid[r][c]
        if p > max_prob:
            max_prob = p
            best_moves = [(r, c)]
        elif p == max_prob:
            best_moves.append((r, c))
            
    # Fallback (should not be reached if valid moves exist)
    if not best_moves:
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    return random.choice(best_moves)
