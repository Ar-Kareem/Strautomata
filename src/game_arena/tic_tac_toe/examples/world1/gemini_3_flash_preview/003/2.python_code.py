
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements an optimal Tic Tac Toe strategy using Minimax with Alpha-Beta Pruning.
    """
    
    def check_winner(b):
        # Check rows and columns
        for i in range(3):
            if abs(sum(b[i])) == 3:
                return b[i][0]
            if abs(sum(b[j][i] for j in range(3))) == 3:
                return b[0][i]
        # Check diagonals
        if abs(b[0][0] + b[1][1] + b[2][2]) == 3:
            return b[1][1]
        if abs(b[0][2] + b[1][1] + b[2][0]) == 3:
            return b[1][1]
        return 0

    def is_full(b):
        return all(cell != 0 for row in b for cell in row)

    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1: return 10 - depth
        if winner == -1: return depth - 10
        if is_full(b): return 0

        if is_maximizing:
            best_score = -float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        score = minimax(b, depth + 1, False, alpha, beta)
                        b[r][c] = 0
                        best_score = max(score, best_score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            break
            return best_score
        else:
            best_score = float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        score = minimax(b, depth + 1, True, alpha, beta)
                        b[r][c] = 0
                        best_score = min(score, best_score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
            return best_score

    best_val = -float('inf')
    best_move = (-1, -1)

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                move_val = minimax(board, 0, False, -float('inf'), float('inf'))
                board[r][c] = 0
                if move_val > best_val:
                    best_val = move_val
                    best_move = (r, c)

    return best_move
