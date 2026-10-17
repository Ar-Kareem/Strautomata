
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 Policy: Uses Minimax with Alpha-Beta pruning.
    Board: 6x7 (rows x cols). 1 is self, -1 is opponent, 0 is empty.
    """
    
    ROWS = 6
    COLS = 7
    
    def get_valid_columns(state):
        return [c for c in range(COLS) if state[0][c] == 0]

    def get_next_open_row(state, col):
        for r in range(ROWS-1, -1, -1):
            if state[r][col] == 0:
                return r
        return -1

    def check_win(state, piece):
        # Horizontal
        for c in range(COLS - 3):
            for r in range(ROWS):
                if state[r][c] == piece and state[r][c+1] == piece and state[r][c+2] == piece and state[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if state[r][c] == piece and state[r+1][c] == piece and state[r+2][c] == piece and state[r+3][c] == piece:
                    return True
        # Positive Diagonal
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if state[r][c] == piece and state[r-1][c+1] == piece and state[r-2][c+2] == piece and state[r-3][c+3] == piece:
                    return True
        # Negative Diagonal
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if state[r][c] == piece and state[r+1][c+1] == piece and state[r+2][c+2] == piece and state[r+3][c+3] == piece:
                    return True
        return False

    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        if window.count(piece) == 4:
            score += 1000
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 10
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 80  # Prioritize blocking opponent
        return score

    def score_position(state, piece):
        score = 0
        # Center column preference
        center_array = [state[r][COLS//2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Horizontal
        for r in range(ROWS):
            row_array = state[r]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
        # Vertical
        for c in range(COLS):
            col_array = [state[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
        # Diagonals
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [state[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [state[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        return score

    def minimax(state, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_columns(state)
        is_terminal = check_win(state, 1) or check_win(state, -1) or len(valid_locations) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(state, 1):
                    return (None, 10000000)
                elif check_win(state, -1):
                    return (None, -10000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(state, 1))

        if maximizingPlayer:
            value = -float('inf')
            column = valid_locations[0]
            # Order moves: center first
            valid_locations.sort(key=lambda x: abs(x - 3))
            for col in valid_locations:
                row = get_next_open_row(state, col)
                state_copy = [r[:] for r in state]
                state_copy[row][col] = 1
                new_score = minimax(state_copy, depth - 1, alpha, beta, False)[1]
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
                row = get_next_open_row(state, col)
                state_copy = [r[:] for r in state]
                state_copy[row][col] = -1
                new_score = minimax(state_copy, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Quick check for immediate threat or win
    valid_cols = get_valid_columns(board)
    for c in valid_cols:
        r = get_next_open_row(board, c)
        # Can I win?
        temp_board = [row[:] for row in board]
        temp_board[r][c] = 1
        if check_win(temp_board, 1):
            return c
            
    for c in valid_cols:
        r = get_next_open_row(board, c)
        # Can he win?
        temp_board = [row[:] for row in board]
        temp_board[r][c] = -1
        if check_win(temp_board, -1):
            return c

    # Fallback to minimax
    col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    return col if col is not None else valid_cols[0]
