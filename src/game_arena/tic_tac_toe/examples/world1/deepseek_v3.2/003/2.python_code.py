
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

def minimax(board, depth, alpha, beta, is_maximizing):
    """Minimax with alpha-beta pruning."""
    winner = check_winner(board)
    if winner == 1:
        return 10 - depth
    if winner == -1:
        return depth - 10
    # board full?
    if all(board[i][j] != 0 for i in range(3) for j in range(3)):
        return 0

    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    if is_maximizing:
        max_eval = -math.inf
        for (i, j) in empty_cells:
            board[i][j] = 1
            eval = minimax(board, depth + 1, alpha, beta, False)
            board[i][j] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for (i, j) in empty_cells:
            board[i][j] = -1
            eval = minimax(board, depth + 1, alpha, beta, True)
            board[i][j] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """Return the next move (row, col) for player 1."""
    best_score = -math.inf
    best_move = None
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    if not empty_cells:
        return (0, 0)  # should not happen in a valid game

    # preference order: center, corners, edges
    priority_map = {
        (1, 1): 5,
        (0, 0): 4, (0, 2): 4, (2, 0): 4, (2, 2): 4,
        (0, 1): 3, (1, 0): 3, (1, 2): 3, (2, 1): 3
    }

    for (i, j) in empty_cells:
        board[i][j] = 1
        score = minimax(board, depth=1, alpha=-math.inf, beta=math.inf, is_maximizing=False)
        board[i][j] = 0
        if (best_move is None or
            score > best_score or
            (score == best_score and priority_map[(i, j)] > priority_map[best_move])):
            best_score = score
            best_move = (i, j)

    return best_move
