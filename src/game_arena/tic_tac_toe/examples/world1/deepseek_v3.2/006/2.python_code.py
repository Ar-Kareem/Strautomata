
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the best move for the AI (player 1) on the given Tic Tac Toe board.
    Uses minimax with alpha-beta pruning for optimal play.
    """
    # Helper function to check if a player has won
    def is_winner(b, player):
        # Check rows, columns, diagonals
        for i in range(3):
            if all(b[i][j] == player for j in range(3)):  # row i
                return True
            if all(b[j][i] == player for j in range(3)):  # column i
                return True
        if all(b[i][i] == player for i in range(3)):      # main diagonal
            return True
        if all(b[i][2-i] == player for i in range(3)):    # anti-diagonal
            return True
        return False

    # Helper function to check if the board is full
    def is_full(b):
        return all(b[i][j] != 0 for i in range(3) for j in range(3))

    # Minimax with alpha-beta pruning
    def minimax(b, depth, alpha, beta, maximizing):
        if is_winner(b, 1):
            return 1
        if is_winner(b, -1):
            return -1
        if is_full(b):
            return 0

        if maximizing:
            max_eval = -math.inf
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval = minimax(b, depth+1, alpha, beta, False)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval = minimax(b, depth+1, alpha, beta, True)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval

    # Find the best move for the AI (player 1)
    best_score = -math.inf
    best_move = None
    # Optional: check for immediate winning move or block (can speed up but not required)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try winning move first
                board[i][j] = 1
                if is_winner(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try blocking opponent's winning move
                board[i][j] = -1
                if is_winner(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # If no immediate win/block, use minimax
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, -math.inf, math.inf, False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    # In case no move found (should not happen), return first empty cell
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    return best_move
