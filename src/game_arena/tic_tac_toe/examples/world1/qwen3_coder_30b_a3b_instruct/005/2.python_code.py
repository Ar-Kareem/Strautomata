
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check if we can win in one move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:  # Empty cell
                # Try placing our piece there
                board[i][j] = 1
                if check_winner(board) == 1:  # We win
                    board[i][j] = 0  # Undo the move
                    return (i, j)
                board[i][j] = 0  # Undo the move

    # Check if opponent can win in one move and block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:  # Empty cell
                # Try placing opponent's piece there
                board[i][j] = -1
                if check_winner(board) == -1:  # Opponent wins
                    board[i][j] = 0  # Undo the move
                    return (i, j)
                board[i][j] = 0  # Undo the move

    # If can't win or block, try to take center
    if board[1][1] == 0:
        return (1, 1)
    
    # Try to take a corner
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)
    
    # Take any remaining spot
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

def check_winner(board):
    """Check if there's a winner. Returns 1 if X wins, -1 if O wins, 0 if no winner."""
    # Check rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    
    # Check columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    # No winner
    return 0
