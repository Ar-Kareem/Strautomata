
from typing import List

ROWS = 6
COLS = 7
ME = 1
OP = -1

def get_next_row(board: List[List[int]], col: int) -> int:
    """Return the row index where a disc would land in column col, or -1 if column is full."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def check_win_at(board: List[List[int]], row: int, col: int, player: int) -> bool:
    """Check whether placing at (row,col) for player makes four in a row."""
    if row < 0 or col < 0:
        return False
    directions = [(0,1), (1,0), (1,1), (1,-1)]
    for dr, dc in directions:
        count = 1
        # forward
        r, c = row + dr, col + dc
        while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
            count += 1
            r += dr; c += dc
        # backward
        r, c = row - dr, col - dc
        while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
            count += 1
            r -= dr; c -= dc
        if count >= 4:
            return True
    return False

def valid_moves(board: List[List[int]]) -> List[int]:
    moves = []
    for c in range(COLS):
        if board[0][c] == 0:
            moves.append(c)
    return moves

def evaluate_board(board: List[List[int]]) -> int:
    """Heuristic evaluation of board from ME perspective."""
    score = 0
    # center column preference
    center_col = COLS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == ME)
    score += center_count * 3

    # evaluate all windows of length 4
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c+i] for i in range(4)]
            score += window_score(window)
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r+i][c] for i in range(4)]
            score += window_score(window)
    # diagonals
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += window_score(window)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += window_score(window)
    return score

def window_score(window: List[int]) -> int:
    me_count = window.count(ME)
    op_count = window.count(OP)
    if me_count > 0 and op_count > 0:
        return 0
    # only one player's discs in this window or empty
    if me_count == 4:
        return 100000
    if op_count == 4:
        return -100000
    if me_count == 3:
        # prefer windows that are open (i.e., has at least one empty)
        return 200
    if op_count == 3:
        return -180
    if me_count == 2:
        return 20
    if op_count == 2:
        return -10
    return 0

def policy(board: List[List[int]]) -> int:
    """
    Choose a column index (0..6) to drop the disc.
    Board is a list of 6 rows (top=0..bottom=5), each a list of 7 ints (0 empty, 1 me, -1 opponent).
    """
    moves = valid_moves(board)
    if not moves:
        # should not happen in valid games, but return 0 fallback
        return 0

    # 1) Immediate win: if any move wins now, take it
    for col in moves:
        row = get_next_row(board, col)
        if row == -1:
            continue
        board[row][col] = ME
        if check_win_at(board, row, col, ME):
            board[row][col] = 0
            return col
        board[row][col] = 0

    # 2) Immediate block: if opponent can win next move in some column, block it
    opponent_threats = []
    for col in moves:
        r = get_next_row(board, col)
        if r == -1:
            continue
        board[r][col] = OP
        if check_win_at(board, r, col, OP):
            opponent_threats.append(col)
        board[r][col] = 0
    if opponent_threats:
        # choose block that is most central
        opponent_threats.sort(key=lambda c: abs(c - (COLS // 2)))
        return opponent_threats[0]

    # 3) Heuristic: simulate each move, avoid moves that allow opponent immediate win,
    #    prefer moves with high evaluation score and center bias
    best_col = None
    best_score = -10**9
    for col in moves:
        row = get_next_row(board, col)
        if row == -1:
            continue
        board[row][col] = ME
        # if after our move opponent has a winning reply, penalize heavily
        opp_can_win = False
        for opp_col in valid_moves(board):
            opp_row = get_next_row(board, opp_col)
            if opp_row == -1:
                continue
            board[opp_row][opp_col] = OP
            if check_win_at(board, opp_row, opp_col, OP):
                opp_can_win = True
            board[opp_row][opp_col] = 0
            if opp_can_win:
                break
        score = evaluate_board(board)
        # center bias
        score += (3 - abs(col - (COLS // 2))) * 5
        if opp_can_win:
            score -= 100000  # strongly avoid moves that give immediate opponent win
        board[row][col] = 0
        if score > best_score:
            best_score = score
            best_col = col

    if best_col is not None:
        return best_col

    # fallback: pick the most central available column
    moves.sort(key=lambda c: abs(c - (COLS // 2)))
    return moves[0]
