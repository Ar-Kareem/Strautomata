
import random
from collections import deque

BOARD_SIZE = 19

def neighbors(r, c):
    for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
        nr, nc = r+dr, c+dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield nr, nc

def build_board(me, opponent):
    board = [[0]*(BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
    for r,c in me:
        board[r][c] = 1
    for r,c in opponent:
        board[r][c] = 2
    return board

def group_and_liberties(board, start):
    color = board[start[0]][start[1]]
    q = deque([start])
    visited = set([start])
    stones = []
    liberties = set()
    while q:
        r,c = q.popleft()
        stones.append((r,c))
        for nr,nc in neighbors(r,c):
            if board[nr][nc] == 0:
                liberties.add((nr,nc))
            elif board[nr][nc] == color and (nr,nc) not in visited:
                visited.add((nr,nc))
                q.append((nr,nc))
    return stones, liberties

def get_groups(board, color):
    visited = set()
    groups = []
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] == color and (r,c) not in visited:
                stones, libs = group_and_liberties(board, (r,c))
                for s in stones:
                    visited.add(s)
                groups.append((stones, libs))
    return groups

def simulate_move(board, move, color):
    r,c = move
    new_board = [row[:] for row in board]
    new_board[r][c] = color
    opp = 2 if color == 1 else 1
    # capture adjacent opponent groups with no liberties
    for nr,nc in neighbors(r,c):
        if new_board[nr][nc] == opp:
            stones, libs = group_and_liberties(new_board, (nr,nc))
            if len(libs) == 0:
                for sr,sc in stones:
                    new_board[sr][sc] = 0
    return new_board

def is_legal(board, move, color):
    r,c = move
    if board[r][c] != 0:
        return False
    new_board = simulate_move(board, move, color)
    stones, libs = group_and_liberties(new_board, move)
    if len(libs) == 0:
        return False
    return True

def policy(me, opponent, memory):
    board = build_board(me, opponent)
    empty_points = [(r,c) for r in range(1, BOARD_SIZE+1) for c in range(1, BOARD_SIZE+1) if board[r][c]==0]
    if not empty_points:
        return (0,0), memory

    # 1. Capture opponent groups in atari
    capture_candidates = []
    opp_groups = get_groups(board, 2)
    for stones, libs in opp_groups:
        if len(libs) == 1:
            move = next(iter(libs))
            if is_legal(board, move, 1):
                capture_candidates.append((len(stones), move))
    if capture_candidates:
        capture_candidates.sort(key=lambda x: (-x[0], abs(x[1][0]-10)+abs(x[1][1]-10)))
        return capture_candidates[0][1], memory

    # 2. Save own groups in atari
    defend_candidates = []
    my_groups = get_groups(board, 1)
    for stones, libs in my_groups:
        if len(libs) == 1:
            move = next(iter(libs))
            if is_legal(board, move, 1):
                new_board = simulate_move(board, move, 1)
                _, new_libs = group_and_liberties(new_board, move)
                defend_candidates.append((len(new_libs), move))
    if defend_candidates:
        defend_candidates.sort(key=lambda x: (-x[0], abs(x[1][0]-10)+abs(x[1][1]-10)))
        return defend_candidates[0][1], memory

    # 3. Otherwise, play aggressive and central
    best_score = -1e9
    best_move = None
    for move in empty_points:
        if not is_legal(board, move, 1):
            continue
        r,c = move
        adj_opp = sum(1 for nr,nc in neighbors(r,c) if board[nr][nc] == 2)
        adj_me = sum(1 for nr,nc in neighbors(r,c) if board[nr][nc] == 1)
        center_bias = 10 - (abs(r-10) + abs(c-10))
        score = adj_opp*3 + adj_me + center_bias*0.1
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is not None:
        return best_move, memory

    # If no legal move found, pass
    return (0,0), memory
