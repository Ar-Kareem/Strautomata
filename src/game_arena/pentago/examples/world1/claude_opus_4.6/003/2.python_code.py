
import numpy as np
import time

def policy(you, opponent) -> str:
    # Convert to bitboard representation
    # Bit index = row * 6 + col (0-indexed)
    my_bb = 0
    opp_bb = 0
    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            if you[r][c]:
                my_bb |= (1 << idx)
            if opponent[r][c]:
                opp_bb |= (1 << idx)
    
    # Precompute win lines (all 5-in-a-row masks)
    win_lines = []
    for r in range(6):
        for c in range(2):
            mask = 0
            for i in range(5):
                mask |= (1 << (r * 6 + c + i))
            win_lines.append(mask)
    for c in range(6):
        for r in range(2):
            mask = 0
            for i in range(5):
                mask |= (1 << ((r + i) * 6 + c))
            win_lines.append(mask)
    for r in range(2):
        for c in range(2):
            mask = 0
            for i in range(5):
                mask |= (1 << ((r + i) * 6 + c + i))
            win_lines.append(mask)
    for r in range(2):
        for c in range(4, 6):
            mask = 0
            for i in range(5):
                mask |= (1 << ((r + i) * 6 + c - i))
            win_lines.append(mask)
    
    def has_win(bb):
        for line in win_lines:
            if (bb & line) == line:
                return True
        return False
    
    # Quadrant definitions (0-indexed row, col)
    quad_cells = [
        [(r, c) for r in range(3) for c in range(3)],      # quad 0
        [(r, c) for r in range(3) for c in range(3, 6)],    # quad 1
        [(r, c) for r in range(3, 6) for c in range(3)],    # quad 2
        [(r, c) for r in range(3, 6) for c in range(3, 6)], # quad 3
    ]
    
    # Precompute rotation permutations for each quadrant
    # For a 3x3 sub-grid, clockwise rotation: (r,c) -> (c, 2-r)
    # Anticlockwise: (r,c) -> (2-c, r)
    rot_perms = {}  # (quad, dir) -> list of (from_bit, to_bit)
    for q in range(4):
        cells = quad_cells[q]
        # local coords
        base_r = cells[0][0]
        base_c = cells[0][1]
        for d in ['L', 'R']:
            perm = []
            for (r, c) in cells:
                lr, lc = r - base_r, c - base_c
                if d == 'R':
                    nr, nc = lc, 2 - lr
                else:
                    nr, nc = 2 - lc, lr
                from_bit = r * 6 + c
                to_bit = (nr + base_r) * 6 + (nc + base_c)
                perm.append((from_bit, to_bit))
            rot_perms[(q, d)] = perm
    
    def apply_rotation(bb, q, d):
        perm = rot_perms[(q, d)]
        new_bb = bb
        # Clear all bits in quadrant
        for (fb, tb) in perm:
            new_bb &= ~(1 << fb)
        # Set new bits
        for (fb, tb) in perm:
            if bb & (1 << fb):
                new_bb |= (1 << tb)
        return new_bb
    
    # Precompute quadrant bit masks for faster clearing
    quad_masks = {}
    for q in range(4):
        mask = 0
        for (r, c) in quad_cells[q]:
            mask |= (1 << (r * 6 + c))
        quad_masks[q] = mask
    
    def apply_rotation_fast(bb, q, d):
        perm = rot_perms[(q, d)]
        qmask = quad_masks[q]
        quad_bits = bb & qmask
        new_quad = 0
        for (fb, tb) in perm:
            if quad_bits & (1 << fb):
                new_quad |= (1 << tb)
        return (bb & ~qmask) | new_quad
    
    occupied = my_bb | opp_bb
    empty_cells = []
    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            if not (occupied & (1 << idx)):
                empty_cells.append((r, c, idx))
    
    all_moves = []
    for (r, c, idx) in empty_cells:
        for q in range(4):
            for d in ['L', 'R']:
                all_moves.append((r, c, idx, q, d))
    
    # Evaluation function
    def evaluate(my, opp):
        score = 0
        for line in win_lines:
            my_count = bin(my & line).count('1')
            opp_count = bin(opp & line).count('1')
            if opp_count == 0 and my_count > 0:
                if my_count == 5:
                    score += 100000
                elif my_count == 4:
                    score += 1000
                elif my_count == 3:
                    score += 50
                elif my_count == 2:
                    score += 5
            elif my_count == 0 and opp_count > 0:
                if opp_count == 5:
                    score -= 100000
                elif opp_count == 4:
                    score -= 1000
                elif opp_count == 3:
                    score -= 50
                elif opp_count == 2:
                    score -= 5
        # Center bonus
        center_bits = [14, 15, 20, 21]  # (2,2),(2,3),(3,2),(3,3)
        for b in center_bits:
            if my & (1 << b):
                score += 3
            if opp & (1 << b):
                score -= 3
        return score
    
    def get_legal_moves(my, opp):
        occ = my | opp
        moves = []
        for r in range(6):
            for c in range(6):
                idx = r * 6 + c
                if not (occ & (1 << idx)):
                    for q in range(4):
                        for d in ['L', 'R']:
                            moves.append((r, c, idx, q, d))
        return moves
    
    def apply_move(my, opp, idx, q, d):
        new_my = my | (1 << idx)
        new_my = apply_rotation_fast(new_my, q, d)
        new_opp = apply_rotation_fast(opp, q, d)
        return new_my, new_opp
    
    start_time = time.time()
    best_move = all_moves[0] if all_moves else None
    
    # Simple 1-ply search with evaluation
    best_score = -float('inf')
    for (r, c, idx, q, d) in all_moves:
        if time.time() - start_time > 0.85:
            break
        new_my, new_opp = apply_move(my_bb, opp_bb, idx, q, d)
        if has_win(new_my):
            if has_win(new_opp):
                sc = 0  # draw
            else:
                best_move = (r, c, idx, q, d)
                best_score = 999999
                break
        elif has_win(new_opp):
            sc = -999999
        else:
            sc = evaluate(new_my, new_opp)
        if sc > best_score:
            best_score = sc
            best_move = (r, c, idx, q, d)
    
    r, c, idx, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
