
import numpy as np
import time

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  1,  1,  1,  1,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  1,  1,  1,  1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100],
], dtype=float)

def get_legal_moves(me, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            if me[r][c] or opp[r][c]:
                continue
            found = False
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                cnt = 0
                while 0<=nr<8 and 0<=nc<8 and opp[nr][nc]:
                    nr+=dr; nc+=dc; cnt+=1
                if cnt>0 and 0<=nr<8 and 0<=nc<8 and me[nr][nc]:
                    found = True; break
            if found:
                moves.append((r,c))
    return moves

def apply_move(me, opp, r, c):
    me2 = me.copy(); opp2 = opp.copy()
    me2[r][c] = 1
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        flips = []
        while 0<=nr<8 and 0<=nc<8 and opp2[nr][nc]:
            flips.append((nr,nc)); nr+=dr; nc+=dc
        if flips and 0<=nr<8 and 0<=nc<8 and me2[nr][nc]:
            for fr,fc in flips:
                me2[fr][fc]=1; opp2[fr][fc]=0
    return me2, opp2

def evaluate(me, opp):
    total = int(me.sum() + opp.sum())
    if total > 55:
        # endgame: maximize disc count
        return (me.sum() - opp.sum()) * 10
    
    pos_score = float(np.sum(WEIGHTS * me) - np.sum(WEIGHTS * opp))
    
    my_moves = len(get_legal_moves(me, opp))
    opp_moves = len(get_legal_moves(opp, me))
    if my_moves + opp_moves > 0:
        mob_score = 15.0 * (my_moves - opp_moves) / (my_moves + opp_moves + 1)
    else:
        mob_score = 0
    
    # corner occupancy
    corners = [(0,0),(0,7),(7,0),(7,7)]
    corner_score = sum(10 for r,c in corners if me[r][c]) - sum(10 for r,c in corners if opp[r][c])
    
    return pos_score + mob_score + corner_score

def alphabeta(me, opp, depth, alpha, beta, maximizing, deadline):
    if time.time() > deadline:
        return evaluate(me, opp), True
    
    if depth == 0:
        return evaluate(me, opp), False
    
    if maximizing:
        moves = get_legal_moves(me, opp)
        if not moves:
            opp_moves = get_legal_moves(opp, me)
            if not opp_moves:
                diff = me.sum() - opp.sum()
                return (1000 if diff>0 else -1000 if diff<0 else 0), False
            val, to = alphabeta(opp, me, depth-1, -beta, -alpha, True, deadline)
            return -val, to
        
        best = -99999
        for r,c in moves:
            me2, opp2 = apply_move(me, opp, r, c)
            val, to = alphabeta(opp2, me2, depth-1, -beta, -alpha, True, deadline)
            val = -val
            if to: return val, True
            best = max(best, val)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best, False
    else:
        # not used in negamax style
        return evaluate(me, opp), False

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    
    if len(moves) == 1:
        r, c = moves[0]
        return chr(ord('a')+c) + str(r+1)
    
    deadline = time.time() + 0.85
    best_move = moves[0]
    
    # Order moves: corners first, then by weight
    moves.sort(key=lambda m: -WEIGHTS[m[0]][m[1]])
    
    for depth in range(1, 20):
        if time.time() > deadline - 0.05:
            break
        best_val = -99999
        current_best = moves[0]
        timed_out = False
        for r, c in moves:
            me2, opp2 = apply_move(you, opponent, r, c)
            val, to = alphabeta(opp2, me2, depth-1, -99999, -best_val, True, deadline)
            val = -val
            if to:
                timed_out = True
                break
            if val > best_val:
                best_val = val
                current_best = (r, c)
        if not timed_out:
            best_move = current_best
            # reorder moves for next iteration
            moves.sort(key=lambda m: 0 if m==best_move else 1)
    
    r, c = best_move
    return chr(ord('a')+c) + str(r+1)
