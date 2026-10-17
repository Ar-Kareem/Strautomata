
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Calculates the optimal next move for Tic Tac Toe using Minimax with Alpha-Beta pruning.
    '1' is the AI, '-1' is the opponent, '0' is empty.
    """
    
    # Helper to check for a winner
    def check_winner(b):
        # Rows
        for r in range(3):
            if b[r][0] != 0 and b[r][0] == b[r][1] == b[r][2]:
                return b[r][0]
        # Cols
        for c in range(3):
            if b[0][c] != 0 and b[0][c] == b[1][c] == b[2][c]:
                return b[0][c]
        # Diagonals
        if b[0][0] != 0 and b[0][0] == b[1][1] == b[2][2]:
            return b[0][0]
        if b[0][2] != 0 and b[0][2] == b[1][1] == b[2][0]:
            return b[0][2]
        return 0

    # Helper to check if board is full
    def is_full(b):
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    # Minimax algorithm with Alpha-Beta pruning
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10
        if is_full(b):
            return 0

        if is_maximizing:
            best_score = -math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        score = minimax(b, depth + 1, False, alpha, beta)
                        b[r][c] = 0
                        best_score = max(best_score, score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            break
            return best_score
        else:
            best_score = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        score = minimax(b, depth + 1, True, alpha, beta)
                        b[r][c] = 0
                        best_score = min(best_score, score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
            return best_score

    # 1. Check for immediate win
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if check_winner(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 2. Check for immediate block
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if check_winner(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 3. Opening move: Take center if available
    if board[1][1] == 0:
        return (1, 1)

    # 4. Use Minimax for the optimal move
    best_score = -math.inf
    best_move = (-1, -1)

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = minimax(board, 0, False, -math.inf, math.inf)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    return best_move
