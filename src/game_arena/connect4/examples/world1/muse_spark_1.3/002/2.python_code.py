
import time

WIN_SCORE = 1000000
INF = 10**9

_WINDOWS = []
for _r in range(6):
    for _c in range(4):
        _WINDOWS.append((_r*7+_c, _r*7+_c+1, _r*7+_c+2, _r*7+_c+3))
for _r in range(3):
    for _c in range(7):
        _WINDOWS.append((_r*7+_c, (_r+1)*7+_c, (_r+2)*7+_c, (_r+3)*7+_c))
for _r in range(3):
    for _c in range(4):
        _WINDOWS.append((_r*7+_c, (_r+1)*7+_c+1, (_r+2)*7+_c+2, (_r+3)*7+_c+3))
for _r in range(3, 6):
    for _c in range(4):
        _WINDOWS.append((_r*7+_c, (_r-1)*7+_c+1, (_r-2)*7+_c+2, (_r-3)*7+_c+3))

_ORDER = (3, 2, 4, 1, 5, 0, 6)

class _Timeout(Exception):
    pass

def _is_win(b, r, c, p):
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        n = 1
        rr = r + dr
        cc = c + dc
        while 0 <= rr < 6 and 0 <= cc < 7 and b[rr * 7 + cc] == p:
            n += 1
            rr += dr
            cc += dc
        rr = r - dr
        cc = c - dc
        while 0 <= rr < 6 and 0 <= cc < 7 and b[rr * 7 + cc] == p:
            n += 1
            rr -= dr
            cc -= dc
        if n >= 4:
            return True
    return False

def _evaluate(b):
    score = (b[3] + b[10] + b[17] + b[24] + b[31] + b[38]) * 6
    for w0, w1, w2, w3 in _WINDOWS:
        c1 = (b[w0] == 1) + (b[w1] == 1) + (b[w2] == 1) + (b[w3] == 1)
        if c1 > 0:
            co = (b[w0] == -1) + (b[w1] == -1) + (b[w2] == -1) + (b[w3] == -1)
            if co > 0:
                continue
            if c1 == 3:
                score += 100
            elif c1 == 2:
                score += 10
            elif c1 == 1:
                score += 1
            else:
                score += 100000
        else:
            co = (b[w0] == -1) + (b[w1] == -1) + (b[w2] == -1) + (b[w3] == -1)
            if co == 3:
                score -= 120
            elif co == 2:
                score -= 12
            elif co == 1:
                score -= 1
            elif co == 4:
                score -= 100000
    return score

