
import math
import time

ROWS = 6
COLS = 7
WIN_SCORE = 10**9
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    start = time.time()
    time_limit = 0.92

    # Convert defensively to plain nested lists
    b = [row[:] for row in board]

    legal = valid_moves(b)
    if not legal:
        return 0

    # 1. Immediate win
    for c in CENTER_ORDER:
        if c in legal and is_winning_move(b, c, 1):
            return c

    # 2. Immediate block
    for c in CENTER_ORDER:
        if c in legal and is_winning_move(b, c, -1):
            return c

    # 3. Prefer safe moves if possible: avoid giving opponent immediate win
    safe = []
    for c in legal:
        nb = make_move(b, c, 1)
        opp_legal = valid_moves(nb)
        if not any(is_winning_move(nb, oc, -1) for oc in opp_legal):
            safe.append(c)
    search_moves = safe if safe else legal

    # If board is very open, take center
    if len(legal) == 7 and b[5][3] == 0:
        return 3

    best_move = order_moves(b, search_moves, 1)[0]
    best_score = -math.inf

    # Adaptive search depth based on remaining empty cells
    empties = sum(cell == 0 for row in b for cell in row)
    max_depth = 5
    if empties <= 18:
        max_depth = 7
    if empties <= 12:
        max_depth = 9

    # Iterative deepening so we always have a move if time gets tight
    try:
        for depth in range(1, max_depth + 1):
            if time.time() - start > time_limit:
                break
            score, move = negamax(b, depth, -math.inf, math.inf, 1, start, time_limit)
            if move is not None and move in search_moves:
                best_score, best_move = score, move
            if best_score >= WIN_SCORE // 2:
                break
    except TimeoutError:
        pass

    if best_move not in legal:
        return legal[0]
    return best_move


def valid_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def get_drop_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def make_move(board, col, player):
    nb = [row[:] for row in board]
    r = get_drop_row(nb, col)
    if r is not None:
        nb[r][col] = player
    return nb


def play_inplace(board, col, player):
    r = get_drop_row(board, col)
    board[r][col] = player
    return r


def undo_inplace(board, row, col):
    board[row][col] = 0


def is_winning_move(board, col, player):
    r = get_drop_row(board, col)
    if r is None:
        return False
    return check_win_at(board, r, col, player)


def check_win_at_after_place(board, row, col, player):
    return check_win_at(board, row, col, player)


def check_win_at(board, row, col, player):
    # Temporarily treat (row, col) as occupied by player if it is empty.
    old = board[row][col]
    board[row][col] = player

    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count = 1

        rr, cc = row + dr, col + dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr += dr
            cc += dc

        rr, cc = row - dr, col - dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr -= dr
            cc -= dc

        if count >= 4:
            board[row][col] = old
            return True

    board[row][col] = old
    return False


def negamax(board, depth, alpha, beta, player, start, time_limit):
    if time.time() - start > time_limit:
        raise TimeoutError()

    legal = valid_moves(board)
    if not legal:
        return 0, None

    # Tactical checks at each node
    for c in CENTER_ORDER:
        if c in legal:
            row = play_inplace(board, c, player)
            won = check_win_at_after_place(board, row, c, player)
            undo_inplace(board, row, c)
            if won:
                return WIN_SCORE + depth, c

    if depth == 0:
        return evaluate(board, player), None

    best_move = legal[0]
    best_score = -math.inf

    moves = order_moves(board, legal, player)

    for c in moves:
        row = play_inplace(board, c, player)

        if check_win_at_after_place(board, row, c, player):
            score = WIN_SCORE + depth
        else:
            score, _ = negamax(board, depth - 1, -beta, -alpha, -player, start, time_limit)
            score = -score

        undo_inplace(board, row, c)

        if score > best_score:
            best_score = score
            best_move = c

        alpha = max(alpha, score)
        if alpha >= beta:
            break

    return best_score, best_move


def order_moves(board, moves, player):
    scored = []
    for c in moves:
        score = 0

        # Center preference
        score += 10 * (3 - abs(3 - c))

        # Immediate tactical ordering
        if is_winning_move(board, c, player):
            score += 1000000
        if is_winning_move(board, c, -player):
            score += 500000

        # Prefer moves creating threats
        row = get_drop_row(board, c)
        if row is not None:
            board[row][c] = player
            score += evaluate_local(board, row, c, player)
            board[row][c] = 0

        scored.append((score, c))

    scored.sort(reverse=True)
    return [c for _, c in scored]


def evaluate(board, player):
    opp = -player
    score = 0

    # Center column control
    center_count = sum(1 for r in range(ROWS) if board[r][3] == player)
    opp_center_count = sum(1 for r in range(ROWS) if board[r][3] == opp)
    score += 30 * (center_count - opp_center_count)

    # Slight preference for lower stable pieces
    for r in range(ROWS):
        weight = r + 1
        for c in range(COLS):
            if board[r][c] == player:
                score += weight
            elif board[r][c] == opp:
                score -= weight

    # Score all windows
    for window in generate_windows(board):
        score += score_window(window, player)
        score -= score_window(window, opp) * 1.15

    # Threat bonus: playable immediate winning squares
    score += 250 * count_immediate_wins(board, player)
    score -= 350 * count_immediate_wins(board, opp)

    return int(score)


def evaluate_local(board, row, col, player):
    # Quick local feature for move ordering
    score = 0
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        line = []
        for k in range(-3, 4):
            rr = row + dr * k
            cc = col + dc * k
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                line.append(board[rr][cc])
        for i in range(max(0, len(line) - 3)):
            w = line[i:i+4]
            if player in w:
                score += score_window(w, player)
    return score


def generate_windows(board):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            yield [board[r][c+i] for i in range(4)]

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            yield [board[r+i][c] for i in range(4)]

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            yield [board[r+i][c+i] for i in range(4)]

    # Diagonal down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            yield [board[r+i][c-i] for i in range(4)]


def score_window(window, player):
    opp = -player
    p = window.count(player)
    o = window.count(opp)
    e = window.count(0)

    if p == 4:
        return WIN_SCORE
    if o > 0:
        return 0

    if p == 3 and e == 1:
        return 1200
    if p == 2 and e == 2:
        return 80
    if p == 1 and e == 3:
        return 5
    return 0


def count_immediate_wins(board, player):
    count = 0
    for c in valid_moves(board):
        if is_winning_move(board, c, player):
            count += 1
    return count
