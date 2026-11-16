
import math

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_wins():
        wins = []
        # Orthogonal lines
        for dim in range(3):
            others = [d for d in range(3) if d != dim]
            fixed1 = others[0]
            fixed2 = others[1]
            for f1 in range(3):
                for f2 in range(3):
                    line = []
                    for v in range(3):
                        pos = [0, 0, 0]
                        pos[dim] = v
                        pos[fixed1] = f1
                        pos[fixed2] = f2
                        line.append(tuple(pos))
                    wins.append(line)
        # Diagonals
        diag_lines = [
            [[0, 0], [1, 1], [2, 2]],
            [[0, 2], [1, 1], [2, 0]],
            [[2, 0], [1, 1], [0, 2]]
        ]
        for fixed_dim in range(3):
            others = [d for d in range(3) if d != fixed_dim]
            var1, var2 = others
            for fixed_val in range(3):
                for diag in diag_lines:
                    line = []
                    for p in diag:
                        pos = [0, 0, 0]
                        pos[var1] = p[0]
                        pos[var2] = p[1]
                        pos[fixed_dim] = fixed_val
                        line.append(tuple(pos))
                    wins.append(line)
        return wins

    wins = get_wins()

    def is_terminal(board):
        for win in wins:
            s = sum(board[i][j][k] for i, j, k in win)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return None

    def minimax(board, depth, alpha, beta, maximizing):
        term = is_terminal(board)
        if term is not None:
            return term if maximizing else -term
        if depth == 0:
            heur = 0
            for win in wins:
                s = sum(board[i][j][k] for i, j, k in win)
                if s > 0:
                    heur += [0, 1, 10][s]
                elif s < 0:
                    heur -= [0, 1, 10][-s]
            return heur
        if maximizing:
            max_eval = -math.inf
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            board[i][j][k] = 1
                            eval = minimax(board, depth - 1, alpha, beta, False)
                            board[i][j][k] = 0
                            if eval > max_eval:
                                max_eval = eval
                            if eval > alpha:
                                alpha = eval
                            if beta <= alpha:
                                return max_eval
            return max_eval
        else:
            min_eval = math.inf
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            board[i][j][k] = -1
                            eval = minimax(board, depth - 1, alpha, beta, True)
                            board[i][j][k] = 0
                            if eval < min_eval:
                                min_eval = eval
                            if eval < beta:
                                beta = eval
                            if beta <= alpha:
                                return min_eval
            return min_eval

    # Find the best move
    max_eval = -math.inf
    best_move = None
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = 1
                    eval = minimax(board, 3, -math.inf, math.inf, False)
                    board[i][j][k] = 0
                    if eval > max_eval:
                        max_eval = eval
                        best_move = (i, j, k)
    return best_move
