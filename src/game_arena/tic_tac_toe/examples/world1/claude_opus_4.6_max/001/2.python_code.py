
import copy

def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0:
                return b[0][i]
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        return 0

    def get_empty(b):
        return [(i, j) for i in range(3) for j in range(3) if b[i][j] == 0]

    def minimax(b, maximizing, alpha, beta, depth):
        w = check_winner(b)
        if w == 1:
            return 10 - depth
        if w == -1:
            return -10 + depth
        empty = get_empty(b)
        if not empty:
            return 0
        if maximizing:
            best = -100
            for r, c in empty:
                b[r][c] = 1
                val = minimax(b, False, alpha, beta, depth + 1)
                b[r][c] = 0
                best = max(best, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best
        else:
            best = 100
            for r, c in empty:
                b[r][c] = -1
                val = minimax(b, True, alpha, beta, depth + 1)
                b[r][c] = 0
                best = min(best, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best

    b = copy.deepcopy(board)
    empty = get_empty(b)
    if not empty:
        return (0, 0)

    best_score = -100
    best_move = empty[0]

    for r, c in empty:
        b[r][c] = 1
        score = minimax(b, False, -100, 100, 0)
        b[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
