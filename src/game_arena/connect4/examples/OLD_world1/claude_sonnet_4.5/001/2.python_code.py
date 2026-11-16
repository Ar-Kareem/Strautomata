
import random
import math

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning.
    """
    ROWS = 6
    COLS = 7
    
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(COLS) if is_valid_move(board, col)]
    
    def make_move(board, col, player):
        # Create a copy and drop the disc
        new_board = [row[:] for row in board]
        for row in range(ROWS - 1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board, row
        return new_board, -1
    
    def check_win(board, player):
        # Horizontal
        for row in range(ROWS):
            for col in range(COLS - 3):
                if all(board[row][col + i] == player for i in range(4)):
                    return True
        
        # Vertical
        for row in range(ROWS - 3):
            for col in range(COLS):
                if all(board[row + i][col] == player for i in range(4)):
                    return True
        
        # Diagonal (down-right)
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                if all(board[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Diagonal (down-left)
        for row in range(ROWS - 3):
            for col in range(3, COLS):
                if all(board[row + i][col - i] == player for i in range(4)):
                    return True
        
        return False
    
    def is_terminal(board):
        if check_win(board, 1) or check_win(board, -1):
            return True
        return len(get_valid_moves(board)) == 0
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opponent_count == 3 and empty_count == 1:
            score -= 4
        
        return score
    
    def evaluate_position(board, player):
        score = 0
        
        # Center column preference
        center_array = [board[row][COLS // 2] for row in range(ROWS)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Horizontal
        for row in range(ROWS):
            for col in range(COLS - 3):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical
        for row in range(ROWS - 3):
            for col in range(COLS):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (down-right)
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (down-left)
        for row in range(ROWS - 3):
            for col in range(3, COLS):
                window = [board[row + i][col - i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves(board)
        is_term = is_terminal(board)
        
        if depth == 0 or is_term:
            if is_term:
                if check_win(board, 1):
                    return None, 1000000
                elif check_win(board, -1):
                    return None, -1000000
                else:
                    return None, 0
            else:
                return None, evaluate_position(board, 1)
        
        if maximizing_player:
            value = -math.inf
            best_col = random.choice(valid_moves)
            for col in valid_moves:
                new_board, _ = make_move(board, col, 1)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = math.inf
            best_col = random.choice(valid_moves)
            for col in valid_moves:
                new_board, _ = make_move(board, col, -1)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
    
    # Check for immediate winning move
    for col in get_valid_moves(board):
        new_board, _ = make_move(board, col, 1)
        if check_win(new_board, 1):
            return col
    
    # Check for opponent's winning move and block it
    for col in get_valid_moves(board):
        new_board, _ = make_move(board, col, -1)
        if check_win(new_board, -1):
            return col
    
    # Use minimax
    depth = 5
    best_col, _ = minimax(board, depth, -math.inf, math.inf, True)
    
    return best_col
