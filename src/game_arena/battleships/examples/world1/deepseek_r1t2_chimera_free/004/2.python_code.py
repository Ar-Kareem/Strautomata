
import random
from collections import defaultdict

def compute_weights(board):
    weights = [[0 for _ in range(10)] for _ in range(10)]
    ship_lengths = [5, 4, 3, 3, 2]
    
    for ship_len in ship_lengths:
        # Horizontal placements
        for i in range(10):
            for j in range(11 - ship_len):
                valid = True
                for k in range(ship_len):
                    if board[i][j + k] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(ship_len):
                        weights[i][j + k] += 1
        
        # Vertical placements
        for j in range(10):
            for i in range(11 - ship_len):
                valid = True
                for k in range(ship_len):
                    if board[i + k][j] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(ship_len):
                        weights[i + k][j] += 1
    
    return weights

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect target cells in target mode (adjacent to hits)
    target_cells = []
    
    # Scan the board for hits with adjacent unknowns
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                has_adjacent_unknown = False
                for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        has_adjacent_unknown = True
                        break
                
                if has_adjacent_unknown:
                    # Calculate horizontal line length
                    left = j
                    while left > 0 and board[i][left - 1] == 1:
                        left -= 1
                    right = j
                    while right < 9 and board[i][right + 1] == 1:
                        right += 1
                    h_len = right - left + 1
                    
                    # Calculate vertical line length
                    top = i
                    while top > 0 and board[top - 1][j] == 1:
                        top -= 1
                    bottom = i
                    while bottom < 9 and board[bottom + 1][j] == 1:
                        bottom += 1
                    v_len = bottom - top + 1
                    
                    # Determine direction and add potential targets
                    if h_len > v_len:
                        # Horizontal line is longer
                        if left > 0 and board[i][left - 1] == 0:
                            target_cells.append((i, left - 1, h_len))
                        if right < 9 and board[i][right + 1] == 0:
                            target_cells.append((i, right + 1, h_len))
                    elif v_len > h_len:
                        # Vertical line is longer
                        if top > 0 and board[top - 1][j] == 0:
                            target_cells.append((top - 1, j, v_len))
                        if bottom < 9 and board[bottom + 1][j] == 0:
                            target_cells.append((bottom + 1, j, v_len))
                    else:
                        # Equal length or single cell
                        for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            ni, nj = i + di, j + dj
                            if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                                target_cells.append((ni, nj, max(h_len, v_len)))
    
    # Process target mode if any targets found
    if target_cells:
        cell_priority = defaultdict(int)
        for (i, j, p) in target_cells:
            if p > cell_priority[(i, j)]:
                cell_priority[(i, j)] = p
        
        # If multiple cells, choose the one with highest priority and hunt weight
        weights = compute_weights(board)
        sorted_candidates = sorted(
            cell_priority.keys(),
            key=lambda ij: (-cell_priority[ij], -weights[ij[0]][ij[1]])
        )
        return sorted_candidates[0]
    
    # Hunt mode: no current targets
    weights = compute_weights(board)
    candidates = []
    max_weight = -1
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                if weights[i][j] > max_weight:
                    max_weight = weights[i][j]
                    candidates = [(i, j)]
                elif weights[i][j] == max_weight:
                    candidates.append((i, j))
    
    return random.choice(candidates)
