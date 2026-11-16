
def policy(board: list[list[int]]) -> int:
    def get_next_open_row(col):
        for r in reversed(range(6)):
            if board[r][col] == 0:
                return r
        return -1

    def is_winning_move(current_board, player):
        # Check horizontal
        for row in current_board:
            for c in range(4):
                window = row[c:c+4]
                if window.count(player) == 4:
                    return True
        # Check vertical
        for col in range(7):
            col_data = [current_board[r][col] for r in range(6)]
            for i in range(3):
                window = col_data[i:i+4]
                if window.count(player) == 4:
                    return True
        # Check positive diagonal (going down-right)
        for r in range(3):
            for c in range(4):
                window = [current_board[r + i][c + i] for i in range(4)]
                if window.count(player) == 4:
                    return True
        # Check negative diagonal (going up-right)
        for r in range(3, 6):
            for c in range(4):
                window = [current_board[r - i][c + i] for i in range(4)]
                if window.count(player) == 4:
                    return True
        return False

    # Step 1: Check if any move leads to a win
    for col in range(7):
        row = get_next_open_row(col)
        if row >= 0:
            new_board = [row[:] for row in board]  # Copy the board
            new_board[row][col] = 1
            if is_winning_move(new_board, 1):
                return col

    # Step 2: Block opponent's winning move
    for col in range(7):
        row = get_next_open_row(col)
        if row >= 0:
            new_board = [row[:] for row in board]
            new_board[row][col] = -1
            if is_winning_move(new_board, -1):
                return col

    # Step 3: Evaluate best move using heuristic
    def score_position(current_board, player):
        score = 0
        # Center control
        center_array = [current_board[r][3] for r in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3

        # Horizontal
        for row in current_board:
            for c in range(4):
                window = row[c:c+4]
                score += evaluate_window(window, player)

        # Vertical
        for col in range(7):
            col_data = [current_board[r][col] for r in range(6)]
            for i in range(3):
                window = col_data[i:i+4]
                score += evaluate_window(window, player)

        # Diagonal (positive slope)
        for r in range(3):
            for c in range(4):
                window = [current_board[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, player)

        # Diagonal (negative slope)
        for r in range(3, 6):
            for c in range(4):
                window = [current_board[r - i][c + i] for i in range(4)]
                score += evaluate_window(window, player)

        return score

    def evaluate_window(window, player):
        opp_player = -player
        player_count = window.count(player)
        opp_count = window.count(opp_player)
        empty = window.count(0)

        if player_count == 4:
            return 100
        elif player_count == 3 and empty == 1:
            return 5
        elif player_count == 2 and empty == 2:
            return 2
        elif opp_count == 3 and empty == 1:
            return 4
        else:
            return 0

    valid_cols = [col for col in range(7) if get_next_open_row(col) >= 0]
    best_score = -float('inf')
    best_col = valid_cols[0]
    for col in valid_cols:
        row = get_next_open_row(col)
        temp_board = [r[:] for r in board]
        temp_board[row][col] = 1
        new_score = score_position(temp_board, 1)
        if new_score > best_score:
            best_score = new_score
            best_col = col
    return best_col
