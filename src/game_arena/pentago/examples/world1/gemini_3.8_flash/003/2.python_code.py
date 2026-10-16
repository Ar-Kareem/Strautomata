
import time

# Precompute board geometry and bitboard masks
# Cell index: r * 6 + c, where r, c in [0, 5]

WIN_MASKS = []

# Rows
for r in range(6):
    for c in range(2):
        WIN_MASKS.append(sum(1 << (r * 6 + (c + i)) for i in range(5)))

# Columns
for c in range(6):
    for r in range(2):
        WIN_MASKS.append(sum(1 << ((r + i) * 6 + c) for i in range(5)))

# Main diagonals (\)
for r, c in [(0, 0), (1, 1), (0, 1), (1, 0)]:
    WIN_MASKS.append(sum(1 << ((r + i) * 6 + (c + i)) for i in range(5)))

# Anti-diagonals (/)
for r, c in [(0, 4), (0, 5), (1, 4), (1, 5)]:
    WIN_MASKS.append(sum(1 << ((r + i) * 6 + (c - i)) for i in range(5)))

# Quadrant cell positions
QUAD_CELLS = {
    0: [r * 6 + c for r in range(0, 3) for c in range(0, 3)],
    1: [r * 6 + c for r in range(0, 3) for c in range(3, 6)],
    2: [r * 6 + c for r in range(3, 6) for c in range(0, 3)],
    3: [r * 6 + c for r in range(3, 6) for c in range(3, 6)],
}

QUAD_MASKS = [sum(1 << idx for idx in QUAD_CELLS[q]) for q in range(4)]

# Center cells of each quadrant (invariant to rotation)
CENTER_CELLS = {1 * 6 + 1, 1 * 6 + 4, 4 * 6 + 1, 4 * 6 + 4}
CENTER_MASK = sum(1 << idx for idx in CENTER_CELLS)

# Precomputed quadrant rotation lookup tables:
# ROT_LOOKUP[quad][dir][pattern_9bit] -> 36-bit mask of the rotated quadrant
ROT_LOOKUP = {q: {'R': [0] * 512, 'L': [0] * 512} for q in range(4)}

for q in range(4):
    cells = QUAD_CELLS[q]
    for pattern in range(512):
        # Decode pattern into 3x3 grid
        grid = [[(pattern >> (lr * 3 + lc)) & 1 for lc in range(3)] for lr in range(3)]

        # Rotate 'R' (clockwise): new(lr, lc) = old(2 - lc, lr) -> old_grid[2 - lc][lr]
        mask_r = 0
        for nlr in range(3):
            for nlc in range(3):
                if grid[2 - nlc][nlr]:
                    mask_r |= (1 << cells[nlr * 3 + nlc])
        ROT_LOOKUP[q]['R'][pattern] = mask_r

        # Rotate 'L' (counter-clockwise): new(lr, lc) = old(lc, 2 - lr) -> old_grid[lc][2 - lr]
        mask_l = 0
        for nlr in range(3):
            for nlc in range(3):
                if grid[nlc][2 - nlr]:
                    mask_l |= (1 << cells[nlr * 3 + nlc])
        ROT_LOOKUP[q]['L'][pattern] = mask_l

def rotate_bb(bb: int, quad: int, direction: str) -> int:
    """Rotates quadrant `quad` of bitboard `bb` in `direction` ('L' or 'R')."""
    cells = QUAD_CELLS[quad]
    pat = 0
    for k in range(9):
        if (bb >> cells[k]) & 1:
            pat |= (1 << k)
    return (bb & ~QUAD_MASKS[quad]) | ROT_LOOKUP[quad][direction][pat]

def check_win(bb: int) -> bool:
    for m in WIN_MASKS:
        if (bb & m) == m:
            return True
    return False

