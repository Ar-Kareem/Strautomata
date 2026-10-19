
import math
import random
from collections import deque

BOARD_SIZE = 19

def in_bounds(r, c):
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def neighbors(r, c):
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc):
            yield nr, nc

def build_board(me, opponent):
    # board[r][c] with 1-indexing for convenience; index 0 unused
    board = [[0]*(BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
    for (r,c) in me:
        if in_bounds(r,c):
            board[r][c] = 1
    for (r,c) in opponent:
        if in_bounds(r,c):
            board[r][c] = -1
    return board

def get_group_and_liberties(board, r, c):
    color = board[r][c]
    if color == 0:
        return set(), 0
    visited = set()
    q = deque()
    q.append((r,c))
    visited.add((r,c))
    liberties = set()
    while q:
        x,y = q.popleft()
        for nx, ny in neighbors(x,y):
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx,ny))
            elif v == color and (nx,ny) not in visited:
                visited.add((nx,ny))
                q.append((nx,ny))
    return visited, len(liberties)

def simulate_move_and_check(board, r, c):
    # return (is_legal, new_board)
    if board[r][c] != 0:
        return False, None
    # copy
    newb = [row[:] for row in board]
    newb[r][c] = 1
    # check adjacent opponent groups for captures
    to_remove = set()
    for nx, ny in neighbors(r,c):
        if newb[nx][ny] == -1:
            group, libs = get_group_and_liberties(newb, nx, ny)
            if libs == 0:
                to_remove |= group
    for (x,y) in to_remove:
        newb[x][y] = 0
    # now check the group of the moved stone
    group, libs = get_group_and_liberties(newb, r, c)
    if libs == 0:
        # illegal suicide (no captures occurred if we are here)
        return False, None
    return True, newb

def score_move(r, c, me_list, opp_list, board, total_stones):
    # Influence-based scoring
    # parameters tuned for aggressive/territorial play
    my_influence = 0.0
    opp_influence = 0.0
    scale = 3.0  # distance scale for influence
    for (mr, mc) in me_list:
        d = math.hypot(mr - r, mc - c)
        my_influence += math.exp(-d/scale)
    for (or_, oc) in opp_list:
        d = math.hypot(or_ - r, oc - c)
        opp_influence += math.exp(-d/scale)
    influence_score = my_influence - 1.1 * opp_influence

    # adjacency bonuses
    adj_my = 0
    adj_opp = 0
    for nx, ny in neighbors(r,c):
        if board[nx][ny] == 1:
            adj_my += 1
        elif board[nx][ny] == -1:
            adj_opp += 1
    adj_score = 0.9 * adj_my + 1.6 * adj_opp  # attack slightly prioritized

    # star/hoshi and corner bias in early game
    star_points = {(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)}
    corner_bonus = 0.0
    if (r,c) in star_points:
        # larger weight early
        if total_stones < 20:
            corner_bonus += 3.0
        else:
            corner_bonus += 1.0
    # corners: near corners get a small bonus
    if (r <= 3 and c <= 3) or (r <= 3 and c >= 17) or (r >= 17 and c <= 3) or (r >= 17 and c >= 17):
        corner_bonus += 1.2

    # center bias small
    center_r = (BOARD_SIZE+1)/2
    center_c = (BOARD_SIZE+1)/2
    center_dist = math.hypot(center_r - r, center_c - c)
    center_score = -0.02 * center_dist

    # final weighted sum
    final = 2.0 * influence_score + adj_score + corner_bonus + center_score
    return final

def policy(me, opponent, memory):
    """
    me: list of (row,col) tuples for my stones
    opponent: list of (row,col) tuples for opponent stones
    memory: dict, may be used to store state between calls
    returns: (action (r,c), memory)
    """
    # initialize RNG seed in memory for deterministic tie-breaking if desired
    if 'seed' not in memory:
        memory['seed'] = random.randrange(1<<30)
    rnd = random.Random(memory['seed'] + len(me) + 17)

    board = build_board(me, opponent)
    total_stones = len(me) + len(opponent)

    best_moves = []
    best_score = -1e9

    # iterate over all empty points and evaluate legality + score
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] != 0:
                continue
            legal, newb = simulate_move_and_check(board, r, c)
            if not legal:
                continue
            s = score_move(r, c, me, opponent, board, total_stones)
            # small random jitter to break ties deterministically
            s += rnd.random() * 1e-6
            if s > best_score + 1e-9:
                best_score = s
                best_moves = [(r,c)]
            elif abs(s - best_score) <= 1e-9:
                best_moves.append((r,c))

    if not best_moves:
        # no legal moves found (very unlikely). Pass.
        return (0,0), memory

    # pick random among best
    choice = rnd.choice(best_moves)
    # update seed to change tie-breaking next time
    memory['seed'] = (memory['seed'] * 1664525 + 1013904223) & 0xFFFFFFFF
    return choice, memory

# Expose policy at module level
if __name__ == "__main__":
    # quick test: empty board -> should select a star or good opening
    move, mem = policy([], [], {})
    print("Chosen move on empty board:", move)
