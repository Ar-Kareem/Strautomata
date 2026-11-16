
def policy(you, opponent) -> str:
    # Helper to convert grid to bitboard and coordinate list
    def parse_grid(grid):
        bits = 0
        coords = []
        for r in range(6):
            for c in range(6):
                if grid[r][c] == 1:
                    bits |= (1 << (r * 6 + c))
                    coords.append((r, c))
        return bits, coords

    my_bits, my_coords = parse_grid(you)
    opp_bits, opp_coords = parse_grid(opponent)
    empty_bits = ((1 << 36) - 1) ^ (my_bits | opp_bits)
    
    # Precompute 5-in-a-row masks for checking wins
    masks = []
    # Horizontal
    for r in range(6):
        for c in range(2):
            masks.append(int('1' * 5, 2) << (r * 6 + c))
    # Vertical
    for r in range(2):
        for c in range(6):
            masks.append(int('11111', 2) << (r * 6 + c))
    # Diagonal down-right
    for r in range(2):
        for c in range(2):
            mask = 0
            for k in range(5):
                mask |= 1 << ((r+k)*6 + (c+k))
            masks.append(mask)
    # Diagonal up-right
    for r in range(4, 6):
        for c in range(2):
            mask = 0
            for k in range(5):
                mask |= 1 << ((r-k)*6 + (c+k))
            masks.append(mask)

    def get_rotated_pos(r, c, quad, direction):
        base_r = (quad // 2) * 3
        base_c = (quad % 2) * 3
        lr, lc = r - base_r, c - base_c
        if direction == 'R':
            nr, nc = lc, 2 - lr
        else:
            nr, nc = 2 - lc, lr
        return base_r + nr, base_c + nc

    def check_win(bits):
        for mask in masks:
            if (bits & mask) == mask:
                return True
        return False

    empty_cells = []
    for i in range(36):
        if (empty_bits >> i) & 1:
            empty_cells.append((i // 6, i % 6))

    # 1. Check Immediate Win
    for r, c in empty_cells:
        for q in range(4):
            for d in ['L', 'R']:
                new_my_bits = my_bits | (1 << (r * 6 + c))
                base_r = (q // 2) * 3
                base_c = (q % 2) * 3
                
                my_q_mask = 0
                opp_q_mask = 0
                for i in range(3):
                    for j in range(3):
                        bit = 1 << ((base_r + i) * 6 + (base_c + j))
                        if new_my_bits & bit: my_q_mask |= bit
                        if opp_bits & bit: opp_q_mask |= bit
                
                rot_my_q = 0
                for i in range(3):
                    for j in range(3):
                        src_bit = 1 << ((base_r + i) * 6 + (base_c + j))
                        nr, nc = get_rotated_pos(base_r + i, base_c + j, q, d)
                        dst_bit = 1 << (nr * 6 + nc)
                        if my_q_mask & src_bit: rot_my_q |= dst_bit
                
                clear_mask = 0
                for i in range(3):
                    for j in range(3):
                        clear_mask |= 1 << ((base_r + i) * 6 + (base_c + j))
                final_my = (new_my_bits & ~clear_mask) | rot_my_q
                
                if check_win(final_my):
                    return f"{r+1},{c+1},{q},{d}"

    # 2. Check Forced Block
    opp_threats = []
    for r, c in empty_cells:
        temp_opp = opp_bits | (1 << (r * 6 + c))
        if check_win(temp_opp):
            opp_threats.append((r, c))
            
    if opp_threats:
        tr, tc = opp_threats[0]
        # Attempt to block. We should choose a rotation that doesn't help them if possible.
        # But simply blocking the cell is essential.
        # Try to find a rotation that doesn't rotate their pieces into a win.
        # This is a deep check. For now, we block with a "safe" rotation preference.
        # Let's prioritize rotating a quadrant NOT containing the threat.
        for q in range(4):
            base_r = (q // 2) * 3
            base_c = (q % 2) * 3
            if not (base_r <= tr < base_r + 3 and base_c <= tc < base_c + 3):
                # Safe quadrant
                return f"{tr+1},{tc+1},{q},L"
        # If all quads contain threat (impossible on 6x6 unless threat is center, center is in 4 quads?
        # 6x6 grid: Center is (2.5, 2.5). Cells are integers.
        # (2,2), (2,3), (3,2), (3,3) are center cells. 
        # (2,2) is in Q0 and Q1? No. Q0: 0-2, 0-2. Q1: 0-2, 3-5.
        # Wait, 6x6 split: Q0 (0,1,2 rows, 0,1,2 cols). Q1 (0,1,2 rows, 3,4,5 cols).
        # A single cell cannot be in 2 quadrants. 
        # So there is always a safe quadrant.
        # Fallback:
        return f"{tr+1},{tc+1},0,L"

    # 3. Heuristic Search
    # Simple heuristic: Count lines of 3 and 4.
    def evaluate(bits):
        score = 0
        for mask in masks:
            c = bin(bits & mask).count('1')
            if c == 4: score += 100
            elif c == 3: score += 10
            elif c == 2: score += 1
        return score

    best_score = -float('inf')
    best_move = None

    for r, c in empty_cells:
        center_bonus = (3 - abs(r - 2.5) - abs(c - 2.5)) * 2
        for q in range(4):
            for d in ['L', 'R']:
                new_my = my_bits | (1 << (r * 6 + c))
                base_r = (q // 2) * 3
                base_c = (q % 2) * 3
                my_q_mask = 0
                for i in range(3):
                    for j in range(3):
                        bit = 1 << ((base_r + i) * 6 + (base_c + j))
                        if new_my & bit: my_q_mask |= bit
                
                rot_my_q = 0
                for i in range(3):
                    for j in range(3):
                        src_bit = 1 << ((base_r + i) * 6 + (base_c + j))
                        nr, nc = get_rotated_pos(base_r + i, base_c + j, q, d)
                        dst_bit = 1 << (nr * 6 + nc)
                        if my_q_mask & src_bit: rot_my_q |= dst_bit
                
                clear_mask = 0
                for i in range(3):
                    for j in range(3):
                        clear_mask |= 1 << ((base_r + i) * 6 + (base_c + j))
                final_my = (new_my & ~clear_mask) | rot_my_q
                
                if check_win(final_my):
                    return f"{r+1},{c+1},{q},{d}"
                
                # Weights
                score = evaluate(final_my) * 10 + center_bonus
                
                # Avoid bad rotations: check if we rotate opponent pieces into a win.
                # This is expensive. We assume Step 2 caught immediate losses.
                # But we can check specific case: if we rotate a quadrant containing opponent pieces.
                
                if score > best_score:
                    best_score = score
                    best_move = f"{r+1},{c+1},{q},{d}"

    if best_move:
        return best_move

    return "1,1,0,L"
