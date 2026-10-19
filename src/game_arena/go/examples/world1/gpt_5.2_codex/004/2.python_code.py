
import random
from collections import deque

BOARD_SIZE = 19

def policy(me, opponent):
    # Build board: 0 empty, 1 me, -1 opponent
    board = [[0]*(BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
    for r,c in me:
        board[r][c] = 1
    for r,c in opponent:
        board[r][c] = -1

    def neighbors(r,c):
        if r > 1: yield (r-1,c)
        if r < BOARD_SIZE: yield (r+1,c)
        if c > 1: yield (r,c-1)
        if c < BOARD_SIZE: yield (r,c+1)

    def group_and_libs(r,c):
        color = board[r][c]
        group = set()
        libs = set()
        dq = deque([(r,c)])
        group.add((r,c))
        while dq:
            x,y = dq.popleft()
            for nx,ny in neighbors(x,y):
                if board[nx][ny] == 0:
                    libs.add((nx,ny))
                elif board[nx][ny] == color and (nx,ny) not in group:
                    group.add((nx,ny))
                    dq.append((nx,ny))
        return group, libs

    def is_legal(move_r, move_c):
        if board[move_r][move_c] != 0:
            return False
        # place stone
        board[move_r][move_c] = 1
        captured = []
        for nx,ny in neighbors(move_r, move_c):
            if board[nx][ny] == -1:
                grp, libs = group_and_libs(nx,ny)
                if len(libs) == 0:
                    captured.extend(grp)
        # remove captured
        for x,y in captured:
            board[x][y] = 0
        # check liberties of placed stone
        grp, libs = group_and_libs(move_r, move_c)
        legal = len(libs) > 0
        # undo
        board[move_r][move_c] = 0
        for x,y in captured:
            board[x][y] = -1
        return legal

    # 1. Capture opponent group in atari
    best_capture = None
    best_size = -1
    visited = set()
    for r,c in opponent:
        if (r,c) in visited:
            continue
        grp, libs = group_and_libs(r,c)
        visited |= grp
        if len(libs) == 1:
            (lr,lc) = next(iter(libs))
            if is_legal(lr,lc):
                if len(grp) > best_size:
                    best_size = len(grp)
                    best_capture = (lr,lc)
    if best_capture:
        return best_capture

    # 2. Save own group in atari
    best_save = None
    visited = set()
    for r,c in me:
        if (r,c) in visited:
            continue
        grp, libs = group_and_libs(r,c)
        visited |= grp
        if len(libs) == 1:
            (lr,lc) = next(iter(libs))
            if is_legal(lr,lc):
                best_save = (lr,lc)
                break
    if best_save:
        return best_save

    # 3. Generate candidate moves near stones
    candidates = set()
    if me or opponent:
        for r,c in me + opponent:
            for nx,ny in neighbors(r,c):
                if board[nx][ny] == 0:
                    candidates.add((nx,ny))
    else:
        candidates.add((10,10))

    # If no nearby candidates, add all empties
    if not candidates:
        for r in range(1, BOARD_SIZE+1):
            for c in range(1, BOARD_SIZE+1):
                if board[r][c] == 0:
                    candidates.add((r,c))

    def heuristic(r,c):
        score = 0
        # prefer center
        score += 5 - (abs(r-10)+abs(c-10))/4
        for nx,ny in neighbors(r,c):
            if board[nx][ny] == -1:
                score += 3
            elif board[nx][ny] == 1:
                score += 1
        return score

    best_move = None
    best_score = -1e9
    for r,c in candidates:
        if not is_legal(r,c):
            continue
        sc = heuristic(r,c)
        if sc > best_score:
            best_score = sc
            best_move = (r,c)

    if best_move:
        return best_move

    # 4. Fallback: any legal move
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] == 0 and is_legal(r,c):
                return (r,c)

    return (0,0)
