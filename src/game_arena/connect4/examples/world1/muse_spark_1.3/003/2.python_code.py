
import time

# Precompute all 69 windows as (r0,c0,r1,c1,r2,c2,r3,c3)
WINDOWS = []
for r in range(6):
    for c in range(4):
        WINDOWS.append((r, c, r, c+1, r, c+2, r, c+3))
for r in range(3):
    for c in range(7):
        WINDOWS.append((r, c, r+1, c, r+2, c, r+3, c))
for r in range(3):
    for c in range(4):
        WINDOWS.append((r, c, r+1, c+1, r+2, c+2, r+3, c+3))
for r in range(3, 6):
    for c in range(4):
        WINDOWS.append((r, c, r-1, c+1, r-2, c+2, r-3, c+3))

ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN_SCORE = 1000000

def _check_win(b, r, c, p):
    # count in 4 directions through (r,c)
    cnt = 0
    # horizontal
    cc = c - 1
    n = 0
    while cc >= 0 and b[r][cc] == p:
        n += 1
        cc -= 1
    cc = c + 1
    while cc < 7 and b[r][cc] == p:
        n += 1
        cc += 1
    if n >= 3:
        return True
    # vertical
    n = 0
    rr = r - 1
    while rr >= 0 and b[rr][c] == p:
        n += 1
        rr -= 1
    rr = r + 1
    while rr < 6 and b[rr][c] == p:
        n += 1
        rr += 1
    if n >= 3:
        return True
    # diag \
    n = 0
    rr, cc = r - 1, c - 1
    while rr >= 0 and cc >= 0 and b[rr][cc] == p:
        n += 1
        rr -= 1
        cc -= 1
    rr, cc = r + 1, c + 1
    while rr < 6 and cc < 7 and b[rr][cc] == p:
        n += 1
        rr += 1
        cc += 1
    if n >= 3:
        return True
    # diag /
    n = 0
    rr, cc = r + 1, c - 1
    while rr < 6 and cc >= 0 and b[rr][cc] == p:
        n += 1
        rr += 1
        cc -= 1
    rr, cc = r - 1, c + 1
    while rr >= 0 and cc < 7 and b[rr][cc] == p:
        n += 1
        rr -= 1
        cc += 1
    if n >= 3:
        return True
    return False

def _eval_base(b):
    # score from perspective of player 1
    s = 0
    # center control
    c0 = b[0][3] + b[1][3] + b[2][3] + b[3][3] + b[4][3] + b[5][3]
    s += c0 * 6
    for w in WINDOWS:
        r0, c00, r1, c11, r2, c22, r3, c33 = w
        v0 = b[r0][c00]
        v1 = b[r1][c11]
        v2 = b[r2][c22]
        v3 = b[r3][c33]
        cnt1 = (v0 == 1) + (v1 == 1) + (v2 == 1) + (v3 == 1)
        if cnt1:
            cntm = (v0 == -1) + (v1 == -1) + (v2 == -1) + (v3 == -1)
            if cntm:
                continue
            if cnt1 == 3:
                s += 100
            elif cnt1 == 2:
                s += 10
            else:
                s += 1
        else:
            cntm = (v0 == -1) + (v1 == -1) + (v2 == -1) + (v3 == -1)
            if cntm == 0:
                continue
            if cntm == 3:
                s -= 120
            elif cntm == 2:
                s -= 12
            else:
                s -= 1
    return s

class _Timeout(Exception):
    pass

