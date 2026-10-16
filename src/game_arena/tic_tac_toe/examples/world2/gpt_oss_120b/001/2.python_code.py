
import random
from typing import List, Tuple

# Directions for lines: rows, columns, two main diagonals
def _check_win(board: List[List[int]], player: int) -> bool:
    target = 4 * player
    # rows
    for r in range(4):
        if sum(board[r][c] for c in range(4)) == target:
            return True
    # columns
    for c in range(4):
        if sum(board[r][c] for r in range(4)) == target:
            return True
    # main diagonal
    if sum(board[i][i] for i in range(4)) == target:
        return True
    # anti diagonal
    if sum(board[i][3 - i] for i in range(4)) == target:
        return True
    return False

def _lines_for_cell(row: int, col: int) -> List[Tuple[str, int]]:
    """
    Return identifiers of lines that include the given cell.
    Each line is represented as a tuple (type, index):
    - ('row', r)   for row r
    - ('col', c)   for column c
    - ('diag', 0)  for main diagonal (top‑left to bottom‑right)
    - ('diag', 1)  for anti‑diagonal (top‑right to bottom‑left)
    """
    lines = [('row', row), ('col', col)]
    if row == col:
        lines.append(('diag', 0))
    if row + col == 3:
        lines.append(('diag', 1))
    return lines

def _line_cells(board: List[List[int]], line: Tuple[str, int]) -> List[int]:
    """Extract the four cell values belonging to a line."""
    typ, idx = line
    if typ == 'row':
        return [board[idx][c] for c in range(4)]
    if typ == 'col':
        return [board[r][idx] for r in range(4)]
    if typ == 'diag' and idx == 0:
        return [board[i][i] for i in range(4)]
    # anti‑diagonal
    return [board[i][3 - i] for i in range(4)]

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next move for player 1 on a 4x4 Tic‑Tac‑Toe board.
    Returns (row, col) with 0‑based indices.
    """
    # 1. Immediate winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] != 0:
                continue
            board[r][c] = 1
            if _check_win(board, 1):
                board[r][c] = 0  # restore (not strictly necessary)
                return (r, c)
            board[r][c] = 0

    # 2. Block opponent's immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] != 0:
                continue
            board[r][c] = -1
            if _check_win(board, -1):
                board[r][c] = 0
                return (r, c)
            board[r][c] = 0

    # 3. Heuristic based on number of “good” lines a move participates in
    best_score = -1
    best_move = (0, 0)  # fallback
    for r in range(4):
        for c in range(4):
            if board[r][c] != 0:
                continue
            score = 0
            for line in _lines_for_cell(r, c):
                cells = _line_cells(board, line)
                # a line is good if it contains no opponent pieces
                if -1 not in cells:
                    # count our pieces already in the line (helps creating threats)
                    score += cells.count(1) + 1  # +1 for the potential new piece
            if score > best_score:
                best_score = score
                best_move = (r, c)

    return best_move
