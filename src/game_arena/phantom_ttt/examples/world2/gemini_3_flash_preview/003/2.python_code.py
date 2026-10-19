
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Phantom Tic Tac Toe Policy.
    board: 3x3 list where 1 is our mark, 0 is unknown (empty or opponent).
    Returns (row, col)
    """
    
    def is_win_possible(b, r, c):
        # Simulate placing a mark at r,c and check if we win
        temp_board = [row[:] for row in b]
        temp_board[r][c] = 1
        
        # Check row
        if sum(temp_board[r]) == 3: return True
        # Check col
        if sum(temp_board[i][c] for i in range(3)) == 3: return True
        # Check diagonals
        if r == c:
            if sum(temp_board[i][i] for i in range(3)) == 3: return True
        if r + c == 2:
            if sum(temp_board[i][2-i] for i in range(3)) == 3: return True
        return False

    # 1. Check for immediate winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                if is_win_possible(board, r, c):
                    return (r, c)

    # 2. Prioritize Center
    if board[1][1] == 0:
        return (1, 1)

    # 3. Prioritize Corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # 4. Prioritize Edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(edges)
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)

    # 5. Fallback: Find any valid move (though the above covers all)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)
                
    # If board is full of 1s (should not happen if game is active)
    return (0, 0)
