
HISTORY = set()
PREV_TOTAL = -1

DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
DIAG = [(1,1),(1,-1),(-1,1),(-1,-1)]

def _in(r,c):
    return 0 <= r < 19 and 0 <= c < 19

def _group(board, r, c):
    color = board[r][c]
    stack = [(r,c)]
    visited = set()
    visited.add((r,c))
    stones = []
    libs = set()
    while stack:
        cr, cc = stack.pop()
        stones.append((cr,cc))
        for dr, dc in DIRS:
            nr, nc = cr+dr, cc+dc
            if not _in(nr,nc):
                continue
            v = board[nr][nc]
            if v == 0:
                libs.add((nr,nc))
            elif v == color and (nr,nc) not in visited:
                visited.add((nr,nc))
                stack.append((nr,nc))
    return stones, libs

def _try_move(board, color, r, c):
    if not _in(r,c):
        return None, 0, False
    if board[r][c] != 0:
        return None, 0, False
    nb = [row[:] for row in board]
    nb[r][c] = color
    opp = 3 - color
    captured = 0
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        if _in(nr,nc) and nb[nr][nc] == opp:
            stones, libs = _group(nb, nr, nc)
            if len(libs) == 0:
                for sr, sc in stones:
                    nb[sr][sc] = 0
                captured += len(stones)
    _, mylibs = _group(nb, r, c)
    if len(mylibs) == 0:
        return None, 0, False
    return nb, captured, True

def _is_eye(board, r, c, color):
    opp = 3 - color
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        if _in(nr,nc):
            if board[nr][nc] != color:
                return False
        else:
            pass
    for dr, dc in DIAG:
        nr, nc = r+dr, c+dc
        if _in(nr,nc):
            if board[nr][nc] == opp:
                return False
    return True

def _board_hash(board):
    return tuple(tuple(row) for row in board)

