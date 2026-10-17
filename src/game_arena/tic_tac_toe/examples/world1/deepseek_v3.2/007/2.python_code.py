
import sys

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check if board is empty for first move (optimization)
    if all(board[i][j] == 0 for i in range(3) for j in range(3)):
        return (1, 1)  # center is best first move

    def winner(board):
        # rows
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] and board[i][0] != 0:
                return board[i][0]
        # columns
        for j in range(3):
            if board[0][j] == board[1][j] == board[2][j] and board[0][j] != 0:
                return board[0][j]
        # diagonals
        if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
            return board[0][2]
        return 0

    def minimax(state, depth, is_max, alpha, beta):
        win = winner(state)
        if win != 0:
            # win for maximizing player (1) gives positive, for minimizing (-1) negative
            # adjust by depth to prefer quicker wins
            return (10 - depth) if win == 1 else (-10 + depth)
        # draw
        if all(state[i][j] != 0 for i in range(3) for j in range(3)):
            return 0

        if is_max:
            best = -sys.maxsize
            for i in range(3):
                for j in range(3):
                    if state[i][j] == 0:
                        state[i][j] = 1
                        score = minimax(state, depth + 1, False, alpha, beta)
                        state[i][j] = 0
                        best = max(best, score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            break
                else:
                    continue
                break
            return best
        else:
            best = sys.maxsize
            for i in range(3):
                for j in range(3):
                    if state[i][j] == 0:
                        state[i][j] = -1
                        score = minimax(state, depth + 1, True, alpha, beta)
                        state[i][j] = 0
                        best = min(best, score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
                else:
                    continue
                break
            return best

    best_val = -sys.maxsize
    best_move = None
    # Try to order moves for better pruning: center, corners, edges
    move_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    for (i, j) in move_order:
        if board[i][j] == 0:
            board[i][j] = 1
            move_val = minimax(board, 0, False, -sys.maxsize, sys.maxsize)
            board[i][j] = 0
            if move_val > best_val:
                best_val = move_val
                best_move = (i, j)
    # fallback (should not happen if there is a move)
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    return best_move
