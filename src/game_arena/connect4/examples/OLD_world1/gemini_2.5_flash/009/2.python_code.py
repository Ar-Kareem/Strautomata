
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

    def get_valid_locations(board):
        valid_locations = []
        for col in range(COLS):
            if is_valid_location(board, col):
                valid_locations.append(col)
        return valid_locations

    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece

        if window.count(piece) == 4:
            score += 1000
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4 # Block opponent's winning move, rather than 4 points this makes it more important to prevent them

        return score

    def score_position(board, piece):
        score = 0
        
        # Prefer center column for initial moves
        center_column = COLS // 2
        for r in range(ROWS):
            if board[r][center_column] == piece:
                score += 3
        
        # Score Horizontal
        for r in range(ROWS):
            row_array = board[r]
            for c in range(COLS - 3):
                window = row_array[c:c + 4]
                score += evaluate_window(window, piece)

        # Score Vertical
        for c in range(COLS):
            col_array = [board[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r + 4]
                score += evaluate_window(window, piece)

        # Score Positive sloped diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Score Negative sloped diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)
        
        return score

    # Check for immediate win
    valid_moves = get_valid_locations(board)
    for col in valid_moves:
        temp_board = [row[:] for row in board]
        row = get_next_open_row(temp_board, col)
        drop_piece(temp_board, row, col, 1)
        if check_win(temp_board, 1):
            return col

    # Check for immediate opponent win and block
    for col in valid_moves:
        temp_board = [row[:] for row in board]
        row = get_next_open_row(temp_board, col)
        drop_piece(temp_board, row, col, -1)
        if check_win(temp_board, -1):
            return col
            
    # Try to set up a double threat (look ahead one more move)
    # This is a simplified version, it checks if placing a piece now leads to a winning position
    # but not if it defends against an obvious imminent threat
    best_col = random.choice(valid_moves) if valid_moves else -1
    best_score = -1000000

    for col in valid_moves:
        temp_board = [row[:] for row in board]
        row = get_next_open_row(temp_board, col)
        drop_piece(temp_board, row, col, 1)
        
        score = score_position(temp_board, 1)

        # Consider opponent's response for a more robust check in the future
        # For now, just score our position after placing a piece
        
        if score > best_score:
            best_score = score
            best_col = col

    return best_col
