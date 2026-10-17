
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
        return -1

    def drop_piece(temp_board, row, col, piece):
        temp_board[row][col] = piece

    def check_win(temp_board, piece):
        # Check horizontal locations for win
        for c in range(COLS - 3):
            for r in range(ROWS):
                if all(temp_board[r][c + i] == piece for i in range(4)):
                    return True

        # Check vertical locations for win
        for c in range(COLS):
            for r in range(ROWS - 3):
                if all(temp_board[r + i][c] == piece for i in range(4)):
                    return True

        # Check positively sloped diagonals
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if all(temp_board[r + i][c + i] == piece for i in range(4)):
                    return True

        # Check negatively sloped diagonals
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if all(temp_board[r - i][c + i] == piece for i in range(4)):
                    return True
        return False

    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece

        if window.count(piece) == 4:
            score += 1000000 # Winning move
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 10
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 500 # Block opponent's winning move
        elif window.count(opp_piece) == 2 and window.count(0) == 2:
            score -= 2 # Prevent opponent from getting 3 in a row easily

        return score

    def score_position(temp_board, piece):
        score = 0
        
        # Center column preference
        center_array = [int(temp_board[r][COLS // 2]) for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Horizontal
        for r in range(ROWS):
            row_array = [int(temp_board[r][c]) for c in range(COLS)]
            for c in range(COLS - 3):
                window = row_array[c:c + 4]
                score += evaluate_window(window, piece)

        # Vertical
        for c in range(COLS):
            col_array = [int(temp_board[r][c]) for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r + 4]
                score += evaluate_window(window, piece)

        # Positive sloped diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [temp_board[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Negative sloped diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [temp_board[r - i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    # Check for immediate win
    valid_cols = [c for c in range(COLS) if is_valid_location(board, c)]
    for col in valid_cols:
        row = get_next_open_row(board, col)
        temp_board = [row[:] for row in board]  # Create a deep copy
        drop_piece(temp_board, row, col, 1)
        if check_win(temp_board, 1):
            return col

    # Check for immediate opponent win and block
    for col in valid_cols:
        row = get_next_open_row(board, col)
        temp_board = [row[:] for row in board]  # Create a deep copy
        drop_piece(temp_board, row, col, -1)
        if check_win(temp_board, -1):
            return col

    # If no immediate win or block, evaluate positions
    best_score = -float('inf')
    best_col = random.choice(valid_cols) # Fallback to a random valid column

    for col in valid_cols:
        row = get_next_open_row(board, col)
        temp_board = [row[:] for row in board]
        drop_piece(temp_board, row, col, 1)
        score = score_position(temp_board, 1)
        if score > best_score:
            best_score = score
            best_col = col

    return best_col
