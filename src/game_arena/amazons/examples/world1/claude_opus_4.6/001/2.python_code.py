
import numpy as np
from collections import deque
import time

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(board):
    board = np.array(board, dtype=int)
    moves = generate_moves(board, 1)
    if not moves:
        # No legal moves - shouldn't happen but return something
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"
    
    start_time = time.time()
    best_move = moves[0]
    
    # Score moves for ordering
    def quick_eval(m):
        b = board.copy()
        b[m[0], m[1]] = 0
        b[m[2], m[3]] = 1
        b[m[4], m[5]] = -1
        return evaluate(b)
    
    moves_scored = [(quick_eval(m), m) for m in moves]
    moves_scored.sort(key=lambda x: -x[0])
    moves = [m for _, m in moves_scored]
    best_move = moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > 0.7:
            break
        try:
            score, move = alphabeta(board, depth, float('-inf'), float('inf'), True, start_time)
            best_move = move
            if score > 9000:
                break
        except TimeoutError:
            break
    
    m = best_move
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"

def alphabeta(board, depth, alpha, beta, maximizing, start_time):
    if time.time() - start_time > 0.75:
        raise TimeoutError
    player = 1 if maximizing else 2
    moves = generate_moves(board, player)
    if depth == 0 or not moves:
        return evaluate(board), None
    
    # Move ordering
    if depth >= 2:
        scored = []
        for m in moves:
            b = board.copy()
            b[m[0],m[1]] = 0; b[m[2],m[3]] = player; b[m[4],m[5]] = -1
            scored.append((evaluate(b), m))
        scored.sort(key=lambda x: -x[0] if maximizing else x[0])
        moves = [m for _,m in scored]
    
    best_move = moves[0]
    if maximizing:
        val = float('-inf')
        for m in moves:
            b = board.copy()
            b[m[0],m[1]] = 0; b[m[2],m[3]] = 1; b[m[4],m[5]] = -1
            s, _ = alphabeta(b, depth-1, alpha, beta, False, start_time)
            if s > val:
                val = s; best_move = m
            alpha = max(alpha, val)
            if alpha >= beta: break
        return val, best_move
    else:
        val = float('inf')
        for m in moves:
            b = board.copy()
            b[m[0],m[1]] = 0; b[m[2],m[3]] = 2; b[m[4],m[5]] = -1
            s, _ = alphabeta(b, depth-1, alpha, beta, True, start_time)
            if s < val:
                val = s; best_move = m
            beta = min(beta, val)
            if alpha >= beta: break
        return val, best_move

def generate_moves(board, player):
    moves = []
    amazons = list(zip(*np.where(board == player)))
    for ar, ac in amazons:
        for dr, dc in DIRECTIONS:
            r, c = ar+dr, ac+dc
            while 0<=r<6 and 0<=c<6 and board[r,c]==0:
                for adr, adc in DIRECTIONS:
                    sr, sc = r+adr, c+adc
                    while 0<=sr<6 and 0<=sc<6:
                        if sr==ar and sc==ac:
                            moves.append((ar,ac,r,c,sr,sc))
                        elif board[sr,sc]==0:
                            moves.append((ar,ac,r,c,sr,sc))
                        else:
                            break
                        sr+=adr; sc+=adc
                r+=dr; c+=dc
    return moves

def evaluate(board):
    my_reach = bfs_reach(board, 1)
    opp_reach = bfs_reach(board, 2)
    my_only = np.sum((my_reach > 0) & (opp_reach == 0))
    opp_only = np.sum((opp_reach > 0) & (my_reach == 0))
    shared = np.sum((my_reach > 0) & (opp_reach > 0))
    # Who gets to shared squares first matters
    shared_adv = 0
    both = (my_reach > 0) & (opp_reach > 0)
    if np.any(both):
        shared_adv = np.sum((my_reach < opp_reach) & both) - np.sum((opp_reach < my_reach) & both)
    return (my_only - opp_only) * 3 + shared_adv + count_mobility(board, 1) * 0.1 - count_mobility(board, 2) * 0.1

def bfs_reach(board, player):
    dist = np.zeros((6,6), dtype=int)
    q = deque()
    for r, c in zip(*np.where(board == player)):
        dist[r,c] = 1
        q.append((r,c,1))
    while q:
        r,c,d = q.popleft()
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            while 0<=nr<6 and 0<=nc<6 and board[nr,nc]==0:
                if dist[nr,nc]==0:
                    dist[nr,nc] = d+1
                    q.append((nr,nc,d+1))
                nr+=dr; nc+=dc
    return dist

def count_mobility(board, player):
    count = 0
    for r, c in zip(*np.where(board == player)):
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            while 0<=nr<6 and 0<=nc<6 and board[nr,nc]==0:
                count += 1
                nr+=dr; nc+=dc
    return count
