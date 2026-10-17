
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next move for a 4x4 Tic Tac Toe game.
    1 is the current player, -1 is the opponent, 0 is empty.
    """
    size = 4
    
    def check_line(line):
        if sum(line) == 3 and 0 in line:
            return line.index(0)
        return -1

    # check rows, columns, and diagonals for a winning move or necessary block
    for player in [1, -1]:
        # Rows
        for r in range(size):
            row = board[r]
            c = check_line(row)
            if c != -1:
                return (r, c)
        
        # Cols
        for c in range(size):
            col = [board[r][c] for r in range(size)]
            r = check_line(col)
            if r != -1:
                return (r, c)
        
        # Main Diagonal
        diag1 = [board[i][i] for i in range(size)]
        idx = check_line(diag1)
        if idx != -1:
            return (idx, idx)
            
        # Anti Diagonal
        diag2 = [board[i][size - 1 - i] for i in range(size)]
        idx = check_line(diag2)
        if idx != -1:
            return (idx, size - 1 - idx)

    # Strategic preference: Center, then corners, then others
    preferred_moves = [
        (1, 1), (1, 2), (2, 1), (2, 2), # Center
        (0, 0), (0, 3), (3, 0), (3, 3), # Corners
        (0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2) # Edges
    ]
    
    for r, c in preferred_moves:
        if board[r][c] == 0:
            return (r, c)

    # Final fallback for any empty square
    for r in range(size):
        for c in range(size):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0) # Should not be reachable in a non-full board
