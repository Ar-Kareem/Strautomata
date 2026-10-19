
import random
from collections import deque

# Constants
CAPTURE_WEIGHT = 5
ATARI_WEIGHT = 3
DEFENSE_BONUS = 10000
CONNECTION_BONUS = 10
SELF_ATARI_PENALTY = 50

# Direction vectors
DIRS = [(1,0), (-1,0), (0,1), (0,-1)]

def get_neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            yield nr, nc

def location_bonus_table():
    table = [[0]*19 for _ in range(19)]
    for r in range(19):
        rd = min(r, 18-r)
        frow = max(0, 4 - abs(rd-3))
        for c in range(19):
            cd = min(c, 18-c)
            fcol = max(0, 4 - abs(cd-3))
            table[r][c] = frow + fcol
    return table

def find_groups(board, color):
    visited = [[False]*19 for _ in range(19)]
    groups = []
    group_id = [[-1]*19 for _ in range(19)]
    for r in range(19):
        for c in range(19):
            if board[r][c] == color and not visited[r][c]:
                stack = [(r,c)]
                group = set()
                while stack:
                    x,y = stack.pop()
                    if visited[x][y]:
                        continue
                    visited[x][y] = True
                    group.add((x,y))
                    group_id[x][y] = len(groups)
                    for nx,ny in get_neighbors(x,y):
                        if board[nx][ny] == color and not visited[nx][ny]:
                            stack.append((nx,ny))
                groups.append(group)
    return groups, group_id

def compute_liberties(board, group):
    libs = set()
    for (x,y) in group:
        for nx,ny in get_neighbors(x,y):
            if board[nx][ny] == 0:
                libs.add((nx,ny))
    return libs

def evaluate(board):
    my_stones = 0
    opp_stones = 0
    for r in range(19):
        for c in range(19):
            if board[r][c] == 1:
                my_stones += 1
            elif board[r][c] == -1:
                opp_stones += 1

    # Distance to nearest my stone
    dist_me = [[999]*19 for _ in range(19)]
    q = deque()
    for r in range(19):
        for c in range(19):
            if board[r][c] == 1:
                dist_me[r][c] = 0
                q.append((r,c))
    while q:
        r,c = q.popleft()
        d = dist_me[r][c]
        for nr,nc in get_neighbors(r,c):
            if dist_me[nr][nc] == 999:
                dist_me[nr][nc] = d+1
                q.append((nr,nc))

    # Distance to nearest opponent stone
    dist_opp = [[999]*19 for _ in range(19)]
    q = deque()
    for r in range(19):
        for c in range(19):
            if board[r][c] == -1:
                dist_opp[r][c] = 0
                q.append((r,c))
    while q:
        r,c = q.popleft()
        d = dist_opp[r][c]
        for nr,nc in get_neighbors(r,c):
            if dist_opp[nr][nc] == 999:
                dist_opp[nr][nc] = d+1
                q.append((nr,nc))

    my_terr = 0
    opp_terr = 0
    for r in range(19):
        for c in range(19):
            if board[r][c] == 0:
                if dist_me[r][c] < dist_opp[r][c]:
                    my_terr += 1
                elif dist_opp[r][c] < dist_me[r][c]:
                    opp_terr += 1

    return (my_stones - opp_stones) + (my_terr - opp_terr)

def simulate_move(orig_board, r, c, opp_group_id, opp_groups):
    # Copy board and place stone
    new_board = [row[:] for row in orig_board]
    new_board[r][c] = 1

    # Collect distinct opponent groups adjacent to the move
    processed = set()
    for nr,nc in get_neighbors(r,c):
        if orig_board[nr][nc] == -1:
            gid = opp_group_id[nr][nc]
            if gid != -1:
                processed.add(gid)

    # Determine which of these groups are captured (before removal)
    captured_gids = set()
    for gid in processed:
        group_stones = opp_groups[gid]
        libs = set()
        for (x,y) in group_stones:
            for nx,ny in get_neighbors(x,y):
                if new_board[nx][ny] == 0:
                    libs.add((nx,ny))
        if len(libs) == 0:
            captured_gids.add(gid)

    # Remove captured groups
    capture_bonus = 0
    for gid in captured_gids:
        group_stones = opp_groups[gid]
        capture_bonus += CAPTURE_WEIGHT * len(group_stones)
        for (x,y) in group_stones:
            new_board[x][y] = 0

    # After removal, check which groups are in atari (liberties == 1)
    atari_bonus = 0
    for gid in processed:
        if gid in captured_gids:
            continue
        group_stones = opp_groups[gid]
        libs = set()
        for (x,y) in group_stones:
            for nx,ny in get_neighbors(x,y):
                if new_board[nx][ny] == 0:
                    libs.add((nx,ny))
        if len(libs) == 1:
            atari_bonus += ATARI_WEIGHT * len(group_stones)

    # Check own group liberties after captures
    stack = [(r,c)]
    visited = set()
    libs = set()
    size = 0
    while stack:
        x,y = stack.pop()
        if (x,y) in visited:
            continue
        visited.add((x,y))
        size += 1
        for nx,ny in get_neighbors(x,y):
            if new_board[nx][ny] == 0:
                libs.add((nx,ny))
            elif new_board[nx][ny] == 1 and (nx,ny) not in visited:
                stack.append((nx,ny))
    if len(libs) == 0:
        return (False, None, 0, 0, 0)

    self_atari_penalty = 0
    if len(libs) == 1:
        self_atari_penalty = SELF_ATARI_PENALTY * size

    return (True, new_board, capture_bonus, atari_bonus, self_atari_penalty)

def policy(me, opponent):
    # Convert to internal board (0-indexed, 1 = my stone, -1 = opponent)
    board = [[0]*19 for _ in range(19)]
    for (r,c) in me:
        board[r-1][c-1] = 1
    for (r,c) in opponent:
        board[r-1][c-1] = -1

    # Precompute groups and critical defense points
    my_groups, my_group_id = find_groups(board, 1)
    opp_groups, opp_group_id = find_groups(board, -1)

    critical_defense = set()
    for group in my_groups:
        libs = compute_liberties(board, group)
        if len(libs) == 1:
            (lib,) = libs
            critical_defense.add(lib)

    # Location bonus table
    loc_bonus = location_bonus_table()

    best_score = -float('inf')
    best_move = (0,0)  # pass

    # Evaluate every empty intersection
    for r in range(19):
        for c in range(19):
            if board[r][c] != 0:
                continue

            # Defense bonus if this move saves a group in atari
            defense_bonus = DEFENSE_BONUS if (r,c) in critical_defense else 0

            # Connection bonus (connects multiple of our groups)
            adj_my_gids = set()
            for nr,nc in get_neighbors(r,c):
                if board[nr][nc] == 1:
                    gid = my_group_id[nr][nc]
                    if gid != -1:
                        adj_my_gids.add(gid)
            connection_bonus = CONNECTION_BONUS * (len(adj_my_gids) - 1) if len(adj_my_gids) >= 2 else 0

            # Simulate the move
            legal, new_board, capture_bonus, atari_bonus, self_atari_penalty = simulate_move(board, r, c, opp_group_id, opp_groups)
            if not legal:
                continue

            # Static evaluation of the resulting board
            eval_score = evaluate(new_board)

            # Total score
            total = (eval_score + defense_bonus + capture_bonus + atari_bonus +
                     connection_bonus - self_atari_penalty +
                     loc_bonus[r][c] + random.random())

            if total > best_score:
                best_score = total
                best_move = (r+1, c+1)  # convert back to 1-indexed

    return best_move
