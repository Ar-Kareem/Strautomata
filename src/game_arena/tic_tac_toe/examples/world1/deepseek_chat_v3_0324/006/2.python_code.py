
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to check if a move leads to a win
    def is_win(b, player):
        # Check rows
        for row in range(3):
            if all(cell == player for cell in b[row]):
                return True
        # Check columns
        for col in range(3):
            if all(b[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2 - i] == player for i in range(3)):
            return True
        return False
    
    # Check for a winning move (AI can win immediately)
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if is_win(board, 1):
                    board[row][col] = 0  # Undo the move
                    return (row, col)
                board[row][col] = 0  # Undo the move
    
    # Check if opponent is about to win and block them
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if is_win(board, -1):
                    board[row][col] = 0  # Undo the move
                    return (row, col)
                board[row][col] = 0  # Undo the move
    
    # Take the center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for row, col in corners:
        if board[row][col] == 0:
            return (row, col)
    
    # Take any remaining edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for row, col in edges:
        if board[row][col] == 0:
            return (row, col)
    
    # If no moves left (shouldn't happen in a valid game)
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                return (row, col)
    return (0, 0)  # fallback
