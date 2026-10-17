
import time

# -------------------------------------------------------------
# Precomputed Tables for 6x6 Pentago Bitboards
# -------------------------------------------------------------

# Bit index: r * 6 + c (r in 0..5, c in 0..5)
ALL_MASKS = []

# Rows (12 masks)
for r in range(6):
    ALL_MASKS.append(sum(1 << (r * 6 + c) for c in range(0, 5)))
    ALL_MASKS.append(sum(1 << (r * 6 + c) for c in range(1, 6)))

# Cols (12 masks)
for c in range(6):
    ALL_MASKS.append(sum(1 << (r * 6 + c) for r in range(0, 5)))
    ALL_MASKS.append(sum(1 << (r * 6 + c) for r in range(1, 6)))

# Diagonals (\ direction) (4 masks)
# Main diagonal: (0,0)-(4,4) and (1,1)-(5,5)
ALL_MASKS.append(sum(1 << (i * 6 + i) for i in range(0, 5)))
ALL_MASKS.append(sum(1 << (i * 6 + i) for i in range(1, 6)))
# Sub/Super diagonals of length 5
ALL_MASKS.append(sum(1 << (i * 6 + (i + 1)) for i in range(0, 5)))
ALL_MASKS.append(sum(1 << ((i + 1) * 6 + i) for i in range(0, 5)))

# Anti-diagonals (/ direction) (4 masks)
# Main anti-diagonal: (0,5)-(4,1) and (1,4)-(5,0)
ALL_MASKS.append(sum(1 << (i * 6 + (5 - i)) for i in range(0, 5)))
ALL_MASKS.append(sum(1 << ((i + 1) * 6 + (4 - i)) for i in range(0, 5)))
# Sub/Super anti-diagonals of length 5
ALL_MASKS.append(sum(1 << (i * 6 + (4 - i)) for i in range(0, 5)))
ALL_MASKS.append(sum(1 << ((i + 1) * 6 + (5 - i)) for i in range(0, 5)))

WIN_MASKS = tuple(ALL_MASKS)

# Quadrant row/col ranges
QUAD_RANGES = [
    (0, 3, 0, 3),  # Quad 0: rows 0..2, cols 0..2
    (0, 3, 3, 6),  # Quad 1: rows 0..2, cols 3..5
    (3, 6, 0, 3),  # Quad 2: rows 3..5, cols 0..2
    (3, 6, 3, 6),  # Quad 3: rows 3..5, cols 3..5
]

# Precompute bit permutations for quadrant rotations
# ROT_MAP[(quad, 'L' or 'R')][old_bit] = new_bit
ROT_MAP = {}
for q, (r_start, r_end, c_start, c_end) in enumerate(QUAD_RANGES):
    rot_R = {}
    rot_L = {}
    for r in range(6):
        for c in range(6):
            old_bit = r * 6 + c
            if r_start <= r < r_end and c_start <= c < c_end:
                lr = r - r_start
                lc = c - c_start
                # Clockwise (R): new_lr = lc, new_lc = 2 - lr
                nr_r = r_start + lc
                nc_r = c_start + (2 - lr)
                rot_R[old_bit] = nr_r * 6 + nc_r

                # Anticlockwise (L): new_lr = 2 - lc, new_lc = lr
                nr_l = r_start + (2 - lc)
                nc_l = c_start + lr
                rot_L[old_bit] = nr_l * 6 + nc_l
            else:
                rot_R[old_bit] = old_bit
                rot_L[old_bit] = old_bit
    ROT_MAP[(q, 'R')] = rot_R
    ROT_MAP[(q, 'L')] = rot_L


def rotate_board(board: int, quad: int, direction: str) -> int:
    mapping = ROT_MAP[(quad, direction)]
    new_board = 0
    b = board
    while b:
        lsb = b & -b
        bit = (lsb.bit_length() - 1)
        new_board |= (1 << mapping[bit])
        b &= b - 1
    return new_board


def check_win(board: int) -> bool:
    for m in WIN_MASKS:
        if (board & m) == m:
            return True
    return False


# Quadrant centers: invariant under rotation, highly valuable
CENTERS = (1 << (1 * 6 + 1)) | (1 << (1 * 6 + 4)) | (1 << (4 * 6 + 1)) | (1 << (4 * 6 + 4))


def evaluate_board(my_b: int, opp_b: int) -> float:
    score = 0.0

    # Center control bonus
    score += bin(my_b & CENTERS).count('1') * 15.0
    score -= bin(opp_b & CENTERS).count('1') * 15.0

    # Evaluate potential on winning lines
    for m in WIN_MASKS:
        my_cnt = bin(my_b & m).count('1')
        opp_cnt = bin(opp_b & m).count('1')

        if my_cnt > 0 and opp_cnt == 0:
            if my_cnt == 4:
                score += 300.0
            elif my_cnt == 3:
                score += 30.0
            elif my_cnt == 2:
                score += 4.0
            elif my_cnt == 1:
                score += 1.0
        elif opp_cnt > 0 and my_cnt == 0:
            if opp_cnt == 4:
                score -= 350.0
            elif opp_cnt == 3:
                score -= 35.0
            elif opp_cnt == 2:
                score -= 5.0
            elif opp_cnt == 1:
                score -= 1.0

    return score


