
import math

def policy(board):
    def is_valid_move(col, board_state):
        return board_state[0][col] == 0
    
    def get_next_open_row(col, board_state):
        for row in range(5, -1, -1):
            if board_state[row][col] == 0:
                return row
        return -1
    
    def drop_piece(row, col, board_state, piece):
        new_board = [row[:] for row in board_state]
        new_board[row][col] = piece
        return new_board
    
    def winning_move(board_state, piece):
        # Check horizontal locations
        for r in range(6):
            for c in range(4):
                if all(board_state[r][c+i] == piece for i in range(4)):
                    return True
        
        # Check vertical locations
        for r in range(3):
            for c in range(7):
                if all(board_state[r+i][c] == piece for i in range(4)):
                    return True
        
        # Check positively sloped diagonals
        for r in range(3):
            for c in range(4):
                if all(board_state[r+i][c+i] == piece for i in range(4)):
                    return True
        
        # Check negatively sloped diagonals
        for r in range(3, 6):
            for c in range(4):
                if all(board_state[r-i][c+i] == piece for i in range(4)):
                    return True
        
        return False
    
    def evaluate_window(window, piece):
        score = 0
        opp_piece = -1 if piece == 1 else 1
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
            
        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4
            
        return score
    
    def score_position(board_state, piece):
        score = 0
        
        # Score center column
        center_array = [board_state[i][3] for i in range(6)]
        center_count = center_array.count(piece)
        score += center_count * 3
        
        # Score Horizontal
        for r in range(6):
            row_array = board_state[r][:]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
        
        # Score Vertical
        for c in range(7):
            col_array = [board_state[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
        
        # Score positive diagonal
        for r in range(3):
            for c in range(4):
                window = [board_state[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        # Score negative diagonal
        for r in range(3, 6):
            for c in range(4):
                window = [board_state[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        return score
    
    def is_terminal_node(board_state):
        return (winning_move(board_state, 1) or 
                winning_move(board_state, -1) or 
                len([c for c in range(7) if is_valid_move(c, board_state)]) == 0)
    
    def minimax(board_state, depth, alpha, beta, maximizing_player):
        valid_locations = [c for c in range(7) if is_valid_move(c, board_state)]
        is_terminal = is_terminal_node(board_state)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(board_state, 1):  # We win
                    return (None, 10000000000000)
                elif winning_move(board_state, -1):  # Opponent wins
                    return (None, -10000000000000)
                else:  # Game over, no more moves
                    return (None, 0)
            else:  # Depth is zero
                return (None, score_position(board_state, 1))
        
        if maximizing_player:
            value = -math.inf
            column = valid_locations[0]
            for col in valid_locations:
                row = get_next_open_row(col, board_state)
                if row != -1:
                    b_copy = drop_piece(row, col, board_state, 1)
                    new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
                    if new_score > value:
                        value = new_score
                        column = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return column, value
        else:  # Minimizing player
            value = math.inf
            column = valid_locations[0]
            for col in valid_locations:
                row = get_next_open_row(col, board_state)
                if row != -1:
                    b_copy = drop_piece(row, col, board_state, -1)
                    new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
                    if new_score < value:
                        value = new_score
                        column = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            return column, value
    
    # Check for immediate winning move
    for col in range(7):
        if is_valid_move(col, board):
            row = get_next_open_row(col, board)
            temp_board = drop_piece(row, col, board, 1)
            if winning_move(temp_board, 1):
                return col
    
    # Check for opponent's winning move to block
    for col in range(7):
        if is_valid_move(col, board):
            row = get_next_open_row(col, board)
            temp_board = drop_piece(row, col, board, -1)
            if winning_move(temp_board, -1):
                return col
    
    # Use minimax with depth limit
    try:
        col, minimax_score = minimax(board, 5, -math.inf, math.inf, True)
        if col is not None and is_valid_move(col, board):
            return col
    except:
        pass
    
    # Fallback to center preference with validation
    preferred_cols = [3, 2, 4, 1, 5, 0, 6]
    for col in preferred_cols:
        if is_valid_move(col, board):
            return col
    
    # Last resort: first valid column
    for col in range(7):
        if is_valid_move(col, board):
            return col
    
    # Should never reach here, but included for safety
    return 0
