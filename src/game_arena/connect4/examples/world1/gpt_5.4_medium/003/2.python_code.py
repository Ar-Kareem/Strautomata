
import time

ROWS = 6
COLS = 7
ORDER = (3, 2, 4, 1, 5, 0, 6)
COL_WEIGHT = (3, 4, 5, 7, 5, 4, 3)

WIN_SCORE = 1_000_000
INF = 10**18

DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


WINDOWS = []
for r in range(ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
for r in range(ROWS - 3):
    for c in range(COLS):
        WINDOWS.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))
for r in range(3, ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)))


def is_win_from(board, row, col, player):
    for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
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
            return True
    return False


def legal_moves(heights):
    return [c for c in ORDER if heights[c] < ROWS]


def winning_moves(board, heights, player):
    wins = []
    for col in ORDER:
        if heights[col] >= ROWS:
            continue
        row = ROWS - 1 - heights[col]
        board[row][col] = player
        heights[col] += 1
        won = is_win_from(board, row, col, player)
        heights[col] -= 1
        board[row][col] = 0
        if won:
            wins.append(col)
    return wins


def ordered_moves(board, heights, player, preferred=None):
    scored = []

    for col in ORDER:
        if heights[col] >= ROWS:
            continue

        row = ROWS - 1 - heights[col]
        score = COL_WEIGHT[col] * 10

        if preferred is not None and col == preferred:
            score += 10000

        board[row][col] = player
        heights[col] += 1

        if is_win_from(board, row, col, player):
            score += 1_000_000
        else:
            local = 0
            for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
                cnt = 0

                rr, cc = row + dr, col + dc
                while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
                    cnt += 1
                    rr += dr
                    cc += dc

                rr, cc = row - dr, col - dc
                while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
                    cnt += 1
                    rr -= dr
                    cc -= dc

                local += cnt

            score += local * 5

        heights[col] -= 1
        board[row][col] = 0

        scored.append((score, col))

    scored.sort(reverse=True)
    return [col for _, col in scored]


def evaluate(board, heights, player):
    score = 0

    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            if v == player:
                score += COL_WEIGHT[c]
            elif v == -player:
                score -= COL_WEIGHT[c]

    for window in WINDOWS:
        mine = 0
        opp = 0
        empties = []

        for r, c in window:
            v = board[r][c]
            if v == player:
                mine += 1
            elif v == -player:
                opp += 1
            else:
                empties.append((r, c))

        if mine and opp:
            continue

        if mine:
            if mine == 3:
                er, ec = empties[0]
                if ROWS - 1 - heights[ec] == er:
                    score += 220
                else:
                    score += 45
            elif mine == 2:
                score += 18
            elif mine == 1:
                score += 3
        elif opp:
            if opp == 3:
                er, ec = empties[0]
                if ROWS - 1 - heights[ec] == er:
                    score -= 260
                else:
                    score -= 55
            elif opp == 2:
                score -= 20
            elif opp == 1:
                score -= 3

    my_wins = 0
    opp_wins = 0
    for col in ORDER:
        if heights[col] >= ROWS:
            continue

        row = ROWS - 1 - heights[col]

        board[row][col] = player
        heights[col] += 1
        if is_win_from(board, row, col, player):
            my_wins += 1
        heights[col] -= 1
        board[row][col] = 0

        board[row][col] = -player
        heights[col] += 1
        if is_win_from(board, row, col, -player):
            opp_wins += 1
        heights[col] -= 1
        board[row][col] = 0

    score += 600 * my_wins
    score -= 800 * opp_wins

    if my_wins >= 2:
        score += 3000
    if opp_wins >= 2:
        score -= 4000

    return score


def negamax(board, heights, depth, alpha, beta, player):
    global NODES, DEADLINE

    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    moves = legal_moves(heights)
    if not moves:
        return 0

    if depth == 0:
        return evaluate(board, heights, player)

    best = -INF
    for col in ordered_moves(board, heights, player):
        row = ROWS - 1 - heights[col]
        board[row][col] = player
        heights[col] += 1

        if is_win_from(board, row, col, player):
            score = WIN_SCORE - sum(heights)
        else:
            score = -negamax(board, heights, depth - 1, -beta, -alpha, -player)

        heights[col] -= 1
        board[row][col] = 0

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def search_root(board, heights, depth, candidate_moves, preferred=None):
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = None

    allowed = set(candidate_moves)
    ordered = [c for c in ordered_moves(board, heights, 1, preferred) if c in allowed]

    if not ordered:
        ordered = list(candidate_moves)

    for col in ordered:
        row = ROWS - 1 - heights[col]
        board[row][col] = 1
        heights[col] += 1

        if is_win_from(board, row, col, 1):
            score = WIN_SCORE - sum(heights)
        else:
            score = -negamax(board, heights, depth - 1, -beta, -alpha, -1)

        heights[col] -= 1
        board[row][col] = 0

        if score > best_score:
            best_score = score
            best_move = col
        if score > alpha:
            alpha = score

    return best_score, best_move


def policy(board):
    grid = [row[:] for row in board]
    heights = [0] * COLS

    for c in range(COLS):
        h = 0
        for r in range(ROWS):
            if grid[r][c] != 0:
                h += 1
        heights[c] = h

    legal = legal_moves(heights)
    if not legal:
        return 0

    # Immediate win.
    my_wins = winning_moves(grid, heights, 1)
    if my_wins:
        return my_wins[0]

    # Root tactical safety:
    # prefer moves that do not allow an immediate opponent win next turn.
    safe_moves = []
    for col in legal:
        row = ROWS - 1 - heights[col]
        grid[row][col] = 1
        heights[col] += 1

        if is_win_from(grid, row, col, 1):
            heights[col] -= 1
            grid[row][col] = 0
            return col

        opp_after = winning_moves(grid, heights, -1)

        heights[col] -= 1
        grid[row][col] = 0

        if not opp_after:
            safe_moves.append(col)

    search_moves = safe_moves if safe_moves else legal

    if len(search_moves) == 1:
        return search_moves[0]

    global DEADLINE, NODES
    DEADLINE = time.perf_counter() + 0.92
    NODES = 0

    best_move = search_moves[0]

    # If opponent already has an immediate winning move now,
    # default to the most central legal move in case we timeout very early.
    opp_wins_now = winning_moves(grid, heights, -1)
    if opp_wins_now:
        for col in ORDER:
            if col in search_moves:
                best_move = col
                break

    try:
        preferred = best_move
        for depth in range(1, 11):
            score, move = search_root(grid, heights, depth, search_moves, preferred)
            if move is not None:
                best_move = move
                preferred = move
            if score >= WIN_SCORE // 2:
                break
    except SearchTimeout:
        pass

    if 0 <= best_move < COLS and heights[best_move] < ROWS:
        return best_move

    for col in ORDER:
        if heights[col] < ROWS:
            return col

    return 0
