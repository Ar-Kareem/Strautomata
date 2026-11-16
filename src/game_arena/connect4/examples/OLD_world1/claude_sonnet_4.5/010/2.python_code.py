
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning.
    Returns the column to play.
    """
    board_array = np.array(board)
    rows, cols = board_array.shape
    
    def get_valid_columns(b):
        """Return list of columns that are not full."""
        return [c for c in range(cols) if b[0][c] == 0]
    
    def drop_disc(b, col, player):
        """Return new board with disc dropped in column."""
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
        """Evaluate a window of 4 positions."""
        score = 0
        opp = -player
        
        player_count = np.sum(window == player)
        opp_count = np.sum(window == opp)
        empty_count = np.sum(window == 0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opp_count == 3 and empty_count == 1:
            score -= 4
        
        return score
    
    def score_position(b, player):
        """Heuristic evaluation of board position."""
        score = 0
        
        # Center column preference
        center_array = [int(b[r][cols//2]) for r in range(rows)]
        center_count = center_array.count(player)
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
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(np.array(window), player)
        
        # Diagonal (down-left)
        for r in range(rows - 3):
            for c in range(3, cols):
                window = [b[r+i][c-i] for i in range(4)]
                score += evaluate_window(np.array(window), player)
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing_player, player):
        """Minimax with alpha-beta pruning."""
        valid_cols = get_valid_columns(b)
        
        is_terminal = check_win(b, player) or check_win(b, -player) or len(valid_cols) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(b, player):
                    return (None, 1000000)
                elif check_win(b, -player):
                    return (None, -1000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(b, player))
        
        if maximizing_player:
            value = -np.inf
            best_col = valid_cols[0]
            for col in valid_cols:
                new_board, _ = drop_disc(b, col, player)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, False, player)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = np.inf
            best_col = valid_cols[0]
            for col in valid_cols:
                new_board, _ = drop_disc(b, col, -player)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, True, player)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value
    
    # Check for immediate win
    valid_columns = get_valid_columns(board_array)
    for col in valid_columns:
        temp_board, _ = drop_disc(board_array, col, 1)
        if check_win(temp_board, 1):
            return col
    
    # Check for immediate block
    for col in valid_columns:
        temp_board, _ = drop_disc(board_array, col, -1)
        if check_win(temp_board, -1):
            return col
    
    # Use minimax
    depth = 5
    best_col, _ = minimax(board_array, depth, -np.inf, np.inf, True, 1)
    
    return best_col
