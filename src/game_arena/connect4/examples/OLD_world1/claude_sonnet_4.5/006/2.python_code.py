
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy that uses minimax with alpha-beta pruning.
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
        # Diagonal (down-right)
        for r in range(rows - 3):
            for c in range(cols - 3):
                if all(b[r+i][c+i] == player for i in range(4)):
                    return True
        # Diagonal (down-left)
        for r in range(rows - 3):
            for c in range(3, cols):
                if all(b[r+i][c-i] == player for i in range(4)):
                    return True
        return False
    
    def evaluate_window(window, player):
        """Evaluate a window of 4 cells."""
        score = 0
        opp = -player
        
        if np.count_nonzero(window == player) == 4:
            score += 100
        elif np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
            score += 5
        elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
            score += 2
        
        if np.count_nonzero(window == opp) == 3 and np.count_nonzero(window == 0) == 1:
            score -= 4
        
        return score
    
    def evaluate_position(b, player):
        """Evaluate the board position."""
        score = 0
        
        # Center column preference
        center = cols // 2
        center_count = np.count_nonzero(b[:, center] == player)
        score += center_count * 3
        
        # Horizontal
        for r in range(rows):
            for c in range(cols - 3):
                window = b[r, c:c+4]
                score += evaluate_window(window, player)
        
        # Vertical
        for c in range(cols):
            for r in range(rows - 3):
                window = b[r:r+4, c]
                score += evaluate_window(window, player)
        
        # Diagonal (down-right)
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = np.array([b[r+i][c+i] for i in range(4)])
                score += evaluate_window(window, player)
        
        # Diagonal (down-left)
        for r in range(rows - 3):
            for c in range(3, cols):
                window = np.array([b[r+i][c-i] for i in range(4)])
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing_player, player):
        """Minimax with alpha-beta pruning."""
        valid_moves = get_valid_moves(b)
        
        if depth == 0 or len(valid_moves) == 0:
            return None, evaluate_position(b, player)
        
        if check_win(b, player):
            return None, 1000000
        if check_win(b, -player):
            return None, -1000000
        
        if maximizing_player:
            max_eval = -float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board, _ = drop_disc(b, col, player)
                _, eval_score = minimax(new_board, depth - 1, alpha, beta, False, player)
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
                new_board, _ = drop_disc(b, col, -player)
                _, eval_score = minimax(new_board, depth - 1, alpha, beta, True, player)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_col, min_eval
    
    # Check for immediate win
    for col in get_valid_moves(board):
        test_board, _ = drop_disc(board, col, 1)
        if check_win(test_board, 1):
            return col
    
    # Check for immediate block
    for col in get_valid_moves(board):
        test_board, _ = drop_disc(board, col, -1)
        if check_win(test_board, -1):
            return col
    
    # Use minimax
    best_move, _ = minimax(board, 4, -float('inf'), float('inf'), True, 1)
    
    return best_move if best_move is not None else get_valid_moves(board)[0]
