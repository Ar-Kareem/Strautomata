
import numpy as np
from typing import List, Tuple, Optional

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def get_legal_moves(h, v):
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
        count = 0
        if h[r, c] != 0: count += 1
        if h[r+1, c] != 0: count += 1
        if v[r, c] != 0: count += 1
        if v[r, c+1] != 0: count += 1
        return count

    def boxes_completed_by(h, v, move):
        r, c, d = move
        completed = []
        if d == 'H':
            if r > 0:
                if count_sides(h, v, r-1, c) == 3 and h[r, c] == 0:
                    completed.append((r-1, c))
            if r < 4:
                if count_sides(h, v, r+1, c if c < 4 else 3) == 3 and h[r, c] == 0:
                    pass
                if r < 4 and c < 4:
                    if count_sides(h, v, r, c) == 3 and h[r, c] == 0:
                        completed.append((r, c))
            # Recalculate properly
            completed = []
            # Box above: (r-1, c)
            if r > 0 and c < 4:
                s = (1 if h[r-1, c] != 0 else 0) + (1 if v[r-1, c] != 0 else 0) + (1 if v[r-1, c+1] != 0 else 0)
                if s == 3:
                    completed.append((r-1, c))
            # Box below: (r, c)
            if r < 4 and c < 4:
                s = (1 if h[r+1, c] != 0 else 0) + (1 if v[r, c] != 0 else 0) + (1 if v[r, c+1] != 0 else 0)
                if s == 3:
                    completed.append((r, c))
        else:  # V
            # Box left: (r, c-1)
            if c > 0 and r < 4:
                s = (1 if h[r, c-1] != 0 else 0) + (1 if h[r+1, c-1] != 0 else 0) + (1 if v[r, c-1] != 0 else 0)
                if s == 3:
                    completed.append((r, c-1))
            # Box right: (r, c)
            if c < 4 and r < 4:
                s = (1 if h[r, c] != 0 else 0) + (1 if h[r+1, c] != 0 else 0) + (1 if v[r, c+1] != 0 else 0)
                if s == 3:
                    completed.append((r, c))
        return completed

    def make_move(h, v, cap, move, player):
        nh = h.copy()
        nv = v.copy()
        nc = cap.copy()
        r, c, d = move
        if d == 'H':
            nh[r, c] = player
        else:
            nv[r, c] = player
        completed = []
        # Check all 4x4 boxes for newly completed
        for br in range(4):
            for bc in range(4):
                if nc[br, bc] == 0:
                    if nh[br, bc] != 0 and nh[br+1, bc] != 0 and nv[br, bc] != 0 and nv[br, bc+1] != 0:
                        completed.append((br, bc))
                        nc[br, bc] = player
        return nh, nv, nc, len(completed) > 0

    def evaluate(h, v, cap, my_score_extra, opp_score_extra):
        my_score = np.sum(cap == 1) + my_score_extra
        opp_score = np.sum(cap == -1) + opp_score_extra
        
        # Count boxes by sides
        three_sided = 0
        two_sided = 0
        for r in range(4):
            for c in range(4):
                if cap[r, c] == 0:
                    sides = (1 if h[r, c] != 0 else 0) + (1 if h[r+1, c] != 0 else 0) + \
                            (1 if v[r, c] != 0 else 0) + (1 if v[r, c+1] != 0 else 0)
                    if sides == 3:
                        three_sided += 1
                    elif sides == 2:
                        two_sided += 1
        
        return (my_score - opp_score) * 100 - three_sided * 5

    def minimax(h, v, cap, is_maximizing, depth, alpha, beta, max_depth):
        moves = get_legal_moves(h, v)
        if not moves or depth >= max_depth:
            return evaluate(h, v, cap, 0, 0), None

        player = 1 if is_maximizing else -1
        
        # Order moves: captures first, then safe, then risky
        capturing = []
        safe = []
        risky = []
        for m in moves:
            bc = boxes_completed_by(h, v, m)
            if len(bc) > 0:
                capturing.append((m, len(bc)))
            else:
                # Check if this creates a 3-sided box
                creates_three = False
                r, c, d = m
                # Temporarily place
                if d == 'H':
                    h[r, c] = player
                else:
                    v[r, c] = player
                for br in range(4):
                    for bc2 in range(4):
                        if cap[br, bc2] == 0:
                            sides = (1 if h[br, bc2] != 0 else 0) + (1 if h[br+1, bc2] != 0 else 0) + \
                                    (1 if v[br, bc2] != 0 else 0) + (1 if v[br, bc2+1] != 0 else 0)
                            if sides == 3:
                                # Check if it was already 3 before
                                if d == 'H':
                                    h[r, c] = 0
                                else:
                                    v[r, c] = 0
                                sides_before = (1 if h[br, bc2] != 0 else 0) + (1 if h[br+1, bc2] != 0 else 0) + \
                                               (1 if v[br, bc2] != 0 else 0) + (1 if v[br, bc2+1] != 0 else 0)
                                if d == 'H':
                                    h[r, c] = player
                                else:
                                    v[r, c] = player
                                if sides_before < 3:
                                    creates_three = True
                                    break
                if d == 'H':
                    h[r, c] = 0
                else:
                    v[r, c] = 0
                if creates_three:
                    risky.append(m)
                else:
                    safe.append(m)
        
        capturing.sort(key=lambda x: -x[1])
        ordered_moves = [m for m, _ in capturing] + safe + risky

        if is_maximizing:
            best_val = -float('inf')
            best_move = ordered_moves[0]
            for m in ordered_moves:
                nh, nv, nc, captured = make_move(h, v, cap, m, 1)
                if captured:
                    val, _ = minimax(nh, nv, nc, True, depth + 1, alpha, beta, max_depth)
                else:
                    val, _ = minimax(nh, nv, nc, False, depth + 1, alpha, beta, max_depth)
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            best_val = float('inf')
            best_move = ordered_moves[0]
            for m in ordered_moves:
                nh, nv, nc, captured = make_move(h, v, cap, m, -1)
                if captured:
                    val, _ = minimax(nh, nv, nc, False, depth + 1, alpha, beta, max_depth)
                else:
                    val, _ = minimax(nh, nv, nc, True, depth + 1, alpha, beta, max_depth)
                if val < best_val:
                    best_val = val
                    best_move = m
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_move

    moves = get_legal_moves(horizontal, vertical)
    if not moves:
        return "0,0,H"  # Should not happen
    
    num_moves = len(moves)
    
    # Adaptive depth
    if num_moves <= 8:
        max_depth = 20
    elif num_moves <= 12:
        max_depth = 10
    elif num_moves <= 16:
        max_depth = 8
    elif num_moves <= 20:
        max_depth = 6
    else:
        max_depth = 4

    _, best_move = minimax(horizontal, vertical, capture, True, 0, -float('inf'), float('inf'), max_depth)
    
    if best_move is None:
        best_move = moves[0]
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
