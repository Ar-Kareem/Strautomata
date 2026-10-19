
import time
import math

ROWS = 6
COLS = 7
ORDER = [3, 2, 4, 1, 5, 0, 6]
INF = 10**9


def policy(board: list[list[int]]) -> int:
    start = time.time()
    limit = 0.92

    b = [row[:] for row in board]

    legal = [c for c in ORDER if b[0][c] == 0]
    if not legal:
        return 0

    def legal_moves():
        return [c for c in ORDER if b[0][c] == 0]

    def drop(col, player):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                b[r][col] = player
                return r
        return -1

    def undo(row, col):
        b[row][col] = 0

    def win_from(row, col, player):
        dirs = ((1, 0), (0, 1), (1, 1), (1, -1))
        for dr, dc in dirs:
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

    def is_full():
        return all(b[0][c] != 0 for c in range(COLS))

    def immediate_win(player):
        for c in legal_moves():
            r = drop(c, player)
            ok = win_from(r, c, player)
            undo(r, c)
            if ok:
                return c
        return None

    win_col = immediate_win(1)
    if win_col is not None:
        return win_col

    block_col = immediate_win(-1)
    if block_col is not None:
        return block_col

    def score_window(vals):
        own = vals.count(1)
        opp = vals.count(-1)
        emp = vals.count(0)

        if own and opp:
            return 0

        if own:
            if own == 4:
                return 100000
            if own == 3 and emp == 1:
                return 800
            if own == 2 and emp == 2:
                return 40
            if own == 1 and emp == 3:
                return 4

        if opp:
            if opp == 4:
                return -100000
            if opp == 3 and emp == 1:
                return -950
            if opp == 2 and emp == 2:
                return -50
            if opp == 1 and emp == 3:
                return -5

        return 0

    def evaluate():
        score = 0

        center_count = 0
        for r in range(ROWS):
            if b[r][3] == 1:
                center_count += 1
            elif b[r][3] == -1:
                center_count -= 1
        score += center_count * 18

        for r in range(ROWS):
            for c in range(COLS - 3):
                score += score_window([b[r][c], b[r][c + 1], b[r][c + 2], b[r][c + 3]])

        for c in range(COLS):
            for r in range(ROWS - 3):
                score += score_window([b[r][c], b[r + 1][c], b[r + 2][c], b[r + 3][c]])

        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += score_window([b[r][c], b[r + 1][c + 1], b[r + 2][c + 2], b[r + 3][c + 3]])

        for r in range(3, ROWS):
            for c in range(COLS - 3):
                score += score_window([b[r][c], b[r - 1][c + 1], b[r - 2][c + 2], b[r - 3][c + 3]])

        return score

    trans = {}

    def key(depth, player):
        return (depth, player, tuple(tuple(row) for row in b))

    class Timeout(Exception):
        pass

    def minimax(depth, alpha, beta, player, ply):
        if time.time() - start > limit:
            raise Timeout

        if depth == 0 or is_full():
            return evaluate()

        k = key(depth, player)
        if k in trans:
            return trans[k]

        moves = legal_moves()

        if player == 1:
            best = -INF
            for c in moves:
                r = drop(c, player)
                if win_from(r, c, player):
                    val = INF - ply
                else:
                    val = minimax(depth - 1, alpha, beta, -player, ply + 1)
                undo(r, c)

                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break

            trans[k] = best
            return best

        else:
            best = INF
            for c in moves:
                r = drop(c, player)
                if win_from(r, c, player):
                    val = -INF + ply
                else:
                    val = minimax(depth - 1, alpha, beta, -player, ply + 1)
                undo(r, c)

                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break

            trans[k] = best
            return best

    best_col = legal[0]
    best_score = -INF

    max_depth = 10

    try:
        for depth in range(1, max_depth + 1):
            current_best_col = best_col
            current_best_score = -INF

            for c in legal_moves():
                if time.time() - start > limit:
                    raise Timeout

                r = drop(c, 1)
                if win_from(r, c, 1):
                    val = INF
                else:
                    val = minimax(depth - 1, -INF, INF, -1, 1)
                undo(r, c)

                if val > current_best_score:
                    current_best_score = val
                    current_best_col = c

            best_col = current_best_col
            best_score = current_best_score

            if best_score >= INF // 2:
                break

    except Timeout:
        pass

    if 0 <= best_col < COLS and board[0][best_col] == 0:
        return best_col

    for c in ORDER:
        if board[0][c] == 0:
            return c

    return 0
