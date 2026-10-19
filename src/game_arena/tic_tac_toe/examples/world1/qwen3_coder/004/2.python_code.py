
import copy

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to work with our logic (1 is us, -1 is opponent)
    # Make a deep copy to avoid modifying the original
    game_board = copy.deepcopy(board)
    
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if game_board[i][j] == 0:
                game_board[i][j] = 1  # Try placing our mark
                if check_win(game_board, 1):
                    return (i, j)
                game_board[i][j] = 0  # Reset
    
    # Check for opponent's winning move to block
    for i in range(3):
        for j in range(3):
            if game_board[i][j] == 0:
                game_board[i][j] = -1  # Try opponent's move
                if check_win(game_board, -1):
                    return (i, j)
                game_board[i][j] = 0  # Reset
    
    # If no immediate win or block, use minimax
    best_move = None
    best_score = float('-inf')
    
    for i in range(3):
        for j in range(3):
            if game_board[i][j] == 0:
                game_board[i][j] = 1
                score = minimax(game_board, 0, False, float('-inf'), float('inf'))
                game_board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move

def check_win(board, player):
    # Check rows
    for i in range(3):
        if board[i][0] == player and board[i][1] == player and board[i][2] == player:
            return True
    
    # Check columns
    for j in range(3):
        if board[0][j] == player and board[1][j] == player and board[2][j] == player:
            return True
    
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    
    return False

def is_board_full(board):
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax(board, depth, is_maximizing, alpha, beta):
    # Check for terminal states
    if check_win(board, 1):  # We win
        return 10 - depth
    if check_win(board, -1):  # Opponent wins
        return depth - 10
    if is_board_full(board):  # Draw
        return 0
    
    if is_maximizing:  # Maximizing for us (player 1)
        max_eval = float('-inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_score = minimax(board, depth + 1, False, alpha, beta)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            if beta <= alpha:
                break
        return max_eval
    else:  # Minimizing for opponent (player -1)
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_score = minimax(board, depth + 1, True, alpha, beta)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
            if beta <= alpha:
                break
        return min_eval
