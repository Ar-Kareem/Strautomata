
import time

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN_SCORE = 1000000
INF = 10 ** 9

# precompute all 4-windows
WINDOWS = []
for r in range(ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r, c+1), (r, c+2), (r, c+3)))
for r in range(ROWS - 3):
    for c in range(COLS):
        WINDOWS.append(((r, c), (r+1, c), (r+2, c), (r+3, c)))
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)))
for r in range(3, ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)))

class _Timeout(Exception):
    pass

def _heights(board):
    h = [0]*COLS
    for c in range(COLS):
        if board[0][c] != 0:
            h[c] = -1
        else:
            # lowest empty
            r = 5
            while r >= 0 and board[r][c] != 0:
                r -= 1
            h[c] = r
    return h

def _legal_moves(heights):
    return [c for c in CENTER_ORDER if heights[c] != -1]

def _is_win(board, r, c):
    p = board[r][c]
    # horizontal
    cnt = 0
    cc = c - 3
    if cc < 0:
        cc = 0
    end = c + 3
    if end > 6:
        end = 6
    for cj in range(cc, end+1):
        if board[r][cj] == p:
            cnt += 1
            if cnt == 4:
                return True
        else:
            cnt = 0
    # vertical
    cnt = 0
    for ri in range(max(0, r-3), min(6, r+3)+1):
        if board[ri][c] == p:
            cnt += 1
            if cnt == 4:
                return True
        else:
            cnt = 0
    # diag \
    cnt = 0
    rr = r - 3
    cc2 = c - 3
    for _ in range(7):
        if 0 <= rr < 6 and 0 <= cc2 < 7:
            if board[rr][cc2] == p:
                cnt += 1
                if cnt == 4:
                    return True
            else:
                cnt = 0
        else:
            cnt = 0
        rr += 1
        cc2 += 1
        if rr > r+3:
            break
    # diag /
    cnt = 0
    rr = r + 3
    cc2 = c - 3
    for _ in range(7):
        if 0 <= rr < 6 and 0 <= cc2 < 7:
            if board[rr][cc2] == p:
                cnt += 1
                if cnt == 4:
                    return True
            else:
                cnt = 0
        else:
            cnt = 0
        rr -= 1
        cc2 += 1
        if cc2 > c+3:
            break
    return False

def _evaluate(board):
    score = 0
    # center preference
    if board[5][3] == 1:
        score += 3
    elif board[5][3] == -1:
        score -= 3
    if board[4][3] == 1:
        score += 3
    elif board[4][3] == -1:
        score -= 3
    if board[3][3] == 1:
        score += 3
    elif board[3][3] == -1:
        score -= 3
    if board[2][3] == 1:
        score += 2
    elif board[2][3] == -1:
        score -= 2
    if board[1][3] == 1:
        score += 2
    elif board[1][3] == -1:
        score -= 2
    if board[0][3] == 1:
        score += 2
    elif board[0][3] == -1:
        score -= 2
    # extra center column count
    # windows
    for w in WINDOWS:
        a = board[w[0][0]][w[0][1]]
        b = board[w[1][0]][w[1][1]]
        c_ = board[w[2][0]][w[2][1]]
        d = board[w[3][0]][w[3][1]]
        # fast count
        cnt1 = (a == 1) + (b == 1) + (c_ == 1) + (d == 1)
        if cnt1 > 0:
            cnto = (a == -1) + (b == -1) + (c_ == -1) + (d == -1)
            if cnto > 0:
                continue
            # only mine + empty
            if cnt1 == 4:
                score += 100000
            elif cnt1 == 3:
                score += 500
            elif cnt1 == 2:
                score += 10
            else:
                score += 1
        else:
            cnto = (a == -1) + (b == -1) + (c_ == -1) + (d == -1)
            if cnto == 0:
                continue
            if cnto == 4:
                score -= 100000
            elif cnto == 3:
                score -= 800
            elif cnto == 2:
                score -= 12
            else:
                score -= 1
    return score

