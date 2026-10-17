
import time
import random
import math
from collections import deque

# Lines of Action policy
# Exposes: policy(board) -> "r1,c1:r2,c2"

MAX_TIME = 0.95  # seconds, safety margin
INF = 10**9

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),  # N, S, W, E
        (-1, -1), (-1, 1), (1, -1), (1, 1)]  # diagonals

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def pieces_positions(board, p):
    res = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == p:
                res.append((r, c))
    return res

def count_line_pieces(board, r, c, dr, dc):
    # Count pieces in the line of movement (entire row, column, or diagonal)
    # dr,dc define the axis. For horizontal dr==0, for vertical dc==0, for diagonals abs(dr)==abs(dc)==1
    if dr == 0 and dc != 0:
        # horizontal: row r, all columns
        cnt = 0
        row = board[r]
        for x in row:
            if x != 0:
                cnt += 1
        return cnt
    if dc == 0 and dr != 0:
        # vertical: column c, all rows
        cnt = 0
        for i in range(8):
            if board[i][c] != 0:
                cnt += 1
        return cnt
    # diagonal
    if dr == dc:
        # NW-SE diagonal: r-c constant
        k = r - c
        cnt = 0
        for col in range(8):
            row = col + k
            if 0 <= row < 8:
                if board[row][col] != 0:
                    cnt += 1
        return cnt
    else:
        # NE-SW diagonal: r+c constant
        s = r + c
        cnt = 0
        for col in range(8):
            row = s - col
            if 0 <= row < 8:
                if board[row][col] != 0:
                    cnt += 1
        return cnt

def generate_moves_for_player(board, p):
    moves = []
    pieces = pieces_positions(board, p)
    for (r, c) in pieces:
        for (dr, dc) in DIRS:
            dist = count_line_pieces(board, r, c, dr, dc)
            if dist == 0:
                continue
            tr = r + dr * dist
            tc = c + dc * dist
            if not in_bounds(tr, tc):
                continue
            dest_val = board[tr][tc]
            # cannot land on friendly piece
            if dest_val == p:
                continue
            # check jumps: cannot jump over enemy pieces
            blocked = False
            for k in range(1, dist):
                ir = r + dr * k
                ic = c + dc * k
                if board[ir][ic] == -p:
                    blocked = True
                    break
            if blocked:
                continue
            # legal move
            moves.append(((r, c), (tr, tc)))
    return moves

def apply_move(board, move, p):
    # returns new board after player p moves
    (r1, c1), (r2, c2) = move
    newb = [row[:] for row in board]
    newb[r1][c1] = 0
    newb[r2][c2] = p
    return newb

def count_components(board, p):
    # number of connected components of pieces p using 8-neighbor adjacency
    visited = [[False]*8 for _ in range(8)]
    comps = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == p and not visited[r][c]:
                comps += 1
                # BFS
                dq = deque()
                dq.append((r,c))
                visited[r][c] = True
                while dq:
                    x,y = dq.popleft()
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if dr == 0 and dc == 0:
                                continue
                            nx, ny = x + dr, y + dc
                            if 0 <= nx < 8 and 0 <= ny < 8 and not visited[nx][ny] and board[nx][ny] == p:
                                visited[nx][ny] = True
                                dq.append((nx,ny))
    return comps

def compactness_score(board, p):
    # For each piece compute distance to nearest friendly piece (manhattan),
    # sum these minimal distances (lower = more compact).
    pos = pieces_positions(board, p)
    n = len(pos)
    if n <= 1:
        return 0
    total = 0
    for i in range(n):
        r1,c1 = pos[i]
        best = 100
        for j in range(n):
            if i == j: continue
            r2,c2 = pos[j]
            d = max(abs(r1-r2), abs(c1-c2))  # Chebyshev distance better for grid 8-dir
            if d < best:
                best = d
        if best == 100:
            best = 8
        total += best
    # smaller is better; return total
    return total

def evaluate(board, root):
    # Evaluate from root's perspective (higher is better for root)
    my = root
    opp = -root
    my_comps = count_components(board, my)
    opp_comps = count_components(board, opp)
    # Immediate win/loss
    if my_comps == 1 and len(pieces_positions(board, my)) > 1:
        return 1000000
    if opp_comps == 1 and len(pieces_positions(board, opp)) > 1:
        return -1000000
    # compactness (smaller better)
    my_compact = compactness_score(board, my)
    opp_compact = compactness_score(board, opp)
    # mobility (number of legal moves)
    my_moves = generate_moves_for_player(board, my)
    opp_moves = generate_moves_for_player(board, opp)
    mobility = len(my_moves) - len(opp_moves)
    # combine heuristics with weights
    score = 0
    # fewer components is primary objective
    score += -1200 * (my_comps - 1)
    score += 1000 * (opp_comps - 1)
    # compactness secondary
    score += -20 * my_compact
    score += 10 * opp_compact
    # mobility minor
    score += 5 * mobility
    # small random noise to break ties
    score += random.uniform(-0.5, 0.5)
    return score

