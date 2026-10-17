
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy that uses minimax with alpha-beta pruning and strategic heuristics.
    """
    board = np.array(board)
    rows, cols = board.shape
    
    def get_valid_moves(b):
        """Return list of valid column indices."""
        return [c for c in range(cols) if b[0][c] == 0]
    
    def drop_disc(b, col, player):
        """Drop a disc in the given column and return new board."""
        new_board = b.copy()
        for row in range(rows - 1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board, row
        return new_board, -1
    
    def check_win(b, player):
        """Check if player has won."""
        # Horizontal
        for r in range(rows):
            for c in range(cols - 3):
                if all(b[r][c+i] == player for i in range(4)):
                    return True
        # Vertical
        for r in range(rows - 3):
            for c in range(cols):
                if all(b[r+i][c] == player for i in range(4)):
                    return True
        # Diagonal (positive slope)
        for r in range(rows - 3):
            for c in range(cols - 3):
                if all(b[r+i][c+i] == player for i in range(4)):
                    return True
        # Diagonal (negative slope)
        for r in range(3, rows):
            for c in range(cols - 3):
                if all(b[r-i][c+i] == player for i in range(4)):
                    return True
        return False
    
    def count_windows(b, player):
        """Count strategic windows for evaluation."""
        score = 0
        
        # Check all possible 4-in-a-row windows
        # Horizontal
        for r in range(rows):
            for c in range(cols - 3):
                window = [b[r][c+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical
        for r in range(rows - 3):
            for c in range(cols):
                window = [b[r+i][c] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (positive slope)
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (negative slope)
        for r in range(3, rows):
            for c in range(cols - 3):
                window = [b[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Center column preference
        center_col = cols // 2
        center_count = sum(1 for r in range(rows) if b[r][center_col] == player)
        score += center_count * 3
        
        return score
    
    def evaluate_window(window, player):
        """Evaluate a 4-cell window."""
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
    
    def evaluate_board(b):
        """Evaluate the board state."""
        if check_win(b, 1):
            return 10000
        if check_win(b, -1):
            return -10000
        
        return count_windows(b, 1) - count_windows(b, -1)
    
    def minimax(b, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        valid_moves = get_valid_moves(b)
        
        if depth == 0 or len(valid_moves) == 0:
            return None, evaluate_board(b)
        
        if check_win(b, 1):
            return None, 10000
        if check_win(b, -1):
            return None, -10000
        
        if maximizing:
            max_eval = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board, _ = drop_disc(b, col, 1)
                _, eval_score = minimax(new_board, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return best_col, max_eval
        else:
            min_eval = float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board, _ = drop_disc(b, col, -1)
                _, eval_score = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_col, min_eval
    
    # Check for immediate win
    for col in get_valid_moves(board):
        new_board, _ = drop_disc(board, col, 1)
        if check_win(new_board, 1):
            return col
    
    # Check for immediate block
    for col in get_valid_moves(board):
        new_board, _ = drop_disc(board, col, -1)
        if check_win(new_board, -1):
            return col
    
    # Use minimax with depth 4
    best_move, _ = minimax(board, 4, float('-inf'), float('inf'), True)
    
    return best_move if best_move is not None else get_valid_moves(board)[0]
