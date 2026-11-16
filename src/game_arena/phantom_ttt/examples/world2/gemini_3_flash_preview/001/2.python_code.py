
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Phantom Tic Tac Toe Policy.
    board: 3x3 list where 1 is our mark, 0 is unknown (empty or opponent).
    Returns (row, col).
    """
    
    # helper to find empty cells (not yet confirmed as ours)
    def get_available():
        available = []
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    available.append((r, c))
        return available

    available = get_available()
    
    # 1. Check for Immediate Win
    # If we have two in a row and the third is 0, try it.
    for r in range(3):
        if sum(board[r]) == 2:
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
                    
    for c in range(3):
        col_vals = [board[0][c], board[1][c], board[2][c]]
        if sum(col_vals) == 2:
            for r in range(3):
                if board[r][c] == 0:
                    return (r, c)
                    
    diag1 = [board[0][0], board[1][1], board[2][2]]
    if sum(diag1) == 2:
        for i in range(3):
            if board[i][i] == 0:
                return (i, i)
                
    diag2 = [board[0][2], board[1][1], board[2][0]]
    if sum(diag2) == 2:
        for i in range(3):
            if board[i][2-i] == 0:
                return (i, 2-i)

    # 2. Priority Placing
    # Center
    if board[1][1] == 0:
        return (1, 1)
    
    # Corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
            
    # Sides
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(sides)
    for r, c in sides:
        if board[r][c] == 0:
            return (r, c)

    # Fallback to any available cell (should not be reached if board is not full)
    return available[0] if available else (0, 0)
