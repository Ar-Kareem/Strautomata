
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Targeting phase: find cells adjacent to hits that haven't been shot at
    targeting_candidates = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        targeting_candidates.add((nr, nc))
    
    if targeting_candidates:
        # Weight each candidate by the number of adjacent hits (higher weight = more likely part of ship)
        candidate_weights = {}
        for (r, c) in targeting_candidates:
            weight = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    weight += 1
            candidate_weights[(r, c)] = weight
        
        max_weight = max(candidate_weights.values())
        best_candidates = [cell for cell, w in candidate_weights.items() if w == max_weight]
        return random.choice(best_candidates)
    
    # Hunting phase: compute probability heatmap for unexplored cells
    ship_lengths = [5, 4, 3, 3, 2]
    heatmap = [[0] * 10 for _ in range(10)]
    
    for length in ship_lengths:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                valid = True
                for i in range(length):
                    if board[r][c + i] != 0:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        heatmap[r][c + i] += 1
        
        # Vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                valid = True
                for i in range(length):
                    if board[r + i][c] != 0:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        heatmap[r + i][c] += 1
    
    # Find cell(s) with maximum heatmap value among unexplored cells
    max_heat = -1
    best_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if heatmap[r][c] > max_heat:
                    max_heat = heatmap[r][c]
                    best_cells = [(r, c)]
                elif heatmap[r][c] == max_heat:
                    best_cells.append((r, c))
    
    if best_cells:
        return random.choice(best_cells)
    
    # Fallback: find any unexplored cell (shouldn't occur if game isn't over)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)  # default if all cells are explored (unlikely)
