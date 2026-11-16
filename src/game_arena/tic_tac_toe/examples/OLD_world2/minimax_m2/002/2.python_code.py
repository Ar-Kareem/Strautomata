
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    board_tuple = tuple(tuple(row) for row in board)
    
    def check_win(board):
        n = 4
        # Check rows
        for i in range(n):
            if board[i][0] != 0:
                if all(board[i][j] == board[i][0] for j in range(n)):
                    return board[i][0]
        # Check columns
        for j in range(n):
            if board[0][j] != 0:
                if all(board[i][j] == board[0][j] for i in range(n)):
                    return board[0][j]
        # Check main diagonal
        if board[0][0] != 0 and all(board[i][i] == board[0][0] for i in range(n)):
            return board[0][0]
        # Check anti-diagonal
        if board[0][n-1] != 0 and all(board[i][n-1-i] == board[0][n-1] for i in range(n)):
            return board[0][n-1]
        return 0

    @lru_cache(maxsize=None)
    def minimax(board_tuple, current_player, depth, alpha, beta):
        board = [list(row) for row in board_tuple]
        win = check_win(board)
        if win == 1:
            return (10 - depth, (-1, -1))
        elif win == -1:
            return (depth - 10, (-1, -1))
        if all(cell != 0 for row in board for cell in row):
            return (0, (-1, -1))
        
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    if i in (1, 2) and j in (1, 2):
                        priority = 1
                    elif (i in (0, 3) and j in (0, 3)):
                        priority = 2
                    else:
                        priority = 3
                    empty_cells.append((priority, i, j))
        empty_cells.sort()
        
        best_move = (-1, -1)
        if current_player == 1:
            max_eval = -float('inf')
            for _, i, j in empty_cells:
                board[i][j] = 1
                new_board_tuple = tuple(tuple(row) for row in board)
                score, _ = minimax(new_board_tuple, -1, depth+1, alpha, beta)
                board[i][j] = 0
                if score > max_eval:
                    max_eval = score
                    best_move = (i, j)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return (max_eval, best_move)
        else:
            min_eval = float('inf')
            for _, i, j in empty_cells:
                board[i][j] = -1
                new_board_tuple = tuple(tuple(row) for row in board)
                score, _ = minimax(new_board_tuple, 1, depth+1, alpha, beta)
                board[i][j] = 0
                if score < min_eval:
                    min_eval = score
                    best_move = (i, j)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return (min_eval, best_move)
    
    score, move = minimax(board_tuple, 1, 0, -float('inf'), float('inf'))
    return move