def move_to_str(move):
    (r1,c1),(r2,c2) = move
    return f"{r1},{c1}:{r2},{c2}"

def order_moves(board, moves, p, root):
    # Prioritize captures, moves that reduce components, and shorter compactness
    scored = []
    base_my_comps = count_components(board, p)
    for mv in moves:
        (r1,c1),(r2,c2) = mv
        dest = board[r2][c2]
        is_capture = (dest == -p)
        newb = apply_move(board, mv, p)
        new_comps = count_components(newb, p)
        compact = compactness_score(newb, p)
        # score higher is better for the mover; but we will sort descending for mover==root, else descending for opponent?
        score = 0
        if is_capture:
            score += 500
        # prefer moves that reduce components
        score += 300 * (base_my_comps - new_comps)
        score += -10 * compact
        # also small preference for centralization
        score += - (abs(r2-3.5) + abs(c2-3.5))
        scored.append((score, mv))
    # sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for (_,mv) in scored]

def alphabeta(board, depth, alpha, beta, player, root, start_time, time_limit):
    # returns (best_score, best_move)
    # time check
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    # terminal or depth 0
    my_comps = count_components(board, root)
    opp_comps = count_components(board, -root)
    if my_comps == 1:
        return 1000000, None
    if opp_comps == 1:
        return -1000000, None
    if depth == 0:
        return evaluate(board, root), None
    moves = generate_moves_for_player(board, player)
    if not moves:
        # no moves - very bad
        if player == root:
            return -1000000, None
        else:
            return 1000000, None
    # move ordering
    moves = order_moves(board, moves, player, root)
    best_move = None
    if player == root:
        value = -INF
        for mv in moves:
            newb = apply_move(board, mv, player)
            try:
                score, _ = alphabeta(newb, depth-1, alpha, beta, -player, root, start_time, time_limit)
            except TimeoutError:
                raise
            if score > value:
                value = score
                best_move = mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = INF
        for mv in moves:
            newb = apply_move(board, mv, player)
            try:
                score, _ = alphabeta(newb, depth-1, alpha, beta, -player, root, start_time, time_limit)
            except TimeoutError:
                raise
            if score < value:
                value = score
                best_move = mv
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

def policy(board):
    """
    board: 8x8 list of lists with 0 empty, 1 our piece, -1 opponent
    returns: move string "r1,c1:r2,c2"
    """
    start_time = time.time()
    time_limit = MAX_TIME
    root = 1
    # quick win check: if any move immediately connects all pieces, choose it
    moves = generate_moves_for_player(board, root)
    random.shuffle(moves)
    for mv in moves:
        newb = apply_move(board, mv, root)
        if count_components(newb, root) == 1 and len(pieces_positions(newb, root)) > 1:
            return move_to_str(mv)
    # iterative deepening
    best_move = None
    best_score = -INF
    max_depth_cap = 4  # conservative cap to keep it fast
    try:
        for depth in range(1, max_depth_cap+1):
            # remaining time
            rem = time_limit - (time.time() - start_time)
            if rem < 0.03:
                break
            # call alphabeta, but protect with try/except for TimeoutError
            try:
                score, mv = alphabeta(board, depth, -INF, INF, root, root, start_time, time_limit)
                if mv is not None:
                    best_move = mv
                    best_score = score
                # if score is a decisive win we can stop
                if abs(score) >= 900000:
                    break
            except TimeoutError:
                break
    except Exception:
        # fallback to simple move selection
        pass
    if best_move is None:
        # fallback: choose highest-eval immediate move
        moves = generate_moves_for_player(board, root)
        if not moves:
            # no move; return an arbitrary (shouldn't happen)
            return "0,0:0,0"
        best_move = moves[0]
        best_score = -INF
        for mv in moves:
            sc = evaluate(apply_move(board, mv, root), root)
            if sc > best_score:
                best_score = sc
                best_move = mv
    return move_to_str(best_move)

# The module exposes the policy function.
if __name__ == "__main__":
    # quick random test harness (not used by arena)
    sample = [[0]*8 for _ in range(8)]
    # put some pieces
    sample[0][0] = 1
    sample[7][7] = -1
    print(policy(sample))
