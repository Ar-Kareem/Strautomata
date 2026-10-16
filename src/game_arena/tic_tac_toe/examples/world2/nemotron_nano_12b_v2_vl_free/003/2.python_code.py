
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Generate all possible game lines (rows, columns, diagonals)
    all_lines = []
    for i in range(4):
        all_lines.append([(i, j) for j in range(4)])  # Rows
    for j in range(4):
        all_lines.append([(i, j) for i in range(4)])  # Columns
    all_lines.append([(k, k) for k in range(4)])    # Main diagonal
    all_lines.append([(k, 3 - k) for k in range(4)]) # Anti diagonal

    # Check if AI can win in next move
    for line in all_lines:
        count_ai, empty_pos = 0, []
        for (i, j) in line:
            if board[i][j] == 1:
                count_ai += 1
            elif board[i][j] == 0:
                empty_pos.append((i, j))
        if count_ai == 3 and len(empty_pos) == 1:
            return empty_pos[0]
    
    # Check if opponent can win in their next move (block them)
    for line in all_lines:
        count_opp, empty_pos = 0, []
        for (i, j) in line:
            if board[i][j] == -1:
                count_opp += 1
            elif board[i][j] == 0:
                empty_pos.append((i, j))
        if count_opp == 3 and len(empty_pos) == 1:
            return empty_pos[0]
    
    # Heuristic: prioritize cells part of the most winning lines
    cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Base score: 2 (1 for row + 1 for column)
                score = 2
                # Add 1 if on main diagonal (i == j)
                if i == j:
                    score += 1
                # Add 1 if on anti-diagonal (i + j == 3)
                if i + j == 3:
                    score += 1
                cells.append((-score, i, j))  # Negative for descending sort
    
    if cells:
        cells.sort()
        return (cells[0][1], cells[0][2])
    return (0, 0)  # Fallback (shouldn't reach here)
