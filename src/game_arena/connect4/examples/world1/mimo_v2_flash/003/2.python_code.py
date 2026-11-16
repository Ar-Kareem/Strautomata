
import numpy as np
import sys

# Increase recursion depth to support deeper searches if necessary
sys.setrecursionlimit(2000)

def policy(board: list[list[int]]) -> int:
    """
    Determines the best move for the current player using Minimax with Alpha-Beta pruning.
    """
    # Convert board to numpy array for easier manipulation
    b = np.array(board)
    
    # Define constants for players
    AI_PLAYER = 1
    OPPONENT = -1
    
    # Constants for board dimensions
    ROWS = 6
    COLS = 7
    
    # Order of columns to search: Center -> Sides (helps Alpha-Beta pruning)
    search_order = [3, 2, 4, 1, 5, 0, 6]

    # ---------------------------------------------------------
    # Helper Functions
    # ---------------------------------------------------------

    def get_valid_locations(brd):
        """Returns a list of columns that are not full."""
        valid = []
        for col in search_order:
            if brd[0][col] == 0:
                valid.append(col)
        return valid

    def score_position(brd, piece):
        """
        Heuristic evaluation of the board.
        Positive scores favor the AI, negative favor the opponent.
        """
        score = 0
        
        # 1. Center Column Preference
        center_array = [int(x) for x in list(brd[:, 3])]
        center_count = center_array.count(piece)
        score += center_count * 3

        # 2. Horizontal Evaluation
        for r in range(ROWS):
            row_array = [int(x) for x in list(brd[r, :])]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # 3. Vertical Evaluation
        for c in range(COLS):
            col_array = [int(x) for x in list(brd[:, c])]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # 4. Positive Slope Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [brd[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # 5. Negative Slope Diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [brd[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    def evaluate_window(window, piece):
        """Scores a window of 4 cells."""
        score = 0
        opp_piece = -piece
        
        count_piece = window.count(piece)
        count_empty = window.count(0)
        count_opp = window.count(opp_piece)

        if count_piece == 4:
            score += 100000  # Winning move
        elif count_piece == 3 and count_empty == 1:
            score += 5
        elif count_piece == 2 and count_empty == 2:
            score += 2

        if count_opp == 3 and count_empty == 1:
            score -= 4  # Block opponent
            
        return score

    def is_terminal_node(brd):
        """Check for winner or full board."""
        return winning_move(brd, AI_PLAYER) or winning_move(brd, OPPONENT) or len(get_valid_locations(brd)) == 0

    def winning_move(brd, piece):
        """Check if the given piece has a connect 4."""
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if brd[r][c] == piece and brd[r][c+1] == piece and brd[r][c+2] == piece and brd[r][c+3] == piece:
                    return True
        # Check vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if brd[r][c] == piece and brd[r+1][c] == piece and brd[r+2][c] == piece and brd[r+3][c] == piece:
                    return True
        # Check positively sloped diags
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if brd[r][c] == piece and brd[r+1][c+1] == piece and brd[r+2][c+2] == piece and brd[r+3][c+3] == piece:
                    return True
        # Check negatively sloped diags
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if brd[r][c] == piece and brd[r-1][c+1] == piece and brd[r-2][c+2] == piece and brd[r-3][c+3] == piece:
                    return True
        return False

    def drop_piece(brd, col, piece):
        """Returns a new board with the piece dropped in the specified column."""
        new_brd = brd.copy()
        for r in range(ROWS - 1, -1, -1):
            if new_brd[r][col] == 0:
                new_brd[r][col] = piece
                return new_brd
        return new_brd

    # ---------------------------------------------------------
    # Minimax Algorithm
    # ---------------------------------------------------------

    def minimax(brd, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(brd)
        is_terminal = is_terminal_node(brd)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(brd, AI_PLAYER):
                    return (None, 1000000000)
                elif winning_move(brd, OPPONENT):
                    return (None, -1000000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(brd, AI_PLAYER))

        if maximizingPlayer:
            value = -float('inf')
            column = valid_locations[0]
            for col in valid_locations:
                child_brd = drop_piece(brd, col, AI_PLAYER)
                new_score = minimax(child_brd, depth - 1, alpha, beta, False)[1]
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
            for col in valid_locations:
                child_brd = drop_piece(brd, col, OPPONENT)
                new_score = minimax(child_brd, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # ---------------------------------------------------------
    # Main Logic
    # ---------------------------------------------------------

    # 1. Check if we can win immediately
    for col in search_order:
        if b[0][col] == 0:
            temp_board = drop_piece(b, col, AI_PLAYER)
            if winning_move(temp_board, AI_PLAYER):
                return col

    # 2. Check if opponent can win next turn, and block them
    for col in search_order:
        if b[0][col] == 0:
            temp_board = drop_piece(b, col, OPPONENT)
            if winning_move(temp_board, OPPONENT):
                return col

    # 3. Use Minimax to find best move
    # Depth 5 is generally safe for 1 second on 3GHz CPU for Python, 
    # but depth 4 is safer for complex positions or slower environments.
    # We prioritize depth 5 but could fallback if needed (omitted here for brevity).
    best_move, _ = minimax(b, 5, -float('inf'), float('inf'), True)
    
    # Fallback if minimax returns None (should not happen if board isn't full)
    if best_move is None:
        valid = get_valid_locations(b)
        if valid:
            return valid[0]
            
    return best_move
