
import random

def policy(board: list[list[int]]) -> int:
    ROWS = len(board)
    COLS = len(board[0])

    def is_valid_location(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in range(ROWS - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1 # Should not happen if is_valid_location is checked

    def drop_piece(board, row, col, piece):
        board[row][col] = piece

    def check_win(board, piece):
        # Check horizontal locations for win
        for c in range(COLS - 3):
            for r in range(ROWS):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True

        # Check vertical locations for win
        for c in range(COLS):
            for r in range(ROWS - 3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True

        # Check positively sloped diagonals
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True

        # Check negatively sloped diagonals
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False

    def get_valid_locations(board):
        valid_locations = []
        for col in range(COLS):
            if is_valid_location(board, col):
                valid_locations.append(col)
        return valid_locations

    def evaluate_window(window, piece):
        score = 0
        opponent_piece = 1 if piece == -1 else -1

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        
        if window.count(opponent_piece) == 3 and window.count(0) == 1:
            score -= 4 # Block opponent's three in a row
        if window.count(opponent_piece) == 2 and window.count(0) == 2:
            score -= 1
        
        # Prioritize center column
        if window.count(piece) > 0 and window.count(0) > 0 and window.count(opponent_piece) == 0 :
             score += 1 # Small bonus for keeping a line open

        return score
    
    def score_position(board, piece):
        score = 0
        COL_CENTER = COLS // 2

        # Score center column preference
        center_array = [board[r][COL_CENTER] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Score horizontal
        for r in range(ROWS):
            row_array = [board[r][c] for c in range(COLS)]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Score vertical
        for c in range(COLS):
            col_array = [board[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Score positive sloped diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Score negative sloped diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        return score

    def minimax(board, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(board)
        is_terminal = check_win(board, 1) or check_win(board, -1) or len(valid_locations) == 0

        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(board, 1):
                    return (None, 100000000000000)
                elif check_win(board, -1):
                    return (None, -10000000000000)
                else: # Game is over, no more valid moves
                    return (None, 0)
            else: # Depth is zero
                return (None, score_position(board, 1))

        if maximizingPlayer:
            value = -float('inf')
            column = random.choice(valid_locations) # Default to a random move
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = [row[:] for row in board]
                drop_piece(b_copy, row, col, 1)
                new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else: # Minimizing player
            value = float('inf')
            column = random.choice(valid_locations) # Default to a random move
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = [row[:] for row in board]
                drop_piece(b_copy, row, col, -1)
                new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Choose a depth for the minimax algorithm.
    # A depth of 4-5 is usually a good balance for Connect 4 given time limits.
    # Can be adjusted based on performance requirements.
    # For a 1-second limit, depth 4 is probably safe. Depth 5 might be pushing it.
    DEPTH = 4 
    
    # Check for immediate win
    valid_cols = get_valid_locations(board)
    for col in valid_cols:
        temp_board = [row[:] for row in board]
        row = get_next_open_row(temp_board, col)
        drop_piece(temp_board, row, col, 1)
        if check_win(temp_board, 1):
            return col
    
    # Check for immediate block
    for col in valid_cols:
        temp_board = [row[:] for row in board]
        row = get_next_open_row(temp_board, col)
        drop_piece(temp_board, row, col, -1)
        if check_win(temp_board, -1):
            return col

    # If no immediate win or block, use minimax
    # The default starting column from minimax_search_column is often not used, as 
    # it gets overwritten in the loop. It is provided as a fallback/initialization.
    col, minimax_score = minimax(board, DEPTH, -float('inf'), float('inf'), True)
    
    # Ensure the returned column is valid
    if col is not None and is_valid_location(board, col):
        return col
    else:
        # Fallback to a random valid column if minimax somehow fails or returns an invalid one
        return random.choice(valid_cols)

