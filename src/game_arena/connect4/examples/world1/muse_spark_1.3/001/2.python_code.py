
import time

ORDER = [3, 2, 4, 1, 5, 0, 6]

WINDOWS = []
for _r in range(6):
    for _c in range(4):
        WINDOWS.append(((_r, _c), (_r, _c+1), (_r, _c+2), (_r, _c+3)))
for _r in range(3):
    for _c in range(7):
        WINDOWS.append(((_r, _c), (_r+1, _c), (_r+2, _c), (_r+3, _c)))
for _r in range(3):
    for _c in range(4):
        WINDOWS.append(((_r, _c), (_r+1, _c+1), (_r+2, _c+2), (_r+3, _c+3)))
for _r in range(3, 6):
    for _c in range(4):
        WINDOWS.append(((_r, _c), (_r-1, _c+1), (_r-2, _c+2), (_r-3, _c+3)))

INF = 10 ** 9
WIN_SCORE = 1000000

class _Timeout(Exception):
    pass

def _is_win(b, r, c, p):
    # horizontal
    cnt = 1
    cc = c - 1
    while cc >= 0 and b[r][cc] == p:
        cnt += 1
        cc -= 1
    cc = c + 1
    while cc < 7 and b[r][cc] == p:
        cnt += 1
        cc += 1
    if cnt >= 4:
        return True
    # vertical
    cnt = 1
    rr = r - 1
    while rr >= 0 and b[rr][c] == p:
        cnt += 1
        rr -= 1
    rr = r + 1
    while rr < 6 and b[rr][c] == p:
        cnt += 1
        rr += 1
    if cnt >= 4:
        return True
    # diag \
    cnt = 1
    rr, cc = r - 1, c - 1
    while rr >= 0 and cc >= 0 and b[rr][cc] == p:
        cnt += 1
        rr -= 1
        cc -= 1
    rr, cc = r + 1, c + 1
    while rr < 6 and cc < 7 and b[rr][cc] == p:
        cnt += 1
        rr += 1
        cc += 1
    if cnt >= 4:
        return True
    # diag /
    cnt = 1
    rr, cc = r - 1, c + 1
    while rr >= 0 and cc < 7 and b[rr][cc] == p:
        cnt += 1
        rr -= 1
        cc += 1
    rr, cc = r + 1, c - 1
    while rr < 6 and cc >= 0 and b[rr][cc] == p:
        cnt += 1
        rr += 1
        cc -= 1
    if cnt >= 4:
        return True
    return False

def _evaluate(b):
    score = 0
    # center column dominance
    score += (b[0][3] + b[1][3] + b[2][3] + b[3][3] + b[4][3] + b[5][3]) * 6
    # slight central preference
    score += (b[0][2] + b[1][2] + b[2][2] + b[3][2] + b[4][2] + b[5][2]) * 2
    score += (b[0][4] + b[1][4] + b[2][4] + b[3][4] + b[4][4] + b[5][4]) * 2
    for (r0, c0), (r1, c1), (r2, c2), (r3, c3) in WINDOWS:
        v0 = b[r0][c0]
        v1 = b[r1][c1]
        v2 = b[r2][c2]
        v3 = b[r3][c3]
        c1n = (v0 == 1) + (v1 == 1) + (v2 == 1) + (v3 == 1)
        cm = (v0 == -1) + (v1 == -1) + (v2 == -1) + (v3 == -1)
        if c1n and cm:
            continue
        if c1n:
            if c1n == 4:
                score += 100000
            elif c1n == 3:
                score += 100
            elif c1n == 2:
                score += 10
            else:
                score += 1
        elif cm:
            if cm == 4:
                score -= 100000
            elif cm == 3:
                score -= 120
            elif cm == 2:
                score -= 12
            elif cm == 1:
                score -= 1
    return score

