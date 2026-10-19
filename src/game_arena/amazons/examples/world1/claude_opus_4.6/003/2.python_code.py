
import numpy as np
from collections import deque

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(board):
    board = np.array(board, dtype=int)
    moves = list(gen_moves(board, 1))
    if not moves:
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"
    
    best_score = -999999
    best_move = moves[0]
    
    depth = 3 if len(moves) < 80 else 2
    if len(moves) < 30:
        depth = 4
    
    for m in sorted(moves, key=lambda m: move_heuristic(board, m), reverse=True):
        b2 = apply_move(board, m)
        score = alphabeta(b2, depth - 1, -999999, 999999, False)
        if score > best_score:
            best_score = score
            best_move = m
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"

def move_heuristic(board, m):
    b2 = apply_move(board, m)
    return evaluate(b2)

def alphabeta(board, depth, alpha, beta, maximizing):
    player = 1 if maximizing else 2
    moves = list(gen_moves(board, player))
    if not moves:
        return -10000 if maximizing else 10000
    if depth == 0:
        return evaluate(board)
    
    if maximizing:
        val = -999999
        for m in sorted(moves, key=lambda m: quick_eval(board, m, True), reverse=True)[:15]:
            b2 = apply_move(board, m)
            val = max(val, alphabeta(b2, depth-1, alpha, beta, False))
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return val
    else:
        val = 999999
        for m in sorted(moves, key=lambda m: quick_eval(board, m, False))[:15]:
            b2 = apply_move(board, m)
            val = min(val, alphabeta(b2, depth-1, alpha, beta, True))
            beta = min(beta, val)
            if alpha >= beta:
                break
        return val

def quick_eval(board, m, maximizing):
    b2 = apply_move(board, m)
    return evaluate(b2) if maximizing else -evaluate(b2)

def apply_move(board, m):
    b = board.copy()
    b[m[0], m[1]] = 0
    b[m[2], m[3]] = b[0,0] if False else board[m[0], m[1]]
    b[m[2], m[3]] = board[m[0], m[1]]
    b[m[4], m[5]] = -1
    return b

def evaluate(board):
    t1, t2 = territory(board)
    m1 = len(list(gen_moves(board, 1)))
    m2 = len(list(gen_moves(board, 2)))
    if m2 == 0 and m1 > 0: return 9999
    if m1 == 0 and m2 > 0: return -9999
    return (t1 - t2) * 3 + (m1 - m2)

def territory(board):
    dist = np.full((2, 6, 6), 999)
    for p_idx, p_val in enumerate([1, 2]):
        q = deque()
        for r in range(6):
            for c in range(6):
                if board[r, c] == p_val:
                    dist[p_idx, r, c] = 0
                    q.append((r, c, 0))
        while q:
            r, c, d = q.popleft()
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0<=nr<6 and 0<=nc<6 and board[nr,nc]==0 and dist[p_idx,nr,nc]>d+1:
                    dist[p_idx,nr,nc]=d+1
                    q.append((nr,nc,d+1))
    t1=np.sum(dist[0]<dist[1])
    t2=np.sum(dist[1]<dist[0])
    return t1, t2

def gen_moves(board, player):
    pieces = list(zip(*np.where(board == player)))
    for r, c in pieces:
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            while 0<=nr<6 and 0<=nc<6 and board[nr,nc]==0:
                for adr, adc in DIRS:
                    ar, ac = nr+adr, nc+adc
                    while 0<=ar<6 and 0<=ac<6:
                        if ar==r and ac==c:
                            yield (r,c,nr,nc,ar,ac)
                        elif board[ar,ac]==0:
                            yield (r,c,nr,nc,ar,ac)
                        else:
                            break
                        ar+=adr; ac+=adc
                nr+=dr; nc+=dc
