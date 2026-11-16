
from collections import deque

N = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc):
            yield nr, nc


def _build_board(me, opponent):
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = 2
    return board


def _group_and_liberties(board, r, c):
    color = board[r][c]
    group = []
    liberties = set()
    q = deque([(r, c)])
    seen = {(r, c)}
    while q:
        x, y = q.popleft()
        group.append((x, y))
        for nx, ny in _neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return group, liberties


def _play_and_captures(board, r, c, color):
    if not _inside(r, c) or board[r][c] != 0:
        return None, -1

    opp = 3 - color
    newb = [row[:] for row in board]
    newb[r][c] = color
    captured = 0

    checked = set()
    for nr, nc in _neighbors(r, c):
        if newb[nr][nc] == opp and (nr, nc) not in checked:
            group, libs = _group_and_liberties(newb, nr, nc)
            checked.update(group)
            if len(libs) == 0:
                captured += len(group)
                for gx, gy in group:
                    newb[gx][gy] = 0

    my_group, my_libs = _group_and_liberties(newb, r, c)
    if len(my_libs) == 0:
        return None, -1  # suicide

    return newb, captured


def _all_groups(board, color):
    seen = set()
    groups = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == color and (r, c) not in seen:
                g, libs = _group_and_liberties(board, r, c)
                for p in g:
                    seen.add(p)
                groups.append((g, libs))
    return groups


def _distance_to_center(r, c):
    # r,c are 0-based
    return abs(r - 9) + abs(c - 9)


def _adjacency_counts(board, r, c):
    mine = opp = empty = 0
    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == 1:
            mine += 1
        elif board[nr][nc] == 2:
            opp += 1
        else:
            empty += 1
    return mine, opp, empty


def _move_score(board, newb, r, c, captured, move_count):
    score = 0.0

    # Tactical gain
    score += 30.0 * captured

    mine, opp, empty = _adjacency_counts(board, r, c)
    score += 3.0 * mine + 1.5 * opp + 0.3 * empty

    # Prefer active area, but also center early
    if move_count < 20:
        score += max(0, 10 - _distance_to_center(r, c)) * 0.8
    else:
        score += max(0, 8 - _distance_to_center(r, c)) * 0.2

    # Resulting liberties of placed group
    g, libs = _group_and_liberties(newb, r, c)
    lcount = len(libs)
    score += 1.2 * min(lcount, 6)
    if lcount == 1:
        score -= 12.0  # self-atari-ish
    elif lcount == 2:
        score -= 2.0

    # Prefer extending weak friendly groups / pressuring weak enemy groups
    touched_friendly_ataris = 0
    touched_enemy_ataris = 0
    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == 1:
            _, libs0 = _group_and_liberties(board, nr, nc)
            if len(libs0) == 1:
                touched_friendly_ataris += 1
        elif board[nr][nc] == 2:
            _, libs0 = _group_and_liberties(board, nr, nc)
            if len(libs0) == 1:
                touched_enemy_ataris += 1
    score += 8.0 * touched_friendly_ataris
    score += 10.0 * touched_enemy_ataris

    # Slight preference for not playing on first line unless tactical
    edge_dist = min(r, c, N - 1 - r, N - 1 - c)
    if edge_dist == 0:
        score -= 1.5
    elif edge_dist == 1:
        score -= 0.5

    return score


def policy(me, opponent):
    board = _build_board(me, opponent)
    move_count = len(me) + len(opponent)

    legal_moves = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            newb, captured = _play_and_captures(board, r, c, 1)
            if newb is not None:
                legal_moves.append((r, c, newb, captured))

    if not legal_moves:
        return (0, 0)

    # 1) Immediate best capture
    best_capture = max(captured for _, _, _, captured in legal_moves)
    if best_capture > 0:
        capture_moves = [(r, c, newb, captured) for (r, c, newb, captured) in legal_moves if captured == best_capture]
        best = None
        best_score = -10**18
        for r, c, newb, captured in capture_moves:
            sc = _move_score(board, newb, r, c, captured, move_count)
            if sc > best_score:
                best_score = sc
                best = (r + 1, c + 1)
        return best

    # 2) Save our groups in atari if possible
    my_ataris = []
    seen = set()
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and (r, c) not in seen:
                g, libs = _group_and_liberties(board, r, c)
                seen.update(g)
                if len(libs) == 1:
                    my_ataris.append((g, libs))

    if my_ataris:
        rescue_candidates = set()
        for g, libs in my_ataris:
            for p in libs:
                rescue_candidates.add(p)
            for x, y in g:
                for nx, ny in _neighbors(x, y):
                    if board[nx][ny] == 2:
                        g2, libs2 = _group_and_liberties(board, nx, ny)
                        if len(libs2) == 1:
                            rescue_candidates |= libs2

        best = None
        best_score = -10**18
        for r, c, newb, captured in legal_moves:
            if (r, c) in rescue_candidates:
                sc = _move_score(board, newb, r, c, captured, move_count) + 20.0
                if sc > best_score:
                    best_score = sc
                    best = (r + 1, c + 1)
        if best is not None:
            return best

    # 3) General heuristic choice
    best = None
    best_score = -10**18
    for r, c, newb, captured in legal_moves:
        sc = _move_score(board, newb, r, c, captured, move_count)
        if sc > best_score:
            best_score = sc
            best = (r + 1, c + 1)

    if best is not None:
        return best

    return (0, 0)
