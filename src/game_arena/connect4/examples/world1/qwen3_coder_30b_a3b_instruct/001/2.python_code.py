
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    rows, cols = 6, 7
    
    def is_valid_move(col):
        return board_np[0][col] == 0
    
    def get_next_open_row(col):
        for row in range(rows-1, -1, -1):
            if board_np[row][col] == 0:
                return row
        return -1
    
    def check_win(player, row, col):
        # Check horizontal
        count = 0
        for c in range(max(0, col-3), min(cols, col+4)):
            if board_np[row][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        
        # Check vertical
        count = 0
        for r in range(max(0, row-3), min(rows, row+4)):
            if board_np[r][col] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        
        # Check diagonal (top-left to bottom-right)
        count = 0
        r, c = row, col
        while r >= 0 and c >= 0:
            r -= 1
            c -= 1
        r, c = r + 1, c + 1
        while r < rows and c < cols:
            if board_np[r][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
            r += 1
            c += 1
        
        # Check diagonal (top-right to bottom-left)
        count = 0
        r, c = row, col
        while r >= 0 and c < cols:
            r -= 1
            c += 1
        r, c = r + 1, c - 1
        while r < rows and c >= 0:
            if board_np[r][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
            r += 1
            c -= 1
        
        return False
    
    # Try to win immediately
    for col in range(cols):
        if is_valid_move(col):
            row = get_next_open_row(col)
            board_np[row][col] = 1  # Place my disc temporarily
            if check_win(1, row, col):
                # Reset board before returning
                board_np[row][col] = 0
                return col
            board_np[row][col] = 0  # Remove disc
    
    # Try to block opponent's win
    for col in range(cols):
        if is_valid_move(col):
            row = get_next_open_row(col)
            board_np[row][col] = -1  # Place opponent disc temporarily
            if check_win(-1, row, col):
                # Reset board and block here
                board_np[row][col] = 0
                return col
            board_np[row][col] = 0  # Remove disc
    
    # If no immediate win/block, evaluate board positions
    # Simple scoring function: prefer center columns, and evaluate potential lines
    def evaluate_position(col):
        if not is_valid_move(col):
            return -1  # Invalid move
        
        row = get_next_open_row(col)
        score = 0
        
        # Prefer middle columns (center is better in Connect 4)
        score += (3 - abs(3 - col)) * 2
        
        # Check all possible winning lines from this position
        # We'll evaluate 4-length lines that include this position
        
        # Check horizontal
        for c in range(max(0, col-3), min(cols-3, col+1)):
            line = [board_np[row][c+i] for i in range(4)]
            score += evaluate_line(line)
        
        # Check vertical (we only evaluate lines that go through this position)
        if row < rows - 3:
            line = [board_np[row+i][col] for i in range(4)]
            score += evaluate_line(line)
        
        # Check diagonal (top-left to bottom-right)
        c_start = max(0, col - 3)
        c_end = min(cols - 3, col + 1)
        for c in range(c_start, c_end):
            line = [board_np[row + (c - col) + i][c + i] for i in range(4)]
            score += evaluate_line(line)
        
        # Check diagonal (top-right to bottom-left)
        c_start = max(0, col - 3)
        c_end = min(cols - 3, col + 1)
        for c in range(c_start, c_end):
            line = [board_np[row - (c - col) + i][c + i] for i in range(4)]
            score += evaluate_line(line)
        
        return score
    
    def evaluate_line(line):
        # All positions in line must be the same or empty except one
        # 0 = empty, 1 = mine, -1 = opponent
        count_my = line.count(1)
        count_opponent = line.count(-1)
        count_empty = line.count(0)
        
        if count_my == 4:
            return 100  # Win
        if count_my == 3 and count_empty == 1:
            return 10  # 3 in a row, can win
        if count_my == 2 and count_empty == 2:
            return 2  # 2 in a row, potential
        if count_opponent == 3 and count_empty == 1:
            return 9  # Opponent has 3 in a row, must block
        return 0
    
    # Try optimal moves
    best_score = -1
    best_col = 3  # Default to center
    
    # Try all valid columns 
    for col in range(cols):
        if is_valid_move(col):
            score = evaluate_position(col)
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col
