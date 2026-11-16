
import numpy as np
from collections import deque

targets = deque()

def policy(board: list[list[int]]) -> tuple[int, int]:
    possible_shots = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    if not possible_shots:
        return (0, 0)
    possible_shots_set = set(possible_shots)
    
    if targets:
        next_shot = targets[0]
        if next_shot in possible_shots_set:
            return next_shot
        else:
            targets.popleft()
            return policy(board)
    else:
        hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
        if hits:
            new_targets = []
            for (r, c) in hits:
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10:
                        if board[nr][nc] == 0:
                            new_targets.append((nr, nc))
            unique_new = list(set(new_targets))
            for t in unique_new:
                targets.append(t)
            if targets:
                return targets.popleft()
            else:
                return systematic_shot(possible_shots)
        else:
            return systematic_shot(possible_shots)

def systematic_shot(possible_shots):
    best_score = -1
    best_cells = []
    for (r, c) in possible_shots:
        score = 0
        for length in [5, 4, 3, 3, 2]:
            # Horizontal possibilities
            max_start_col = 10 - length
            min_start_col_for_cell = c - length + 1
            min_start_col = max(0, min_start_col_for_cell)
            max_start_col_for_cell = c
            max_start_col_actual = min(max_start_col_for_cell, max_start_col)
            if min_start_col <= max_start_col_actual:
                horizontal = max_start_col_actual - min_start_col + 1
            else:
                horizontal = 0
            score += horizontal
            
            # Vertical possibilities
            max_start_row = 10 - length
            min_start_row_for_cell = r - length + 1
            min_start_row = max(0, min_start_row_for_cell)
            max_start_row_for_cell = r
            max_start_row_actual = min(max_start_row_for_cell, max_start_row)
            if min_start_row <= max_start_row_actual:
                vertical = max_start_row_actual - min_start_row + 1
            else:
                vertical = 0
            score += vertical
        if score > best_score:
            best_score = score
            best_cells = [(r, c)]
        elif score == best_score:
            best_cells.append((r, c))
    return sorted(best_cells, key=lambda x: (x[0], x[1]))[0]
