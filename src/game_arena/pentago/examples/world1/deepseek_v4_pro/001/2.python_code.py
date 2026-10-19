
import time

# Constants
FULL_MASK = (1 << 36) - 1
WIN_SCORE = 1000000
INF = WIN_SCORE * 10

# Precompute win masks (all 32 possible 5-in-a-row lines)
win_masks = []
# horizontal
for r in range(6):
    for c in range(2):
        mask = 0
        for i in range(5):
            mask |= 1 << (r * 6 + c + i)
        win_masks.append(mask)
# vertical
for c in range(6):
    for r in range(2):
        mask = 0
        for i in range(5):
            mask |= 1 << ((r + i) * 6 + c)
        win_masks.append(mask)
# diagonal \
for r, c in [(0,0), (0,1), (1,0)]:
    if r == 0 and c == 0:
        mask1 = 0
        mask2 = 0
        for i in range(5):
            mask1 |= 1 << ((r+i)*6 + (c+i))
            mask2 |= 1 << ((r+1+i)*6 + (c+1+i))
        win_masks.append(mask1)
        win_masks.append(mask2)
    else:
        mask = 0
        for i in range(5):
            mask |= 1 << ((r+i)*6 + (c+i))
        win_masks.append(mask)
# diagonal /
for r, c in [(0,5), (0,4), (1,5)]:
    if r == 0 and c == 5:
        mask1 = 0
        mask2 = 0
        for i in range(5):
            mask1 |= 1 << ((r+i)*6 + (c-i))
            mask2 |= 1 << ((r+1+i)*6 + (c-1-i))
        win_masks.append(mask1)
        win_masks.append(mask2)
    else:
        mask = 0
        for i in range(5):
            mask |= 1 << ((r+i)*6 + (c-i))
        win_masks.append(mask)

# Precompute quadrant masks and rotation mappings
quad_offsets = [(0,0), (0,3), (3,0), (3,3)]
quad_masks = [0] * 4
rotate_from = [[None, None] for _ in range(4)]
rotate_to = [[None, None] for _ in range(4)]

for quad in range(4):
    r_off, c_off = quad_offsets[quad]
    mask = 0
    for lr in range(3):
        for lc in range(3):
            r = r_off + lr
            c = c_off + lc
            mask |= 1 << (r * 6 + c)
    quad_masks[quad] = mask
    
    for dir_idx, dir_char in enumerate(['L', 'R']):
        from_list = []
        to_list = []
        for lr in range(3):
            for lc in range(3):
                r = r_off + lr
                c = c_off + lc
                from_bit = 1 << (r * 6 + c)
                if dir_char == 'L':   # anticlockwise
                    nr = r_off + (2 - lc)
                    nc = c_off + lr
                else:                 # clockwise
                    nr = r_off + lc
                    nc = c_off + (2 - lr)
                to_bit = 1 << (nr * 6 + nc)
                from_list.append(from_bit)
                to_list.append(to_bit)
        rotate_from[quad][dir_idx] = from_list
        rotate_to[quad][dir_idx] = to_list

# Priority ordering: cells near the center first
cell_info = []
for r in range(6):
    for c in range(6):
        bit = 1 << (r * 6 + c)
        dist = (r - 2.5) ** 2 + (c - 2.5) ** 2
        cell_info.append((dist, bit, r, c))
cell_info.sort(key=lambda x: x[0])
priority_bits = [bit for dist, bit, r, c in cell_info]

# Precomputed list of all (bit, quad, dir_idx) in static priority order
all_moves_priority = []
for bit in priority_bits:
    for quad in range(4):
        for dir_idx in (0, 1):
            all_moves_priority.append((bit, quad, dir_idx))

# Mapping from bit to 1-indexed (row, col)
bit_to_rc = {}
for r in range(6):
    for c in range(6):
        bit = 1 << (r * 6 + c)
        bit_to_rc[bit] = (r + 1, c + 1)


def apply_move(my, opp, bit, quad, dir_idx):
    """Apply placement + rotation; returns (new_my, new_opp)."""
    new_my = my | bit
    mask = quad_masks[quad]
    new_my_out = new_my & ~mask
    opp_out = opp & ~mask
    from_bits = rotate_from[quad][dir_idx]
    to_bits = rotate_to[quad][dir_idx]
    for i in range(9):
        if new_my & from_bits[i]:
            new_my_out |= to_bits[i]
        if opp & from_bits[i]:
            opp_out |= to_bits[i]
    return new_my_out, opp_out


def is_win(bits):
    """Return True if `bits` contains any 5-in-a-row."""
    for mask in win_masks:
        if (bits & mask) == mask:
            return True
    return False


