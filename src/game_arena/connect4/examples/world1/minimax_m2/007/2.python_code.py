
def find_drop_row(board, col):
    """Find the row where a disc would drop in the given column."""
    for i in range(5, -1, -1):  # Check from bottom to top
        if board[i][col] == 0:
            return i
    return None  # Column is full

def is_full(board, col):
    """Check if the column is full (no empty cells)."""
    for i in range(6):
        if board[i][col] == 0:
            return False
    return True

def check_win(board, player):
    """Check if the player has won on the board."""
    # Check horizontal
    for i in range(6):
        for j in range(4):
            if board[i][j] == board[i][j+1] == board[i][j+2] == board[i][j+3] == player:
                return True
    # Check vertical
    for i in range(3):
        for j in range(7):
            if board[i][j] == board[i+1][j] == board[i+2][j] == board[i+3][j] == player:
                return True
    # Check diagonal down-right
    for i in range(3):
        for j in range(4):
            if board[i][j] == board[i+1][j+1] == board[i+2][j+2] == board[i+3][j+3] == player:
                return True
    # Check diagonal down-left
    for i in range(3):
        for j in range(3, 7):
            if board[i][j] == board[i+1][j-1] == board[i+2][j-2] == board[i+3][j-3] == player:
                return True
    return False

def get_winning_moves(board, player):
    """Return a list of columns where the player can win immediately."""
    winning_moves = []
    for col in range(7):
        if is_full(board, col):
            continue
        drop_row = find_drop_row(board, col)
        # Simulate the move
        new_board = [row[:] for row in board]  # Shallow copy of each row
        new_board[drop_row][col] = player
        if check_win(new_board, player):
            winning_moves.append(col)
    return winning_moves

def policy(board):
    """Choose a column to drop the disc based on the current board state."""
    # Check for immediate winning moves for the current player
    my_moves = get_winning_moves(board, 1)
    if my_moves:
        return my_moves[0]  # Return the first winning move found

    # Find safe moves that do not allow the opponent to win immediately
    safe_moves = []
    for col in range(7):
        if is_full(board, col):
            continue
        drop_row = find_drop_row(board, col)
        new_board = [row[:] for row in board]  # Simulate the move
        new_board[drop_row][col] = 1  # Current player's disc
        # Check if the opponent has any winning moves after this
        opponent_moves = get_winning_moves(new_board, -1)
        if not opponent_moves:
            safe_moves.append(col)

    if safe_moves:
        # Choose the safe move closest to the center (column 3)
        best_col = safe_moves[0]
        for col in safe_moves:
            if abs(col - 3) < abs(best_col - 3):
                best_col = col
        return best_col

    # If no safe moves, choose the move closest to center from all available moves
    all_moves = []
    for col in range(7):
        if not is_full(board, col):
            all_moves.append(col)
    if not all_moves:
        return 0  # Fallback, though board should not be full
    best_col = all_moves[0]
    for col in all_moves:
        if abs(col - 3) < abs(best_col - 3):
            best_col = col
    return best_col
