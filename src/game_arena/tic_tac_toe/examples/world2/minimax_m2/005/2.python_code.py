
import functools

def check_winner(board):
    """Check for a winner or draw in the 4x4 board.
    Returns 1 if player 1 wins, -1 if player 2 wins, 0 for draw, or None if game continues."""
    # Check rows
    for i in range(4):
        if board[i][0] != 0:
            winner = board[i][0]
            for j in range(1, 4):
                if board[i][j] != winner:
                    break
            else:
                return winner
    # Check columns
    for j in range(4):
        if board[0][j] != 0:
            winner = board[0][j]
            for i in range(1, 4):
                if board[i][j] != winner:
                    break
            else:
                return winner
    # Check diagonals
    if board[0][0] != 0:
        winner = board[0][0]
        for i in range(1, 4):
            if board[i][i] != winner:
                break
        else:
            return winner
    if board[0][3] != 0:
        winner = board[0][3]
        for i in range(1, 4):
            if board[i][3 - i] != winner:
                break
        else:
            return winner
    # Check for draw
    if all(board[i][j] != 0 for i in range(4) for j in range(4)):
        return 0
    return None

@functools.lru_cache(maxsize=None)
def minimax(board_tuple, depth, maximizing_player):
    """Minimax algorithm with memoization to evaluate the board state.
    Returns a tuple (score, best_move) where best_move is (row, col) or None if game over."""
    board = [list(row) for row in board_tuple]  # Convert to list for easier manipulation
    winner = check_winner(board)
    if winner is not None:
        if winner == 1:
            return (1000 - depth, None)
        elif winner == -1:
            return (-1000 + depth, None)
        else:
            return (0, None)
    
    if maximizing_player:
        max_eval = -float('inf')
        best_move = None
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    # Make a move for player 1
                    new_board = [row[:] for row in board]
                    new_board[i][j] = 1
                    new_board_tuple = tuple(tuple(row) for row in new_board)
                    eval_score, _ = minimax(new_board_tuple, depth + 1, False)
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = (i, j)
        return (max_eval, best_move)
    else:
        min_eval = float('inf')
        best_move = None
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    # Make a move for player 2
                    new_board = [row[:] for row in board]
                    new_board[i][j] = -1
                    new_board_tuple = tuple(tuple(row) for row in new_board)
                    eval_score, _ = minimax(new_board_tuple, depth + 1, True)
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = (i, j)
        return (min_eval, best_move)

def policy(board):
    """Return the next move (row, col) for player 1 given the board state."""
    board_tuple = tuple(tuple(row) for row in board)
    _, move = minimax(board_tuple, 0, True)
    return move
