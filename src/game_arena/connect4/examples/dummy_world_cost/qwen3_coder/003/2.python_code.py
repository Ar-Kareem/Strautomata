
import numpy as np
import random

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    np_board = np.array(board)
    
    def is_valid_move(col):
        return np_board[0][col] == 0
    
    def get_next_open_row(col):
        for r in range(5, -1, -1):
            if np_board[r][col] == 0:
                return r
        return -1
    
    def drop_piece(temp_board, row, col, piece):
        temp_board[row][col] = piece
    
    def check_winner(temp_board, piece):
        # Check horizontal locations
        for c in range(4):
            for r in range(6):
                if (temp_board[r][c] == piece and 
                    temp_board[r][c+1] == piece and 
                    temp_board[r][c+2] == piece and 
                    temp_board[r][c+3] == piece):
                    return True

        # Check vertical locations
        for c in range(7):
            for r in range(3):
                if (temp_board[r][c] == piece and 
                    temp_board[r+1][c] == piece and 
                    temp_board[r+2][c] == piece and 
                    temp_board[r+3][c] == piece):
                    return True

        # Check positively sloped diagonals
        for c in range(4):
            for r in range(3):
                if (temp_board[r][c] == piece and 
                    temp_board[r+1][c+1] == piece and 
                    temp_board[r+2][c+2] == piece and 
                    temp_board[r+3][c+3] == piece):
                    return True

        # Check negatively sloped diagonals
        for c in range(4):
            for r in range(3, 6):
                if (temp_board[r][c] == piece and 
                    temp_board[r-1][c+1] == piece and 
                    temp_board[r-2][c+2] == piece and 
                    temp_board[r-3][c+3] == piece):
                    return True
        return False
    
    def count_sequence(temp_board, piece, length):
        count = 0
        
        # Horizontal
        for r in range(6):
            for c in range(7 - length + 1):
                empty_count = 0
                piece_count = 0
                for i in range(length):
                    if temp_board[r][c+i] == piece:
                        piece_count += 1
                    elif temp_board[r][c+i] == 0:
                        empty_count += 1
                if piece_count == length-1 and empty_count == 1:
                    count += 1
                    
        # Vertical
        for r in range(6 - length + 1):
            for c in range(7):
                empty_count = 0
                piece_count = 0
                for i in range(length):
                    if temp_board[r+i][c] == piece:
                        piece_count += 1
                    elif temp_board[r+i][c] == 0:
                        empty_count += 1
                if piece_count == length-1 and empty_count == 1:
                    count += 1
                    
        # Diagonal up
        for r in range(3, 6):
            for c in range(4):
                empty_count = 0
                piece_count = 0
                for i in range(length):
                    if temp_board[r-i][c+i] == piece:
                        piece_count += 1
                    elif temp_board[r-i][c+i] == 0:
                        empty_count += 1
                if piece_count == length-1 and empty_count == 1:
                    count += 1
                    
        # Diagonal down
        for r in range(3):
            for c in range(4):
                empty_count = 0
                piece_count = 0
                for i in range(length):
                    if temp_board[r+i][c+i] == piece:
                        piece_count += 1
                    elif temp_board[r+i][c+i] == 0:
                        empty_count += 1
                if piece_count == length-1 and empty_count == 1:
                    count += 1
                    
        return count
    
    def evaluate_board(temp_board):
        score = 0
        
        # Prefer center column
        center_array = [int(i) for i in list(temp_board[:, 3])]
        center_count = center_array.count(1)
        score += center_count * 3
        
        # Score horizontal positions
        for r in range(6):
            row_array = [int(i) for i in list(temp_board[r,:])]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window)
                
        # Score vertical positions
        for c in range(7):
            col_array = [int(i) for i in list(temp_board[:,c])]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window)
        
        # Score positive diagonal positions
        for r in range(3):
            for c in range(4):
                window = [temp_board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window)
                
        # Score negative diagonal positions
        for r in range(3):
            for c in range(4):
                window = [temp_board[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window)
                
        return score
    
    def evaluate_window(window):
        score = 0
        if window.count(1) == 4:
            score += 100
        elif window.count(1) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(1) == 2 and window.count(0) == 2:
            score += 2
            
        if window.count(-1) == 3 and window.count(0) == 1:
            score -= 80
            
        return score
    
    def minimax(temp_board, depth, alpha, beta, maximizing_player):
        valid_locations = [c for c in range(7) if is_valid_move(c)]
        
        # Terminal conditions
        if depth == 0 or len(valid_locations) == 0 or check_winner(temp_board, 1) or check_winner(temp_board, -1):
            if check_winner(temp_board, 1):
                return (None, 100000000000000)
            elif check_winner(temp_board, -1):
                return (None, -10000000000000)
            elif len(valid_locations) == 0:  # Game over, no more valid moves
                return (None, 0)
            else:  # Depth is zero
                return (None, evaluate_board(temp_board))
        
        if maximizing_player:
            value = -np.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(col)
                if row != -1:
                    temp_board_copy = temp_board.copy()
                    drop_piece(temp_board_copy, row, col, 1)
                    new_score = minimax(temp_board_copy, depth-1, alpha, beta, False)[1]
                    if new_score > value:
                        value = new_score
                        column = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return column, value
            
        else:  # Minimizing player
            value = np.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(col)
                if row != -1:
                    temp_board_copy = temp_board.copy()
                    drop_piece(temp_board_copy, row, col, -1)
                    new_score = minimax(temp_board_copy, depth-1, alpha, beta, True)[1]
                    if new_score < value:
                        value = new_score
                        column = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            return column, value
    
    # First check if there's a winning move
    valid_moves = [c for c in range(7) if is_valid_move(c)]
    
    # Check for immediate win
    for col in valid_moves:
        row = get_next_open_row(col)
        if row != -1:
            temp_board = np_board.copy()
            drop_piece(temp_board, row, col, 1)
            if check_winner(temp_board, 1):
                return col
    
    # Check for blocking opponent's win
    for col in valid_moves:
        row = get_next_open_row(col)
        if row != -1:
            temp_board = np_board.copy()
            drop_piece(temp_board, row, col, -1)
            if check_winner(temp_board, -1):
                return col
    
    # Use minimax to determine best move
    try:
        col, minimax_score = minimax(np_board, 5, -np.inf, np.inf, True)
        if col is not None and is_valid_move(col):
            return col
    except:
        pass
    
    # Fallback to random valid move
    return random.choice(valid_moves)
