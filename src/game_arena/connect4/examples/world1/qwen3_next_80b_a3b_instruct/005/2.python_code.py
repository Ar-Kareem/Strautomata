
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for efficient computation
    board = np.array(board, dtype=int)
    
    # Define player and opponent
    player = 1
    opponent = -1
    
    def get_valid_moves(board):
        """Return list of columns that are not full."""
        return [col for col in range(7) if board[0][col] == 0]
    
    def drop_disc(board, col, player):
        """Return a new board with the disc dropped in the specified column."""
        new_board = board.copy()
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board
        return new_board  # Should not reach here if col is valid
    
    def is_winning_move(board, player):
        """Check if the player has won."""
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
    
    def evaluate_board(board, player):
        """Heuristic evaluation of board state."""
        opponent = -player
        score = 0
        
        # Center column preference
        center_col = 3
        center_count = sum(1 for row in range(6) if board[row][center_col] == player)
        score += center_count * 3
        
        # Check for potential winning moves and blocking opponent wins
        # Score positions that can lead to 3 in a row
        for row in range(6):
            for col in range(7):
                # Horizontal
                if col <= 3:
                    window = board[row, col:col+4]
                    score += evaluate_window(window, player, opponent)
                
                # Vertical
                if row <= 2:
                    window = board[row:row+4, col]
                    score += evaluate_window(window, player, opponent)
                
                # Diagonal down-right
                if row <= 2 and col <= 3:
                    window = [board[row+i][col+i] for i in range(4)]
                    score += evaluate_window(window, player, opponent)
                
                # Diagonal up-right
                if row >= 3 and col <= 3:
                    window = [board[row-i][col+i] for i in range(4)]
                    score += evaluate_window(window, player, opponent)
        
        return score
    
    def evaluate_window(window, player, opponent):
        """Evaluate a 4-cell window for scoring."""
        score = 0
        player_count = np.sum(window == player)
        opponent_count = np.sum(window == opponent)
        empty_count = np.sum(window == 0)
        
        if player_count == 4:
            score += 100  # Win
        elif player_count == 3 and empty_count == 1:
            score += 5   # Potential win
        elif player_count == 2 and empty_count == 2:
            score += 2   # Potential connect
        elif opponent_count == 3 and empty_count == 1:
            score -= 4   # Block opponent's win
        elif opponent_count == 2 and empty_count == 2:
            score -= 1   # Block potential threat
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning."""
        valid_moves = get_valid_moves(board)
        
        # Check for terminal states
        if depth == 0 or len(valid_moves) == 0:
            return evaluate_board(board, player), None
        
        if is_winning_move(board, player):
            return 1000000, None
        if is_winning_move(board, opponent):
            return -1000000, None
        
        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            
            # Move ordering: center first, then other columns
            sorted_moves = sorted(valid_moves, key=lambda x: abs(x - 3), reverse=False)
            
            for col in sorted_moves:
                new_board = drop_disc(board, col, player)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = col
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval, best_move
        
        else:
            min_eval = float('inf')
            best_move = None
            
            # Move ordering: center first, then other columns
            sorted_moves = sorted(valid_moves, key=lambda x: abs(x - 3), reverse=False)
            
            for col in sorted_moves:
                new_board = drop_disc(board, col, opponent)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = col
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval, best_move
    
    # For very early game, prioritize center
    if np.sum(board != 0) <= 2:
        return 3  # Prefer center column
    
    # If we can win immediately, do it
    valid_moves = get_valid_moves(board)
    for col in valid_moves:
        temp_board = drop_disc(board, col, player)
        if is_winning_move(temp_board, player):
            return col
    
    # If opponent can win immediately, block it
    for col in valid_moves:
        temp_board = drop_disc(board, col, opponent)
        if is_winning_move(temp_board, opponent):
            return col
    
    # Otherwise, use minimax with depth 6 (within 1 second limit)
    # For faster performance on moderate hardware, we use depth 6
    _, best_move = minimax(board, 6, float('-inf'), float('inf'), True)
    return best_move if best_move is not None else valid_moves[0] if valid_moves else 3
