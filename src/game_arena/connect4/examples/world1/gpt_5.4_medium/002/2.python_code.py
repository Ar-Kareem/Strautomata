
import time
import random

ROWS = 6
COLS = 7
MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)

INF = 10**18
WIN_SCORE = 10**9

# Precompute all 4-cell windows on the board.
WINDOWS = []
# Horizontal
for r in range(ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
# Vertical
for r in range(ROWS - 3):
    for c in range(COLS):
        WINDOWS.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
# Diagonal /
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))
# Diagonal \
for r in range(3, ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)))

_rng = random.Random(0)
ZOBRIST = [[[ _rng.getrandbits(64) for _ in range(2)] for _ in range(COLS)] for _ in range(ROWS)]
SIDE_KEY = _rng.getrandbits(64)

EXACT = 0
LOWER = 1
UPPER = 2


def policy(board: list[list[int]]) -> int:
    # Quick opening: take center on empty board.
    is_empty = True
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != 0:
                is_empty = False
                break
        if not is_empty:
            break
    if is_empty:
        return 3

    # Internal board uses row 0 as bottom for easier gravity handling.
    grid = [[board[ROWS - 1 - r][c] for c in range(COLS)] for r in range(ROWS)]
    heights = [0] * COLS
    for c in range(COLS):
        h = 0
        while h < ROWS and grid[h][c] != 0:
            h += 1
        heights[c] = h

    legal_moves = [c for c in MOVE_ORDER if heights[c] < ROWS]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    board_hash = 0
    for r in range(ROWS):
        for c in range(COLS):
            v = grid[r][c]
            if v == 1:
                board_hash ^= ZOBRIST[r][c][0]
            elif v == -1:
                board_hash ^= ZOBRIST[r][c][1]

    tt = {}
    start = time.perf_counter()
    deadline = start + 0.85
    node_counter = 0

    def check_time():
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 255) == 0 and time.perf_counter() > deadline:
            raise TimeoutError

    def is_win(row, col, player):
        # Vertical
        cnt = 1
        rr = row + 1
        while rr < ROWS and grid[rr][col] == player:
            cnt += 1
            rr += 1
        rr = row - 1
        while rr >= 0 and grid[rr][col] == player:
            cnt += 1
            rr -= 1
        if cnt >= 4:
            return True

        # Horizontal
        cnt = 1
        cc = col + 1
        while cc < COLS and grid[row][cc] == player:
            cnt += 1
            cc += 1
        cc = col - 1
        while cc >= 0 and grid[row][cc] == player:
            cnt += 1
            cc -= 1
        if cnt >= 4:
            return True

        # Diagonal /
        cnt = 1
        rr, cc = row + 1, col + 1
        while rr < ROWS and cc < COLS and grid[rr][cc] == player:
            cnt += 1
            rr += 1
            cc += 1
        rr, cc = row - 1, col - 1
        while rr >= 0 and cc >= 0 and grid[rr][cc] == player:
            cnt += 1
            rr -= 1
            cc -= 1
        if cnt >= 4:
            return True

        # Diagonal \
        cnt = 1
        rr, cc = row + 1, col - 1
        while rr < ROWS and cc >= 0 and grid[rr][cc] == player:
            cnt += 1
            rr += 1
            cc -= 1
        rr, cc = row - 1, col + 1
        while rr >= 0 and cc < COLS and grid[rr][cc] == player:
            cnt += 1
            rr -= 1
            cc += 1
        return cnt >= 4

    def make_move(col, player):
        nonlocal board_hash
        row = heights[col]
        grid[row][col] = player
        heights[col] += 1
        board_hash ^= ZOBRIST[row][col][0 if player == 1 else 1]
        return row

    def undo_move(col, row, player):
        nonlocal board_hash
        heights[col] -= 1
        grid[row][col] = 0
        board_hash ^= ZOBRIST[row][col][0 if player == 1 else 1]

    def legal_list():
        return [c for c in MOVE_ORDER if heights[c] < ROWS]

    def immediate_winning_moves(player):
        wins = []
        for c in MOVE_ORDER:
            if heights[c] >= ROWS:
                continue
            row = make_move(c, player)
            won = is_win(row, c, player)
            undo_move(c, row, player)
            if won:
                wins.append(c)
        return wins

    def evaluate():
        score = 0

        # Center control.
        center_col = 3
        for r in range(ROWS):
            v = grid[r][center_col]
            if v == 1:
                score += 6
            elif v == -1:
                score -= 6

        # Immediate tactical threats.
        my_win_moves = 0
        opp_win_moves = 0
        for c in MOVE_ORDER:
            if heights[c] >= ROWS:
                continue
            row = heights[c]
            grid[row][c] = 1
            if is_win(row, c, 1):
                my_win_moves += 1
            grid[row][c] = -1
            if is_win(row, c, -1):
                opp_win_moves += 1
            grid[row][c] = 0

        score += 900 * my_win_moves
        score -= 1100 * opp_win_moves

        # Window-based pattern evaluation.
        for window in WINDOWS:
            c1 = 0
            c2 = 0
            empties = []

            for r, c in window:
                v = grid[r][c]
                if v == 1:
                    c1 += 1
                elif v == -1:
                    c2 += 1
                else:
                    empties.append((r, c))

            if c1 and c2:
                continue

            if c1:
                if c1 == 4:
                    score += 100000
                elif c1 == 3:
                    score += 60
                    er, ec = empties[0]
                    if heights[ec] == er:
                        score += 260
                elif c1 == 2:
                    score += 12
                elif c1 == 1:
                    score += 2
            elif c2:
                if c2 == 4:
                    score -= 100000
                elif c2 == 3:
                    score -= 70
                    er, ec = empties[0]
                    if heights[ec] == er:
                        score -= 320
                elif c2 == 2:
                    score -= 14
                elif c2 == 1:
                    score -= 2

        return score

    def ordered_moves(tt_move=None):
        moves = legal_list()
        if tt_move in moves:
            return [tt_move] + [c for c in moves if c != tt_move]
        return moves

    def negamax(depth, alpha, beta, player, ply):
        check_time()

        moves = legal_list()
        if not moves:
            return 0

        key = board_hash ^ (SIDE_KEY if player == -1 else 0)
        entry = tt.get(key)
        tt_move = None
        alpha_orig = alpha
        beta_orig = beta

        if entry is not None:
            e_depth, e_flag, e_val, e_move = entry
            if e_depth >= depth:
                if e_flag == EXACT:
                    return e_val
                if e_flag == LOWER:
                    alpha = max(alpha, e_val)
                elif e_flag == UPPER:
                    beta = min(beta, e_val)
                if alpha >= beta:
                    return e_val
            tt_move = e_move

        if depth == 0:
            # Small tactical extension: if current side can win immediately, treat as terminal.
            for c in ordered_moves(tt_move):
                row = make_move(c, player)
                won = is_win(row, c, player)
                undo_move(c, row, player)
                if won:
                    return WIN_SCORE - ply
            return player * evaluate()

        best_val = -INF
        best_move = moves[0]

        for c in ordered_moves(tt_move):
            row = make_move(c, player)
            if is_win(row, c, player):
                val = WIN_SCORE - ply
            else:
                val = -negamax(depth - 1, -beta, -alpha, -player, ply + 1)
            undo_move(c, row, player)

            if val > best_val:
                best_val = val
                best_move = c
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        flag = EXACT
        if best_val <= alpha_orig:
            flag = UPPER
        elif best_val >= beta_orig:
            flag = LOWER
        tt[key] = (depth, flag, best_val, best_move)
        return best_val

    # 1) Immediate win.
    my_wins = immediate_winning_moves(1)
    if my_wins:
        return my_wins[0]

    # 2) Forced block if opponent has exactly one immediate win.
    opp_wins = immediate_winning_moves(-1)
    if len(opp_wins) == 1:
        return opp_wins[0]
    if len(opp_wins) >= 2:
        # Unavoidable loss in normal play; return a legal move.
        return legal_moves[0]

    # 3) Filter out moves that allow an immediate opponent win, if possible.
    safe_moves = []
    for c in legal_moves:
        row = make_move(c, 1)
        if is_win(row, c, 1):
            undo_move(c, row, 1)
            return c
        bad = False
        for oc in MOVE_ORDER:
            if heights[oc] >= ROWS:
                continue
            orow = make_move(oc, -1)
            if is_win(orow, oc, -1):
                bad = True
                undo_move(oc, orow, -1)
                break
            undo_move(oc, orow, -1)
        undo_move(c, row, 1)
        if not bad:
            safe_moves.append(c)

    root_moves = safe_moves if safe_moves else legal_moves
    best_move = root_moves[0]
    prev_best = best_move

    def root_order(moves, first):
        ordered = []
        if first in moves:
            ordered.append(first)
        for c in MOVE_ORDER:
            if c in moves and c not in ordered:
                ordered.append(c)
        return ordered

    # 4) Iterative deepening alpha-beta.
    empties = sum(1 for r in range(ROWS) for c in range(COLS) if grid[r][c] == 0)
    max_depth = empties

    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            current_best_move = best_move
            current_best_val = -INF

            for c in root_order(root_moves, prev_best):
                check_time()
                row = make_move(c, 1)
                if is_win(row, c, 1):
                    val = WIN_SCORE
                else:
                    val = -negamax(depth - 1, -beta, -alpha, -1, 1)
                undo_move(c, row, 1)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = c
                if val > alpha:
                    alpha = val

            best_move = current_best_move
            prev_best = best_move

            if current_best_val >= WIN_SCORE - 50:
                break

        except TimeoutError:
            break

    # Final safety: guarantee a legal move.
    if heights[best_move] < ROWS:
        return best_move
    for c in MOVE_ORDER:
        if heights[c] < ROWS:
            return c
    return 0
