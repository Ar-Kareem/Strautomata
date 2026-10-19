
import time

ROWS = 6
COLS = 7
PLAYER = 1
OPPONENT = -1


class TimeoutError(Exception):
    """Raised when the search exceeds the time limit."""
    pass


def get_valid_moves(board):
    """Return list of columns that are not full."""
    return [c for c in range(COLS) if board[0][c] == 0]


def get_winner(board):
    """Return 1 if PLAYER wins, -1 if OPPONENT wins, else 0."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if board[r][c] != 0 and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return board[r][c]
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if board[r][c] != 0 and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return board[r][c]
    # Diagonal (positive slope)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if board[r][c] != 0 and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return board[r][c]
    # Diagonal (negative slope)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if board[r][c] != 0 and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                return board[r][c]
    return 0


def evaluate_window(window):
    """
    Score a window of 4 cells.
    window: list of 4 ints (1, -1, 0)
    Returns score from PLAYER's perspective.
    """
    if 1 in window and -1 not in window:
        cnt = window.count(1)
        if cnt == 4:
            return 1000000
        elif cnt == 3:
            return 1000
        elif cnt == 2:
            return 10
        elif cnt == 1:
            return 1
    elif -1 in window and 1 not in window:
        cnt = window.count(-1)
        if cnt == 4:
            return -1000000
        elif cnt == 3:
            return -10000
        elif cnt == 2:
            return -10
        elif cnt == 1:
            return -1
    return 0


def evaluate(board):
    """Heuristic evaluation of the board for PLAYER=1."""
    score = 0

    # Center column bonus
    center = COLS // 2
    for r in range(ROWS):
        if board[r][center] == PLAYER:
            score += 3
        elif board[r][center] == OPPONENT:
            score -= 3

    # Collect all windows of length 4
    windows = []
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            windows.append([board[r][c+i] for i in range(4)])
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            windows.append([board[r+i][c] for i in range(4)])
    # Diagonal /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            windows.append([board[r+i][c+i] for i in range(4)])
    # Diagonal \
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            windows.append([board[r-i][c+i] for i in range(4)])

    for w in windows:
        score += evaluate_window(w)
    return score


def drop_piece(board, col, piece):
    """Return a new board with the piece dropped in the column."""
    new_board = [row[:] for row in board]
    for r in range(ROWS - 1, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = piece
            return new_board
    # Should never reach here if column is valid
    return new_board


def minimax(board, depth, alpha, beta, maximizing, start_time, time_limit):
    """Minimax with alpha-beta pruning and time limit."""
    if time.perf_counter() - start_time > time_limit:
        raise TimeoutError()

    winner = get_winner(board)
    if winner == PLAYER:
        return 1000000 + depth
    elif winner == OPPONENT:
        return -1000000 - depth

    moves = get_valid_moves(board)
    if not moves:
        return 0  # draw

    if depth == 0:
        return evaluate(board)

    # Move ordering: center first
    moves.sort(key=lambda c: abs(c - 3))

    if maximizing:
        max_eval = -float('inf')
        for col in moves:
            new_board = drop_piece(board, col, PLAYER)
            eval_score = minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
            if eval_score > max_eval:
                max_eval = eval_score
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in moves:
            new_board = drop_piece(board, col, OPPONENT)
            eval_score = minimax(new_board, depth - 1, alpha, beta, True, start_time, time_limit)
            if eval_score < min_eval:
                min_eval = eval_score
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def policy(board):
    """
    Main entry point.
    Given the 6x7 board (list of lists of ints), return the column (0-6)
    where the current player (1) should drop the disc.
    """
    start_time = time.perf_counter()
    time_limit = 0.9

    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0  # fallback, should not happen
    if len(valid_moves) == 1:
        return valid_moves[0]

    # Order moves for initial best guess
    valid_moves.sort(key=lambda c: abs(c - 3))
    best_move = valid_moves[0]

    depth = 1
    while True:
        current_best = best_move
        max_eval = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        try:
            for col in valid_moves:
                new_board = drop_piece(board, col, PLAYER)
                eval_score = minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
                if eval_score > max_eval:
                    max_eval = eval_score
                    current_best = col
                alpha = max(alpha, eval_score)
            # Completed depth without timeout
            best_move = current_best
            # Take the win immediately if found
            if max_eval >= 1000000:
                break
            depth += 1
        except TimeoutError:
            break

    return best_move