def _find_atari(board, color):
    visited = [[False]*19 for _ in range(19)]
    res = []
    for r in range(19):
        for c in range(19):
            if board[r][c] == color and not visited[r][c]:
                stones, libs = _group(board, r, c)
                for sr, sc in stones:
                    visited[sr][sc] = True
                if len(libs) == 1:
                    res.append((stones, libs))
    return res

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    global HISTORY, PREV_TOTAL
    try:
        me_set = set()
        opp_set = set()
        board = [[0]*19 for _ in range(19)]
        try:
            for rc in me:
                r, c = rc
                if 1 <= r <= 19 and 1 <= c <= 19:
                    board[r-1][c-1] = 1
                    me_set.add((r,c))
            for rc in opponent:
                r, c = rc
                if 1 <= r <= 19 and 1 <= c <= 19:
                    if board[r-1][c-1] == 0:
                        board[r-1][c-1] = 2
                        opp_set.add((r,c))
                    else:
                        # overlap, keep mine
                        pass
        except Exception:
            pass

        total = len(me_set) + len(opp_set)
        # detect new game
        if total == 0 or total < PREV_TOTAL - 5 or PREV_TOTAL == -1 and total <= 4:
            HISTORY = set()
        PREV_TOTAL = total

        def first_empty():
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in me_set and (r,c) not in opp_set:
                        return (r,c)
            return (0,0)

        # 1. immediate capture: opponent in atari
        opp_atari = _find_atari(board, 2)
        if opp_atari:
            best = None
            best_score = -10**9
            for stones, libs in opp_atari:
                lr, lc = next(iter(libs))
                nb, cap, legal = _try_move(board, 1, lr, lc)
                if not legal:
                    continue
                h = _board_hash(nb)
                if h in HISTORY:
                    continue
                _, mylibs = _group(nb, lr, lc)
                score = cap*1000 + len(mylibs)*10 + len(stones)
                if score > best_score:
                    best_score = score
                    best = (lr, lc, nb, h)
            if best is not None:
                HISTORY.add(best[3])
                return (best[0]+1, best[1]+1)

        # 2. save own atari
        my_atari = _find_atari(board, 1)
        if my_atari:
            # save largest first
            my_atari_sorted = sorted(my_atari, key=lambda x: len(x[0]), reverse=True)
            for stones, libs in my_atari_sorted:
                lr, lc = next(iter(libs))
                nb, cap, legal = _try_move(board, 1, lr, lc)
                if not legal:
                    continue
                h = _board_hash(nb)
                if h in HISTORY:
                    continue
                _, mylibs = _group(nb, lr, lc)
                if len(mylibs) > 1 or cap > 0:
                    HISTORY.add(h)
                    return (lr+1, lc+1)
            # if no saving move works, fall through (group dead)

        # 3. opening
        if total < 14:
            stars = [(3,3),(3,15),(15,3),(15,15),(9,9),(3,9),(15,9),(9,3),(9,15),(12,3),(3,12),(12,15),(15,12),(5,15),(15,5),(5,3),(3,5)]
            # collect stone positions 0-indexed
            stone_pos = []
            for r in range(19):
                for c in range(19):
                    if board[r][c] != 0:
                        stone_pos.append((r,c))
            best_pos = None
            best_dist = -1
            for sr, sc in stars:
                if board[sr][sc] != 0:
                    continue
                # legality (always legal early but check suicide/ko)
                nb, cap, legal = _try_move(board, 1, sr, sc)
                if not legal:
                    continue
                h = _board_hash(nb)
                if h in HISTORY:
                    continue
                if not stone_pos:
                    best_pos = (sr, sc, nb, h)
                    break
                md = min(max(abs(sr-pr), abs(sc-pc)) for pr, pc in stone_pos)
                # prefer far
                if md > best_dist:
                    best_dist = md
                    best_pos = (sr, sc, nb, h)
            if best_pos is not None:
                # if very early, play it directly
                HISTORY.add(best_pos[3])
                return (best_pos[0]+1, best_pos[1]+1)

        # 4. candidate generation near stones
        cand_set = set()
        has_stone = False
        for r in range(19):
            for c in range(19):
                if board[r][c] != 0:
                    has_stone = True
                    for dr in range(-2,3):
                        for dc in range(-2,3):
                            nr, nc = r+dr, c+dc
                            if _in(nr,nc) and board[nr][nc] == 0:
                                cand_set.add((nr,nc))
        if not has_stone:
            return (4,4)
        if not cand_set:
            return (0,0)

        # prune if too many
        cand_list = list(cand_set)
        if len(cand_list) > 60:
            scored = []
            for (r,c) in cand_list:
                f = 0
                e = 0
                emp = 0
                for dr, dc in DIRS:
                    nr, nc = r+dr, c+dc
                    if _in(nr,nc):
                        v = board[nr][nc]
                        if v == 1:
                            f += 1
                        elif v == 2:
                            e += 1
                        else:
                            emp += 1
                # diagonal contact
                for dr, dc in DIAG:
                    nr, nc = r+dr, c+dc
                    if _in(nr,nc):
                        v = board[nr][nc]
                        if v == 1:
                            f += 0.5
                        elif v == 2:
                            e += 0.5
                edge_pen = 0
                if r == 0 or r == 18 or c == 0 or c == 18:
                    edge_pen = -1.5
                elif r == 1 or r == 17 or c == 1 or c == 17:
                    edge_pen = -0.5
                s = f*2 + e*2 + edge_pen
                # boost if adjacent to group with few liberties
                scored.append((s, r, c))
            scored.sort(reverse=True)
            cand_list = [(r,c) for _, r, c in scored[:60]]

        best_move = None
        best_nb = None
        best_hash = None
        best_score = -10**9

        # precompute eye map for current board to penalize
        for (r,c) in cand_list:
            nb, cap, legal = _try_move(board, 1, r, c)
            if not legal:
                continue
            h = _board_hash(nb)
            if h in HISTORY:
                continue
            # eye fill?
            eye = _is_eye(board, r, c, 1)
            _, mylibs = _group(nb, r, c)
            nl = len(mylibs)
            s = 0
            s += cap * 60
            s += nl * 6
            # atari bonuses / penalties around
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if _in(nr,nc) and nb[nr][nc] == 2:
                    _, olibs = _group(nb, nr, nc)
                    lo = len(olibs)
                    if lo == 1:
                        s += 70
                    elif lo == 2:
                        s += 12
                    elif lo == 3:
                        s += 3
            if nl == 1:
                # self atari
                if cap == 0:
                    s -= 90
                else:
                    s -= 40
            elif nl == 2:
                s -= 4
            if eye and cap == 0:
                s -= 500
            # edge penalty
            if r == 0 or r == 18 or c == 0 or c == 18:
                s -= 8
            elif r == 1 or r == 17 or c == 1 or c == 17:
                s -= 4
            # connectivity: stones in new group
            stones_new, _ = _group(nb, r, c)
            s += min(len(stones_new), 8) * 1.0
            # friendly adjacency bonus already via libs, add small
            # center bias slight for midgame? prefer 3rd-10th lines
            # tie-break deterministically by position
            s += ((r*19+c) % 7) * 0.01
            if s > best_score:
                best_score = s
                best_move = (r,c)
                best_nb = nb
                best_hash = h

        if best_move is None:
            # no legal non-ko move
            # try any legal empty ignoring history
            for (r,c) in cand_list:
                nb, cap, legal = _try_move(board, 1, r, c)
                if legal:
                    return (r+1, c+1)
            fe = first_empty()
            # verify legality
            if fe != (0,0):
                nb, cap, legal = _try_move(board, 1, fe[0]-1, fe[1]-1)
                if legal:
                    HISTORY.add(_board_hash(nb))
                    return fe
                else:
                    # scan for any legal
                    for r in range(19):
                        for c in range(19):
                            if board[r][c] == 0:
                                nb2, _, lg2 = _try_move(board, 1, r, c)
                                if lg2:
                                    HISTORY.add(_board_hash(nb2))
                                    return (r+1, c+1)
                    return (0,0)
            return (0,0)

        # pass if only bad eye-filling moves
        if best_score < -100 and total > 30:
            return (0,0)

        HISTORY.add(best_hash)
        return (best_move[0]+1, best_move[1]+1)
    except Exception:
        try:
            ms = set(me) if me else set()
            os_ = set(opponent) if opponent else set()
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in ms and (r,c) not in os_:
                        return (r,c)
        except Exception:
            pass
        return (0,0)
