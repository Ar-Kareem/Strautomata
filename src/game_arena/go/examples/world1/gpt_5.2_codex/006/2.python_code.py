
from typing import List, Tuple

SIZE = 19
DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

def in_bounds(r, c):
    return 0 <= r < SIZE and 0 <= c < SIZE

def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc):
            yield nr, nc

def group_and_libs(board, r, c):
    """Return the group (set of stones) and its liberties (set of points)."""
    color = board[r][c]
    stack = [(r,c)]
    visited = set([(r,c)])
    stones = set()
    libs = set()
    while stack:
        x,y = stack.pop()
        stones.add((x,y))
        for nx, ny in neighbors(x,y):
            if board[nx][ny] == 0:
                libs.add((nx,ny))
            elif board[nx][ny] == color and (nx,ny) not in visited:
                visited.add((nx,ny))
                stack.append((nx,ny))
    return stones, libs

def all_groups(board, player):
    visited = set()
    groups = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == player and (r,c) not in visited:
                stones, libs = group_and_libs(board, r, c)
                visited |= stones
                groups.append((stones, libs))
    return groups

def apply_move(board, move, player):
    """Return (new_board, captured, libs_count) or (None,0,0) if illegal."""
    r, c = move
    if board[r][c] != 0:
        return None, 0, 0
    b = [row[:] for row in board]
    b[r][c] = player
    captured = 0
    # capture opponent groups with no liberties
    for nr, nc in neighbors(r,c):
        if b[nr][nc] == -player:
            stones, libs = group_and_libs(b, nr, nc)
            if len(libs) == 0:
                captured += len(stones)
                for sr, sc in stones:
                    b[sr][sc] = 0
    # check our new group liberties
    stones, libs = group_and_libs(b, r, c)
    if len(libs) == 0:
        return None, 0, 0  # suicide
    return b, captured, len(libs)

def policy(me: List[Tuple[int,int]], opponent: List[Tuple[int,int]]) -> Tuple[int,int]:
    # build board
    board = [[0]*SIZE for _ in range(SIZE)]
    for r,c in me:
        board[r-1][c-1] = 1
    for r,c in opponent:
        board[r-1][c-1] = -1

    # 1. urgent capture
    opp_groups = all_groups(board, -1)
    best_cap = None
    max_cap = -1
    for stones, libs in opp_groups:
        if len(libs) == 1:
            liberty = next(iter(libs))
            nb, cap, _ = apply_move(board, liberty, 1)
            if nb is not None and cap > max_cap:
                max_cap = cap
                best_cap = liberty
    if best_cap is not None:
        return (best_cap[0]+1, best_cap[1]+1)

    # 2. urgent defense
    my_groups = all_groups(board, 1)
    best_save = None
    best_size = -1
    for stones, libs in my_groups:
        if len(libs) == 1:
            liberty = next(iter(libs))
            nb, cap, _ = apply_move(board, liberty, 1)
            if nb is not None and len(stones) > best_size:
                best_size = len(stones)
                best_save = liberty
    if best_save is not None:
        return (best_save[0]+1, best_save[1]+1)

    # 3. evaluate all legal moves
    best_score = -1e9
    best_move = None
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0:
                continue
            nb, cap, libs_count = apply_move(board, (r,c), 1)
            if nb is None:
                continue  # illegal
            # heuristic scoring
            adj_opp = sum(1 for nr,nc in neighbors(r,c) if board[nr][nc] == -1)
            adj_own = sum(1 for nr,nc in neighbors(r,c) if board[nr][nc] == 1)
            dist = abs(r-9) + abs(c-9)
            center_bonus = (9 - dist) * 0.5
            score = 0
            score += cap * 100
            score += adj_opp * 5
            score += adj_own * 2
            score += libs_count * 1.5
            score += center_bonus
            if libs_count == 1:
                score -= 50
            if score > best_score:
                best_score = score
                best_move = (r,c)

    if best_move is None:
        return (0,0)
    return (best_move[0]+1, best_move[1]+1)