def evaluate(my, opp):
    """Heuristic evaluation from the perspective of `my`."""
    score = 0
    for mask in win_masks:
        m = (my & mask).bit_count()
        o = (opp & mask).bit_count()
        if o == 0:
            if m == 5:
                return WIN_SCORE
            if m == 4:
                score += 1000
            elif m == 3:
                score += 100
            elif m == 2:
                score += 10
            elif m == 1:
                score += 1
        elif m == 0:
            if o == 5:
                return -WIN_SCORE
            if o == 4:
                score -= 1000
            elif o == 3:
                score -= 100
            elif o == 2:
                score -= 10
            elif o == 1:
                score -= 1
    return score


def format_move(move):
    """Convert (bit, quad, dir_idx) to 'row,col,quad,dir' string."""
    bit, quad, dir_idx = move
    row, col = bit_to_rc[bit]
    dir_char = 'L' if dir_idx == 0 else 'R'
    return f"{row},{col},{quad},{dir_char}"


def negamax(my, opp, depth, alpha, beta, start_time, time_limit):
    """Negamax search with simple static move ordering."""
    if time.perf_counter() - start_time > time_limit:
        return 0
    if depth == 0:
        return evaluate(my, opp)
    
    empty = FULL_MASK ^ (my | opp)
    if empty == 0:
        return 0  # draw
    
    for bit, quad, dir_idx in all_moves_priority:
        if bit & empty:
            if time.perf_counter() - start_time > time_limit:
                return 0
            new_my, new_opp = apply_move(my, opp, bit, quad, dir_idx)
            my_win = is_win(new_my)
            opp_win = is_win(new_opp)
            if my_win and opp_win:
                score = 0
            elif my_win:
                score = WIN_SCORE
            elif opp_win:
                score = -WIN_SCORE
            else:
                score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha, start_time, time_limit)
            if score > alpha:
                alpha = score
            if alpha >= beta:
                return alpha
    return alpha


def get_best_move(my, opp):
    """Iterative deepening root search, returns best move string."""
    start_time = time.perf_counter()
    TIME_LIMIT = 0.9
    
    empty = FULL_MASK ^ (my | opp)
    
    # Step 1: evaluate all moves statically for initial ordering
    moves = []
    for bit, quad, dir_idx in all_moves_priority:
        if bit & empty:
            new_my, new_opp = apply_move(my, opp, bit, quad, dir_idx)
            my_win = is_win(new_my)
            opp_win = is_win(new_opp)
            if my_win and opp_win:
                score = 0
            elif my_win:
                # immediate win – return at once
                return format_move((bit, quad, dir_idx))
            elif opp_win:
                score = -WIN_SCORE
            else:
                score = evaluate(new_my, new_opp)
            moves.append((score, (bit, quad, dir_idx)))
    
    moves.sort(key=lambda x: x[0], reverse=True)
    sorted_moves = [m for _, m in moves]
    
    if not sorted_moves:
        # fallback (should not be reached)
        for bit, quad, dir_idx in all_moves_priority:
            if bit & empty:
                return format_move((bit, quad, dir_idx))
        return "1,1,0,L"
    
    best_move = sorted_moves[0]
    best_score = -INF
    
    # Step 2: iterative deepening
    for depth in range(1, 10):
        alpha = -INF
        beta = INF
        current_best_move = None
        for bit, quad, dir_idx in sorted_moves:
            if time.perf_counter() - start_time > TIME_LIMIT:
                break
            new_my, new_opp = apply_move(my, opp, bit, quad, dir_idx)
            my_win = is_win(new_my)
            opp_win = is_win(new_opp)
            if my_win and opp_win:
                score = 0
            elif my_win:
                score = WIN_SCORE
            elif opp_win:
                score = -WIN_SCORE
            else:
                score = -negamax(new_opp, new_my, depth - 1, -beta, -alpha, start_time, TIME_LIMIT)
            
            if time.perf_counter() - start_time > TIME_LIMIT:
                break
            
            if score > best_score:
                best_score = score
                current_best_move = (bit, quad, dir_idx)
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        
        if time.perf_counter() - start_time > TIME_LIMIT:
            break
        
        if current_best_move is not None:
            best_move = current_best_move
        
        # forced win found – stop early
        if best_score >= WIN_SCORE:
            break
    
    return format_move(best_move)


def policy(you, opponent):
    """
    Return the next Pentago move.
    Inputs: two 6x6 arrays (you, opponent) of 0/1.
    Output: move string "row,col,quad,dir".
    """
    # Convert array-likes into bitboards
    my = 0
    opp = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                my |= 1 << (r * 6 + c)
            if opponent[r][c]:
                opp |= 1 << (r * 6 + c)
    
    return get_best_move(my, opp)
