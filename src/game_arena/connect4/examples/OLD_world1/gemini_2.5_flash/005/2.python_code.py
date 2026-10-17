
import random

def policy(board: list[list[int]]) -> int:
    rows = len(board)
    cols = len(board[0])

    def is_valid_location(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in range(rows - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1 # Should not happen if is_valid_location is true

    def check_win(board, player_piece):
        # Check horizontal locations for win
        for c in range(cols - 3):
            for r in range(rows):
                if board[r][c] == player_piece and board[r][c+1] == player_piece and board[r][c+2] == player_piece and board[r][c+3] == player_piece:
                    return True

        # Check vertical locations for win
        for c in range(cols):
            for r in range(rows - 3):
                if board[r][c] == player_piece and board[r+1][c] == player_piece and board[r+2][c] == player_piece and board[r+3][c] == player_piece:
                    return True

        # Check positively sloped diagonals
        for c in range(cols - 3):
            for r in range(rows - 3):
                if board[r][c] == player_piece and board[r+1][c+1] == player_piece and board[r+2][c+2] == player_piece and board[r+3][c+3] == player_piece:
                    return True

        # Check negatively sloped diagonals
        for c in range(cols - 3):
            for r in range(3, rows):
                if board[r][c] == player_piece and board[r-1][c+1] == player_piece and board[r-2][c+2] == player_piece and board[r-3][c+3] == player_piece:
                    return True
        return False

    def evaluate_window(window, player_piece):
        score = 0
        opponent_piece = -player_piece

        if window.count(player_piece) == 4:
            score += 100000
        elif window.count(player_piece) == 3 and window.count(0) == 1:
            score += 50
        elif window.count(player_piece) == 2 and window.count(0) == 2:
            score += 10

        if window.count(opponent_piece) == 3 and window.count(0) == 1:
            score -= 60
        elif window.count(opponent_piece) == 4:
            score -= 100000

        return score

    def score_position(board, player_piece):
        score = 0

        # Score center column
        center_array = [board[r][cols // 2] for r in range(rows)]
        center_count = center_array.count(player_piece)
        score += center_count * 5

        # Score Horizontal
        for r in range(rows):
            row_array = [board[r][c] for c in range(cols)]
            for c in range(cols - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, player_piece)

        # Score Vertical
        for c in range(cols):
            col_array = [board[r][c] for r in range(rows)]
            for r in range(rows - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, player_piece)

        # Score positive sloped diagonal
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, player_piece)

        # Score negative sloped diagonal
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, player_piece)

        return score

    # 1. Check for immediate win
    for col in range(cols):
        if is_valid_location(board, col):
            temp_board = [row[:] for row in board]
            row = get_next_open_row(temp_board, col)
            temp_board[row][col] = 1
            if check_win(temp_board, 1):
                return col

    # 2. Block opponent's immediate win
    for col in range(cols):
        if is_valid_location(board, col):
            temp_board = [row[:] for row in board]
            row = get_next_open_row(temp_board, col)
            temp_board[row][col] = -1
            if check_win(temp_board, -1):
                return col

    # 3. Choose the column that maximizes our score (simple heuristic)
    valid_locations = [col for col in range(cols) if is_valid_location(board, col)]
    best_score = -float('inf')
    best_cols = []

    for col in valid_locations:
        temp_board = [row[:] for row in board]
        row = get_next_open_row(temp_board, col)
        temp_board[row][col] = 1
        score = score_position(temp_board, 1)

        # Look for opponent's response and minimize their score
        opponent_can_win = False
        for op_col in range(cols):
            if is_valid_location(temp_board, op_col):
                temp_board_op = [row[:] for row in temp_board]
                op_row = get_next_open_row(temp_board_op, op_col)
                temp_board_op[op_row][op_col] = -1
                if check_win(temp_board_op, -1):
                    opponent_can_win = True
                    break
        
        if opponent_can_win:
            score -= 10000  # Heavily penalize moves that lead to opponent winning next turn


        if score > best_score:
            best_score = score
            best_cols = [col]
        elif score == best_score:
            best_cols.append(col)

    if best_cols:
        return random.choice(best_cols)

    # Fallback: choose a random valid column if no strategic move is found (should not happen with scoring)
    valid_cols = [col for col in range(cols) if is_valid_location(board, col)]
    if valid_cols:
        return random.choice(valid_cols)
    else:
        # This case implies the board is full, which should not happen in a valid game state for policy call
        # As a safeguard, return -1 (invalid) or raise an error
        return -1 # Should never be reached in a normal game.
