
import numpy as np
import copy

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    
    # Define player and opponent
    player = 1
    opponent = -1
    
    def is_valid_move(col):
        return 0 <= col < 7 and board_np[0][col] == 0
    
    def get_valid_moves():
        return [col for col in range(7) if is_valid_move(col)]
    
    def drop_disc(board, col, player):
        # Find lowest empty row in the column
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                board[row][col] = player
                return row
        return -1  # Should not happen if move is valid
    
    def remove_disc(board, col):
        # Remove the topmost disc in the column
        for row in range(6):
            if board[row][col] != 0:
                board[row][col] = 0
                return
    
    def check_win(board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if all(board[row][col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if all(board[row + i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (down-right)
        for row in range(3):
            for col in range(4):
                if all(board[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Check diagonal (up-right)
        for row in range(3, 6):
            for col in range(4):
                if all(board[row - i][col + i] == player for i in range(4)):
                    return True
        
        return False
    
    def score_position(board, player):
        score = 0
        
        # Center column control
        center_array = [board[i][3] for i in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Score horizontal windows
        for row in range(6):
            row_array = list(board[row])
            for col in range(4):
                window = row_array[col:col+4]
                score += evaluate_window(window, player)
        
        # Score vertical windows
        for col in range(7):
            col_array = [board[i][col] for i in range(6)]
            for row in range(3):
                window = col_array[row:row+4]
                score += evaluate_window(window, player)
        
        # Score positive sloped diagonal windows
        for row in range(3):
            for col in range(4):
                window = [board[row+i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score negative sloped diagonal windows
        for row in range(3, 6):
            for col in range(4):
                window = [board[row-i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        if window.count(player) == 4:
            score += 100
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 10
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 5
        
        if window.count(opponent) == 3 and window.count(0) == 1:
            score -= 80  # Block opponent's winning move
                
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves()
        is_terminal = len(valid_moves) == 0 or check_win(board, player) or check_win(board, opponent)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(board, player):
                    return (None, 1000000)
                elif check_win(board, opponent):
                    return (None, -1000000)
                else:  # Game over, no more moves
                    return (None, 0)
            else:  # Depth is 0
                return (None, score_position(board, player))
        
        if maximizing_player:
            value = -float('inf')
            best_col = valid_moves[0] if valid_moves else 3
            
            for col in valid_moves:
                # Make move
                row = drop_disc(board, col, player)
                
                # Recurse
                new_score = minimax(board, depth-1, alpha, beta, False)[1]
                
                # Undo move
                remove_disc(board, col)
                
                if new_score > value:
                    value = new_score
                    best_col = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            
            return best_col, value
        
        else:  # Minimizing player
            value = float('inf')
            best_col = valid_moves[0] if valid_moves else 3
            
            for col in valid_moves:
                # Make move
                row = drop_disc(board, col, opponent)
                
                # Recurse
                new_score = minimax(board, depth-1, alpha, beta, True)[1]
                
                # Undo move
                remove_disc(board, col)
                
                if new_score < value:
                    value = new_score
                    best_col = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break
            
            return best_col, value
    
    # Check for immediate win
    valid_moves = get_valid_moves()
    for col in valid_moves:
        drop_disc(board_np, col, player)
        if check_win(board_np, player):
            remove_disc(board_np, col)
            return col
        remove_disc(board_np, col)
    
    # Check for opponent's immediate win and block
    for col in valid_moves:
        drop_disc(board_np, col, opponent)
        if check_win(board_np, opponent):
            remove_disc(board_np, col)
            return col
        remove_disc(board_np, col)
    
    # If center is available, take it (strong opening strategy)
    if is_valid_move(3):
        return 3
    
    # Use minimax with adaptive depth based on remaining moves
    remaining_moves = len(valid_moves)
    depth = 5 if remaining_moves > 10 else 6
    
    best_move, _ = minimax(copy.deepcopy(board_np), depth, -float('inf'), float('inf'), True)
    
    # Fallback: if minimax returns invalid move, pick first valid move
    if not is_valid_move(best_move):
        return valid_moves[0] if valid_moves else 3
    
    return best_move
