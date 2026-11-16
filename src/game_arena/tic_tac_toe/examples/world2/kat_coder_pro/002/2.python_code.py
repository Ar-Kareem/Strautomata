
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    def get_empty_cells(board):
        return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    def is_win(board, player):
        # Check rows
        for i in range(4):
            if np.all(board[i, :] == player):
                return True
        # Check columns
        for j in range(4):
            if np.all(board[:, j] == player):
                return True
        # Check diagonals
        if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
            return True
        return False
    
    def evaluate(board):
        if is_win(board, 1):
            return 10
        elif is_win(board, -1):
            return -10
        return 0
    
    def minimax(board, depth, alpha, beta, maximizing):
        score = evaluate(board)
        
        if score == 10:
            return score
        if score == -10:
            return score
        if len(get_empty_cells(board)) == 0:
            return 0
        
        if maximizing:
            best = -1000
            for cell in get_empty_cells(board):
                board[cell[0]][cell[1]] = 1
                best = max(best, minimax(board, depth + 1, alpha, beta, not maximizing))
                board[cell[0]][cell[1]] = 0
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = 1000
            for cell in get_empty_cells(board):
                board[cell[0]][cell[1]] = -1
                best = min(best, minimax(board, depth + 1, alpha, beta, not maximizing))
                board[cell[0]][cell[1]] = 0
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best
    
    def find_best_move(board):
        best_val = -1000
        best_move = (-1, -1)
        for cell in get_empty_cells(board):
            board[cell[0]][cell[1]] = 1
            move_val = minimax(board, 0, -1000, 1000, False)
            board[cell[0]][cell[1]] = 0
            if move_val > best_val:
                best_move = (cell[0], cell[1])
                best_val = move_val
        return best_move
    
    return find_best_move(board)
