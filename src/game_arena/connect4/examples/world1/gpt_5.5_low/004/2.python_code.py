
import time
import math

ROWS = 6
COLS = 7
WIN_SCORE = 10_000_000
ORDER = [3, 2, 4, 1, 5, 0, 6]


def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    time_limit = 0.92

    b = [row[:] for row in board]

    def legal_moves():
        return [c for c in ORDER if b[0][c] == 0]

    def get_row(col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return -1

    def make_move(col, player):
        r = get_row(col)
        if r >= 0:
            b[r][col] = player
        return r

    def undo_move(row, col):
        b[row][col] = 0

    def is_win_from(row, col, player):
        if row < 0:
            return False

        directions = ((1, 0), (0, 1), (1, 1), (1, -1))

        for dr, dc in directions:
            count = 1

            rr, cc = row + dr, col + dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                count += 1
                rr += dr
                cc += dc

            rr, cc = row - dr, col - dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                count += 1
                rr -= dr
                cc -= dc

            if count >= 4:
                return True

        return False

    def window_score(vals):
        mine = vals.count(1)
        opp = vals.count(-1)
        empty = vals.count(0)

        if mine and opp:
            return 0

        if mine == 4:
            return 100000
        if opp == 4:
            return -100000

        score = 0

        if mine == 3 and empty == 1:
            score += 160
        elif mine == 2 and empty == 2:
            score += 18
        elif mine == 1 and empty == 3:
            score += 2

        if opp == 3 and empty == 1:
            score -= 190
        elif opp == 2 and empty == 2:
            score -= 22
        elif opp == 1 and empty == 3:
            score -= 2

        return score

    def evaluate():
        score = 0

        # Center control is very important in Connect 4.
        center_count = 0
        for r in range(ROWS):
            if b[r][3] == 1:
                center_count += 1
            elif b[r][3] == -1:
                center_count -= 1
        score += center_count * 9

        # Slight preference for near-center columns.
        weights = [3, 4, 5, 7, 5, 4, 3]
        for r in range(ROWS):
            for c in range(COLS):
                score += b[r][c] * weights[c]

        # Horizontal windows.
        for r in range(ROWS):
            for c in range(COLS - 3):
                score += window_score([b[r][c], b[r][c + 1], b[r][c + 2], b[r][c + 3]])

        # Vertical windows.
        for c in range(COLS):
            for r in range(ROWS - 3):
                score += window_score([b[r][c], b[r + 1][c], b[r + 2][c], b[r + 3][c]])

        # Positive diagonals.
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += window_score([b[r][c], b[r + 1][c + 1], b[r + 2][c + 2], b[r + 3][c + 3]])

        # Negative diagonals.
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                score += window_score([b[r][c], b[r - 1][c + 1], b[r - 2][c + 2], b[r - 3][c + 3]])

        return score

    def ordered_moves(player):
        moves = legal_moves()
        scored = []

        for c in moves:
            r = make_move(c, player)
            if is_win_from(r, c, player):
                s = WIN_SCORE
            else:
                # Prefer center and moves that improve static evaluation.
                s = evaluate() if player == 1 else -evaluate()
                s += 10 - abs(3 - c)
            undo_move(r, c)
            scored.append((s, c))

        scored.sort(reverse=True)
        return [c for _, c in scored]

    def alphabeta(depth, alpha, beta, player, ply):
        if time.time() - start_time > time_limit:
            raise TimeoutError

        moves = legal_moves()

        if depth == 0 or not moves:
            return evaluate()

        if player == 1:
            value = -math.inf

            for c in ordered_moves(player):
                r = make_move(c, player)

                if is_win_from(r, c, player):
                    score = WIN_SCORE - ply
                else:
                    score = alphabeta(depth - 1, alpha, beta, -player, ply + 1)

                undo_move(r, c)

                if score > value:
                    value = score
                alpha = max(alpha, value)
                if alpha >= beta:
                    break

            return value

        else:
            value = math.inf

            for c in ordered_moves(player):
                r = make_move(c, player)

                if is_win_from(r, c, player):
                    score = -WIN_SCORE + ply
                else:
                    score = alphabeta(depth - 1, alpha, beta, -player, ply + 1)

                undo_move(r, c)

                if score < value:
                    value = score
                beta = min(beta, value)
                if alpha >= beta:
                    break

            return value

    moves = legal_moves()

    if not moves:
        return 0

    # 1. Take an immediate win.
    for c in moves:
        r = make_move(c, 1)
        win = is_win_from(r, c, 1)
        undo_move(r, c)
        if win:
            return c

    # 2. Block an immediate opponent win.
    opponent_wins = []
    for c in moves:
        r = make_move(c, -1)
        win = is_win_from(r, c, -1)
        undo_move(r, c)
        if win:
            opponent_wins.append(c)

    if len(opponent_wins) == 1:
        return opponent_wins[0]

    # If opponent has multiple immediate wins, choose one legal blocker if possible.
    if len(opponent_wins) > 1:
        return opponent_wins[0]

    # Fallback move: center-first.
    best_move = moves[0]
    best_score = -math.inf

    # Dynamic search depth. Early/midgame can usually handle depth 6-7 in time.
    empties = sum(1 for r in range(ROWS) for c in range(COLS) if b[r][c] == 0)

    if empties >= 34:
        max_depth = 6
    elif empties >= 22:
        max_depth = 7
    elif empties >= 12:
        max_depth = 8
    else:
        max_depth = 10

    try:
        for depth in range(1, max_depth + 1):
            current_best_move = best_move
            current_best_score = -math.inf

            for c in ordered_moves(1):
                if time.time() - start_time > time_limit:
                    raise TimeoutError

                r = make_move(c, 1)

                if is_win_from(r, c, 1):
                    score = WIN_SCORE
                else:
                    score = alphabeta(depth - 1, -math.inf, math.inf, -1, 1)

                undo_move(r, c)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = c

            best_move = current_best_move
            best_score = current_best_score

    except TimeoutError:
        pass

    if best_move in moves:
        return best_move

    return moves[0]
