
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winner(b, player):
        # Check rows, columns, diagonals
        for i in range(3):
            if all(b[i][j] == player for j in range(3)) or all(b[j][i] == player for j in range(3)):
                return True
        if all(b[i][i] == player for i in range(3)) or all(b[i][2-i] == player for i in range(3)):
            return True
        return False

    def is_draw(b):
        return all(b[i][j] != 0 for i in range(3) for j in range(3)) and not is_winner(b, 1) and not is_winner(b, -1)

    def minimax(b, is_maximizing, alpha=float('-inf'), beta=float('inf')):
        if is_winner(b, 1):
            return 10
        if is_winner(b, -1):
            return -10
        if is_draw(b):
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval = minimax(b, False, alpha, beta)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval = minimax(b, True, alpha, beta)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return min_eval

    # Get all legal moves with their scores
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, False)  # Opponent's turn next
                board[i][j] = 0
                moves.append((score, i, j))

    # Sort by score (best first), then by priority: center (1,1), then corners, then edges
    def move_priority(move):
        i, j = move[1], move[2]
        if i == 1 and j == 1:
            return 10
        elif i % 2 == 0 and j % 2 == 0:  # Corners
            return 5
        else:  # Edges
            return 0

    moves.sort(key=lambda x: (-x[0], -move_priority(x)))  # Highest score first, then highest priority

    # Return the best move
    _, row, col = moves[0]
    return (row, col)