def policy(you, opponent) -> str:
    start_time = time.time()
    time_limit = 0.88  # Safely within 1 second constraint

    # Convert inputs to bitboards
    my_board = 0
    opp_board = 0
    empty_cells = []

    for r in range(6):
        for c in range(6):
            bit = r * 6 + c
            if you[r][c] == 1:
                my_board |= (1 << bit)
            elif opponent[r][c] == 1:
                opp_board |= (1 << bit)
            else:
                empty_cells.append((r, c))

    occupied = my_board | opp_board

    # Default fallback move (first legal)
    first_r, first_c = empty_cells[0]
    best_move_str = f"{first_r + 1},{first_c + 1},0,R"

    # Pre-sort empty cells (favor center positions)
    center_coords = {(1, 1), (1, 4), (4, 1), (4, 4), (2, 2), (2, 3), (3, 2), (3, 3)}
    empty_cells.sort(key=lambda pos: 0 if pos in center_coords else 1)

    # 1. IMMEDIATE WIN CHECK (Depth 1)
    # Check if we have an instant win on this move
    winning_moves = []
    blocking_moves = []

    for r, c in empty_cells:
        put_bit = 1 << (r * 6 + c)
        my_put = my_board | put_bit

        for q in range(4):
            for d in ('L', 'R'):
                my_rot = rotate_board(my_put, q, d)
                opp_rot = rotate_board(opp_board, q, d)

                my_w = check_win(my_rot)
                opp_w = check_win(opp_rot)

                if my_w and not opp_w:
                    return f"{r + 1},{c + 1},{q},{d}"
                if my_w and opp_w:
                    winning_moves.append((r, c, q, d))

    if winning_moves:
        # A draw is better than risking a loss
        wr, wc, wq, wd = winning_moves[0]
        best_move_str = f"{wr + 1},{wc + 1},{wq},{wd}"

    # 2. IMMEDIATE OPPONENT THREAT DETECTION
    # Check opponent single-move wins
    opp_win_count = 0
    for r, c in empty_cells:
        put_bit = 1 << (r * 6 + c)
        opp_put = opp_board | put_bit
        for q in range(4):
            for d in ('L', 'R'):
                opp_rot = rotate_board(opp_put, q, d)
                my_rot = rotate_board(my_board, q, d)
                if check_win(opp_rot) and not check_win(my_rot):
                    opp_win_count += 1
                    break
            if opp_win_count > 0:
                break

    # 3. HEURISTIC SEARCH / CANDIDATE GENERATION
    # Candidate moves for our turn
    candidates = []
    for r, c in empty_cells:
        put_bit = 1 << (r * 6 + c)
        my_put = my_board | put_bit

        # Quadrant of placement
        placement_quad = (r // 3) * 2 + (c // 3)

        for q in range(4):
            for d in ('L', 'R'):
                my_rot = rotate_board(my_put, q, d)
                opp_rot = rotate_board(opp_board, q, d)

                # Skip moves where opponent immediately wins from rotation
                if check_win(opp_rot):
                    continue

                val = evaluate_board(my_rot, opp_rot)

                # Small bias to rotate the quadrant we just played in or active quadrants
                if q == placement_quad:
                    val += 2.0

                candidates.append((val, r, c, q, d, my_rot, opp_rot))

    if not candidates:
        return best_move_str

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_move_str = f"{candidates[0][1] + 1},{candidates[0][2] + 1},{candidates[0][3]},{candidates[0][4]}"

    # 4. 2-PLY VERIFICATION
    # Verify top candidates against opponent responses
    top_candidates = candidates[:min(20, len(candidates))]
    best_score = -float('inf')

    for cand_val, r, c, q, d, cand_my, cand_opp in top_candidates:
        if time.time() - start_time > time_limit:
            break

        cand_occupied = cand_my | cand_opp
        worst_opp_score = float('inf')
        opp_can_win = False

        # Generate opponent's available response cells
        opp_empty = [
            (rr, cc) for rr in range(6) for cc in range(6)
            if not (cand_occupied & (1 << (rr * 6 + cc)))
        ]

        # Prioritize center responses
        opp_empty.sort(key=lambda pos: 0 if pos in center_coords else 1)

        # Check opponent counter-moves
        for orr, occ in opp_empty:
            if opp_can_win:
                break
            opp_put_bit = 1 << (orr * 6 + occ)
            opp_counter_put = cand_opp | opp_put_bit

            for oq in range(4):
                for od in ('L', 'R'):
                    opp_counter_rot = rotate_board(opp_counter_put, oq, od)
                    my_counter_rot = rotate_board(cand_my, oq, od)

                    if check_win(opp_counter_rot) and not check_win(my_counter_rot):
                        opp_can_win = True
                        worst_opp_score = -10000.0
                        break

                    res_val = evaluate_board(my_counter_rot, opp_counter_rot)
                    if res_val < worst_opp_score:
                        worst_opp_score = res_val

                if opp_can_win:
                    break

        move_score = -10000.0 if opp_can_win else worst_opp_score
        if move_score > best_score:
            best_score = move_score
            best_move_str = f"{r + 1},{c + 1},{q},{d}"

    return best_move_str
