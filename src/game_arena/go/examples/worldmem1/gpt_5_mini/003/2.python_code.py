
#!/usr/bin/env python3
from typing import List, Tuple, Dict
from collections import deque

BOARD_SIZE = 19
MY = 1
OPP = 2
EMPTY = 0

def neighbors(r: int, c: int):
    if r > 0:
        yield r-1, c
    if r < BOARD_SIZE-1:
        yield r+1, c
    if c > 0:
        yield r, c-1
    if c < BOARD_SIZE-1:
        yield r, c+1

def get_group_and_liberties(board: List[List[int]], r: int, c: int):
    color = board[r][c]
    if color == EMPTY:
        return set(), set()
    visited = set()
    libs = set()
    stack = [(r,c)]
    while stack:
        x,y = stack.pop()
        if (x,y) in visited:
            continue
        visited.add((x,y))
        for nx,ny in neighbors(x,y):
            if board[nx][ny] == EMPTY:
                libs.add((nx,ny))
            elif board[nx][ny] == color and (nx,ny) not in visited:
                stack.append((nx,ny))
    return visited, libs

def board_from_lists(me: List[Tuple[int,int]], opp: List[Tuple[int,int]]):
    # 0-based internal board
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for (r,c) in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r-1][c-1] = MY
    for (r,c) in opp:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r-1][c-1] = OPP
    return board

def simulate_move_and_score(board: List[List[int]], r: int, c: int):
    # r,c are 0-based empty position
    # Simulate placing MY at (r,c), remove captured opponent groups,
    # check for suicide (illegal), and compute heuristic score.
    # Returns (legal:bool, captured_count:int, liberties_after:int, adj_my:int, adj_opp:int, score:float)
    if board[r][c] != EMPTY:
        return False, 0, 0, 0, 0, -1e9

    # copy board
    b = [row[:] for row in board]
    b[r][c] = MY

    # check adjacent opponent groups for capture
    captured = 0
    removed_any = False
    seen = set()
    for nx,ny in neighbors(r,c):
        if b[nx][ny] == OPP and (nx,ny) not in seen:
            group, libs = get_group_and_liberties(b, nx, ny)
            seen.update(group)
            if len(libs) == 0:
                # capture
                removed_any = True
                captured += len(group)
                for (gx,gy) in group:
                    b[gx][gy] = EMPTY

    # now check own group liberties (including the new stone)
    group_my, libs_my = get_group_and_liberties(b, r, c)
    if len(libs_my) == 0:
        # suicide (illegal) unless we captured something
        if not removed_any:
            return False, 0, 0, 0, 0, -1e9
        # if we captured, and still have no liberties, that would be suicide as well
        # but capture should have freed liberties normally. We still treat as illegal.
        if len(libs_my) == 0:
            return False, 0, 0, 0, 0, -1e9

    # adjacency after captures
    adj_my = 0
    adj_opp = 0
    for nx,ny in neighbors(r,c):
        if b[nx][ny] == MY:
            adj_my += 1
        elif b[nx][ny] == OPP:
            adj_opp += 1

    liberties_after = len(libs_my)

    # center influence (closer to center is slightly better)
    center_row = (BOARD_SIZE - 1) / 2.0  # 9.0 for 19x19 (0-based)
    center_col = (BOARD_SIZE - 1) / 2.0
    dist = abs(r - center_row) + abs(c - center_col)
    center_bonus = max(0.0, (BOARD_SIZE/2.0 - dist))  # larger if closer

    # Score weights (tuned heuristics)
    score = (
        captured * 1000.0
        + adj_opp * 80.0
        + adj_my * 30.0
        + liberties_after * 8.0
        + center_bonus * 1.5
    )

    # avoid obvious self-atari: if after move our group's liberties == 1 and we didn't capture, penalize
    if liberties_after == 1 and captured == 0:
        score -= 200.0

    return True, captured, liberties_after, adj_my, adj_opp, score

def policy(me: List[Tuple[int,int]], opponent: List[Tuple[int,int]], memory: Dict) -> Tuple[Tuple[int,int], Dict]:
    """
    Returns (action, memory). action is (row, col) 1-based. (0,0) to pass.
    """
    board = board_from_lists(me, opponent)

    best_move = (0, 0)
    best_score = -1e12
    best_details = None

    # iterate over all empty points and evaluate
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue
            legal, captured, liberties_after, adj_my, adj_opp, score = simulate_move_and_score(board, r, c)
            if not legal:
                continue
            # tie-breaker deterministic: prefer smaller row then col if scores near equal
            if score > best_score + 1e-6 or (abs(score - best_score) <= 1e-6 and (r, c) < (best_move[0]-1, best_move[1]-1) if best_move != (0,0) else True):
                best_score = score
                best_move = (r+1, c+1)  # convert to 1-based
                best_details = (captured, liberties_after, adj_my, adj_opp, score)

    # If no legal move found (very unlikely), pass
    if best_move == (0,0):
        result_move = (0, 0)
    else:
        result_move = best_move

    # store some minimal memory (number of moves played so far)
    move_count = memory.get('move_count', 0) + 1
    memory_out = dict(memory)
    memory_out['move_count'] = move_count
    memory_out['last_move'] = result_move

    return result_move, memory_out

# For direct module test (optional)
if __name__ == "__main__":
    # empty board opening: expect near center
    mv, mem = policy([], [], {})
    print("Move on empty board:", mv)  # debug if run directly