def policy(board: list[list[int]]) -> int:
    try:
        t0 = time.perf_counter()
        limit = 0.90
        # heights
        heights = [0]*7
        empties = 0
        for c in range(7):
            h = 0
            # count from bottom
            if board[5][c] != 0:
                # contiguous under gravity
                for r in range(5, -1, -1):
                    if board[r][c] != 0:
                        h += 1
                    else:
                        break
            heights[c] = h
            if h < 6:
                empties += (6 - h)
        valid = [c for c in range(7) if heights[c] < 6]
        if len(valid) == 1:
            return valid[0]
        # order central
        valid_sorted = sorted(valid, key=lambda x: abs(x-3))
        # immediate win for us
        for c in valid_sorted:
            r = 5 - heights[c]
            board[r][c] = 1
            w = _check_win(board, r, c, 1)
            board[r][c] = 0
            if w:
                return c
        # immediate block opponent win
        opp_win = []
        for c in valid_sorted:
            r = 5 - heights[c]
            board[r][c] = -1
            w = _check_win(board, r, c, -1)
            board[r][c] = 0
            if w:
                opp_win.append(c)
        if len(opp_win) == 1:
            return opp_win[0]
        if len(opp_win) > 1:
            # double threat: must play one of them, let search decide but restrict?
            # fall through to search
            pass
        if empties == 42:
            return 3

        b = board
        hts = heights
        nodes = [0]
        WIN = WIN_SCORE

        def negamax(depth, alpha, beta, player):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0:
                if time.perf_counter() - t0 > limit:
                    raise _Timeout()
            # generate moves in center order
            # build list quickly
            if depth == 0:
                base = _eval_base(b)
                return base if player == 1 else -base
            best = -WIN*2
            # move ordering: center first
            for c in ORDER:
                if hts[c] >= 6:
                    continue
                r = 5 - hts[c]
                b[r][c] = player
                hts[c] += 1
                if _check_win(b, r, c, player):
                    b[r][c] = 0
                    hts[c] -= 1
                    return WIN + depth  # prefer faster win (higher depth remaining)
                # draw check handled by no moves at next level
                # quick draw: if no empties left
                val = None
                # if board full after this move -> draw
                # check if any move left
                full = True
                for cc in range(7):
                    if hts[cc] < 6:
                        full = False
                        break
                if full:
                    base = _eval_base(b)
                    # value from perspective of player after move? draw ~0 but compute eval
                    # negamax returns value for player, next player would be -player with no moves
                    # so value = eval for player
                    ev = base if player == 1 else -base
                    val = ev
                else:
                    val = -negamax(depth-1, -beta, -alpha, -player)
                b[r][c] = 0
                hts[c] -= 1
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            # if best still -inf (no moves) -> draw
            if best == -WIN*2:
                base = _eval_base(b)
                return base if player == 1 else -base
            return best

        # iterative deepening
        best_move = valid_sorted[0]
        # root ordering
        root_order = valid_sorted[:]
        # max depth heuristic
        if empties > 25:
            max_depth = 6
        elif empties > 15:
            max_depth = 7
        elif empties > 10:
            max_depth = 9
        else:
            max_depth = empties  # solve endgame

        # cap max_depth to avoid explosion early
        max_depth = min(max_depth, 12)

        for depth in range(1, max_depth+1):
            if time.perf_counter() - t0 > limit - 0.05:
                break
            try:
                alpha = -WIN*2
                beta = WIN*2
                cur_best = root_order[0]
                cur_best_val = -WIN*2
                # score each root move to allow reordering
                scored = []
                for c in root_order:
                    if time.perf_counter() - t0 > limit:
                        raise _Timeout()
                    r = 5 - hts[c]
                    b[r][c] = 1
                    hts[c] += 1
                    if _check_win(b, r, c, 1):
                        b[r][c] = 0
                        hts[c] -= 1
                        return c
                    v = -negamax(depth-1, -beta, -alpha, -1)
                    b[r][c] = 0
                    hts[c] -= 1
                    scored.append((v, c))
                    if v > cur_best_val:
                        cur_best_val = v
                        cur_best = c
                    if v > alpha:
                        alpha = v
                # reorder for next iteration (best first)
                scored.sort(reverse=True, key=lambda x: x[0])
                root_order = [c for _, c in scored]
                best_move = cur_best
                # if winning line found, stop
                if cur_best_val > WIN - 50:
                    break
                # if time low, stop
                if time.perf_counter() - t0 > limit - 0.15:
                    break
            except _Timeout:
                break
        # ensure legal
        if best_move in valid:
            return best_move
        return valid_sorted[0]
    except Exception:
        # fallback: first legal center-first
        try:
            for c in ORDER:
                if board[0][c] == 0:
                    return c
            for c in range(7):
                if board[0][c] == 0:
                    return c
        except Exception:
            pass
        return 3
