
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winner(board_state, player):
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            if all(board_state[i][j] == player for j in range(3)):
                return True
            if all(board_state[j][i] == player for j in range(3)):
                return True
        if all(board_state[i][i] == player for i in range(3)):
            return True
        if all(board_state[i][2 - i] == player for i in range(3)):
            return True
        return False

    def is_draw(board_state):
        return all(board_state[i][j] != 0 for i in range(3) for j in range(3))

    def get_available_moves(board_state):
        return [(i, j) for i in range(3) for j in range(3) if board_state[i][j] == 0]

    def minimax(board_state, depth, alpha, beta, is_maximizing):
        if is_winner(board_state, 1):
            return 10 - depth
        if is_winner(board_state, -1):
            return depth - 10
        if is_draw(board_state):
            return 0

        if is_maximizing:
            best = -math.inf
            for i, j in get_available_moves(board_state):
                board_state[i][j] = 1
                best = max(best, minimax(board_state, depth + 1, alpha, beta, False))
                board_state[i][j] = 0
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = math.inf
            for i, j in get_available_moves(board_state):
                board_state[i][j] = -1
                best = min(best, minimax(board_state, depth + 1, alpha, beta, True))
                board_state[i][j] = 0
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    # Check for immediate winning move
    for i, j in get_available_moves(board):
        board[i][j] = 1
        if is_winner(board, 1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0

    # Check for opponent's immediate threat
    for i, j in get_available_moves(board):
        board[i][j] = -1
        if is_winner(board, -1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0

    # Use minimax to find optimal move
    best_move = (-1, -1)
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf
    board_copy = [row[:] for row in board]

    for i, j in get_available_moves(board_copy):
        board_copy[i][j] = 1
        move_value = minimax(board_copy, 0, alpha, beta, False)
        board_copy[i][j] = 0
        if move_value > best_value:
            best_value = move_value
            best_move = (i, j)
        alpha = max(alpha, best_value)

    return best_move
