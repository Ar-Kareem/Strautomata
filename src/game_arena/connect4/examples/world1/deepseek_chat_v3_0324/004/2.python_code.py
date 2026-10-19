
import numpy as np

def policy(board: list[list[int]]) -> int:
    board = np.array(board)
    current_player = 1
    
    # Check for immediate winning move
    for col in range(7):
        if is_valid_move(board, col):
            temp_board = make_move(board, col, current_player)
            if check_win(temp_board, current_player):
                return col
    
    # Check if opponent can win next move and block them
    opponent = -1
    for col in range(7):
        if is_valid_move(board, col):
            temp_board = make_move(board, col, opponent)
            if check_win(temp_board, opponent):
                return col
    
    # Evaluate columns based on strategic value
    scores = evaluate_columns(board, current_player)
    
    # Choose the column with highest score
    valid_cols = [col for col in range(7) if is_valid_move(board, col)]
    best_col = max(valid_cols, key=lambda col: scores[col])
    return best_col

def is_valid_move(board, col):
    return 0 in board[:, col]

def make_move(board, col, player):
    temp_board = board.copy()
    row = np.where(temp_board[:, col] == 0)[0][-1]
    temp_board[row, col] = player
    return temp_board

def check_win(board, player):
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row, col+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if all(board[row+i, col] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            if all(board[row+i, col+i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            if all(board[row-i, col+i] == player for i in range(4)):
                return True
    
    return False

def evaluate_columns(board, player):
    scores = [0] * 7
    opponent = -1 if player == 1 else 1
    
    # Center preference
    center_cols = [3, 2, 4, 1, 5, 0, 6]
    for i, col in enumerate(center_cols):
        if is_valid_move(board, col):
            scores[col] += 7 - i
    
    # Evaluate potential to create threats
    for col in range(7):
        if not is_valid_move(board, col):
            scores[col] = -1
            continue
        
        temp_board = make_move(board, col, player)
        # Count potential winning lines
        scores[col] += count_potential_wins(temp_board, player)
        
        # Consider opponent's response
        temp_board_opp = make_move(temp_board, col, opponent)
        scores[col] -= count_potential_wins(temp_board_opp, opponent) * 0.5
    
    return scores

def count_potential_wins(board, player):
    count = 0
    # Check all possible lines of 4
    for row in range(6):
        for col in range(7):
            # Check horizontal right
            if col <= 3:
                line = board[row, col:col+4]
                if sum(line == player) == 3 and sum(line == 0) == 1:
                    count += 1
            
            # Check vertical down
            if row <= 2:
                line = board[row:row+4, col]
                if sum(line == player) == 3 and sum(line == 0) == 1:
                    count += 1
            
            # Check diagonal down-right
            if row <= 2 and col <= 3:
                line = [board[row+i, col+i] for i in range(4)]
                if sum(line == player) == 3 and sum(line == 0) == 1:
                    count += 1
            
            # Check diagonal up-right
            if row >= 3 and col <= 3:
                line = [board[row-i, col+i] for i in range(4)]
                if sum(line == player) == 3 and sum(line == 0) == 1:
                    count += 1
    
    return count