def evaluate(my_bb: int, opp_bb: int) -> int:
    """Heuristic static evaluation from perspective of `my_bb`."""
    my_win = check_win(my_bb)
    opp_win = check_win(opp_bb)
    if my_win and not opp_win:
        return 1000000
    if opp_win and not my_win:
        return -1000000
    if my_win and opp_win:
        return 0

    score = 0
    # Center control bonus
    score += (bin(my_bb & CENTER_MASK).count('1') - bin(opp_bb & CENTER_MASK).count('1')) * 30

    # Line potential evaluation
    for m in WIN_MASKS:
        my_c = bin(my_bb & m).count('1')
        opp_c = bin(opp_bb & m).count('1')
        if my_c > 0 and opp_c > 0:
            continue
        if my_c == 4:
            score += 1200
        elif my_c == 3:
            score += 150
        elif my_c == 2:
            score += 15

        if opp_c == 4:
            score -= 1500
        elif opp_c == 3:
            score -= 200
        elif opp_c == 2:
            score -= 20

    return score

def policy(you, opponent) -> str:
    start_time = time.time()
    time_limit = 0.85

    # Convert boards to bitboards
    my_bb = 0
    opp_bb = 0
    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            if you[r][c] == 1:
                my_bb |= (1 << idx)
            elif opponent[r][c] == 1:
                opp_bb |= (1 << idx)

    occupied = my_bb | opp_bb
    empty_cells = [idx for idx in range(36) if not ((occupied >> idx) & 1)]

    # Prioritize center cells, then middle, then corners
    def cell_pref(idx):
        if idx in CENTER_CELLS:
            return 3
        r, c = idx // 6, idx % 6
        if 1 <= r <= 4 and 1 <= c <= 4:
            return 2
        return 1

    empty_cells.sort(key=cell_pref, reverse=True)

    rotations = [(q, d) for q in range(4) for d in ('L', 'R')]

    # Pass 1: Find immediate win or forced move
    scored_moves = []
    best_move = None
    best_score = -float('inf')

    for idx in empty_cells:
        put_my = my_bb | (1 << idx)
        put_opp = opp_bb
        for q, d in rotations:
            r_my = rotate_bb(put_my, q, d)
            r_opp = rotate_bb(put_opp, q, d)
            my_w = check_win(r_my)
            opp_w = check_win(r_opp)

            if my_w and not opp_w:
                r_1idx = (idx // 6) + 1
                c_1idx = (idx % 6) + 1
                return f"{r_1idx},{c_1idx},{q},{d}"

            if not opp_w:
                base_eval = evaluate(r_my, r_opp)
                scored_moves.append((base_eval, idx, q, d, r_my, r_opp))

    if not scored_moves:
        # Fallback if all moves give opponent a win
        idx = empty_cells[0]
        return f"{(idx // 6) + 1},{(idx % 6) + 1},0,L"

    # Sort candidates by static evaluation
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    best_move = (scored_moves[0][1], scored_moves[0][2], scored_moves[0][3])
    best_score = scored_moves[0][0]

    # Pass 2: 2-ply search on the top candidates
    candidate_limit = min(20, len(scored_moves))
    for i in range(candidate_limit):
        if time.time() - start_time > time_limit:
            break

        _, idx, q, d, after_my, after_opp = scored_moves[i]

        # Opponent's turn: find opponent's best reply
        opp_occupied = after_my | after_opp
        opp_empty = [c_idx for c_idx in range(36) if not ((opp_occupied >> c_idx) & 1)]
        opp_empty.sort(key=cell_pref, reverse=True)

        worst_opp_eval = float('inf')
        opp_can_win = False

        for o_idx in opp_empty:
            o_put_opp = after_opp | (1 << o_idx)
            o_put_my = after_my
            for oq, od in rotations:
                o_r_opp = rotate_bb(o_put_opp, oq, od)
                o_r_my = rotate_bb(o_put_my, oq, od)

                if check_win(o_r_opp) and not check_win(o_r_my):
                    worst_opp_eval = -1000000
                    opp_can_win = True
                    break

                ev = evaluate(o_r_my, o_r_opp)
                if ev < worst_opp_eval:
                    worst_opp_eval = ev

            if opp_can_win:
                break

        if worst_opp_eval > best_score:
            best_score = worst_opp_eval
            best_move = (idx, q, d)

    chosen_idx, chosen_quad, chosen_dir = best_move
    r_1idx = (chosen_idx // 6) + 1
    c_1idx = (chosen_idx % 6) + 1
    return f"{r_1idx},{c_1idx},{chosen_quad},{chosen_dir}"
