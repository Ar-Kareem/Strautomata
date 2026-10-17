
import math
import copy

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Minimax with alpha-beta pruning for Tic Tac Toe.
    Returns optimal move as (row, col).
    """
    
    def check_win(board, player):
        # Check rows, columns, diagonals
        for i in range(3):
            if all(board[i][j] == player for j in range(3)):
                return True
            if all(board[j][i] == player for j in range(3)):
                return True
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2-i] == player for i in range(3)):
            return True
        return False
    
    def get_empty_cells(board):
        return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        # Terminal states
        if check_win(board, 1):
            return 10 - depth
        if check_win(board, -1):
            return depth - 10
        if len(get_empty_cells(board)) == 0:
            return 0
        
        if is_maximizing:
            max_eval = -math.inf
            for row, col in get_empty_cells(board):
                board_copy = copy.deepcopy(board)
                board_copy[row][col] = 1
                eval_score = minimax(board_copy, depth + 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for row, col in get_empty_cells(board):
                board_copy = copy.deepcopy(board)
                board_copy[row][col] = -1
                eval_score = minimax(board_copy, depth + 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # First, check for immediate win
    for row, col in get_empty_cells(board):
        board_copy = copy.deepcopy(board)
        board_copy[row][col] = 1
        if check_win(board_copy, 1):
            return (row, col)
    
    # Then, check if need to block opponent's win
    for row, col in get_empty_cells(board):
        board_copy = copy.deepcopy(board)
        board_copy[row][col] = -1
        if check_win(board_copy, -1):
            return (row, col)
    
    # If center available, take it (best strategic position)
    if board[1][1] == 0:
        return (1, 1)
    
    # Use minimax to find the best move
    best_score = -math.inf
    best_move = None
    alpha = -math.inf
    beta = math.inf
    
    for row, col in get_empty_cells(board):
        board_copy = copy.deepcopy(board)
        board_copy[row][col] = 1
        move_score = minimax(board_copy, 0, False, alpha, beta)
        if move_score > best_score:
            best_score = move_score
            best_move = (row, col)
        alpha = max(alpha, best_score)
    
    # Fallback (should never reach here if board has empty cells)
    if best_move is None:
        empty = get_empty_cells(board)
        if empty:
            return empty[0]
    
    return best_move
