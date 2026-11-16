
import time

# Precompute winning masks (32 lines of 5 cells)
def _cell_to_bit(r, c):
    quad = (1 if r >= 3 else 0) * 2 + (1 if c >= 3 else 0)
    sub_r = r % 3
    sub_c = c % 3
    return quad * 9 + sub_r * 3 + sub_c

WIN_MASKS = []

# Horizontal
for r in range(6):
    for c in range(2):
        mask = sum(1 << _cell_to_bit(r, c + i) for i in range(5))
        WIN_MASKS.append(mask)

# Vertical
for c in range(6):
    for r in range(2):
        mask = sum(1 << _cell_to_bit(r + i, c) for i in range(5))
        WIN_MASKS.append(mask)

# Diagonals (\)
for r in range(2):
    for c in range(2):
        mask = sum(1 << _cell_to_bit(r + i, c + i) for i in range(5))
        WIN_MASKS.append(mask)

# Anti-diagonals (/)
for r in range(2):
    for c in range(4, 6):
        mask = sum(1 << _cell_to_bit(r + i, c - i) for i in range(5))
        WIN_MASKS.append(mask)

WIN_MASKS = tuple(WIN_MASKS)

# Precompute 9-bit quadrant rotation lookup tables
ROT_R = [0] * 512
ROT_L = [0] * 512

for m in range(512):
    v_r = 0
    v_l = 0
    for i in range(9):
        if (m >> i) & 1:
            sub_r, sub_c = divmod(i, 3)
            # Clockwise (R): (r, c) -> (c, 2-r)
            new_r_cw = sub_c
            new_c_cw = 2 - sub_r
            v_r |= 1 << (new_r_cw * 3 + new_c_cw)
            # Anticlockwise (L): (r, c) -> (2-c, r)
            new_r_ccw = 2 - sub_c
            new_c_ccw = sub_r
            v_l |= 1 << (new_r_ccw * 3 + new_c_ccw)
    ROT_R[m] = v_r
    ROT_L[m] = v_l

ROT_R = tuple(ROT_R)
ROT_L = tuple(ROT_L)

CENTER_MASK = (1 << _cell_to_bit(1, 1)) | (1 << _cell_to_bit(1, 4)) | (1 << _cell_to_bit(4, 1)) | (1 << _cell_to_bit(4, 4))
ALL_ONES = (1 << 36) - 1

LINE_SCORES = [0, 2, 25, 350, 4500]


def check_win(b):
    for m in WIN_MASKS:
        if (b & m) == m:
            return True
    return False


def eval_pos(you_b, opp_b):
    score = 0
    for m in WIN_MASKS:
        ym = you_b & m
        om = opp_b & m
        if om == 0 and ym > 0:
            score += LINE_SCORES[bin(ym).count('1')]
        elif ym == 0 and om > 0:
            score -= LINE_SCORES[bin(om).count('1')]
    # Center control bonus
    yc = bin(you_b & CENTER_MASK).count('1')
    oc = bin(opp_b & CENTER_MASK).count('1')
    score += (yc - oc) * 50
    return score


def generate_moves(player_b, other_b):
    occupied = player_b | other_b
    moves = []
    seen = set()
    for bit in range(36):
        if (occupied >> bit) & 1:
            continue
        temp_player = player_b | (1 << bit)
        for q in range(4):
            shift = q * 9
            mask_q = 0x1FF << shift
            clear_mask = ~mask_q
            p_q = (temp_player >> shift) & 0x1FF
            o_q = (other_b >> shift) & 0x1FF

            # Rotation L
            np_b = (temp_player & clear_mask) | (ROT_L[p_q] << shift)
            no_b = (other_b & clear_mask) | (ROT_L[o_q] << shift)
            k = (np_b, no_b)
            if k not in seen:
                seen.add(k)
                moves.append((bit, q, 'L', np_b, no_b))

            # Rotation R
            np_b = (temp_player & clear_mask) | (ROT_R[p_q] << shift)
            no_b = (other_b & clear_mask) | (ROT_R[o_q] << shift)
            k = (np_b, no_b)
            if k not in seen:
                seen.add(k)
                moves.append((bit, q, 'R', np_b, no_b))
    return moves


class TimeoutException(Exception):
    pass


