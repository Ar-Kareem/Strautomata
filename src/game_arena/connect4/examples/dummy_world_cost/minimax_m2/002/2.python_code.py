
import sys

ROW_COUNT = 6
COLUMN_COUNT = 7

# centre‑column preference (used only as a tiny tie‑breaker)
col_weights = [2, 3, 4, 5, 4, 3, 2]


def get_valid_locations(board):
    """Columns that are not full (top cell is empty)."""
    return [c for c in range(COLUMN_COUNT) if board[0][c] == 0]


def drop_piece(board, col, piece):
    """Return a new board with *piece* placed in the lowest empty row of column *col*."""
    new_board = [row[:] for row in board]
    for r in range(ROW_COUNT - 1, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = piece
            break
    return new_board


def check_win(board, piece):
    """Return True iff *piece* has a four‑in‑a‑row anywhere on the board."""
    # horizontal
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if board[r][c] == board[r][c + 1] == board[r][c + 2] == board[r][c + 3] == piece:
                return True
    # vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == board[r + 1][c] == board[r + 2][c] == board[r + 3][c] == piece:
                return True
    # diagonal down‑right
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            if board[r][c] == board[r + 1][c + 1] == board[r + 2][c + 2] == board[r + 3][c + 3] == piece:
                return True
    # diagonal down‑left
    for r in range(ROW_COUNT - 3):
        for c in range(3, COLUMN_COUNT):
            if board[r][c] == board[r + 1][c - 1] == board[r + 2][c - 2] == board[r + 3][c - 3] == piece:
                return True
    return False


def is_terminal_node(board):
    """True if the game is over (win or board full)."""
    return not get_valid_locations(board) or check_win(board, 1) or check_win(board, -1)


def evaluate_window(window, piece):
    """Score a single 4‑cell window from the perspective of *piece*."""
    opp_piece = -piece
    score = 0
    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 2

    if window.count(opp_piece) == 3 and window.count(0) == 1:
        score -= 4
    return score


def evaluate_board(board, piece):
    """Static evaluation of the whole board for *piece*."""
    score = 0

    # centre‑column bonus
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            if board[r][c] == piece:
                score += col_weights[c] * 0.1

    # horizontal windows
    for r in range(ROW_COUNT):
        row = board[r]
        for c in range(COLUMN_COUNT - 3):
            score += evaluate_window(row[c:c + 4], piece)

    # vertical windows
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            window = [board[r + i][c] for i in range(4)]
            score += evaluate_window(window, piece)

    # diagonal down‑right
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    # diagonal down‑left
    for r in range(ROW_COUNT - 3):
        for c in range(3, COLUMN_COUNT):
            window = [board[r + i][c - i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score


# Simple transposition cache for leaf scores
transposition = {}


def minimax(board, depth, alpha, beta, maximizing):
    """Alpha‑beta minimax. Returns (best_column, value)."""
    valid_locations = get_valid_locations(board)
    terminal = is_terminal_node(board)

    # terminal or depth 0 -> static score
    if depth == 0 or terminal:
        if terminal:
            if check_win(board, 1):
                return (None, 1000000)
            if check_win(board, -1):
                return (None, -1000000)
            return (None, 0)  # draw
        # leaf node: use cached value if available
        board_tuple = tuple(map(tuple, board))
        key = (board_tuple, depth, maximizing)
        if key in transposition:
            return (None, transposition[key])
        score = evaluate_board(board, 1)
        transposition[key] = score
        return (None, score)

    # move ordering – evaluate children statically and try best first
    if maximizing:
        # our turn (piece = 1)
        children = []
        for col in valid_locations:
            new_board = drop_piece(board, col, 1)
            static = evaluate_board(new_board, 1)
            children.append((static, col))
        children.sort(reverse=True, key=lambda x: x[0])  # best first

        best_col = children[0][1]
        value = -float('inf')
        for _, col in children:
            new_board = drop_piece(board, col, 1)
            new_score = minimax(new_board, depth - 1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return (best_col, value)
    else:
        # opponent's turn (piece = -1)
        children = []
        for col in valid_locations:
            new_board = drop_piece(board, col, -1)
            # evaluate from our perspective (still piece = 1)
            static = evaluate_board(new_board, 1)
            children.append((static, col))
        children.sort(key=lambda x: x[0])  # worst for us first

        best_col = children[0][1]
        value = float('inf')
        for _, col in children:
            new_board = drop_piece(board, col, -1)
            new_score = minimax(new_board, depth - 1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return (best_col, value)


def get_best_move(board):
    """Top‑level move selector: win → block → minimax."""
    # 1) immediate win
    for col in get_valid_locations(board):
        if check_win(drop_piece(board, col, 1), 1):
            return col
    # 2) block opponent's immediate win
    for col in get_valid_locations(board):
        if check_win(drop_piece(board, col, -1), -1):
            return col
    # 3) minimax search (depth 5 works well inside 1 s)
    col, _ = minimax(board, 5, -float('inf'), float('inf'), True)
    return col


def policy(board):
    """
    Called by the arena.  board is a 6x7 list of lists:
    0 = empty, 1 = us, -1 = opponent.
    Returns a column index (0‑6) that is not full.
    """
    # ensure we have a mutable list of lists (input may be tuple of tuples)
    if board and isinstance(board[0], (list, tuple)):
        board = [list(row) for row in board]
    return get_best_move(board)


if __name__ == "__main__":
    # optional test harness (not required for the submission)
    pass
