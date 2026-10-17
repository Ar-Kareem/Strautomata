
import numpy as np
import time

def policy(you, opponent) -> str:
    you_arr = np.array(you, dtype=np.int8)
    opp_arr = np.array(opponent, dtype=np.int8)
    
    # Convert to bitboards (bit i = row*6+col)
    def to_bb(arr):
        bb = 0
        for r in range(6):
            for c in range(6):
                if arr[r][c]:
                    bb |= 1 << (r*6+c)
        return bb
    
    me_bb = to_bb(you_arr)
    op_bb = to_bb(opp_arr)
    
    # Precompute all 5-in-a-row line masks
    lines = []
    for r in range(6):
        for c in range(2):
            mask = 0
            for i in range(5): mask |= 1<<(r*6+c+i)
            lines.append(mask)
    for c in range(6):
        for r in range(2):
            mask = 0
            for i in range(5): mask |= 1<<((r+i)*6+c)
            lines.append(mask)
    for r in range(2):
        for c in range(2):
            mask = 0
            for i in range(5): mask |= 1<<((r+i)*6+c+i)
            lines.append(mask)
    for r in range(2):
        for c in range(4, 6):
            mask = 0
            for i in range(5): mask |= 1<<((r+i)*6+c-i)
            lines.append(mask)
    
    def has_five(bb):
        for lm in lines:
            if (bb & lm) == lm:
                return True
        return False
    
    # Quadrant rotation mappings
    quad_cells = []
    for q in range(4):
        rs = (q//2)*3
        cs = (q%2)*3
        cells = []
        for r in range(3):
            for c in range(3):
                cells.append((rs+r)*6 + (cs+c))
        quad_cells.append(cells)
    
    # CW rotation: (r,c)->(c,2-r) in 3x3
    cw_perm = []
    for q in range(4):
        p = [0]*9
        for r in range(3):
            for c in range(3):
                nr, nc = c, 2-r
                p[r*3+c] = nr*3+nc
        cw_perm.append(p)
    
    def rotate_bb(bb, q, d):
        cells = quad_cells[q]
        bits = [(bb >> cells[i]) & 1 for i in range(9)]
        perm = cw_perm[q]
        if d == 'L':
            new_bits = [0]*9
            for i in range(9): new_bits[i] = bits[perm[i]]
        else:
            new_bits = [0]*9
            for i in range(9): new_bits[perm[i]] = bits[i]
        mask = 0
        for i in range(9): mask |= 1 << cells[i]
        bb2 = bb & ~mask
        for i in range(9):
            if new_bits[i]: bb2 |= 1 << cells[i]
        return bb2
    
    empties = [i for i in range(36) if not ((me_bb|op_bb)>>i & 1)]
    
    best_move = None
    best_score = -10**9
    
    for pos in empties:
        r, c = divmod(pos, 6)
        new_me = me_bb | (1 << pos)
        for q in range(4):
            for d in ['L','R']:
                rm = rotate_bb(new_me, q, d)
                ro = rotate_bb(op_bb, q, d)
                mw = has_five(rm)
                ow = has_five(ro)
                if mw and not ow:
                    return f"{r+1},{c+1},{q},{d}"
                score = 0
                if mw and ow: score = 500
                elif ow: score = -1000
                else:
                    for lm in lines:
                        mb = bin(rm & lm).count('1')
                        ob = bin(ro & lm).count('1')
                        if ob == 0: score += [0,1,10,100,1000][mb] if mb<=4 else 0
                        if mb == 0: score -= [0,1,10,100,1000][ob] if ob<=4 else 0
                if score > best_score:
                    best_score = score
                    best_move = f"{r+1},{c+1},{q},{d}"
    
    return best_move
