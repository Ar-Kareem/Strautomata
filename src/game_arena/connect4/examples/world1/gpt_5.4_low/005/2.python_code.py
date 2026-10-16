
import time

ROWS = 6
COLS = 7
MOVE_ORDER = [3, 2, 4, 1, 5, 0, 6]
INF = 10**9


def policy(board: list[list[int]]) -> int:
    deadline = time.perf_counter() + 0.92

    def legal_moves(b):
        return [c for c in MOVE_ORDER if b[0][c] == 0]

    def get_row(b, col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return -1

    def play(b, col, player):
        r = get_row(b, col)
        b[r][col] = player
        return r

    def undo(b, col, row):
        b[row][col] = 0

    def is_win_from(b, row, col, player):
        # Horizontal
        cnt = 1
        c = col - 1
        while c >= 0 and b[row][c] == player:
            cnt += 1
            c -= 1
        c = col + 1
        while c < COLS and b[row][c] == player:
            cnt += 1
            c += 1
        if cnt >= 4:
            return True

        # Vertical
        cnt = 1
        r = row - 1
        while r >= 0 and b[r][col] == player:
            cnt += 1
            r -= 1
        r = row + 1
        while r < ROWS and b[r][col] == player:
            cnt += 1
            r += 1
        if cnt >= 4:
            return True

        # Diagonal /
        cnt = 1
        r, c = row - 1, col + 1
        while r >= 0 and c < COLS and b[r][c] == player:
            cnt += 1
            r -= 1
            c += 1
        r, c = row + 1, col - 1
        while r < ROWS and c >= 0 and b[r][c] == player:
            cnt += 1
            r += 1
            c -= 1
        if cnt >= 4:
            return True

        # Diagonal \
        cnt = 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and b[r][c] == player:
            cnt += 1
            r -= 1
            c -= 1
        r, c = row + 1, col + 1
        while r < ROWS and c < COLS and b[r][c] == player:
            cnt += 1
            r += 1
            c += 1
        return cnt >= 4

    def winning_moves(b, player):
        wins = []
        for col in legal_moves(b):
            row = play(b, col, player)
            if is_win_from(b, row, col, player):
                wins.append(col)
            undo(b, col, row)
        return wins

    def score_window(window, player):
        opp = -player
        pc = window.count(player)
        oc = window.count(opp)
        ec = window.count(0)

        if pc and oc:
            return 0

        if pc == 4:
            return 100000
        if oc == 4:
            return -100000

        if pc == 3 and ec == 1:
            return 120
        if pc == 2 and ec == 2:
            return 12
        if pc == 1 and ec == 3:
            return 1

        if oc == 3 and ec == 1:
            return -140
        if oc == 2 and ec == 2:
            return -14
        if oc == 1 and ec == 3:
            return -1

        return 0

    def evaluate(b, player):
        score = 0

        # Center preference
        center = [b[r][COLS // 2] for r in range(ROWS)]
        score += center.count(player) * 6
        score -= center.count(-player) * 6

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                w = [b[r][c + i] for i in range(4)]
                score += score_window(w, player)

        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                w = [b[r + i][c] for i in range(4)]
                score += score_window(w, player)

        # Diagonal \
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                w = [b[r + i][c + i] for i in range(4)]
                score += score_window(w, player)

        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                w = [b[r - i][c + i] for i in range(4)]
                score += score_window(w, player)

        return score

    tt = {}

    def board_key(b):
        return tuple(cell for row in b for cell in row)

    def negamax(b, depth, alpha, beta, player):
        if time.perf_counter() > deadline:
            raise TimeoutError

        moves = legal_moves(b)
        if not moves:
            return 0, None

        key = (board_key(b), player, depth)
        if key in tt:
            return tt[key]

        if depth == 0:
            val = evaluate(b, player)
            tt[key] = (val, None)
            return val, None

        best_val = -INF
        best_move = moves[0]

        # Move ordering: wins first, then center-first order
        ordered = []
        for col in moves:
            row = play(b, col, player)
            win = is_win_from(b, row, col, player)
            undo(b, col, row)
            ordered.append((0 if win else 1, MOVE_ORDER.index(col), col))
        ordered.sort()

        for _, _, col in ordered:
            row = play(b, col, player)
            if is_win_from(b, row, col, player):
                val = 10000000 + depth
            else:
                val, _ = negamax(b, depth - 1, -beta, -alpha, -player)
                val = -val
            undo(b, col, row)

            if val > best_val:
                best_val = val
                best_move = col
            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                break

        tt[key] = (best_val, best_move)
        return best_val, best_move

    moves = legal_moves(board)
    if not moves:
        return 0

    # 1) Immediate win
    for col in moves:
        row = play(board, col, 1)
        won = is_win_from(board, row, col, 1)
        undo(board, col, row)
        if won:
            return col

    # 2) If possible, choose a move after which opponent has no immediate win
    safe_moves = []
    for col in moves:
        row = play(board, col, 1)
        opp_wins = winning_moves(board, -1)
        undo(board, col, row)
        if not opp_wins:
            safe_moves.append(col)

    # 3) If opponent has immediate wins now, prioritize blocks / safe responses
    opp_now_wins = set(winning_moves(board, -1))
    if opp_now_wins:
        blocking = [c for c in moves if c in opp_now_wins]
        if blocking:
            for c in MOVE_ORDER:
                if c in blocking and c in safe_moves:
                    return c
            for c in MOVE_ORDER:
                if c in blocking:
                    return c

    # 4) Prefer safe center-ish move quickly if search times out
    fallback_moves = safe_moves if safe_moves else moves
    fallback = next((c for c in MOVE_ORDER if c in fallback_moves), moves[0])

    # 5) Iterative deepening search
    best_move = fallback
    empties = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] == 0)
    max_depth = 8 if empties <= 14 else 7 if empties <= 24 else 6

    try:
        for depth in range(1, max_depth + 1):
            _, move = negamax(board, depth, -INF, INF, 1)
            if move is not None and move in moves:
                best_move = move
    except TimeoutError:
        pass

    if best_move in moves:
        return best_move
    return fallback
