
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h, v, cap = horizontal, vertical, capture
    
    def get_legal_moves():
        moves = []
        for row in range(5):
            for col in range(4):
                if h[row, col] == 0:
                    moves.append((row, col, 'H'))
        for row in range(4):
            for col in range(5):
                if v[row, col] == 0:
                    moves.append((row, col, 'V'))
        return moves
    
    def box_sides(r, c):
        if not (0 <= r < 4 and 0 <= c < 4):
            return -1
        return sum([h[r,c]!=0, h[r+1,c]!=0, v[r,c]!=0, v[r,c+1]!=0])
    
    def affected_boxes(row, col, d):
        boxes = []
        if d == 'H':
            if row >= 1: boxes.append((row-1, col))
            if row <= 3: boxes.append((row, col))
        else:
            if col >= 1: boxes.append((row, col-1))
            if col <= 3: boxes.append((row, col))
        return [(r,c) for r,c in boxes if 0<=r<4 and 0<=c<4 and cap[r,c]==0]
    
    def move_effect(row, col, d):
        boxes = affected_boxes(row, col, d)
        captures = sum(1 for r,c in boxes if box_sides(r,c) == 3)
        creates_3 = sum(1 for r,c in boxes if box_sides(r,c) == 2)
        return captures, creates_3
    
    def find_chains():
        two_sided = {(r,c) for r in range(4) for c in range(4) 
                     if cap[r,c]==0 and box_sides(r,c)==2}
        visited, chains = set(), []
        for start in sorted(two_sided):
            if start in visited: continue
            chain, stack = set(), [start]
            while stack:
                box = stack.pop()
                if box in visited or box not in two_sided: continue
                visited.add(box)
                chain.add(box)
                r, c = box
                if r>0 and h[r,c]==0 and (r-1,c) in two_sided: stack.append((r-1,c))
                if r<3 and h[r+1,c]==0 and (r+1,c) in two_sided: stack.append((r+1,c))
                if c>0 and v[r,c]==0 and (r,c-1) in two_sided: stack.append((r,c-1))
                if c<3 and v[r,c+1]==0 and (r,c+1) in two_sided: stack.append((r,c+1))
            if chain: chains.append(chain)
        return chains
    
    legal = get_legal_moves()
    if not legal: return "0,0,H"
    
    capturing, safe, risky = [], [], []
    for m in legal:
        caps, risk = move_effect(*m)
        if caps > 0: capturing.append((m, caps, risk))
        elif risk > 0: risky.append((m, risk))
        else: safe.append(m)
    
    if capturing:
        capturing.sort(key=lambda x: (-x[1], x[2], x[0]))
        m = capturing[0][0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    if safe:
        def safe_score(m):
            boxes = affected_boxes(*m)
            return (sum(box_sides(r,c) for r,c in boxes), len(boxes))
        safe.sort(key=lambda m: (safe_score(m), m))
        m = safe[0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    if risky:
        chains = find_chains()
        def estimate_giveaway(m):
            boxes = affected_boxes(*m)
            total, counted = 0, set()
            for r,c in boxes:
                if box_sides(r,c) == 2:
                    for i, chain in enumerate(chains):
                        if (r,c) in chain:
                            if i not in counted:
                                total += len(chain)
                                counted.add(i)
                            break
                    else:
                        total += 1
            return total
        risky_scored = [(m, estimate_giveaway(m), risk) for m, risk in risky]
        risky_scored.sort(key=lambda x: (x[1], x[2], x[0]))
        m = risky_scored[0][0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    m = legal[0]
    return f"{m[0]},{m[1]},{m[2]}"
