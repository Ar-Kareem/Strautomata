
# policy_go.py
# A policy that simulates captures and avoids suicide, prefers captures, connections and center influence.
# Implements the required API:
# def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:

from collections import deque

BOARD_SIZE = 19

def inside(r, c):
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def neighbors(r, c):
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr, nc = r+dr, c+dc
        if inside(nr, nc):
            yield nr, nc

def build_board(me, opponent):
    # 0 empty, 1 me, -1 opponent
    board = [[0]*(BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
    for (r,c) in me:
        if inside(r,c):
            board[r][c] = 1
    for (r,c) in opponent:
        if inside(r,c):
            # if both lists contain same coordinate, opponent takes precedence here,
            # but such inputs should not occur in a valid position.
            board[r][c] = -1
    return board

def group_and_liberties(board, r, c):
    color = board[r][c]
    if color == 0:
        return set(), set()
    visited = set()
    liberties = set()
    q = deque()
    q.append((r,c))
    visited.add((r,c))
    while q:
        x,y = q.popleft()
        for nx, ny in neighbors(x,y):
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx,ny))
            elif v == color and (nx,ny) not in visited:
                visited.add((nx,ny))
                q.append((nx,ny))
    return visited, liberties

def simulate_move(board, move, color):
    # color: 1 for me, -1 for opponent
    r, c = move
    if not inside(r,c):
        return None, False, 0
    if board[r][c] != 0:
        return None, False, 0
    # copy board
    b = [row[:] for row in board]
    b[r][c] = color
    # check adjacent opponent groups for capture
    captured = 0
    opp_color = -color
    to_remove = set()
    for nr, nc in neighbors(r, c):
        if b[nr][nc] == opp_color:
            grp, libs = group_and_liberties(b, nr, nc)
            if len(libs) == 0:
                to_remove |= grp
    # remove captured stones
    for (x,y) in to_remove:
        b[x][y] = 0
    captured = len(to_remove)
    # Now check our new group's liberties to detect suicide
    grp, libs = group_and_liberties(b, r, c)
    if len(libs) == 0:
        # illegal suicide
        return None, False, 0
    return b, True, captured

def score_move(board, move):
    # Evaluate a legal move by simulating it as 'me' (1)
    sim_board, legal, captured = simulate_move(board, move, 1)
    if not legal:
        return None
    # Heuristic components
    r, c = move
    # adjacency counts on the simulated board (after captures removed)
    adj_my = 0
    adj_empty = 0
    for nr, nc in neighbors(r, c):
        v = sim_board[nr][nc]
        if v == 1:
            adj_my += 1
        elif v == 0:
            adj_empty += 1
    # compute liberties of the placed stone's group
    grp, libs = group_and_liberties(sim_board, r, c)
    liberties = len(libs)
    # center proximity (lower distance is better)
    center = (BOARD_SIZE+1)/2.0
    dist_center = abs(r - center) + abs(c - center)
    # Score weights (tuned heuristics)
    score = 0
    score += captured * 200          # capturing is very valuable
    score += adj_my * 10             # connect to own stones
    score += adj_empty * 3           # create more immediate liberties
    score += liberties * 8           # overall group liberties
    score += -dist_center * 0.5      # prefer center influence
    # small deterministic tie-breaker to keep choices stable
    score += - (r*0.001 + c*0.00001)
    return score

def find_best_move(me, opponent):
    board = build_board(me, opponent)
    # Opening heuristics: if board empty, play center (10,10 on 19x19)
    if len(me) == 0 and len(opponent) == 0:
        if board[10][10] == 0:
            return (10,10)
    # First priority: immediate captures (max captured)
    best_capture = None
    best_capture_count = -1
    # Evaluate all empty points collecting legal moves and scores
    best_move = None
    best_score = None
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] != 0:
                continue
            sim_board, legal, captured = simulate_move(board, (r,c), 1)
            if not legal:
                continue
            # prioritize maximum capture
            if captured > 0:
                if captured > best_capture_count:
                    best_capture_count = captured
                    best_capture = (r,c)
            # otherwise compute heuristic score
            sc = score_move(board, (r,c))
            if sc is None:
                continue
            if (best_score is None) or (sc > best_score):
                best_score = sc
                best_move = (r,c)
    if best_capture is not None:
        return best_capture
    if best_move is not None:
        return best_move
    # If no legal moves found, pass
    return (0,0)

def policy(me, opponent, memory):
    """
    me: list of (row,col) of my stones
    opponent: list of (row,col) of opponent stones
    memory: dict (can be used to store state between calls)
    returns: (action (r,c), memory)
    """
    # Defensive: ensure inputs are lists
    if me is None:
        me = []
    if opponent is None:
        opponent = []
    move = find_best_move(me, opponent)
    # we don't maintain memory for now, but return it unchanged (or empty)
    return move, memory if memory is not None else {}
