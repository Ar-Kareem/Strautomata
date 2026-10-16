
def policy(board):
    ROWS = 6
    COLS = 7
    ORIGINAL_PLAYER = 1

    def simulate_move(board, col, player):
        new_board = [row[:] for row in board]
        for row in range(ROWS-1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board

    def get_available_moves(board):
        moves = []
        for col in range(COLS):
            if board[0][col] == 0:
                moves.append(col)
        return moves

    def check_win(board, player):
        for row in range(ROWS):
            for col in range(COLS - 3):
                if board[row][col] == player and board[row][col+1] == player and board[row][col+2] == player and board[row][col+3] == player:
                    return True
        for row in range(ROWS - 3):
            for col in range(COLS):
                if board[row][col] == player and board[row+1][col] == player and board[row+2][col] == player and board[row+3][col] == player:
                    return True
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                if board[row][col] == player and board[row+1][col+1] == player and board[row+2][col+2] == player and board[row+3][col+3] == player:
                    return True
        for row in range(ROWS - 3):
            for col in range(3, COLS):
                if board[row][col] == player and board[row+1][col-1] == player and board[row+2][col-2] == player and board[row+3][col-3] == player:
                    return True
        return False

    def score_window(window, player):
        score = 0
        opp = -player
        count_player = 0
        count_opp = 0
        count_empty = 0
        for cell in window:
            if cell == player:
                count_player += 1
            elif cell == opp:
                count_opp += 1
            else:
                count_empty += 1
        if count_player == 4:
            score += 100000
        elif count_opp == 4:
            score -= 100000
        else:
            if count_player == 3 and count_empty == 1:
                score += 120
            elif count_player == 2 and count_empty == 2:
                score += 12
            elif count_player == 1 and count_empty == 3:
                score += 1.5
            if count_opp == 3 and count_empty == 1:
                score -= 120
            elif count_opp == 2 and count_empty == 2:
                score -= 12
            elif count_opp == 1 and count_empty == 3:
                score -= 1.5
        return score

    def evaluate_board(board, original_player):
        score = 0
        center_col = board[0].index(board[0][3]) if board[0][3] != 0 else 3
        count_player = 0
        count_opp = 0
        for row in range(ROWS):
            if board[row][3] == original_player:
                count_player += 1
            elif board[row][3] == -original_player:
                count_opp += 1
        score += count_player * 3
        score -= count_opp * 3
        for row in range(ROWS):
            for col in range(COLS - 3):
                window = board[row][col:col+4]
                score += score_window(window, original_player)
        for row in range(ROWS - 3):
            for col in range(COLS):
                window = [board[row+i][col] for i in range(4)]
                score += score_window(window, original_player)
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                window = [board[row+i][col+i] for i in range(4)]
                score += score_window(window, original_player)
        for row in range(ROWS - 3):
            for col in range(3, COLS):
                window = [board[row+i][col-i] for i in range(4)]
                score += score_window(window, original_player)
        return score

    def minimax(board, depth, current_player, alpha, beta, original_player):
        if check_win(board, original_player):
            return 1000000
        if check_win(board, -original_player):
            return -1000000
        if depth == 0:
            return evaluate_board(board, original_player)
        available_moves = get_available_moves(board)
        if not available_moves:
            return evaluate_board(board, original_player)
        if current_player == original_player:
            max_score = -float('inf')
            for col in available_moves:
                new_board = simulate_move(board, col, current_player)
                score = minimax(new_board, depth-1, -current_player, alpha, beta, original_player)
                if score > max_score:
                    max_score = score
                if score > alpha:
                    alpha = score
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for col in available_moves:
                new_board = simulate_move(board, col, current_player)
                score = minimax(new_board, depth-1, -current_player, alpha, beta, original_player)
                if score < min_score:
                    min_score = score
                if score < beta:
                    beta = score
                if beta <= alpha:
                    break
            return min_score

    available_moves = get_available_moves(board)
    if not available_moves:
        return 0
    for col in available_moves:
        new_board = simulate_move(board, col, ORIGINAL_PLAYER)
        if check_win(new_board, ORIGINAL_PLAYER):
            return col
    best_score = -float('inf')
    best_col = None
    moves = available_moves.copy()
    moves.sort(key=lambda x: abs(x - 3))
    for col in moves:
        new_board = simulate_move(board, col, ORIGINAL_PLAYER)
        score = minimax(new_board, 1, -ORIGINAL_PLAYER, -float('inf'), float('inf'), ORIGINAL_PLAYER)
        if score > best_score:
            best_score = score
            best_col = col
        elif score == best_score:
            if best_col is not None and abs(col - 3) < abs(best_col - 3):
                best_col = col
    if best_col is None:
        best_col = moves[0]
    return best_col
