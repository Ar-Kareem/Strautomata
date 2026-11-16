
def policy(board):
    # Helper functions
    def is_valid_location(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in range(5, -1, -1):
            if board[r][col] == 0:
                return r
        return None

    def drop_piece(board, row, col, piece):
        board[row][col] = piece

    def winning_move(board, piece):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Check vertical
        for r in range(3):
            for c in range(7):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Check positive diagonal
        for r in range(3):
            for c in range(4):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        # Check negative diagonal
        for r in range(3):
            for c in range(4):
                if board[r][c+3] == piece and board[r+1][c+2] == piece and board[r+2][c+1] == piece and board[r+3][c] == piece:
                    return True
        return False

    def is_terminal_node(board):
        return winning_move(board, 1) or winning_move(board, -1) or len(get_valid_locations(board)) == 0

    def get_valid_locations(board):
        valid = []
        for col in range(7):
            if board[0][col] == 0:
                valid.append(col)
        return valid

    def evaluate_window(window, piece):
        score = 0
        count_piece = window.count(piece)
        count_opponent = window.count(-piece)
        count_empty = window.count(0)

        if count_piece == 3 and count_empty == 1:
            score += 1000
        elif count_piece == 2 and count_empty == 2:
            score += 100
        elif count_piece == 1 and count_empty == 3:
            score += 10

        if count_opponent == 3 and count_empty == 1:
            score -= 1000
        elif count_opponent == 2 and count_empty == 2:
            score -= 100
        elif count_opponent == 1 and count_empty == 3:
            score -= 10

        return score

    def score_position(board):
        score = 0
        # Center column preference
        center_array = [board[r][3] for r in range(6)]
        center_count_piece = center_array.count(1)
        center_count_opponent = center_array.count(-1)
        score += center_count_piece * 3
        score -= center_count_opponent * 3

        # Horizontal
        for r in range(6):
            row_array = board[r]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, 1) - evaluate_window(window, -1)

        # Vertical
        for c in range(7):
            col_array = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, 1) - evaluate_window(window, -1)

        # Positive diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, 1) - evaluate_window(window, -1)

        # Negative diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+3-i] for i in range(4)]
                score += evaluate_window(window, 1) - evaluate_window(window, -1)

        return score

    def minimax(board, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(board)
        is_terminal = is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(board, 1):
                    return 10000000
                elif winning_move(board, -1):
                    return -10000000
                else:
                    return 0
            else:
                return score_position(board)

        # Order moves by center preference
        valid_locations.sort(key=lambda x: abs(x-3))

        if maximizingPlayer:
            value = -10000000
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                drop_piece(b_copy, row, col, 1)
                new_score = minimax(b_copy, depth-1, alpha, beta, False)
                value = max(value, new_score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 10000000
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                drop_piece(b_copy, row, col, -1)
                new_score = minimax(b_copy, depth-1, alpha, beta, True)
                value = min(value, new_score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # Step 1: Check for immediate win
    for col in range(7):
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            temp_board = [r[:] for r in board]
            drop_piece(temp_board, row, col, 1)
            if winning_move(temp_board, 1):
                return col

    # Step 2: Check for opponent win and block
    for col in range(7):
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            temp_board = [r[:] for r in board]
            drop_piece(temp_board, row, col, -1)
            if winning_move(temp_board, -1):
                return col

    # Step 3: Use minimax to find best move
    valid_locations = get_valid_locations(board)
    valid_locations.sort(key=lambda x: abs(x-3))
    best_score = -10000000
    best_col = None
    
    for col in valid_locations:
        row = get_next_open_row(board, col)
        b_copy = [r[:] for r in board]
        drop_piece(b_copy, row, col, 1)
        score = minimax(b_copy, 3, -10000000, 10000000, False)
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