def policy(board: list[list[int]]) -> int:
    try:
        start = time.perf_counter()
        deadline = start + 0.90
        valid = [c for c in range(7) if board[0][c] == 0]
        if not valid:
            return 0
        if len(valid) == 1:
            return int(valid[0])
        valid_set = set(valid)
        ordered_valid = [c for c in _ORDER if c in valid_set]
        # flat board and next row
        b = [0] * 42
        for r in range(6):
            row = board[r]
            base = r * 7
            for c in range(7):
                b[base + c] = row[c]
        nxt = [-1] * 7
        for c in range(7):
            for r in range(5, -1, -1):
                if b[r * 7 + c] == 0:
                    nxt[c] = r
                    break
            else:
                nxt[c] = -1
        # immediate win
        for c in ordered_valid:
            r = nxt[c]
            b[r * 7 + c] = 1
            w = _is_win(b, r, c, 1)
            b[r * 7 + c] = 0
            if w:
                return int(c)
        # immediate block (single threat)
        threats = []
        for c in ordered_valid:
            r = nxt[c]
            b[r * 7 + c] = -1
            w = _is_win(b, r, c, -1)
            b[r * 7 + c] = 0
            if w:
                threats.append(c)
        if len(threats) == 1:
            return int(threats[0])
        # empty count
        empty = 0
        for c in range(7):
            if nxt[c] >= 0:
                empty += nxt[c] + 1
        if empty == 0:
            return int(ordered_valid[0])
        # pure opening: empty board -> center
        if empty == 42:
            return 3
        if empty <= 16:
            max_depth = empty
        else:
            max_depth = 7
        if max_depth < 1:
            max_depth = 1
        nodes = [0]
        # alpha-beta closure
        def alphabeta(depth, alpha, beta, maximizing):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
                raise _Timeout()
            if depth == 0:
                return _evaluate(b)
            if maximizing:
                value = -INF
                moved = False
                for c in _ORDER:
                    r = nxt[c]
                    if r < 0:
                        continue
                    moved = True
                    b[r * 7 + c] = 1
                    nxt[c] = r - 1
                    if _is_win(b, r, c, 1):
                        v = WIN_SCORE + depth
                    else:
                        # draw check: any move left?
                        full = True
                        for cc in range(7):
                            if nxt[cc] >= 0:
                                full = False
                                break
                        if full:
                            v = 0
                        else:
                            v = alphabeta(depth - 1, alpha, beta, False)
                    nxt[c] = r
                    b[r * 7 + c] = 0
                    if v > value:
                        value = v
                    if v > alpha:
                        alpha = v
                    if alpha >= beta:
                        break
                    if value >= WIN_SCORE - 10000:
                        break
                if not moved:
                    return 0
                return value
            else:
                value = INF
                moved = False
                for c in _ORDER:
                    r = nxt[c]
                    if r < 0:
                        continue
                    moved = True
                    b[r * 7 + c] = -1
                    nxt[c] = r - 1
                    if _is_win(b, r, c, -1):
                        v = -WIN_SCORE - depth
                    else:
                        full = True
                        for cc in range(7):
                            if nxt[cc] >= 0:
                                full = False
                                break
                        if full:
                            v = 0
                        else:
                            v = alphabeta(depth - 1, alpha, beta, True)
                    nxt[c] = r
                    b[r * 7 + c] = 0
                    if v < value:
                        value = v
                    if v < beta:
                        beta = v
                    if alpha >= beta:
                        break
                    if value <= -WIN_SCORE + 10000:
                        break
                if not moved:
                    return 0
                return value
        best_move = ordered_valid[0]
        if threats:
            # multiple threats: default to one of them if search fails
            best_move = threats[0]
        prev_scores = {}
        # iterative deepening
        for depth in range(1, max_depth + 1):
            try:
                if prev_scores:
                    ordered = sorted(ordered_valid, key=lambda x: prev_scores.get(x, -INF), reverse=True)
                else:
                    ordered = ordered_valid
                cur_scores = {}
                alpha = -INF
                best_this = ordered[0]
                for c in ordered:
                    if time.perf_counter() > deadline:
                        raise _Timeout()
                    r = nxt[c]
                    b[r * 7 + c] = 1
                    nxt[c] = r - 1
                    if _is_win(b, r, c, 1):
                        v = WIN_SCORE + depth
                    else:
                        full = True
                        for cc in range(7):
                            if nxt[cc] >= 0:
                                full = False
                                break
                        if full:
                            v = 0
                        else:
                            v = alphabeta(depth - 1, alpha, INF, False)
                    nxt[c] = r
                    b[r * 7 + c] = 0
                    cur_scores[c] = v
                    if v > alpha:
                        alpha = v
                        best_this = c
                    if v >= WIN_SCORE - 10000:
                        best_this = c
                        break
                prev_scores = cur_scores
                best_move = best_this
                if alpha >= WIN_SCORE - 10000:
                    break
                if time.perf_counter() > deadline:
                    break
                # if depth reached and time low, stop
                if depth >= 4 and time.perf_counter() > deadline - 0.05:
                    break
            except _Timeout:
                break
        if best_move not in valid_set:
            return int(ordered_valid[0])
        return int(best_move)
    except Exception:
        try:
            for c in (3, 2, 4, 1, 5, 0, 6):
                if board[0][c] == 0:
                    return int(c)
            for c in range(7):
                if board[0][c] == 0:
                    return int(c)
        except Exception:
            pass
        return 0
