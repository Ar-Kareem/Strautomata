
import numpy as np
import random
import time

def policy(horizontal, vertical, capture):
    H = (np.asarray(horizontal) != 0).astype(np.int8).copy()
    V = (np.asarray(vertical) != 0).astype(np.int8).copy()
    
    edges_left = 40 - int(H.sum()) - int(V.sum())
    start = time.time()
    SEARCH_LIMIT = 0.55
    
    def get_moves():
        moves = []
        for r in range(5):
            for c in range(4):
                if H[r,c] == 0:
                    moves.append(('H', r, c))
        for r in range(4):
            for c in range(5):
                if V[r,c] == 0:
                    moves.append(('V', r, c))
        return moves
    
    def would_complete(m):
        d, r, c = m
        n = 0
        if d == 'H':
            if r > 0 and H[r-1,c] + V[r-1,c] + V[r-1,c+1] == 3: n += 1
            if r < 4 and H[r+1,c] + V[r,c] + V[r,c+1] == 3: n += 1
        else:
            if c > 0 and H[r,c-1] + H[r+1,c-1] + V[r,c-1] == 3: n += 1
            if c < 4 and H[r,c] + H[r+1,c] + V[r,c+1] == 3: n += 1
        return n
    
    def creates_three(m):
        d, r, c = m
        if d == 'H':
            if r > 0 and H[r-1,c] + V[r-1,c] + V[r-1,c+1] == 2: return True
            if r < 4 and H[r+1,c] + V[r,c] + V[r,c+1] == 2: return True
        else:
            if c > 0 and H[r,c-1] + H[r+1,c-1] + V[r,c-1] == 2: return True
            if c < 4 and H[r,c] + H[r+1,c] + V[r,c+1] == 2: return True
        return False
    
    def play(m):
        d, r, c = m
        if d == 'H': H[r,c] = 1
        else: V[r,c] = 1
    
    def unplay(m):
        d, r, c = m
        if d == 'H': H[r,c] = 0
        else: V[r,c] = 0
    
    def fmt(m):
        d, r, c = m
        return f"{r},{c},{d}"
    
    timeout_flag = [False]
    
    def ab(alpha, beta, my_turn, diff):
        if time.time() - start > SEARCH_LIMIT:
            timeout_flag[0] = True
            return diff, None
        moves = get_moves()
        if not moves:
            return diff, None
        cap_moves = []
        non_cap = []
        for m in moves:
            n = would_complete(m)
            if n > 0: cap_moves.append((n, m))
            else: non_cap.append(m)
        cap_moves.sort(key=lambda x: -x[0])
        # Order non-captures: safe moves first
        safe_nc = [m for m in non_cap if not creates_three(m)]
        unsafe_nc = [m for m in non_cap if creates_three(m)]
        ordered = [m for _, m in cap_moves] + safe_nc + unsafe_nc
        
        best_move = ordered[0]
        if my_turn:
            value = -100
            for m in ordered:
                n = would_complete(m)
                play(m)
                if n > 0:
                    v, _ = ab(alpha, beta, True, diff + n)
                else:
                    v, _ = ab(alpha, beta, False, diff)
                unplay(m)
                if v > value:
                    value = v
                    best_move = m
                if value > alpha: alpha = value
                if alpha >= beta: break
                if timeout_flag[0]: break
            return value, best_move
        else:
            value = 100
            for m in ordered:
                n = would_complete(m)
                play(m)
                if n > 0:
                    v, _ = ab(alpha, beta, False, diff - n)
                else:
                    v, _ = ab(alpha, beta, True, diff)
                unplay(m)
                if v < value:
                    value = v
                    best_move = m
                if value < beta: beta = value
                if alpha >= beta: break
                if timeout_flag[0]: break
            return value, best_move
    
    if edges_left <= 13:
        _, move = ab(-100, 100, True, 0)
        if move is not None and not timeout_flag[0]:
            return fmt(move)
    
    moves = get_moves()
    if not moves:
        return "0,0,H"
    
    cap_moves = [(would_complete(m), m) for m in moves]
    cap_moves = [(n, m) for n, m in cap_moves if n > 0]
    if cap_moves:
        cap_moves.sort(key=lambda x: -x[0])
        return fmt(cap_moves[0][1])
    
    safe = [m for m in moves if not creates_three(m)]
    if safe:
        return fmt(random.choice(safe))
    
    def sim_sac(m):
        H2 = H.copy(); V2 = V.copy()
        d, r0, c0 = m
        if d == 'H': H2[r0,c0] = 1
        else: V2[r0,c0] = 1
        total = 0
        while True:
            found = False
            for r in range(5):
                if found: break
                for c in range(4):
                    if H2[r,c] == 0:
                        n = 0
                        if r > 0 and H2[r-1,c] + V2[r-1,c] + V2[r-1,c+1] == 3: n += 1
                        if r < 4 and H2[r+1,c] + V2[r,c] + V2[r,c+1] == 3: n += 1
                        if n > 0:
                            H2[r,c] = 1; total += n; found = True; break
            if found: continue
            for r in range(4):
                if found: break
                for c in range(5):
                    if V2[r,c] == 0:
                        n = 0
                        if c > 0 and H2[r,c-1] + H2[r+1,c-1] + V2[r,c-1] == 3: n += 1
                        if c < 4 and H2[r,c] + H2[r+1,c] + V2[r,c+1] == 3: n += 1
                        if n > 0:
                            V2[r,c] = 1; total += n; found = True; break
            if not found: break
        return total
    
    best_cost = 1000
    best_m = moves[0]
    for m in moves:
        cost = sim_sac(m)
        if cost < best_cost:
            best_cost = cost
            best_m = m
    return fmt(best_m)
