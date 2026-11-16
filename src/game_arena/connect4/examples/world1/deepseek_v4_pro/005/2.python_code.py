
import time

def policy(board):
    ROWS = 6
    COLS = 7
    PLAYER = 1
    OPPONENT = -1
    start_time = time.time()
    time_limit = 0.95
    timeout = [False]

    # Center-first move ordering for better pruning
    move_order = [3, 2, 4, 1, 5, 0, 6]

    def get_valid_moves(board):
        return [c for c in move_order if board[0][c] == 0]

    def drop_piece(board, col, player):
        new_board = [row[:] for row in board]
        for r in range(ROWS - 1, -1, -1):
            if new_board[r][col] == 0:
                new_board[r][col] = player
                break
        return new_board

    def check_win(board, player):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if (board[r][c] == player and board[r][c+1] == player and
                    board[r][c+2] == player and board[r][c+3] == player):
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if (board[r][c] == player and board[r+1][c] == player and
                    board[r+2][c] == player and board[r+3][c] == player):
                    return True
        # Diagonal (down-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if (board[r][c] == player and board[r+1][c+1] == player and
                    board[r+2][c+2] == player and board[r+3][c+3] == player):
                    return True
        # Diagonal (up-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if (board[r][c] == player and board[r-1][c+1] == player and
                    board[r-2][c+2] == player and board[r-3][c+3] == player):
                    return True
        return False

    def evaluate_window(window, player):
        opp = -player
        p_count = window.count(player)
        opp_count = window.count(opp)
        empty = window.count(0)

        if p_count == 4:
            return 1000000
        if opp_count == 4:
            return -1000000
        if p_count == 3 and empty == 1:
            return 200
        if opp_count == 3 and empty == 1:
            return -250  # prioritize blocking opponent threats
        if p_count == 2 and empty == 2:
            return 10
        if opp_count == 2 and empty == 2:
            return -10
        if p_count == 1 and empty == 3:
            return 1
        if opp_count == 1 and empty == 3:
            return -1
        return 0

    def evaluate(board, player):
        score = 0
        # Center column bonus
        for r in range(ROWS):
            if board[r][3] == player:
                score += 3
            elif board[r][3] == -player:
                score -= 3

        # Horizontal windows
        for r in range(ROWS):
            row_arr = board[r]
            for c in range(COLS - 3):
                window = row_arr[c:c+4]
                score += evaluate_window(window, player)

        # Vertical windows
        for c in range(COLS):
            col_arr = [board[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_arr[r:r+4]
                score += evaluate_window(window, player)

        # Diagonal (down-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, player)

        # Diagonal (up-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, player)

        return score

    def minimax(board, depth, alpha, beta, maximizingPlayer):
        if timeout[0]:
            return 0, None

        # Terminal checks
        if check_win(board, PLAYER):
            return 1000000 + depth, None
        if check_win(board, OPPONENT):
            return -1000000 - depth, None

        valid_moves = get_valid_moves(board)
        if depth == 0 or not valid_moves:
            return evaluate(board, PLAYER), None

        if maximizingPlayer:
            max_eval = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                if time.time() - start_time > time_limit:
                    timeout[0] = True
                    return 0, None
                new_board = drop_piece(board, col, PLAYER)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_col
        else:
            min_eval = float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                if time.time() - start_time > time_limit:
                    timeout[0] = True
                    return 0, None
                new_board = drop_piece(board, col, OPPONENT)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_col

    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0  # fallback (board full)

    # Immediate win
    for col in valid_moves:
        if check_win(drop_piece(board, col, PLAYER), PLAYER):
            return col

    # Block opponent's immediate win
    for col in valid_moves:
        if check_win(drop_piece(board, col, OPPONENT), OPPONENT):
            return col

    # Iterative deepening search
    best_move = valid_moves[0]
    depth = 1
    while not timeout[0]:
        try:
            score, move = minimax(board, depth, float('-inf'), float('inf'), True)
            if move is not None and not timeout[0]:
                best_move = move
            depth += 1
        except RecursionError:
            break
        except Exception:
            break

    return best_move
