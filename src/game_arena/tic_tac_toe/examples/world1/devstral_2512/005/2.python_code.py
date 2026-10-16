
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a minimax algorithm with alpha-beta pruning for Tic Tac Toe.
    Returns the best move for the current player (1) on the given board.
    """
    def evaluate(board):
        # Check rows for a win
        for row in board:
            if row[0] == row[1] == row[2]:
                if row[0] == 1:
                    return 10
                elif row[0] == -1:
                    return -10

        # Check columns for a win
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col]:
                if board[0][col] == 1:
                    return 10
                elif board[0][col] == -1:
                    return -10

        # Check diagonals for a win
        if board[0][0] == board[1][1] == board[2][2]:
            if board[0][0] == 1:
                return 10
            elif board[0][0] == -1:
                return -10

        if board[0][2] == board[1][1] == board[2][0]:
            if board[0][2] == 1:
                return 10
            elif board[0][2] == -1:
                return -10

        # If no winner, return 0
        return 0

    def is_moves_left(board):
        for row in board:
            for cell in row:
                if cell == 0:
                    return True
        return False

    def minimax(board, depth, is_maximizing, alpha, beta):
        score = evaluate(board)

        # If maximizer has won
        if score == 10:
            return score - depth

        # If minimizer has won
        if score == -10:
            return score + depth

        # If no moves left and no winner, it's a draw
        if not is_moves_left(board):
            return 0

        if is_maximizing:
            best = -float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        best = max(best, minimax(board, depth + 1, False, alpha, beta))
                        board[i][j] = 0
                        alpha = max(alpha, best)
                        if beta <= alpha:
                            return best
            return best
        else:
            best = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        best = min(best, minimax(board, depth + 1, True, alpha, beta))
                        board[i][j] = 0
                        beta = min(beta, best)
                        if beta <= alpha:
                            return best
            return best

    best_val = -float('inf')
    best_move = (-1, -1)

    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                move_val = minimax(board, 0, False, -float('inf'), float('inf'))
                board[i][j] = 0

                if move_val > best_val:
                    best_move = (i, j)
                    best_val = move_val

    return best_move
