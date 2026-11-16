
import numpy as np

def policy(board):
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    
    # Constants
    ROWS, COLS = 6, 7
    WINNING_LENGTH = 4
    INF = float('inf')
    
    def is_valid(col):
        return grid[0, col] == 0  # Top row empty means column not full
    
    def drop_piece(col, player):
        for r in range(ROWS-1, -1, -1):
            if grid[r, col] == 0:
                grid[r, col] = player
                return r
        return -1
    
    def undo_move(r, c):
        grid[r, c] = 0
    
    def get_valid_moves():
        return [c for c in range(COLS) if is_valid(c)]
    
    # Heuristic evaluation function
    def evaluate_window(window, player):
        opponent = -player
        player_count = np.count_nonzero(window == player)
        empty_count = np.count_nonzero(window == 0)
        opponent_count = WINNING_LENGTH - player_count - empty_count
        
        if player_count == 4:
            return 100000
        elif player_count == 3 and empty_count == 1:
            return 100
        elif player_count == 2 and empty_count == 2:
            return 10
        elif player_count == 1 and empty_count == 3:
            return 1
        
        if opponent_count == 3 and empty_count == 1:
            return -1000  # Block opponent's potential win
        
        if opponent_count == 2 and empty_count == 2:
            return -100  # Block strong threat
        
        return 0

    def score_position():
        score = 0
        center_array = grid[:, COLS//2]
        score += np.count_nonzero(center_array == 1) * 6  # Prefer center column
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = grid[r, c:c+WINNING_LENGTH]
                score += evaluate_window(window, 1)
        
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = grid[r:r+WINNING_LENGTH, c]
                score += evaluate_window(window, 1)
        
        # Positive diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+i][c+i] for i in range(WINNING_LENGTH)]
                score += evaluate_window(window, 1)
        
        # Negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [grid[r-i][c+i] for i in range(WINNING_LENGTH)]
                score += evaluate_window(window, 1)
        
        return score

    # Alpha-beta pruning with move ordering
    def minimax(depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves()
        
        # Use move ordering: sort by center proximity
        valid_moves.sort(key=lambda x: abs(x - COLS//2))
        
        if depth == 0 or len(valid_moves) == 0:
            return None, score_position()
        
        # Check for terminal conditions
        for col in valid_moves:
            row = drop_piece(col, 1 if maximizing_player else -1)
            if check_win(row, col, 1 if maximizing_player else -1):
                score = 1000000 if maximizing_player else -1000000
                undo_move(row, col)
                return col, score
            undo_move(row, col)
        
        if maximizing_player:
            max_val = -INF
            best_col = valid_moves[0]
            for col in valid_moves:
                row = drop_piece(col, 1)
                _, value = minimax(depth-1, alpha, beta, False)
                undo_move(row, col)
                if value > max_val:
                    max_val = value
                    best_col = col
                alpha = max(alpha, max_val)
                if alpha >= beta:
                    break  # Beta cutoff
            return best_col, max_val
        else:
            min_val = INF
            best_col = valid_moves[0]
            for col in valid_moves:
                row = drop_piece(col, -1)
                _, value = minimax(depth-1, alpha, beta, True)
                undo_move(row, col)
                if value < min_val:
                    min_val = value
                    best_col = col
                beta = min(beta, min_val)
                if beta <= alpha:
                    break  # Alpha cutoff
            return best_col, min_val
    
    def check_win(row, col, player):
        # Check all directions: horizontal, vertical, diagonal
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # positive diagonal
            (1, -1)   # negative diagonal
        ]
        
        for dr, dc in directions:
            count = 0
            # Check in positive direction
            r, c = row, col
            while 0 <= r < ROWS and 0 <= c < COLS and grid[r, c] == player:
                count += 1
                r += dr
                c += dc
            
            # Check in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < ROWS and 0 <= c < COLS and grid[r, c] == player:
                count += 1
                r -= dr
                c -= dc
            
            if count >= WINNING_LENGTH:
                return True
        return False
    
    # Main decision logic
    valid_moves = get_valid_moves()
    
    # Immediate win check
    for col in valid_moves:
        row = drop_piece(col, 1)
        if check_win(row, col, 1):
            undo_move(row, col)
            return col
        undo_move(row, col)
    
    # Block opponent immediate win
    for col in valid_moves:
        row = drop_piece(col, -1)
        if check_win(row, col, -1):
            undo_move(row, col)
            return col
        undo_move(row, col)
    
    # Determine depth based on number of available moves
    num_moves = len(valid_moves)
    if num_moves <= 4:
        depth = 8
    elif num_moves <= 6:
        depth = 7
    else:
        depth = 6
    
    # Use minimax to find best move
    try:
        best_col, _ = minimax(depth, -INF, INF, True)
        if best_col in valid_moves:
            return best_col
        else:
            return valid_moves[0]  # Fallback
    except:
        return valid_moves[0]