def policy(board: list[list[int]]) -> int:
    try:
        b = [row[:] for row in board]
        nxt = [-1] * 7
        for c in range(7):
            for r in range(5, -1, -1):
                if b[r][c] == 0:
                    # lowest empty is first empty from bottom in legal position,
                    # but scan bottom-up to be safe: need bottom contiguous check
                    pass
            # compute lowest empty: largest r with 0 such that all below are non-zero
            # simple: find first occupied from top, go one up; or scan bottom up
            rr = 5
            while rr >= 0 and b[rr][c] != 0:
                rr -= 1
            nxt[c] = rr  # -1 if full else row index
        valid0 = [c for c in ORDER if nxt[c] >= 0]
        if not valid0:
            return 0
        if len(valid0) == 1:
            return valid0[0]

        empties = 0
        for c in range(7):
            if nxt[c] >= 0:
                empties += nxt[c] + 1
        played = 42 - empties
        if played == 0:
            return 3
        if played == 1 and nxt[3] >= 0:
            return 3

        # immediate win
        for c in valid0:
            r = nxt[c]
            b[r][c] = 1
            w = _is_win(b, r, c, 1)
            b[r][c] = 0
            if w:
                return c
        # immediate block (single or multiple -> must block one)
        opp_wins = []
        for c in valid0:
            r = nxt[c]
            b[r][c] = -1
            w = _is_win(b, r, c, -1)
            b[r][c] = 0
            if w:
                opp_wins.append(c)
        if len(opp_wins) == 1:
            return opp_wins[0]
        if len(opp_wins) > 1:
            # losing anyway, block one of them (prefer center)
            for c in valid0:
                if c in opp_wins:
                    return c

        start = time.perf_counter()
        deadline = start + 0.88

        nodes = [0]

        def check_timeout():
            if nodes[0] & 1023 == 0:
                if time.perf_counter() > deadline:
                    raise _Timeout()

        # alpha-beta, score from root (player 1) perspective
        # maximizing True means player 1 to move
        def alphabeta(depth, alpha, beta, maximizing):
            nodes[0] += 1
            check_timeout()
            # generate moves in ORDER
            if maximizing:
                best = -INF
                for c in ORDER:
                    r = nxt[c]
                    if r < 0:
                        continue
                    b[r][c] = 1
                    nxt[c] = r - 1
                    if _is_win(b, r, c, 1):
                        b[r][c] = 0
                        nxt[c] = r
                        return WIN_SCORE + depth
                    if depth <= 1:
                        s = _evaluate(b)
                    else:
                        s = alphabeta(depth - 1, alpha, beta, False)
                    b[r][c] = 0
                    nxt[c] = r
                    if s > best:
                        best = s
                    if s > alpha:
                        alpha = s
                    if alpha >= beta:
                        break
                # no move? draw
                if best == -INF:
                    return 0
                return best
            else:
                best = INF
                for c in ORDER:
                    r = nxt[c]
                    if r < 0:
                        continue
                    b[r][c] = -1
                    nxt[c] = r - 1
                    if _is_win(b, r, c, -1):
                        b[r][c] = 0
                        nxt[c] = r
                        return -WIN_SCORE - depth
                    if depth <= 1:
                        s = _evaluate(b)
                    else:
                        s = alphabeta(depth - 1, alpha, beta, True)
                    b[r][c] = 0
                    nxt[c] = r
                    if s < best:
                        best = s
                    if s < beta:
                        beta = s
                    if alpha >= beta:
                        break
                if best == INF:
                    return 0
                return best

        # iterative deepening at root with move ordering
        ordered = valid0[:]
        best_move = ordered[0]
        if empties <= 7:
            max_depth = empties
        elif empties <= 12:
            max_depth = 7
        else:
            max_depth = 6
        # try to go deeper if lots of time left (handled by loop)
        max_depth = max(max_depth, 4)
        if max_depth > 10:
            max_depth = 10

        try:
            for depth in range(1, max_depth + 1):
                alpha = -INF
                beta = INF
                cur_best = best_move
                cur_best_score = -INF
                # score each move
                scored = []
                for c in ordered:
                    r = nxt[c]
                    b[r][c] = 1
                    nxt[c] = r - 1
                    if _is_win(b, r, c, 1):
                        b[r][c] = 0
                        nxt[c] = r
                        return c
                    s = alphabeta(depth - 1, alpha, beta, False)
                    b[r][c] = 0
                    nxt[c] = r
                    scored.append((s, c))
                    if s > cur_best_score:
                        cur_best_score = s
                        cur_best = c
                    if s > alpha:
                        alpha = s
                    # timeout check at root
                    if time.perf_counter() > deadline:
                        raise _Timeout()
                # sort for next iteration (descending)
                scored.sort(reverse=True)
                ordered = [c for _, c in scored]
                best_move = cur_best
                # early exit on forced win / loss
                if cur_best_score >= WIN_SCORE:
                    break
                if time.perf_counter() > deadline:
                    break
                # if only little time left, stop
                # estimate: if depth >=4 and time used > 60%, stop to be safe
                # (iterative will otherwise timeout mid-next-depth and keep this best)
                elapsed = time.perf_counter() - start
                if depth >= 4 and elapsed > 0.55:
                    # allow one more depth only if very fast
                    if elapsed > 0.75:
                        break
        except _Timeout:
            pass

        if best_move < 0 or best_move > 6 or nxt[best_move] < 0:
            for c in ORDER:
                if nxt[c] >= 0:
                    return c
        return int(best_move)
    except Exception:
        try:
            for c in ORDER:
                if board[0][c] == 0:
                    # need to check full column: top cell empty means not full
                    return c
            for c in range(7):
                r = 5
                while r >= 0 and board[r][c] != 0:
                    r -= 1
                if r >= 0:
                    return c
        except Exception:
            pass
        return 3
