
import time
import math
import random

# Directions: 8-way
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

WIN_SCORE = 100000

class Timeout(Exception):
    pass

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def precompute_counts(board):
    row_counts = [0]*8
    col_counts = [0]*8
    diag_counts = [0]*15   # r-c+7
    anti_counts = [0]*15   # r+c
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                anti_counts[r + c] += 1
    return row_counts, col_counts, diag_counts, anti_counts

def generate_moves(board, player):
    moves = []
    row_counts, col_counts, diag_counts, anti_counts = precompute_counts(board)
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in DIRS:
                if dr == 0:
                    count = row_counts[r]
                elif dc == 0:
                    count = col_counts[c]
                elif dr == dc:
                    count = diag_counts[r - c + 7]
                else:
                    count = anti_counts[r + c]

                tr = r + dr * count
                tc = c + dc * count
                if not in_bounds(tr, tc):
                    continue
                if board[tr][tc] == player:
                    continue

                # Check path: cannot jump over opponent
                blocked = False
                for step in range(1, count):
                    rr = r + dr * step
                    cc = c + dc * step
                    if board[rr][cc] == -player:
                        blocked = True
                        break
                if blocked:
                    continue
                moves.append((r, c, tr, tc))
    return moves

def apply_move(board, move, player):
    r, c, tr, tc = move
    newb = [row[:] for row in board]
    newb[r][c] = 0
    newb[tr][tc] = player
    return newb

def components_count(board, player):
    visited = [[False]*8 for _ in range(8)]
    comps = 0
    largest = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                comps += 1
                # BFS/DFS
                stack = [(r, c)]
                visited[r][c] = True
                size = 0
                while stack:
                    cr, cc = stack.pop()
                    size += 1
                    for dr, dc in DIRS:
                        nr, nc = cr+dr, cc+dc
                        if in_bounds(nr, nc) and not visited[nr][nc] and board[nr][nc] == player:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                largest = max(largest, size)
    if comps == 0:
        largest = 0
    return comps, largest

def adjacency_score(board, player):
    score = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                for dr, dc in DIRS:
                    nr, nc = r+dr, c+dc
                    if in_bounds(nr, nc) and board[nr][nc] == player:
                        score += 1
    return score

def center_distance(board, player):
    center = 3.5
    dist = 0.0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                dist += abs(r-center) + abs(c-center)
    return dist

def evaluate(board, player):
    myc, myl = components_count(board, player)
    oppc, oppl = components_count(board, -player)

    if oppc == 1:
        # If both connected, current player loses (opponent just moved)
        return -WIN_SCORE
    if myc == 1:
        return WIN_SCORE

    # Connectivity and size of largest component
    score = (oppc - myc) * 100 + (myl - oppl) * 10

    # Adjacency encourages clustering
    score += (adjacency_score(board, player) - adjacency_score(board, -player)) * 2

    # Centering
    score += (center_distance(board, -player) - center_distance(board, player)) * 0.5

    # Mobility (small weight)
    mymob = len(generate_moves(board, player))
    oppmob = len(generate_moves(board, -player))
    score += (mymob - oppmob) * 0.2

    return score

def move_order_key(board, move, player):
    r, c, tr, tc = move
    capture = 1 if board[tr][tc] == -player else 0
    center = 7 - (abs(tr-3.5) + abs(tc-3.5))
    return capture*10 + center

def negamax(board, depth, alpha, beta, player, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise Timeout()
    if depth == 0:
        return evaluate(board, player)

    moves = generate_moves(board, player)
    if not moves:
        return evaluate(board, player)

    # Order moves for better pruning
    moves.sort(key=lambda m: move_order_key(board, m, player), reverse=True)

    best = -math.inf
    for move in moves:
        newb = apply_move(board, move, player)
        val = -negamax(newb, depth-1, -beta, -alpha, -player, start_time, time_limit)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(board) -> str:
    start_time = time.time()
    time_limit = 0.85  # seconds

    moves = generate_moves(board, 1)
    if not moves:
        # Should not happen in LOA, but return something safe
        return "0,0:0,0"

    # Default move
    best_move = moves[0]
    best_score = -math.inf

    # Iterative deepening
    max_depth = 3
    for depth in range(1, max_depth+1):
        try:
            # Order moves for this depth
            ordered = sorted(moves, key=lambda m: move_order_key(board, m, 1), reverse=True)
            alpha = -math.inf
            beta = math.inf
            local_best = ordered[0]
            local_best_score = -math.inf
            for move in ordered:
                if time.time() - start_time > time_limit:
                    raise Timeout()
                newb = apply_move(board, move, 1)
                score = -negamax(newb, depth-1, -beta, -alpha, -1, start_time, time_limit)
                if score > local_best_score:
                    local_best_score = score
                    local_best = move
                if score > alpha:
                    alpha = score
            best_move = local_best
            best_score = local_best_score
        except Timeout:
            break

    r, c, tr, tc = best_move
    return f"{r},{c}:{tr},{tc}"
