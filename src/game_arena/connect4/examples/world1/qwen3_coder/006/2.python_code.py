
import random
from typing import List

def policy(board: List[List[int]]) -> int:
    # Constants
    ROWS, COLS = 6, 7
    PLAYER = 1
    OPPONENT = -1
    
    def is_valid_location(col):
        return board[0][col] == 0
    
    def get_next_open_row(col):
        for r in range(ROWS-1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1
    
    def drop_piece(temp_board, row, col, piece):
        temp_board[row][col] = piece
    
    def is_terminal_node(temp_board):
        return check_win(temp_board, PLAYER) or check_win(temp_board, OPPONENT) or len(get_valid_locations(temp_board)) == 0
    
    def check_win(temp_board, piece):
        # Check horizontal locations
        for r in range(ROWS):
            for c in range(COLS-3):
                if temp_board[r][c] == piece and temp_board[r][c+1] == piece and temp_board[r][c+2] == piece and temp_board[r][c+3] == piece:
                    return True

        # Check vertical locations
        for r in range(ROWS-3):
            for c in range(COLS):
                if temp_board[r][c] == piece and temp_board[r+1][c] == piece and temp_board[r+2][c] == piece and temp_board[r+3][c] == piece:
                    return True

        # Check positively sloped diagonals
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if temp_board[r][c] == piece and temp_board[r+1][c+1] == piece and temp_board[r+2][c+2] == piece and temp_board[r+3][c+3] == piece:
                    return True

        # Check negatively sloped diagonals
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if temp_board[r][c] == piece and temp_board[r-1][c+1] == piece and temp_board[r-2][c+2] == piece and temp_board[r-3][c+3] == piece:
                    return True
        return False
    
    def evaluate_window(window, piece):
        score = 0
        opp_piece = OPPONENT if piece == PLAYER else PLAYER
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
            
        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4
            
        return score
    
    def score_position(temp_board, piece):
        score = 0
        
        # Score center column
        center_array = [temp_board[r][COLS//2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3
        
        # Score Horizontal
        for r in range(ROWS):
            row_array = temp_board[r]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
                
        # Score Vertical
        for c in range(COLS):
            col_array = [temp_board[r][c] for r in range(ROWS)]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
                
        # Score positive diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [temp_board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        # Score negative diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [temp_board[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        return score
    
    def get_valid_locations(temp_board):
        return [col for col in range(COLS) if is_valid_location(col)]
    
    def minimax(temp_board, depth, alpha, beta, maximizing_player):
        valid_locations = get_valid_locations(temp_board)
        is_terminal = is_terminal_node(temp_board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(temp_board, PLAYER):
                    return (None, 10000000000000)
                elif check_win(temp_board, OPPONENT):
                    return (None, -10000000000000)
                else:  # Game is over, no more valid moves
                    return (None, 0)
            else:  # Depth is zero
                return (None, score_position(temp_board, PLAYER))
        
        if maximizing_player:
            value = float('-inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(col)
                if row != -1:
                    b_copy = [row[:] for row in temp_board]
                    drop_piece(b_copy, row, col, PLAYER)
                    new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
                    if new_score > value:
                        value = new_score
                        column = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return column, value
        else:  # Minimizing player
            value = float('inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(col)
                if row != -1:
                    b_copy = [row[:] for row in temp_board]
                    drop_piece(b_copy, row, col, OPPONENT)
                    new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
                    if new_score < value:
                        value = new_score
                        column = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            return column, value
    
    # Check for immediate winning move
    valid_locations = get_valid_locations(board)
    for col in valid_locations:
        row = get_next_open_row(col)
        if row != -1:
            b_copy = [row[:] for row in board]
            drop_piece(b_copy, row, col, PLAYER)
            if check_win(b_copy, PLAYER):
                return col
    
    # Check for opponent winning move and block
    for col in valid_locations:
        row = get_next_open_row(col)
        if row != -1:
            b_copy = [row[:] for row in board]
            drop_piece(b_copy, row, col, OPPONENT)
            if check_win(b_copy, OPPONENT):
                return col
    
    # If no immediate threats, use minimax
    try:
        col, minimax_score = minimax(board, 5, float('-inf'), float('inf'), True)
        if col is not None and is_valid_location(col):
            return col
    except:
        pass
    
    # Fallback to center or random valid column
    if is_valid_location(COLS//2):
        return COLS//2
    
    return random.choice(valid_locations)
