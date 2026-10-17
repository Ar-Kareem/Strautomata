
#!/usr/bin/env python3
# Go-playing policy for 19x19 board.
# Implements a simulated-placement evaluator:
# - simulates placing at each empty point
# - removes captured opponent groups
# - rejects suicide moves
# - scores moves by captures, connection to own stones, proximity to opponent, centrality, and star/corner bonuses
# Returns a single legal move (row, col) in 1..19 or (0,0) to pass.

from collections import deque
import math

BOARD_SIZE = 19

def neighbors(r, c):
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        rr, cc = r+dr, c+dc
        if 1 <= rr <= BOARD_SIZE and 1 <= cc <= BOARD_SIZE:
            yield rr, cc

def build_board(me, opponent):
    # 0 empty, 1 me, 2 opponent
    board = [[0]*(BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
    for (r,c) in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r][c] = 1
    for (r,c) in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r][c] = 2
    return board

def find_group_and_liberties(board, start_r, start_c):
    color = board[start_r][start_c]
    if color == 0:
        return [], 0
    visited = set()
    q = deque()
    q.append((start_r, start_c))
    visited.add((start_r, start_c))
    liberties = set()
    stones = []
    while q:
        r,c = q.popleft()
        stones.append((r,c))
        for nr, nc in neighbors(r,c):
            if board[nr][nc] == 0:
                liberties.add((nr,nc))
            elif board[nr][nc] == color and (nr,nc) not in visited:
                visited.add((nr,nc))
                q.append((nr,nc))
    return stones, len(liberties)

def all_groups(board):
    seen = [[False]*(BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
    groups = []  # list of (color, stones_list, liberties_count)
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] != 0 and not seen[r][c]:
                color = board[r][c]
                stones, libs = find_group_and_liberties(board, r, c)
                for (sr,sc) in stones:
                    seen[sr][sc] = True
                groups.append((color, stones, libs))
    return groups

def simulate_move_and_score(board, move_r, move_c):
    # Copy board
    b = [row[:] for row in board]
    if b[move_r][move_c] != 0:
        return None  # not empty
    # place our stone
    b[move_r][move_c] = 1
    # Find opponent groups with 0 liberties and remove them
    groups = all_groups(b)
    captured = 0
    for color, stones, libs in groups:
        if color == 2 and libs == 0:
            # remove
            captured += len(stones)
            for (sr,sc) in stones:
                b[sr][sc] = 0
    # After captures, check liberties of the group that contains the placed stone
    my_stones_group, my_libs = find_group_and_liberties(b, move_r, move_c)
    if my_libs == 0:
        return None  # suicide, illegal under standard rules
    # scoring
    score = 0.0
    score += 1000.0 * captured  # big priority for captures
    # closeness to our stones: prefer connecting or expanding near existing stones
    # compute nearest distance to our stones (excluding the placed stone)
    min_dist_me = None
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] == 1:
                d = math.hypot(r - move_r, c - move_c)
                if min_dist_me is None or d < min_dist_me:
                    min_dist_me = d
    if min_dist_me is None:
        # no existing stones: opening move, favor star points and center
        min_dist_me = 100.0
    score += 80.0 / (1.0 + min_dist_me)  # closer is better

    # proximity to opponent: moderate preference to be near but not right on top
    min_dist_opp = None
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] == 2:
                d = math.hypot(r - move_r, c - move_c)
                if min_dist_opp is None or d < min_dist_opp:
                    min_dist_opp = d
    if min_dist_opp is None:
        min_dist_opp = 100.0
    # If very close to opponent (<1.5), be cautious (could be fighting), else mild bonus
    if min_dist_opp <= 1.5:
        score += 10.0 / (1.0 + min_dist_opp)
    else:
        score += 30.0 / (1.0 + min_dist_opp)

    # centrality: prefer center slightly in mid-game, but small weight
    center = ( (BOARD_SIZE+1)/2.0, (BOARD_SIZE+1)/2.0 )
    dcenter = math.hypot(move_r - center[0], move_c - center[1])
    max_center = math.hypot(center[0]-1, center[1]-1)
    score += 5.0 * (1.0 - (dcenter / max_center))

    # star points and corner / 3-3 or 4-4 points bonuses (early-game)
    star_coords = {(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)}
    if (move_r, move_c) in star_coords:
        score += 25.0

    # corner 3-3 (1-based): 3,3 and symmetrical - on 19x19, 3-3 is (3,3) etc
    corner33 = {(3,3),(3,17),(17,3),(17,17)}
    if (move_r, move_c) in corner33:
        score += 35.0

    # slight preference for moves that give the group more liberties (resilience)
    score += 2.0 * my_libs

    return score

def policy(me, opponent):
    """
    me, opponent: lists of (row,col) with 1-based indices
    Return (row,col) for next move, or (0,0) to pass.
    """
    board = build_board(me, opponent)
    best_move = None
    best_score = None

    # enumerate all empty points and evaluate
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            if board[r][c] != 0:
                continue
            res = simulate_move_and_score(board, r, c)
            if res is None:
                continue
            # deterministic tie-breaker: prefer smaller row then col
            if best_score is None or res > best_score or (abs(res - best_score) < 1e-9 and (r, c) < best_move):
                best_score = res
                best_move = (r, c)

    if best_move is not None:
        return best_move
    # No legal moves (very unlikely) -> pass
    return (0, 0)

# If this file is executed directly, expose a simple test (not used in arena).
if __name__ == "__main__":
    # tiny smoke test: empty board
    print(policy([], []))
