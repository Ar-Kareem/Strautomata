
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, p):
        # Check rows
        for i in range(4):
            if all(b[i][j] == p for j in range(4)):
                return True
        # Check columns
        for j in range(4):
            if all(b[i][j] == p for i in range(4)):
                return True
        # Check main diagonal
        if all(b[i][i] == p for i in range(4)):
            return True
        # Check anti-diagonal
        if all(b[i][3-i] == p for i in range(4)):
            return True
        return False
    
    # Get all empty positions
    empty = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    if not empty:
        return (0, 0)  # Fallback, though shouldn't happen
    
    # 1. Check for winning move
    for r, c in empty:
        board[r][c] = 1
        if check_win(board, 1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # 2. Check for blocking opponent's win
    for r, c in empty:
        board[r][c] = -1
        if check_win(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # 3. Prefer center positions
    centers = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for r, c in centers:
        if (r, c) in empty:
            return (r, c)
    
    # 4. Otherwise, prefer corners
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for r, c in corners:
        if (r, c) in empty:
            return (r, c)
    
    # 5. Random edge (not corner or center)
    edges = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
    available_edges = [(r, c) for r, c in edges if (r, c) in empty]
    if available_edges:
        return random.choice(available_edges)
    
    # 6. If all else fails, random move
    return random.choice(empty)