def policy(board: list[list[int]]) -> int:
    try:
        start = time.perf_counter()
        deadline = start + 0.85
        # copy board to avoid mutating caller
        b = [row[:] for row in board]
        heights = _heights(b)
        legal = _legal_moves(heights)
        if not legal:
            return 0
        if len(legal) == 1:
            return legal[0]
        # immediate win
        for c in legal:
            r = heights[c]
            b[r][c] = 1
            w = _is_win(b, r, c)
            b[r][c] = 0
            if w:
                return c
        # immediate block (opponent win)
        opp_wins = []
        for c in legal:
            r = heights[c]
            b[r][c] = -1
            w = _is_win(b, r, c)
            b[r][c] = 0
            if w:
                opp_wins.append(c)
        if len(opp_wins) == 1:
            return opp_wins[0]
        if len(opp_wins) > 1:
            # must block one, prefer center-most winning block
            return opp_wins[0]

        n_empty = 0
        for r in range(6):
            for c in range(7):
                if b[r][c] == 0:
                    n_empty += 1
        if n_empty > 30:
            max_depth = 4
        elif n_empty > 20:
            max_depth = 5
        elif n_empty > 10:
            max_depth = 6
        else:
            max_depth = 8

        # fast opening: empty board
        if n_empty == 42:
            return 3

        nodes = [0]

        def check_time():
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
                raise _Timeout()

        def negamax(depth, alpha, beta, player):
            check_time()
            if depth == 0:
                return player * _evaluate(b)
            # generate moves center ordered
            # build list quickly
            best = -INF
            # iterate center order filtered
            for c in CENTER_ORDER:
                h = heights[c]
                if h == -1:
                    continue
                b[h][c] = player
                heights[c] = h - 1 if h - 1 >= 0 and b[h-1][c] == 0 else (-1 if h == 0 or b[0][c] != 0 else h-1)
                # recompute correctly: if column now full heights=-1 else h-1
                # fix: check top
                if b[0][c] != 0:
                    heights[c] = -1
                else:
                    # h-1 is next empty because no gaps
                    heights[c] = h - 1
                if _is_win(b, h, c):
                    score = WIN_SCORE + depth
                else:
                    # draw check: any move left?
                    any_left = False
                    for cc in range(7):
                        if heights[cc] != -1:
                            any_left = True
                            break
                    if not any_left:
                        score = 0
                    else:
                        score = -negamax(depth-1, -beta, -alpha, -player)
                # undo
                b[h][c] = 0
                heights[c] = h
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

        ordered = legal[:]  # already center ordered
        best_move = ordered[0]
        prev_scores = {}
        try:
            for depth in range(1, max_depth+1):
                # order by previous scores
                if prev_scores:
                    ordered = sorted(ordered, key=lambda x: prev_scores.get(x, 0), reverse=True)
                alpha = -INF
                best_this = ordered[0]
                best_score_this = -INF
                for c in ordered:
                    check_time()
                    r = heights[c]
                    b[r][c] = 1
                    if b[0][c] != 0:
                        nh = -1
                    else:
                        nh = r - 1
                    old_h = heights[c]
                    heights[c] = nh
                    if _is_win(b, r, c):
                        score = WIN_SCORE + depth
                    else:
                        if depth == 1:
                            score = _evaluate(b)
                        else:
                            score = -negamax(depth-1, -INF, -alpha if alpha != -INF else INF, -1)
                    b[r][c] = 0
                    heights[c] = old_h
                    prev_scores[c] = score
                    if score > best_score_this:
                        best_score_this = score
                        best_this = c
                    if score > alpha:
                        alpha = score
                    if time.perf_counter() > deadline:
                        raise _Timeout()
                best_move = best_this
                if best_score_this >= WIN_SCORE - 10000:
                    break
                if time.perf_counter() > deadline - 0.05:
                    break
        except _Timeout:
            pass
        # safety
        if best_move not in legal:
            return legal[0]
        return best_move
    except Exception:
        try:
            for c in CENTER_ORDER:
                if board[0][c] == 0:
                    return c
        except Exception:
            pass
        return 0
