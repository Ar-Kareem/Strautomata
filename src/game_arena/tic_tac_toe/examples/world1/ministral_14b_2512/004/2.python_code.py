
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next best move for the player (1) in a Tic Tac Toe game.
    The strategy is based on minimax with alpha-beta pruning to guarantee a win or draw.
    """
    # Check if the current player can win immediately
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                if is_winning_move(board, row, col, 1):
                    return (row, col)

    # Block opponent's immediate win
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                if is_winning_move(board, row, col, -1):
                    return (row, col)

    # If no immediate win or block, use minimax to find the best move
    best_score = -np.inf
    best_move = None
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                # Simulate the move
                board[row][col] = 1
                score = minimax(board, -np.inf, np.inf, False)
                board[row][col] = 0
                if score > best_score:
                    best_score = score
                    best_move = (row, col)

    return best_move

def minimax(board: list[list[int]], alpha: float, beta: float, is_maximizing: bool) -> int:
    """
    Minimax algorithm with alpha-beta pruning to evaluate the best move.
    """
    # Check if the game is over
    if check_winner(board) != 0:
        return evaluate(board)

    if is_maximizing:
        best_score = -np.inf
        for row in range(3):
            for col in range(3):
                if board[row][col] == 0:
                    board[row][col] = 1
                    score = minimax(board, alpha, beta, False)
                    board[row][col] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = np.inf
        for row in range(3):
            for col in range(3):
                if board[row][col] == 0:
                    board[row][col] = -1
                    score = minimax(board, alpha, beta, True)
                    board[row][col] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
        return best_score

def evaluate(board: list[list[int]]) -> int:
    """
    Evaluates the board state.
    Returns 1 if the current player (1) wins, -1 if the opponent (-1) wins, 0 otherwise.
    """
    return check_winner(board)

def check_winner(board: list[list[int]]) -> int:
    """
    Checks if there is a winner or if the game is a draw.
    Returns 1 if the current player (1) wins, -1 if the opponent (-1) wins, 0 otherwise.
    """
    # Check rows
    for row in range(3):
        if board[row][0] != 0 and board[row][0] == board[row][1] == board[row][2]:
            return board[row][0]

    # Check columns
    for col in range(3):
        if board[0][col] != 0 and board[0][col] == board[1][col] == board[2][col]:
            return board[0][col]

    # Check diagonals
    if board[0][0] != 0 and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != 0 and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]

    # Check if the board is full (draw)
    if all(cell != 0 for row in board for cell in row):
        return 0

    return None

def is_winning_move(board: list[list[int]], row: int, col: int, player: int) -> bool:
    """
    Checks if placing a player's mark in the specified cell would result in a win.
    """
    # Save the current state
    original = board[row][col]
    board[row][col] = player

    # Check if the move results in a win
    winner = check_winner(board)
    board[row][col] = original

    return winner == player
