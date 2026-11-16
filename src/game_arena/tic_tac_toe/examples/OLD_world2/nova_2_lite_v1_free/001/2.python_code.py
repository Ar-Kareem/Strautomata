
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns a move (row, column) for a 4x4 Tic Tac Toe game.
    
    Strategy:
    1. If we can win immediately, take that move.
    2. If the opponent can win on their next move, block it.
    3. Otherwise, prefer the center, then corners, then edges.
    """
    # Convert board to a numpy array for easier indexing
    board_np = np.array(board, dtype=int)
    ROWS, COLS = 4, 4

    # Helper to flatten a line (row, column, diagonal)
    def get_line(line_indices):
        return [board_np[i, j] for (i, j) in line_indices]

    # All possible winning lines in 4x4 Tic Tac Toe
    lines = []

    # Rows
    for r in range(ROWS):
        lines.append([(r, c) for c in range(COLS)])

    # Columns
    for c in range(COLS):
        lines.append([(r, c) for r in range(ROWS)])

    # Diagonals (main and anti)
    lines.append([(i, i) for i in range(ROWS)])          # main diagonal
    lines.append([(i, ROWS - 1 - i) for i in range(ROWS)])  # anti diagonal

    # Also include 4-in-a-row patterns that are not full board? In 4x4, the above covers all.

    # 1. Check for a winning move for us (player 1)
    for line in lines:
        cells = get_line(line)
        if cells.count(1) == 3 and cells.count(0) == 1:
            # There is an empty cell that would complete a line for us
            for (r, c) in line:
                if board[r][c] == 0:
                    return (r, c)

    # 2. Check for a winning move for the opponent (player -1)
    for line in lines:
        cells = get_line(line)
        if cells.count(-1) == 3 and cells.count(0) == 1:
            for (r, c) in line:
                if board[r][c] == 0:
                    return (r, c)

    # 3. Choose the best empty cell: center > corners > edges
    # Center of 4x4 is positions (1,1) and (2,2) also (1,2),(2,1) but typical "center" is (1,1) and (2,2)
    center_candidates = [(1, 1), (1, 2), (2, 1), (2, 2)]
    corner_candidates = [(0, 0), (0, 3), (3, 0), (3, 3)]
    edge_candidates = [(0, 1), (0, 2), (1, 0), (2, 0), (1, 3), (2, 3), (3, 1), (3, 2)]

    for cand in center_candidates:
        r, c = cand
        if board[r][c] == 0:
            return (r, c)

    for cand in corner_candidates:
        r, c = cand
        if board[r][c] == 0:
            return (r, c)

    for cand in edge_candidates:
        r, c = cand
        if board[r][c] == 0:
            return (r, c)

    # Fallback: if somehow no empty spots were found (shouldn't happen), pick the first zero
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 0:
                return (r, c)

    # If board is full, return (0,0) as a safe placeholder (should never be reached in a valid game)
    return (0, 0)
