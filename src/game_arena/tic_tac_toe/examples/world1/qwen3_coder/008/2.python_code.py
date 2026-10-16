
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to list of lists if needed
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing our piece here
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Check for opponent's winning move to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's piece here
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # No immediate threats, use strategic positioning
    # Priority: center, corners, edges
    
    # Center
    if board[1][1] == 0:
        return (1, 1)
    
    # Corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
    
    # Edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)
    
    # Should never reach here in a valid game state
    # But just in case, find any empty spot
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

def check_win(board: list[list[int]], player: int) -> bool:
    # Check rows
    for i in range(3):
        if board[i][0] == player and board[i][1] == player and board[i][2] == player:
            return True
    
    # Check columns
    for j in range(3):
        if board[0][j] == player and board[1][j] == player and board[2][j] == player:
            return True
    
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    
    return False
