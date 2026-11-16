
import math

def check_winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    # rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    # columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    # diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return 0

def is_full(board):
    """Return True if the board has no empty cells."""
    for row in board:
        if 0 in row:
            return False
    return True

def get_empty_cells(board):
    """Return a list of (row, col) tuples for all empty cells."""
    return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

def priority(cell):
    """Static move importance: center > corners > edges."""
    i, j = cell
    if (i, j) == (1, 1):
        return 3
    if i in (0, 2) and j in (0, 2):
        return 2
    return 1

def alphabeta(board, depth, alpha, beta, maximizing):
    """
    Alpha‑beta pruning search. Returns the score for the current node
    from the perspective of the maximizing player (player 1).
    """
    winner = check_winner(board)
    if winner == 1:
        return 10 - depth          # win earlier → higher score
    if winner == -1:
        return depth - 10          # lose later → less negative
    if is_full(board):
        return 0

    empty_cells = get_empty_cells(board)
    # Order moves to improve pruning; high priority first works well for both sides
    empty_cells.sort(key=priority, reverse=True)

    if maximizing:
        value = -math.inf
        for i, j in empty_cells:
            board[i][j] = 1
            value = max(value, alphabeta(board, depth + 1, alpha, beta, False))
            board[i][j] = 0
            if value >= beta:
                break
            alpha = max(alpha, value)
        return value
    else:
        value = math.inf
        for i, j in empty_cells:
            board[i][j] = -1
            value = min(value, alphabeta(board, depth + 1, alpha, beta, True))
            board[i][j] = 0
            if value <= alpha:
                break
            beta = min(beta, value)
        return value

def get_best_move(board):
    """Use alphabeta to find the best move for player 1."""
    best_score = -math.inf
    best_move = None
    empty_cells = get_empty_cells(board)
    empty_cells.sort(key=priority, reverse=True)   # better pruning + tie‑breaking
    for i, j in empty_cells:
        board[i][j] = 1
        score = alphabeta(board, 1, -math.inf, math.inf, False)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    return best_move

def policy(board):
    """
    Given a 3x3 board (0 = empty, 1 = us, -1 = opponent), return the next move
    as a tuple (row, col) with 0‑based indices.
    """
    # Immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Block opponent's immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Otherwise, search for the optimal move
    move = get_best_move(board)
    if move is not None:
        return move

    # Fallback (should never be reached)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)
