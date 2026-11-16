
import numpy as np
from collections import deque

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(board):
    board = np.array(board, dtype=int)
    moves = list(gen_moves(board, 1))
    if not moves:
        # Should not happen, but return something
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"
    
    # Iterative deepening
    import time
    start = time.time()
    best_move = moves[0]
    
    try:
        for depth in range(1, 20):
            if time.time() - start > 0.7:
                break
            score, move = alphabeta(board, depth, -100000, 100000, True, start)
            if move is not None:
                best_move = move
            if time.time() - start > 0.7:
                break
    except TimeoutError:
        pass
    
    m = best_move
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"

def gen_queen_moves(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        while 0<=nr<6 and 0<=nc<6 and board[nr][nc]==0:
            yield (nr, nc)
            nr+=dr; nc+=dc

def gen_moves(board, player):
    amazons = list(zip(*np.where(board == player)))
    for (fr, fc) in amazons:
        for (tr, tc) in gen_queen_moves(board, fr, fc):
            board[fr][fc] = 0
            board[tr][tc] = player
            for (ar, ac) in gen_queen_moves(board, tr, tc):
                yield (fr, fc, tr, tc, ar, ac)
            board[fr][fc] = player
            board[tr][tc] = 0

def evaluate(board):
    # Territory estimation using BFS
    dist1 = np.full((6,6), 999); dist2 = np.full((6,6), 999)
    q = deque()
    for r in range(6):
        for c in range(6):
            if board[r][c]==1: dist1[r][c]=0; q.append((r,c))
    while q:
        r,c = q.popleft()
        for dr,dc in DIRS:
            nr,nc=r+dr,c+dc
            while 0<=nr<6 and 0<=nc<6 and board[nr][nc]==0:
                if dist1[r][c]+1 < dist1[nr][nc]:
                    dist1[nr][nc]=dist1[r][c]+1; q.append((nr,nc))
                nr+=dr; nc+=dc
    q = deque()
    for r in range(6):
        for c in range(6):
            if board[r][c]==2: dist2[r][c]=0; q.append((r,c))
    while q:
        r,c = q.popleft()
        for dr,dc in DIRS:
            nr,nc=r+dr,c+dc
            while 0<=nr<6 and 0<=nc<6 and board[nr][nc]==0:
                if dist2[r][c]+1 < dist2[nr][nc]:
                    dist2[nr][nc]=dist2[r][c]+1; q.append((nr,nc))
                nr+=dr; nc+=dc
    t1 = np.sum((dist1<dist2)&(board==0))
    t2 = np.sum((dist2<dist1)&(board==0))
    m1 = sum(1 for _ in gen_moves(board,1))
    m2 = sum(1 for _ in gen_moves(board,2))
    return 3*(t1-t2) + (m1-m2)

def alphabeta(board, depth, alpha, beta, maximizing, start):
    import time
    if time.time()-start > 0.75:
        raise TimeoutError
    player = 1 if maximizing else 2
    moves = list(gen_moves(board, player))
    if not moves:
        return (-50000 if maximizing else 50000), None
    if depth == 0:
        return evaluate(board), None
    best_move = moves[0]
    if maximizing:
        val = -100000
        for m in moves:
            fr,fc,tr,tc,ar,ac = m
            board[fr][fc]=0; board[tr][tc]=1; board[ar][ac]=-1
            v,_ = alphabeta(board, depth-1, alpha, beta, False, start)
            board[fr][fc]=1; board[tr][tc]=0; board[ar][ac]=0
            if v>val: val=v; best_move=m
            alpha=max(alpha,val)
            if alpha>=beta: break
        return val, best_move
    else:
        val = 100000
        for m in moves:
            fr,fc,tr,tc,ar,ac = m
            board[fr][fc]=0; board[tr][tc]=2; board[ar][ac]=-1
            v,_ = alphabeta(board, depth-1, alpha, beta, True, start)
            board[fr][fc]=2; board[tr][tc]=0; board[ar][ac]=0
            if v<val: val=v; best_move=m
            beta=min(beta,val)
            if alpha>=beta: break
        return val, best_move
