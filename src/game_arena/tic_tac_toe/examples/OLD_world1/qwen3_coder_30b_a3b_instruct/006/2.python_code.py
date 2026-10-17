
def policy(board: list[list[int]]) -> tuple[int, int]:
    import numpy as np
    
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Check if we can win in one move
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:  # Empty cell
                # Try placing our mark there
                board[i, j] = 1
                # Check if this leads to a win
                if check_win(board, 1):
                    board[i, j] = 0  # Reset
                    return (i, j)
                board[i, j] = 0  # Reset
    
    # Check if opponent can win in one move and block them
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:  # Empty cell
                # Try placing opponent's mark there
                board[i, j] = -1
                # Check if this leads to opponent winning
                if check_win(board, -1):
                    board[i, j] = 0  # Reset
                    return (i, j)
                board[i, j] = 0  # Reset
    
    # If center is available, take it
    if board[1, 1] == 0:
        return (1, 1)
    
    # Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [pos for pos in corners if board[pos[0], pos[1]] == 0]
    if available_corners:
        return available_corners[0]
    
    # Otherwise, take any available edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [pos for pos in edges if board[pos[0], pos[1]] == 0]
    if available_edges:
        return available_edges[0]
    
    # Fallback - return first empty cell
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                return (i, j)

def check_win(board, player):
    # Check rows
    for i in range(3):
        if all(board[i, j] == player for j in range(3)):
            return True
    
    # Check columns
    for j in range(3):
        if all(board[i, j] == player for i in range(3)):
            return True
    
    # Check diagonals
    if all(board[i, i] == player for i in range(3)):
        return True
    if all(board[i, 2-i] == player for i in range(3)):
        return True
    
    return False
