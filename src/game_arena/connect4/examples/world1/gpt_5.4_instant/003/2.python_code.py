
from math import inf

ROWS = 6
COLS = 7
ORDER = [3, 2, 4, 1, 5, 0, 6]


def legal_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def next_open_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def drop_disc(board, col, piece):
    r = next_open_row(board, col)
    if r is None:
        return None
    new_board = [row[:] for row in board]
    new_board[r][col] = piece
    return new_board


def winning_move(board, piece):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece
                and board[r][c + 1] == piece
                and board[r][c + 2] == piece
                and board[r][c + 3] == piece
            ):
                return True

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if (
                board[r][c] == piece
                and board[r + 1][c] == piece
                and board[r + 2][c] == piece
                and board[r + 3][c] == piece
            ):
                return True

    # Positive slope diagonal
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece
                and board[r + 1][c + 1] == piece
                and board[r + 2][c + 2] == piece
                and board[r + 3][c + 3] == piece
            ):
                return True

    # Negative slope diagonal
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece
                and board[r - 1][c + 1] == piece
                and board[r - 2][c + 2] == piece
                and board[r - 3][c + 3] == piece
            ):
                return True

    return False


def is_terminal(board):
    return winning_move(board, 1) or winning_move(board, -1) or len(legal_moves(board)) == 0


def evaluate_window(window):
    score = 0
    my_count = window.count(1)
    opp_count = window.count(-1)
    empty_count = window.count(0)

    if my_count == 4:
        score += 100000
    elif my_count == 3 and empty_count == 1:
        score += 120
    elif my_count == 2 and empty_count == 2:
        score += 12

    if opp_count == 4:
        score -= 100000
    elif opp_count == 3 and empty_count == 1:
        score -= 150
    elif opp_count == 2 and empty_count == 2:
        score -= 15

    return score


def score_position(board):
    score = 0

    # Center control
    center_col = COLS // 2
    center_array = [board[r][center_col] for r in range(ROWS)]
    score += center_array.count(1) * 10
    score -= center_array.count(-1) * 10

    # Horizontal
    for r in range(ROWS):
        row_array = board[r]
        for c in range(COLS - 3):
            window = row_array[c:c + 4]
            score += evaluate_window(window)

    # Vertical
    for c in range(COLS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r + 4]
            score += evaluate_window(window)

    # Positive slope diagonals
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window)

    # Negative slope diagonals
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(window)

    return score


def count_immediate_wins(board, piece):
    count = 0
    for c in legal_moves(board):
        nb = drop_disc(board, c, piece)
        if nb is not None and winning_move(nb, piece):
            count += 1
    return count


def safe_moves(board):
    moves = legal_moves(board)
    safe = []
    for c in moves:
        nb = drop_disc(board, c, 1)
        if nb is None:
            continue
        opp_wins = False
        for oc in legal_moves(nb):
            nbb = drop_disc(nb, oc, -1)
            if nbb is not None and winning_move(nbb, -1):
                opp_wins = True
                break
        if not opp_wins:
            safe.append(c)
    return safe


def minimax(board, depth, alpha, beta, maximizing):
    valid_locations = legal_moves(board)
    terminal = is_terminal(board)

    if depth == 0 or terminal:
        if terminal:
            if winning_move(board, 1):
                return (None, 10**12)
            elif winning_move(board, -1):
                return (None, -10**12)
            else:
                return (None, 0)
        else:
            val = score_position(board)
            my_wins = count_immediate_wins(board, 1)
            opp_wins = count_immediate_wins(board, -1)
            val += my_wins * 500
            val -= opp_wins * 700
            return (None, val)

    ordered_moves = [c for c in ORDER if c in valid_locations]

    if maximizing:
        value = -inf
        best_col = ordered_moves[0]
        for col in ordered_moves:
            child = drop_disc(board, col, 1)
            _, new_score = minimax(child, depth - 1, alpha, beta, False)
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = inf
        best_col = ordered_moves[0]
        for col in ordered_moves:
            child = drop_disc(board, col, -1)
            _, new_score = minimax(child, depth - 1, alpha, beta, True)
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value


def policy(board):
    moves = legal_moves(board)
    if not moves:
        return 0

    ordered_moves = [c for c in ORDER if c in moves]

    # 1. Immediate win
    for c in ordered_moves:
        nb = drop_disc(board, c, 1)
        if nb is not None and winning_move(nb, 1):
            return c

    # 2. Immediate block
    opp_winning_cols = []
    for c in ordered_moves:
        nb = drop_disc(board, c, -1)
        if nb is not None and winning_move(nb, -1):
            opp_winning_cols.append(c)
    if opp_winning_cols:
        for c in ordered_moves:
            if c in opp_winning_cols:
                return c

    # 3. Prefer safe moves
    safe = safe_moves(board)
    candidate_moves = safe if safe else ordered_moves

    # 4. Search
    best_col = candidate_moves[0]
    best_score = -inf

    # Search each candidate with minimax
    # Depth 5 is a good strength/speed compromise
    for c in [x for x in ORDER if x in candidate_moves]:
        nb = drop_disc(board, c, 1)
        _, score = minimax(nb, 4, -inf, inf, False)

        # Slight preference for center in ties
        score -= abs(3 - c) * 0.01

        if score > best_score:
            best_score = score
            best_col = c

    # Final legality guarantee
    if best_col in moves:
        return best_col
    return ordered_moves[0]
