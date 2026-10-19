
import math
import numpy as np

ROWS = 6
COLS = 7
CONNECT = 4

def _legal_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]

def _drop_row(board, col):
    # returns the row index where a disc would land, or None if full
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def _check_winner_after_move(b, r, c, player):
    # Check all directions from (r,c)
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in directions:
        cnt = 1
        # forward
        rr, cc = r+dr, c+dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
            cnt += 1
            rr += dr
            cc += dc
        # backward
        rr, cc = r-dr, c-dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
            cnt += 1
            rr -= dr
            cc -= dc
        if cnt >= CONNECT:
            return True
    return False

def _terminal_state(board):
    # returns (is_terminal, winner) where winner is 1, -1, or 0 for draw/none
    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            if v == 0:
                continue
            if _check_winner_after_move(board, r, c, v):
                return True, v
    if not _legal_moves(board):
        return True, 0
    return False, 0

def _heuristic(board):
    # Heuristic evaluation from perspective of current player (1)
    # Board uses: 1 = me, -1 = opp, 0 empty.
    score = 0

    # Center column preference
    center = COLS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center] == 1)
    score += center_count * 6

    # Window scoring
    # Evaluate all length-4 segments
    def window_score(window):
        nonlocal score
        arr = list(window)
        s = 0
        count1 = arr.count(1)
        countm = arr.count(-1)
        count0 = arr.count(0)
        # Strongly reward good formations for me; strongly punish opponent
        if count1 == 4:
            return 10_000
        if countm == 4:
            return -10_000
        if count1 == 3 and count0 == 1:
            s += 200
        elif count1 == 2 and count0 == 2:
            s += 20
        elif count1 == 1 and count0 == 3:
            s += 2

        if countm == 3 and count0 == 1:
            s -= 220
        elif countm == 2 and count0 == 2:
            s -= 25
        elif countm == 1 and count0 == 3:
            s -= 3
        return s

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c+i] for i in range(4)]
            score += window_score(window)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r+i][c] for i in range(4)]
            score += window_score(window)

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += window_score(window)

    # Diagonal down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [board[r+i][c-i] for i in range(4)]
            score += window_score(window)

    # Mild mobility/tempo: prefer having more legal moves later (optional)
    score += len(_legal_moves(board)) * 1

    return score

def _minimax(board, depth, alpha, beta, maximizing):
    terminal, winner = _terminal_state(board)
    if terminal:
        if winner == 1:
            return 10_000_000, None
        elif winner == -1:
            return -10_000_000, None
        else:
            return 0, None
    if depth == 0:
        return _heuristic(board), None

    legal = _legal_moves(board)
    # Move ordering: center-first tends to work well
    center = COLS // 2
    legal.sort(key=lambda c: abs(c - center))

    best_col = None
    if maximizing:
        value = -math.inf
        for col in legal:
            row = _drop_row(board, col)
            if row is None:
                continue
            b2 = [list(rw) for rw in board]
            b2[row][col] = 1
            # Fast win detection
            if _check_winner_after_move(b2, row, col, 1):
                return 10_000_000 - (3 - depth), col
            v, _ = _minimax(b2, depth-1, alpha, beta, False)
            if v > value:
                value = v
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_col
    else:
        value = math.inf
        for col in legal:
            row = _drop_row(board, col)
            if row is None:
                continue
            b2 = [list(rw) for rw in board]
            b2[row][col] = -1
            if _check_winner_after_move(b2, row, col, -1):
                return -10_000_000 + (3 - depth), col
            v, _ = _minimax(b2, depth-1, alpha, beta, True)
            if v < value:
                value = v
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_col

def policy(board: list[list[int]]) -> int:
    # Convert to our internal list[list[int]] (assumed already correct size)
    b = [list(row) for row in board]

    legal = _legal_moves(b)
    if not legal:
        return 0  # Should not happen in a legal game state

    # 1) Immediate win
    for col in legal:
        row = _drop_row(b, col)
        if row is None:
            continue
        b2 = [list(rw) for rw in b]
        b2[row][col] = 1
        if _check_winner_after_move(b2, row, col, 1):
            return col

    # 2) Block opponent immediate win
    for col in legal:
        row = _drop_row(b, col)
        if row is None:
            continue
        b2 = [list(rw) for rw in b]
        b2[row][col] = -1
        if _check_winner_after_move(b2, row, col, -1):
            return col

    # 3) Search
    # Depth choice: keep it fast; tactical positions often resolved within 3-4 plies.
    depth = 4
    _, best = _minimax(b, depth, -math.inf, math.inf, True)
    if best is not None:
        return best

    # Fallback: center-most legal
    center = COLS // 2
    return min(legal, key=lambda c: abs(c - center))
