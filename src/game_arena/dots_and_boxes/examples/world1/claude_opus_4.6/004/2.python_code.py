
import numpy as np
from typing import List, Tuple, Optional

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h = horizontal.copy()
    v = vertical.copy()
    cap = capture.copy()
    
    def get_legal_moves():
        moves = []
        for r in range(5):
            for c in range(4):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def count_sides(h, v, r, c):
        return (abs(h[r, c]) + abs(h[r+1, c]) + abs(v[r, c]) + abs(v[r, c+1]))
    
    def boxes_completed_by(h, v, r, c, d):
        completed = []
        if d == 'H':
            # horizontal edge at (r,c) borders box above (r-1,c) and below (r,c)
            if r > 0 and r-1 < 4 and c < 4:
                sides = abs(h[r-1, c]) + abs(h[r, c]) + abs(v[r-1, c]) + abs(v[r-1, c+1])
                if sides == 3:  # this move would be the 4th
                    completed.append((r-1, c))
            if r < 4 and c < 4:
                sides = abs(h[r, c]) + abs(h[r+1, c]) + abs(v[r, c]) + abs(v[r, c+1])
                if sides == 3:
                    completed.append((r, c))
        else:  # V
            if c > 0 and r < 4 and c-1 < 4:
                sides = abs(h[r, c-1]) + abs(h[r+1, c-1]) + abs(v[r, c-1]) + abs(v[r, c])
                if sides == 3:
                    completed.append((r, c-1))
            if c < 4 and r < 4:
                sides = abs(h[r, c]) + abs(h[r+1, c]) + abs(v[r, c]) + abs(v[r, c+1])
                if sides == 3:
                    completed.append((r, c))
        return completed
    
    def make_move(h, v, cap, r, c, d, player):
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()
        if d == 'H':
            h2[r, c] = player
        else:
            v2[r, c] = player
        captured = boxes_completed_by(h2, v2, r, c, d)
        for br, bc in captured:
            cap2[br, bc] = player
        return h2, v2, cap2, len(captured) > 0
    
    # Find capturing moves
    legal = get_legal_moves()
    if not legal:
        return "0,0,H"  # shouldn't happen
    
    capturing = []
    safe = []
    unsafe = []
    
    for (r, c, d) in legal:
        comps = boxes_completed_by(h, v, r, c, d)
        if comps:
            capturing.append((r, c, d, len(comps)))
        else:
            # Check if this move creates a 3-sided box for opponent
            h2, v2, cap2, _ = make_move(h, v, cap, r, c, d, 1)
            gives_opponent = False
            for br in range(4):
                for bc in range(4):
                    if cap2[br, bc] == 0:
                        s = abs(h2[br, bc]) + abs(h2[br+1, bc]) + abs(v2[br, bc]) + abs(v2[br, bc+1])
                        if s == 3:
                            # check if this box had 3 sides before
                            s_before = abs(h[br, bc]) + abs(h[br+1, bc]) + abs(v[br, bc]) + abs(v[br, bc+1])
                            if s_before < 3:
                                gives_opponent = True
                                break
                if gives_opponent:
                    break
            if gives_opponent:
                unsafe.append((r, c, d))
            else:
                safe.append((r, c, d))
    
    # If we can capture, do greedy capture chain with minimax for the rest
    if capturing:
        # Take all captures greedily (take the one that captures most first)
        capturing.sort(key=lambda x: -x[3])
        r, c, d, _ = capturing[0]
        return f"{r},{c},{d}"
    
    # If safe moves exist, pick the best one
    if safe:
        # Prefer moves that don't reduce options badly
        # Heuristic: prefer moves adjacent to boxes with fewer sides
        best_move = None
        best_score = -1000
        for (r, c, d) in safe:
            # Score: prefer interior edges, prefer edges near boxes with 0-1 sides
            score = 0
            h2, v2, cap2, _ = make_move(h, v, cap, r, c, d, 1)
            # Count how many safe moves remain for opponent
            opp_safe = 0
            for mr in range(5):
                for mc in range(4):
                    if h2[mr, mc] == 0:
                        comps = boxes_completed_by(h2, v2, mr, mc, 'H')
                        if not comps:
                            creates3 = False
                            h3 = h2.copy(); h3[mr, mc] = -1
                            for br in range(4):
                                for bc in range(4):
                                    if cap2[br, bc] == 0:
                                        s = abs(h3[br, bc]) + abs(h3[br+1, bc]) + abs(v2[br, bc]) + abs(v2[br, bc+1])
                                        if s == 3:
                                            s0 = abs(h2[br, bc]) + abs(h2[br+1, bc]) + abs(v2[br, bc]) + abs(v2[br, bc+1])
                                            if s0 < 3:
                                                creates3 = True
                                                break
                                if creates3:
                                    break
                            if not creates3:
                                opp_safe += 1
            for mr in range(4):
                for mc in range(5):
                    if v2[mr, mc] == 0:
                        comps = boxes_completed_by(h2, v2, mr, mc, 'V')
                        if not comps:
                            creates3 = False
                            v3 = v2.copy(); v3[mr, mc] = -1
                            for br in range(4):
                                for bc in range(4):
                                    if cap2[br, bc] == 0:
                                        s = abs(h2[br, bc]) + abs(h2[br+1, bc]) + abs(v3[br, bc]) + abs(v3[br, bc+1])
                                        if s == 3:
                                            s0 = abs(h2[br, bc]) + abs(h2[br+1, bc]) + abs(v2[br, bc]) + abs(v2[br, bc+1])
                                            if s0 < 3:
                                                creates3 = True
                                                break
                                if creates3:
                                    break
                            if not creates3:
                                opp_safe += 1
            # Fewer safe moves for opponent = better for us
            score = -opp_safe
            if score > best_score:
                best_score = score
                best_move = (r, c, d)
        if best_move:
            r, c, d = best_move
            return f"{r},{c},{d}"
        r, c, d = safe[0]
        return f"{r},{c},{d}"
    
    # Only unsafe moves - use minimax to find best sacrifice
    # Find chains and pick the shortest one to open
    def minimax(h, v, cap, player, depth, alpha, beta):
        legal2 = []
        for rr in range(5):
            for cc in range(4):
                if h[rr, cc] == 0:
                    legal2.append((rr, cc, 'H'))
        for rr in range(4):
            for cc in range(5):
                if v[rr, cc] == 0:
                    legal2.append((rr, cc, 'V'))
        if not legal2:
            s = np.sum(cap)
            return s, None
        if depth <= 0:
            s = np.sum(cap)
            return s, None
        
        best_val = -100 if player == 1 else 100
        best_m = legal2[0]
        for (rr, cc, dd) in legal2:
            h2, v2, cap2, got_capture = make_move(h, v, cap, rr, cc, dd, player)
            if got_capture:
                val, _ = minimax(h2, v2, cap2, player, depth - 1, alpha, beta)
            else:
                val, _ = minimax(h2, v2, cap2, -player, depth - 1, alpha, beta)
            if player == 1:
                if val > best_val:
                    best_val = val
                    best_m = (rr, cc, dd)
                alpha = max(alpha, val)
            else:
                if val < best_val:
                    best_val = val
                    best_m = (rr, cc, dd)
                beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_m
    
    remaining = len(legal)
    depth = min(remaining, 20) if remaining <= 20 else 8
    
    val, best_m = minimax(h, v, cap, 1, depth, -100, 100)
    if best_m:
        r, c, d = best_m
        return f"{r},{c},{d}"
    
    r, c, d = unsafe[0]
    return f"{r},{c},{d}"
