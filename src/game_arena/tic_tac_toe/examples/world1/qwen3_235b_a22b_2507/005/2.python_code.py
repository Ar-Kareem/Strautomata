
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    def is_terminal(state):
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            if abs(state[i, :].sum()) == 3:
                return state[i, 0]
            if abs(state[:, i].sum()) == 3:
                return state[0, i]
        if abs(state[[0,1,2],[0,1,2]].sum()) == 3:
            return state[0,0]
        if abs(state[[0,1,2],[2,1,0]].sum()) == 3:
            return state[0,2]
        # Check for draw or ongoing
        if not (state == 0).any():
            return 0
        return None

    def minimax(state, depth, alpha, beta, maximizing):
        winner = is_terminal(state)
        if winner is not None:
            return winner

        if maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if state[i, j] == 0:
                        state[i, j] = 1
                        eval = minimax(state, depth + 1, alpha, beta, False)
                        state[i, j] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if state[i, j] == 0:
                        state[i, j] = -1
                        eval = minimax(state, depth + 1, alpha, beta, True)
                        state[i, j] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
            return min_eval

    best_score = -float('inf')
    best_move = (0, 0)
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                board[i, j] = 1
                score = minimax(board, 0, -float('inf'), float('inf'), False)
                board[i, j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move
