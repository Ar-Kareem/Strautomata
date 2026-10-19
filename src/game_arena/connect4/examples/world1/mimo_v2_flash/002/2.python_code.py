
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI using Minimax with Alpha-Beta Pruning.
    """
    import sys

    # Set recursion limit higher just in case, though we limit depth manually
    sys.setrecursionlimit(2000)

    ROWS = 6
    COLS = 7
    PLAYER = 1  # AI
    OPPONENT = -1
    MAX_DEPTH = 6  # Depth for iterative search

    # ------------------- Helper Functions -------------------

    def get_valid_locations(b):
        """Returns a list of column indices that are not full."""
        valid = []
        for col in range(COLS):
            if b[0][col] == 0:
                valid.append(col)
        return valid

    def is_terminal_node(b):
        """Checks if the game is over (win or draw)."""
        return check_win(b, PLAYER) or check_win(b, OPPONENT) or len(get_valid_locations(b)) == 0

    def check_win(b, piece):
        """Check if the given piece has won."""
        # Check horizontal locations
        for r in range(ROWS):
            for c in range(COLS - 3):
                if b[r][c] == piece and b[r][c+1] == piece and b[r][c+2] == piece and b[r][c+3] == piece:
                    return True

        # Check vertical locations
        for r in range(ROWS - 3):
            for c in range(COLS):
                if b[r][c] == piece and b[r+1][c] == piece and b[r+2][c] == piece and b[r+3][c] == piece:
                    return True

        # Check positively sloped diagonals
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r][c] == piece and b[r+1][c+1] == piece and b[r+2][c+2] == piece and b[r+3][c+3] == piece:
                    return True

        # Check negatively sloped diagonals
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if b[r][c] == piece and b[r-1][c+1] == piece and b[r-2][c+2] == piece and b[r-3][c+3] == piece:
                    return True
        return False

    def evaluate_window(window, piece):
        """
        Heuristic function to score a window of 4 cells.
        Returns a score based on the number of pieces and empty slots.
        """
        score = 0
        opp_piece = PLAYER if piece == OPPONENT else OPPONENT
        
        count_piece = window.count(piece)
        count_empty = window.count(0)
        count_opp = window.count(opp_piece)

        if count_piece == 4:
            score += 100000  # Should be caught by check_win, but for safety
        elif count_piece == 3 and count_empty == 1:
            score += 100
        elif count_piece == 2 and count_empty == 2:
            score += 10
        
        if count_opp == 3 and count_empty == 1:
            score -= 80 # Urgent block (though search handles explicit blocks, this helps with forks)
            
        return score

    def score_position(b, piece):
        """Calculate the heuristic score of the board for the given piece."""
        score = 0

        # Preference for center column
        center_array = [b[r][3] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [b[r][c], b[r][c+1], b[r][c+2], b[r][c+3]]
                score += evaluate_window(window, piece)

        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                window = [b[r][c], b[r+1][c], b[r+2][c], b[r+3][c]]
                score += evaluate_window(window, piece)

        # Positive Sloped Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [b[r][c], b[r+1][c+1], b[r+2][c+2], b[r+3][c+3]]
                score += evaluate_window(window, piece)

        # Negative Sloped Diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [b[r][c], b[r-1][c+1], b[r-2][c+2], b[r-3][c+3]]
                score += evaluate_window(window, piece)

        return score

    def drop_piece(b, col, piece):
        """
        Returns a new board state with the piece dropped in the specified column.
        Assumes the move is valid.
        """
        new_board = [row[:] for row in b] # Deep copy
        for r in range(ROWS - 1, -1, -1):
            if new_board[r][col] == 0:
                new_board[r][col] = piece
                return new_board
        return new_board # Should not happen if valid

    # ------------------- Minimax Algorithm -------------------

    def minimax(b, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(b)
        is_terminal = is_terminal_node(b)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(b, PLAYER):
                    return (None, 100000000000000)
                elif check_win(b, OPPONENT):
                    return (None, -100000000000000)
                else: # Draw
                    return (None, 0)
            else: # Depth is zero
                return (None, score_position(b, PLAYER))

        if maximizingPlayer:
            value = -float('inf')
            column = valid_locations[0]
            
            # Move ordering: Center columns first for better pruning
            valid_locations.sort(key=lambda x: abs(x - 3))
            
            for col in valid_locations:
                new_board = drop_piece(b, col, PLAYER)
                new_score = minimax(new_board, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = valid_locations[0]
            
            valid_locations.sort(key=lambda x: abs(x - 3))
            
            for col in valid_locations:
                new_board = drop_piece(b, col, OPPONENT)
                new_score = minimax(new_board, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # ------------------- Main Execution -------------------

    # 1. Immediate Win
    valid_moves = get_valid_locations(board)
    for col in valid_moves:
        temp_board = drop_piece(board, col, PLAYER)
        if check_win(temp_board, PLAYER):
            return col

    # 2. Immediate Block
    for col in valid_moves:
        temp_board = drop_piece(board, col, OPPONENT)
        if check_win(temp_board, OPPONENT):
            return col

    # 3. Minimax Search
    best_col, best_score = minimax(board, MAX_DEPTH, -float('inf'), float('inf'), True)
    
    # Fallback if minimax fails (shouldn't happen if valid moves exist)
    if best_col is None and valid_moves:
        return valid_moves[0] # Pick first valid move
        
    return best_col
