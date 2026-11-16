
from collections import deque

N = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
STAR_ORDER = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (7, 7), (7, 13), (13, 7), (13, 13),
]

def in_bounds(r, c):
    return 1 <= r <= N and 1 <= c <= N

def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= N and 1 <= nc <= N:
            yield nr, nc

def make_board(me, opponent):
    board = [[0] * (N + 1) for _ in range(N + 1)]
    for r, c in me:
        if in_bounds(r, c):
            board[r][c] = 1
    for r, c in opponent:
        if in_bounds(r, c):
            board[r][c] = 2
    return board

def group_and_liberties(board, r, c):
    color = board[r][c]
    if color == 0:
        return [], set()
    q = deque([(r, c)])
    seen = {(r, c)}
    group = []
    libs = set()
    while q:
        x, y = q.popleft()
        group.append((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return group, libs

def play_move(board, move, color):
    r, c = move
    if not in_bounds(r, c) or board[r][c] != 0:
        return None
    opp = 3 - color

    # Copy board
    nb = [row[:] for row in board]
    nb[r][c] = color

    captured = 0
    checked = set()
    # Capture adjacent opponent groups with no liberties
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == opp and (nr, nc) not in checked:
            grp, libs = group_and_liberties(nb, nr, nc)
            for p in grp:
                checked.add(p)
            if not libs:
                captured += len(grp)
                for gx, gy in grp:
                    nb[gx][gy] = 0

    # Check suicide
    my_grp, my_libs = group_and_liberties(nb, r, c)
    if not my_libs:
        return None

    return nb, captured, len(my_libs), len(my_grp)

def collect_groups(board, color):
    seen = set()
    groups = []
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == color and (r, c) not in seen:
                grp, libs = group_and_liberties(board, r, c)
                for p in grp:
                    seen.add(p)
                groups.append((grp, libs))
    return groups

def distance_to_center(r, c):
    return abs(r - 10) + abs(c - 10)

def move_score(board, move, my_groups_atari, opp_groups_atari, total_stones):
    sim = play_move(board, move, 1)
    if sim is None:
        return None
    nb, captured, my_libs_after, my_size_after = sim
    r, c = move
    score = 0.0

    # Tactical priority: captures
    score += captured * 10000

    # Saving own groups in atari
    if move in my_groups_atari:
        saved = my_groups_atari[move]
        score += 4000 + 300 * saved

    # Putting opponent in atari / reducing liberties nearby
    opp_pressure = 0
    checked = set()
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == 2 and (nr, nc) not in checked:
            grp, libs = group_and_liberties(nb, nr, nc)
            for p in grp:
                checked.add(p)
            if len(libs) == 1:
                opp_pressure += len(grp) * 180
            elif len(libs) == 2:
                opp_pressure += len(grp) * 60
    score += opp_pressure

    # If this move was the last liberty of an opponent atari group, emphasize
    if move in opp_groups_atari:
        threatened = opp_groups_atari[move]
        score += 2500 + 200 * threatened

    # Connection / shape
    adjacent_me = 0
    adjacent_opp = 0
    empty_neighbors = 0
    diag_me = 0
    diag_opp = 0

    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 1:
            adjacent_me += 1
        elif board[nr][nc] == 2:
            adjacent_opp += 1
        else:
            empty_neighbors += 1

    for dr in (-1, 1):
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                if board[nr][nc] == 1:
                    diag_me += 1
                elif board[nr][nc] == 2:
                    diag_opp += 1

    score += adjacent_me * 120
    score += diag_me * 25
    score += adjacent_opp * 40
    score += empty_neighbors * 18

    # Avoid self-atari / cramped groups
    score += my_libs_after * 45
    if my_libs_after == 1:
        score -= 2500
    elif my_libs_after == 2:
        score -= 180

    # Prefer moves near action, but not filling hopelessly isolated points
    near_stones = 0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr][nc] != 0:
                near_stones += 1
    score += near_stones * 10

    # Opening preference: star points / center
    if total_stones < 12:
        if move in STAR_ORDER:
            score += 700
        score -= distance_to_center(r, c) * 8
    else:
        score -= distance_to_center(r, c) * 2

    # Mild edge penalty early/midgame
    if r in (1, 19) or c in (1, 19):
        score -= 120
    elif r in (2, 18) or c in (2, 18):
        score -= 40

    # Small preference for larger connected result
    score += min(my_size_after, 8) * 12

    return score

def policy(me, opponent):
    board = make_board(me, opponent)
    total_stones = len(me) + len(opponent)

    # Opening book: fast good defaults if legal
    if total_stones < 4:
        for mv in STAR_ORDER:
            if play_move(board, mv, 1) is not None:
                return mv

    # Precompute atari information
    my_groups_atari = {}
    for grp, libs in collect_groups(board, 1):
        if len(libs) == 1:
            lib = next(iter(libs))
            my_groups_atari[lib] = my_groups_atari.get(lib, 0) + len(grp)

    opp_groups_atari = {}
    for grp, libs in collect_groups(board, 2):
        if len(libs) == 1:
            lib = next(iter(libs))
            opp_groups_atari[lib] = opp_groups_atari.get(lib, 0) + len(grp)

    best_move = None
    best_score = -10**18

    # Candidate ordering: tactical points first, then neighbors of stones, then all
    candidates = []
    seen = set()

    for mv in list(opp_groups_atari.keys()) + list(my_groups_atari.keys()) + STAR_ORDER:
        if mv not in seen:
            seen.add(mv)
            candidates.append(mv)

    # Add empty points near existing stones
    stones = me + opponent
    for r, c in stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and board[nr][nc] == 0 and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    candidates.append((nr, nc))

    # Fallback: all empties
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0 and (r, c) not in seen:
                candidates.append((r, c))

    for mv in candidates:
        sc = move_score(board, mv, my_groups_atari, opp_groups_atari, total_stones)
        if sc is not None and sc > best_score:
            best_score = sc
            best_move = mv

    if best_move is not None:
        return best_move
    return (0, 0)
