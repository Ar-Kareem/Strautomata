
def check_winner(board):
    """Check for a winner on the 3x3 board. Returns 1, -1, or 0 for no winner."""
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return 0

def is_board_full(board):
    """Check if the board is full (no empty cells)."""
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax_with_move(board, current_player):
    """
    Minimax algorithm with move extraction.
    Returns a tuple (best_move, value) where value is from player 1's perspective.
    best_move is None if the board is terminal.
    """
    winner = check_winner(board)
    if winner == 1:
        return (None, 1)  # player 1 wins
    elif winner == -1:
        return (None, -1)  # player -1 wins
    elif is_board_full(board):
        return (None, 0)  # draw

    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                moves.append((i, j))

    if current_player == 1:
        best_score = -float('inf')
        best_move = None
        for move in moves:
            new_board = [row[:] for row in board]  # deep copy
            new_board[move[0]][move[1]] = current_player
            _, score = minimax_with_move(new_board, -current_player)
            if score > best_score:
                best_score = score
                best_move = move
        return (best_move, best_score)
    else:
        best_score = float('inf')
        best_move = None
        for move in moves:
            new_board = [row[:] for row in board]
            new_board[move[0]][move[1]] = current_player
            _, score = minimax_with_move(new_board, -current_player)
            if score < best_score:
                best_score = score
                best_move = move
        return (best_move, best_score)

def policy(board):
    """
    Provide the next move for the Tic Tac Toe game.
    Assumes it is the AI's turn (player 1).
    Returns a tuple (row, col) for the chosen move.
    """
    best_move, _ = minimax_with_move(board, 1)
    return best_move
