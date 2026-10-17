
import numpy as np

def policy(board):
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Check for immediate win
    for col in range(7):
        if can_win(board, col, 1):
            return col
    
    # Check if opponent can win next move
    for col in range(7):
        if can_win(board, col, -1):
            return col
    
    # Evaluate columns and choose best move
    best_score = -float('inf')
    best_col = 3  # Default to center column
    
    # Prefer columns closer to center if scores are equal
    column_order = [3, 2, 4, 1, 5, 0, 6]
    
    for col in column_order:
        if not is_valid_move(board, col):
            continue
            
        # Make temporary move
        temp_board = board.copy()
        row = get_next_open_row(temp_board, col)
        temp_board[row, col] = 1
        
        # Score the move
        score = evaluate_position(temp_board, col, row)
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col

def is_valid_move(board, col):
    """Check if column has space"""
    return board[0, col] == 0

def get_next_open_row(board, col):
    """Return lowest empty row in column"""
    for row in range(5, -1, -1):
        if board[row, col] == 0:
            return row
    return -1

def can_win(board, col, player):
    """Check if placing in column would result in win for player"""
    if not is_valid_move(board, col):
        return False
        
    temp_board = board.copy()
    row = get_next_open_row(temp_board, col)
    temp_board[row, col] = player
    
    # Check all directions for connect 4
    directions = [
        (0, 1),  # Horizontal
        (1, 0),  # Vertical
        (1, 1),  # Diagonal down-right
        (1, -1)   # Diagonal down-left
    ]
    
    for dr, dc in directions:
        count = 1
        
        # Search in positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and temp_board[r, c] == player:
            count += 1
            r += dr
            c += dc
        
        # Search in negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and temp_board[r, c] == player:
            count += 1
            r -= dr
            c -= dc
        
        if count >= 4:
            return True
            
    return False

def evaluate_position(board, col, row):
    """Simple evaluation of position's value"""
    player = 1
    opponent = -1
    score = 0
    
    # Give some advantage to center columns
    center_bonus = [0, 0, 1, 2, 1, 0, 0]
    score += center_bonus[col] * 3
    
    # Score patterns in all directions
    directions = [
        (0, 1),  # Horizontal
        (1, 0),  # Vertical
        (1, 1),  # Diagonal down-right
        (1, -1)   # Diagonal down-left
    ]
    
    for dr, dc in directions:
        for player_type, weight in [(player, 1), (opponent, 0.8)]:
            # Look in both directions from the placed piece
            line = [player_type]
            
            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r, c] != -player_type:
                line.append(board[r, c])
                r += dr
                c += dc
            
            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r, c] != -player_type:
                line.insert(0, board[r, c])
                r -= dr
                c -= dc
            
            # Count player discs in this line
            player_count = line.count(player_type)
            empty_count = line.count(0)
            
            if player_count == 3 and empty_count >= 1:
                score += 100 * weight
            elif player_count == 2 and empty_count >= 2:
                score += 10 * weight
            elif player_count == 1 and empty_count >= 3:
                score += 1 * weight
    
    return score
