
from collections import deque

SIZE = 19
EMPTY = 0
ME = 1
OPP = 2

def neighbors(r, c):
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        nr, nc = r+dr, c+dc
        if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
            yield nr, nc

def build_board(me, opponent):
    board = [[EMPTY]*(SIZE+1) for _ in range(SIZE+1)]
    for r,c in me:
        board[r][c] = ME
    for r,c in opponent:
        board[r][c] = OPP
    return board

def get_group_and_liberties(board, r, c):
    color = board[r][c]
    q = deque([(r,c)])
    visited = set([(r,c)])
    group = []
    liberties = set()
    while q:
        cr, cc = q.popleft()
        group.append((cr,cc))
        for nr, nc in neighbors(cr, cc):
            v = board[nr][nc]
            if v == EMPTY:
                liberties.add((nr,nc))
            elif v == color and (nr,nc) not in visited:
                visited.add((nr,nc))
                q.append((nr,nc))
    return group, liberties

def simulate_move(board, r, c, player):
    if board[r][c] != EMPTY:
        return None
    # copy board
    newb = [row[:] for row in board]
    newb[r][c] = player
    opponent = ME if player == OPP else OPP
    captured = 0
    # capture adjacent opponent groups
    for nr, nc in neighbors(r,c):
        if newb[nr][nc] == opponent:
            group, libs = get_group_and_liberties(newb, nr, nc)
            if len(libs) == 0:
                for gr, gc in group:
                    newb[gr][gc] = EMPTY
                captured += len(group)
    # check own liberties
    group, libs = get_group_and_liberties(newb, r, c)
    if len(libs) == 0:
        return None  # suicide
    return newb, captured, len(libs)

def legal_moves(board):
    moves = []
    for r in range(1, SIZE+1):
        for c in range(1, SIZE+1):
            if board[r][c] == EMPTY:
                sim = simulate_move(board, r, c, ME)
                if sim is not None:
                    moves.append((r,c))
    return moves

def policy(me, opponent):
    if not me and not opponent:
        return (10,10)  # center opening
    board = build_board(me, opponent)

    # 1. Immediate captures of opponent groups in atari
    best_capture = None
    best_cap_size = -1
    checked = set()
    for r in range(1, SIZE+1):
        for c in range(1, SIZE+1):
            if board[r][c] == OPP and (r,c) not in checked:
                group, libs = get_group_and_liberties(board, r, c)
                checked.update(group)
                if len(libs) == 1:
                    lr, lc = next(iter(libs))
                    sim = simulate_move(board, lr, lc, ME)
                    if sim is not None:
                        _, cap, _ = sim
                        if cap > best_cap_size:
                            best_cap_size = cap
                            best_capture = (lr, lc)
    if best_capture is not None:
        return best_capture

    # 2. Save own groups in atari
    checked = set()
    save_move = None
    save_group_size = -1
    for r in range(1, SIZE+1):
        for c in range(1, SIZE+1):
            if board[r][c] == ME and (r,c) not in checked:
                group, libs = get_group_and_liberties(board, r, c)
                checked.update(group)
                if len(libs) == 1:
                    lr, lc = next(iter(libs))
                    sim = simulate_move(board, lr, lc, ME)
                    if sim is not None:
                        if len(group) > save_group_size:
                            save_group_size = len(group)
                            save_move = (lr, lc)
    if save_move is not None:
        return save_move

    # 3. Heuristic best move
    best_move = None
    best_score = -10**9
    center = (10,10)
    for r in range(1, SIZE+1):
        for c in range(1, SIZE+1):
            if board[r][c] != EMPTY:
                continue
            sim = simulate_move(board, r, c, ME)
            if sim is None:
                continue
            _, cap, libs = sim
            adj_empty = 0
            adj_opp = 0
            adj_me = 0
            for nr, nc in neighbors(r,c):
                if board[nr][nc] == EMPTY:
                    adj_empty += 1
                elif board[nr][nc] == OPP:
                    adj_opp += 1
                else:
                    adj_me += 1
            dist_center = abs(r-center[0]) + abs(c-center[1])
            score = cap*1000 + libs*10 + adj_empty*2 + adj_opp*3 - adj_me - dist_center
            if score > best_score:
                best_score = score
                best_move = (r,c)
    if best_move is not None:
        return best_move

    return (0,0)
