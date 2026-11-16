
# Precomputed lines for the 3x3 board
lines = [
    [(0,0), (0,1), (0,2)],
    [(1,0), (1,1), (1,2)],
    [(2,0), (2,1), (2,2)],
    [(0,0), (1,0), (2,0)],
    [(0,1), (1,1), (2,1)],
    [(0,2), (1,2), (2,2)],
    [(0,0), (1,1), (2,2)],
    [(0,2), (1,1), (2,0)]
]

# Precomputed cell_lines: for each cell (i,j), list of line indices that include it.
cell_lines = [
    [0, 3, 6],  # (0,0)
    [0, 4, 7],  # (0,1)
    [0, 5, 6],  # (0,2)
    [1, 3, 7],  # (1,0)
    [1, 4, 6],  # (1,1)
    [1, 5, 7],  # (1,2)
    [2, 3, 5],  # (2,0)
    [2, 4, 5],  # (2,1)
    [2, 6, 7]   # (2,2)
]

def policy(board):
    candidates = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                threat_count = 0
                for line_idx in cell_lines[i][j]:
                    line = lines[line_idx]
                    other_cells = [cell for cell in line if cell != (i,j)]
                    if all(board[cell[0]][cell[1]] == 1 for cell in other_cells):
                        threat_count += 1
                candidates.append((threat_count, i, j))
    
    if not candidates:
        return (0, 0)
    
    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    best = candidates[0]
    return (best[1], best[2])
