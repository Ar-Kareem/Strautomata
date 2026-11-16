
import numpy as np
import time
from collections import deque

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(board):
    board = np.array(board, dtype=int)
    start_time = time.time()
    time_limit = 0.85
    
    def get_queen_moves(b, r, c):
        moves = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and b[nr][nc] == 0:
                moves.append((nr, nc))
                nr += dr
                nc += dc
        return moves
    
    def gen_all_moves(b, player):
        moves = []
        positions = list(zip(*np.where(b == player)))
        for fr, fc in positions:
            amazon_moves = get_queen_moves(b, fr, fc)
            for tr, tc in amazon_moves:
                b[fr][fc] = 0
                b[tr][tc] = player
                arrow_moves = get_queen_moves(b, tr, tc)
                for ar, ac in arrow_moves:
                    moves.append((fr, fc, tr, tc, ar, ac))
                b[tr][tc] = 0
                b[fr][fc] = player
        return moves
    
    def territory_eval(b):
        q1 = deque()
        q2 = deque()
        dist1 = np.full((6,6), 999, dtype=int)
        dist2 = np.full((6,6), 999, dtype=int)
        for r in range(6):
            for c in range(6):
                if b[r][c] == 1:
                    dist1[r][c] = 0
                    q1.append((r,c))
                elif b[r][c] == 2:
                    dist2[r][c] = 0
                    q2.append((r,c))
        for dist, q in [(dist1, q1), (dist2, q2)]:
            while q:
                r, c = q.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r+dr, c+dc
                    while 0<=nr<6 and 0<=nc<6 and b[nr][nc]==0:
                        nd = dist[r][c]+1
                        if nd < dist[nr][nc]:
                            dist[nr][nc] = nd
                            q.append((nr,nc))
                        nr+=dr
                        nc+=dc
        t1 = np.sum((dist1 < dist2) & (b == 0))
        t2 = np.sum((dist2 < dist1) & (b == 0))
        return t1 - t2
    
    def evaluate(b):
        m1 = len(gen_all_moves(b, 1))
        m2 = len(gen_all_moves(b, 2))
        if m1 == 0 and m2 == 0:
            return 0
        if m1 == 0:
            return -1000
        if m2 == 0:
            return 1000
        t = territory_eval(b)
        return t * 3 + (m1 - m2)
    
    def minimax(b, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(b), None
        player = 1 if maximizing else 2
        moves = gen_all_moves(b, player)
        if not moves:
            return (-1000 if maximizing else 1000), None
        if depth == 0:
            return evaluate(b), None
        best_move = moves[0]
        if maximizing:
            val = -9999
            for m in moves:
                fr,fc,tr,tc,ar,ac = m
                b[fr][fc]=0; b[tr][tc]=1; b[ar][ac]=-1
                v, _ = minimax(b, depth-1, alpha, beta, False)
                b[ar][ac]=0; b[tr][tc]=0; b[fr][fc]=1
                if v > val:
                    val = v; best_move = m
                alpha = max(alpha, v)
                if alpha >= beta or time.time()-start_time > time_limit:
                    break
            return val, best_move
        else:
            val = 9999
            for m in moves:
                fr,fc,tr,tc,ar,ac = m
                b[fr][fc]=0; b[tr][tc]=2; b[ar][ac]=-1
                v, _ = minimax(b, depth-1, alpha, beta, True)
                b[ar][ac]=0; b[tr][tc]=0; b[fr][fc]=2
                if v < val:
                    val = v; best_move = m
                beta = min(beta, v)
                if alpha >= beta or time.time()-start_time > time_limit:
                    break
            return val, best_move
    
    best_overall = None
    b = board.copy()
    
    # Quick fallback
    moves = gen_all_moves(b, 1)
    if not moves:
        # Should not happen, but return something
        return "0,0:0,1:0,2"
    best_overall = moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > time_limit:
            break
        val, move = minimax(b, depth, -9999, 9999, True)
        if move is not None:
            best_overall = move
        if time.time() - start_time > time_limit:
            break
        if abs(val) >= 999:
            break
    
    fr,fc,tr,tc,ar,ac = best_overall
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
