
import time

ROWS = 6
COLS = 7
ORDER = (3, 2, 4, 1, 5, 0, 6)
WIN_SCORE = 1_000_000
INF = 10**18

POS_WEIGHTS = (
    (3, 4, 5, 7, 5, 4, 3),
    (4, 6, 8, 10, 8, 6, 4),
    (5, 8, 11, 13, 11, 8, 5),
    (5, 8, 11, 13, 11, 8, 5),
    (4, 6, 8, 10, 8, 6, 4),
    (3, 4, 5, 7, 5, 4, 3),
)

LINES = []
for r in range(ROWS):
    for c in range(COLS - 3):
        LINES.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
for r in range(ROWS - 3):
    for c in range(COLS):
        LINES.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        LINES.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))
for r in range(3, ROWS):
    for c in range(COLS - 3):
        LINES.append(((r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)))
LINES = tuple(LINES)


class _Timeout(Exception):
    pass


def _build_heights(board):
    heights = [-1] * COLS
    for c in range(COLS):
        for r in range(ROWS - 1, -1, -1):
            if board[r][c] == 0:
                heights[c] = r
                break
    return heights


def _is_winning_move(board, row, col, player):
    def count(dr, dc):
        rr, cc = row + dr, col + dc
        n = 0
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            n += 1
            rr += dr
            cc += dc
        return n

    if 1 + count(0, 1) + count(0, -1) >= 4:
        return True
    if 1 + count(1, 0) + count(-1, 0) >= 4:
        return True
    if 1 + count(1, 1) + count(-1, -1) >= 4:
        return True
    if 1 + count(1, -1) + count(-1, 1) >= 4:
        return True
    return False


def _has_immediate_win(board, heights, player):
    for c in ORDER:
        r = heights[c]
        if r < 0:
            continue
        board[r][c] = player
        heights[c] = r - 1
        won = _is_winning_move(board, r, c, player)
        board[r][c] = 0
        heights[c] = r
        if won:
            return True
    return False


def _immediate_wins(board, heights, player):
    wins = []
    for c in ORDER:
        r = heights[c]
        if r < 0:
            continue
        board[r][c] = player
        heights[c] = r - 1
        won = _is_winning_move(board, r, c, player)
        board[r][c] = 0
        heights[c] = r
        if won:
            wins.append(c)
    return wins


def _evaluate_absolute(board, heights):
    score = 0

    for r in range(ROWS):
        br = board[r]
        wr = POS_WEIGHTS[r]
        for c in range(COLS):
            score += br[c] * wr[c]

    for line in LINES:
        p1 = 0
        p2 = 0
        er = ec = -1

        for r, c in line:
            v = board[r][c]
            if v == 1:
                p1 += 1
            elif v == -1:
                p2 += 1
            else:
                er, ec = r, c

        if p1 and p2:
            continue

        if p1 == 4:
            score += 100000
        elif p2 == 4:
            score -= 100000
        elif p1 == 3:
            score += 90 if heights[ec] == er else 30
        elif p2 == 3:
            score -= 100 if heights[ec] == er else 35
        elif p1 == 2 and p2 == 0:
            score += 8
        elif p2 == 2 and p1 == 0:
            score -= 9
        elif p1 == 1 and p2 == 0:
            score += 1
        elif p2 == 1 and p1 == 0:
            score -= 1

    return score


def policy(board: list[list[int]]) -> int:
    legal = [c for c in ORDER if board[0][c] == 0]
    if not legal:
        return 0

    try:
        b = [row[:] for row in board]
        heights = _build_heights(b)

        empty_count = sum(1 for r in range(ROWS) for c in range(COLS) if b[r][c] == 0)
        if empty_count == ROWS * COLS:
            return 3

        # Immediate win
        for c in legal:
            r = heights[c]
            b[r][c] = 1
            heights[c] = r - 1
            won = _is_winning_move(b, r, c, 1)
            b[r][c] = 0
            heights[c] = r
            if won:
                return c

        # Immediate block if exactly one exists
        opp_wins = _immediate_wins(b, heights, -1)
        if len(opp_wins) == 1:
            return opp_wins[0]

        # Safe move filter: avoid moves that allow an immediate opponent win
        safe_moves = []
        for c in legal:
            r = heights[c]
            b[r][c] = 1
            heights[c] = r - 1
            if not _has_immediate_win(b, heights, -1):
                safe_moves.append(c)
            b[r][c] = 0
            heights[c] = r

        candidates = safe_moves if safe_moves else legal
        if len(candidates) == 1:
            return candidates[0]

        if empty_count >= 30:
            max_depth = 6
        elif empty_count >= 18:
            max_depth = 7
        else:
            max_depth = 8

        start = time.perf_counter()
        time_limit = 0.92
        nodes = 0

        def negamax(depth, alpha, beta, player):
            nonlocal nodes
            nodes += 1
            if (nodes & 511) == 0 and time.perf_counter() - start > time_limit:
                raise _Timeout

            moved = False
            if depth == 0:
                return player * _evaluate_absolute(b, heights)

            best = -INF

            for c in ORDER:
                r = heights[c]
                if r < 0:
                    continue
                moved = True

                b[r][c] = player
                heights[c] = r - 1

                if _is_winning_move(b, r, c, player):
                    score = WIN_SCORE + depth
                elif _has_immediate_win(b, heights, -player):
                    score = -WIN_SCORE - depth
                else:
                    score = -negamax(depth - 1, -beta, -alpha, -player)

                b[r][c] = 0
                heights[c] = r

                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break

            if not moved:
                return 0
            return best

        best_move = candidates[0]
        best_score = -INF

        for depth in range(2, max_depth + 1):
            if time.perf_counter() - start > time_limit:
                break

            try:
                current_best_move = best_move
                current_best_score = -INF
                alpha = -INF
                beta = INF

                ordered_moves = [best_move] + [c for c in candidates if c != best_move]

                for c in ordered_moves:
                    if time.perf_counter() - start > time_limit:
                        raise _Timeout

                    r = heights[c]
                    b[r][c] = 1
                    heights[c] = r - 1

                    if _is_winning_move(b, r, c, 1):
                        score = WIN_SCORE + depth
                    elif _has_immediate_win(b, heights, -1):
                        score = -WIN_SCORE - depth
                    else:
                        score = -negamax(depth - 1, -beta, -alpha, -1)

                    b[r][c] = 0
                    heights[c] = r

                    if score > current_best_score:
                        current_best_score = score
                        current_best_move = c
                    if score > alpha:
                        alpha = score

                best_move = current_best_move
                best_score = current_best_score

                if best_score >= WIN_SCORE // 2:
                    break

            except _Timeout:
                break

        return best_move if best_move in legal else legal[0]

    except Exception:
        return legal[0]
