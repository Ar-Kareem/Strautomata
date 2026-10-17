
def policy(board: list[list[int]]) -> int:
    import numpy as np
    
    # Convert to numpy array for easier manipulation
    np_board = np.array(board)
    
    # Get the dimensions
    rows, cols = np_board.shape
    
    # Check for immediate win
    for col in range(cols):
        if is_valid_move(np_board, col):
            # Try dropping a disc
            temp_board = np_board.copy()
            drop_disc(temp_board, col, 1)
            if check_winner(temp_board, 1):
                return col
    
    # Check for blocking opponent win
    for col in range(cols):
        if is_valid_move(np_board, col):
            # Try dropping opponent's disc
            temp_board = np_board.copy()
            drop_disc(temp_board, col, -1)
            if check_winner(temp_board, -1):
                return col
    
    # Evaluate and choose the best column
    best_score = -float('inf')
    best_cols = []
    
    for col in range(cols):
        if not is_valid_move(np_board, col):
            continue
            
        # Make a temporary move
        temp_board = np_board.copy()
        drop_disc(temp_board, col, 1)
        
        # Score this move
        score = evaluate_board(temp_board, 1)
        
        # Also consider opponent's response
        opponent_score = 0
        for op_col in range(cols):
            if not is_valid_move(temp_board, op_col):
                continue
            op_temp_board = temp_board.copy()
            drop_disc(op_temp_board, op_col, -1)
            opponent_score = max(opponent_score, evaluate_board(op_temp_board, -1))
        
        # Final score is our score minus opponent's best response
        total_score = score - opponent_score
        
        if total_score > best_score:
            best_score = total_score
            best_cols = [col]
        elif total_score == best_score:
            best_cols.append(col)
    
    # Prefer center columns
    center_cols = [cols//2 - 1, cols//2, cols//2 + 1]
    for col in best_cols:
        if col in center_cols:
            return col
    
    # If no center preference, return first best
    return best_cols[0] if best_cols else cols // 2

def is_valid_move(board, col):
    """Check if a move to the column is valid (not full)"""
    return board[0][col] == 0

def drop_disc(board, col, player):
    """Drop a disc in the specified column"""
    for row in range(len(board) - 1, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            break

def check_winner(board, player):
    """Check if the player has won"""
    rows, cols = len(board), len(board[0])
    
    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            if all(board[row][col + i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            if all(board[row + i][col] == player for i in range(4)):
                return True
    
    # Check diagonal (top-left to bottom-right)
    for row in range(rows - 3):
        for col in range(cols - 3):
            if all(board[row + i][col + i] == player for i in range(4)):
                return True
    
    # Check diagonal (top-right to bottom-left)
    for row in range(rows - 3):
        for col in range(3, cols):
            if all(board[row + i][col - i] == player for i in range(4)):
                return True
    
    return False

def evaluate_board(board, player):
    """Evaluate the board position for the player"""
    score = 0
    opponent = -player
    
    # Scoring weights
    weights = {
        1: 1,
        2: 10,
        3: 100,
        4: 1000
    }
    
    rows, cols = len(board), len(board[0])
    
    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            window = [board[row][col + i] for i in range(4)]
            score += evaluate_window(window, player, weights)
    
    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            window = [board[row + i][col] for i in range(4)]
            score += evaluate_window(window, player, weights)
    
    # Check diagonal (top-left to bottom-right)
    for row in range(rows - 3):
        for col in range(cols - 3):
            window = [board[row + i][col + i] for i in range(4)]
            score += evaluate_window(window, player, weights)
    
    # Check diagonal (top-right to bottom-left)
    for row in range(rows - 3):
        for col in range(3, cols):
            window = [board[row + i][col - i] for i in range(4)]
            score += evaluate_window(window, player, weights)
    
    return score

def evaluate_window(window, player, weights):
    """Evaluate a window of 4 positions"""
    score = 0
    opponent = -player
    
    # Count discs
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    # If player has 4 in a row, big score
    if player_count == 4:
        score += weights[4]
    # If player has 3 and one empty, good score
    elif player_count == 3 and empty_count == 1:
        score += weights[3]
    # If player has 2 and two empty, moderate score
    elif player_count == 2 and empty_count == 2:
        score += weights[2]
    # If opponent has 3 and one empty, block it
    elif opponent_count == 3 and empty_count == 1:
        score -= weights[3]
    # If opponent has 2 and two empty, bad score
    elif opponent_count == 2 and empty_count == 2:
        score -= weights[2]
        
    return score