def alphabeta_min(you_b, opp_b, depth, alpha, beta, ply, deadline):
    if time.time() > deadline:
        raise TimeoutException()

    occupied = you_b | opp_b
    if occupied == ALL_ONES:
        return 0

    best_val = float('inf')
    moves = generate_moves(opp_b, you_b)
    if depth > 1:
        moves.sort(key=lambda m: eval_pos(m[4], m[3]))

    for bit, q, d, no, ny in moves:
        yw = check_win(ny)
        ow = check_win(no)
        if ow and not yw:
            return -1000000 + ply
        if yw and ow:
            val = 0
        elif yw and not ow:
            val = 1000000 - ply
        elif (ny | no) == ALL_ONES:
            val = 0
        elif depth <= 1:
            val = eval_pos(ny, no)
        else:
            val = alphabeta_max(ny, no, depth - 1, alpha, beta, ply + 1, deadline)

        if val < best_val:
            best_val = val
        if best_val < beta:
            beta = best_val
        if alpha >= beta:
            break
    return best_val


def alphabeta_max(you_b, opp_b, depth, alpha, beta, ply, deadline):
    if time.time() > deadline:
        raise TimeoutException()

    occupied = you_b | opp_b
    if occupied == ALL_ONES:
        return 0

    best_val = -float('inf')
    moves = generate_moves(you_b, opp_b)
    if depth > 1:
        moves.sort(key=lambda m: eval_pos(m[3], m[4]), reverse=True)

    for bit, q, d, ny, no in moves:
        yw = check_win(ny)
        ow = check_win(no)
        if yw and not ow:
            return 1000000 - ply
        if yw and ow:
            val = 0
        elif ow and not yw:
            val = -1000000 + ply
        elif (ny | no) == ALL_ONES:
            val = 0
        elif depth <= 1:
            val = eval_pos(ny, no)
        else:
            val = alphabeta_min(ny, no, depth - 1, alpha, beta, ply + 1, deadline)

        if val > best_val:
            best_val = val
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break
    return best_val


def _bit_to_rc(bit):
    quad = bit // 9
    sub = bit % 9
    sub_r, sub_c = divmod(sub, 3)
    r = sub_r + (3 if quad >= 2 else 0)
    c = sub_c + (3 if quad % 2 == 1 else 0)
    return r, c


def policy(you, opponent) -> str:
    start_time = time.time()
    deadline = start_time + 0.85

    you_b = 0
    opp_b = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                you_b |= 1 << _cell_to_bit(r, c)
            elif opponent[r][c]:
                opp_b |= 1 << _cell_to_bit(r, c)

    root_moves = generate_moves(you_b, opp_b)
    if not root_moves:
        return "1,1,0,L"

    # Immediate 1-ply winning check
    for bit, q, d, ny, no in root_moves:
        if check_win(ny) and not check_win(no):
            r, c = _bit_to_rc(bit)
            return f"{r + 1},{c + 1},{q},{d}"

    best_move = root_moves[0]
    move_scores = {}

    for depth in range(1, 6):
        try:
            current_best = None
            current_best_val = -float('inf')
            alpha = -float('inf')
            beta = float('inf')

            for move in root_moves:
                bit, q, d, ny, no = move
                yw = check_win(ny)
                ow = check_win(no)
                if yw and not ow:
                    r, c = _bit_to_rc(bit)
                    return f"{r + 1},{c + 1},{q},{d}"
                if yw and ow:
                    val = 0
                elif ow and not yw:
                    val = -1000000 + 1
                elif (ny | no) == ALL_ONES:
                    val = 0
                elif depth <= 1:
                    val = eval_pos(ny, no)
                else:
                    val = alphabeta_min(ny, no, depth - 1, alpha, beta, 1, deadline)

                move_scores[move] = val
                if val > current_best_val:
                    current_best_val = val
                    current_best = move
                if val > alpha:
                    alpha = val

            if current_best is not None:
                best_move = current_best

            root_moves.sort(key=lambda m: move_scores.get(m, -float('inf')), reverse=True)

            if current_best_val >= 900000:
                break
            if time.time() - start_time > 0.35:
                break
        except TimeoutException:
            break

    r, c = _bit_to_rc(best_move[0])
    return f"{r + 1},{c + 1},{best_move[1]},{best_move[2]}"
