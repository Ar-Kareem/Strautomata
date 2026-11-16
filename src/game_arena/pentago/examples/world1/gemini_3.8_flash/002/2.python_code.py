
import time
import numpy as np

# ---------------------------------------------------------------------------
# Precomputed bitboard structures and constants
# ---------------------------------------------------------------------------

# Coordinates mapping: r in [0..5], c in [0..5] -> bit index 0..35
def coord_to_bit(r: int, c: int) -> int:
    return r * 6 + c

# Generate all 32 winning masks of length 5
WIN_MASKS = []

# Rows
for r in range(6):
    for c in range(2):
        mask = sum(1 << coord_to_bit(r, c + i) for i in range(5))
        WIN_MASKS.append(mask)

# Columns
for c in range(6):
    for r in range(2):
        mask = sum(1 << coord_to_bit(r + i, c) for i in range(5))
        WIN_MASKS.append(mask)

# Main diagonals (\)
for r, c in [(0, 0), (1, 1), (0, 1), (1, 0)]:
    mask = sum(1 << coord_to_bit(r + i, c + i) for i in range(5))
    WIN_MASKS.append(mask)

# Anti-diagonals (/)
for r, c in [(0, 4), (1, 5), (0, 5), (1, 4)]:
    mask = sum(1 << coord_to_bit(r + i, c - i) for i in range(5))
    WIN_MASKS.append(mask)

# Quadrant boundaries: (row_start, col_start)
QUAD_OFFSETS = [
    (0, 0),  # quad 0: top-left
    (0, 3),  # quad 1: top-right
    (3, 0),  # quad 2: bottom-left
    (3, 3),  # quad 3: bottom-right
]

# Rotation bit permutations: ROT_PERM[quad][dir_code] -> list of (old_bit, new_bit)
# dir_code: 0 for 'L' (anticlockwise), 1 for 'R' (clockwise)
ROT_MAP = {}
for q, (r_off, c_off) in enumerate(QUAD_OFFSETS):
    for d_idx, d_name in enumerate(['L', 'R']):
        mapping = list(range(36))
        for r in range(3):
            for c in range(3):
                old_bit = coord_to_bit(r_off + r, c_off + c)
                if d_name == 'R':  # Clockwise
                    new_r, new_c = c, 2 - r
                else:              # Anticlockwise ('L')
                    new_r, new_c = 2 - c, r
                new_bit = coord_to_bit(r_off + new_r, c_off + new_c)
                mapping[old_bit] = new_bit
        
        # Precompute mask for the quadrant and bit shifts for fast rotation
        quad_bits = [coord_to_bit(r_off + r, c_off + c) for r in range(3) for c in range(3)]
        clear_mask = ~sum(1 << b for b in quad_bits) & 0xFFFFFFFFF
        ROT_MAP[(q, d_name)] = (clear_mask, [(b, mapping[b]) for b in quad_bits])

def rotate_board(b: int, q: int, d: str) -> int:
    clear_mask, bit_pairs = ROT_MAP[(q, d)]
    new_b = b & clear_mask
    for old_b, new_pos in bit_pairs:
        if (b >> old_b) & 1:
            new_b |= (1 << new_pos)
    return new_b

def check_win(b: int) -> bool:
    for m in WIN_MASKS:
        if (b & m) == m:
            return True
    return False

# Invariant center cells of quadrants: (1,1), (1,4), (4,1), (4,4)
CENTER_MASK = (1 << coord_to_bit(1, 1)) | (1 << coord_to_bit(1, 4)) | \
              (1 << coord_to_bit(4, 1)) | (1 << coord_to_bit(4, 4))

def evaluate_board(my_b: int, opp_b: int) -> float:
    score = 0.0
    
    # Value invariant quadrant centers
    my_centers = bin(my_b & CENTER_MASK).count('1')
    opp_centers = bin(opp_b & CENTER_MASK).count('1')
    score += (my_centers - opp_centers) * 15.0

    # Line potential evaluation
    for m in WIN_MASKS:
        has_my = (my_b & m)
        has_opp = (opp_b & m)
        
        if has_my and not has_opp:
            cnt = bin(has_my).count('1')
            if cnt == 4:
                score += 150.0
            elif cnt == 3:
                score += 20.0
            elif cnt == 2:
                score += 4.0
        elif has_opp and not has_my:
            cnt = bin(has_opp).count('1')
            if cnt == 4:
                score -= 180.0
            elif cnt == 3:
                score -= 25.0
            elif cnt == 2:
                score -= 5.0

    return score

# ---------------------------------------------------------------------------
# Policy implementation
# ---------------------------------------------------------------------------

def policy(you, opponent) -> str:
    start_time = time.time()
    time_limit = 0.88  # stay safely within the 1.0 second limit

    # Convert inputs to 36-bit integers
    my_board = 0
    opp_board = 0
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                my_board |= (1 << coord_to_bit(r, c))
            elif opponent[r][c] == 1:
                opp_board |= (1 << coord_to_bit(r, c))

    occ = my_board | opp_board
    empty_cells = [b for b in range(36) if not ((occ >> b) & 1)]

    # Center-biased move ordering for placements
    def placement_priority(bit: int) -> int:
        r, c = bit // 6, bit % 6
        # Quadrant centers are best, followed by other central cells
        if (r in (1, 4)) and (c in (1, 4)):
            return 3
        if (1 <= r <= 4) and (1 <= c <= 4):
            return 2
        return 1

    empty_cells.sort(key=placement_priority, reverse=True)

    # Generate all candidate actions
    candidates = []
    directions = ['L', 'R']
    for bit in empty_cells:
        r = (bit // 6) + 1
        c = (bit % 6) + 1
        for q in range(4):
            for d in directions:
                candidates.append((bit, r, c, q, d))

    best_move_str = f"{candidates[0][1]},{candidates[0][2]},{candidates[0][3]},{candidates[0][4]}"
    best_score = -float('inf')

    # Pass 1: Check for an immediate win
    for bit, r, c, q, d in candidates:
        next_my = rotate_board(my_board | (1 << bit), q, d)
        next_opp = rotate_board(opp_board, q, d)
        my_win = check_win(next_my)
        opp_win = check_win(next_opp)
        
        if my_win and not opp_win:
            return f"{r},{c},{q},{d}"

    # Pass 2: Filter out moves that directly allow opponent an immediate win
    # We score moves with shallow search + heuristics
    scored_candidates = []
    for bit, r, c, q, d in candidates:
        if time.time() - start_time > time_limit:
            break

        next_my = rotate_board(my_board | (1 << bit), q, d)
        next_opp = rotate_board(opp_board, q, d)
        my_win = check_win(next_my)
        opp_win = check_win(next_opp)

        # Draw scenario
        if my_win and opp_win:
            score = -500.0
        elif opp_win:
            score = -10000.0
        else:
            score = evaluate_board(next_my, next_opp)

        scored_candidates.append((score, bit, r, c, q, d, next_my, next_opp))

    if not scored_candidates:
        return best_move_str

    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    best_score = scored_candidates[0][0]
    best_move_str = f"{scored_candidates[0][2]},{scored_candidates[0][3]},{scored_candidates[0][4]},{scored_candidates[0][5]}"

    # Pass 3: Check opponent responses to top candidates (Alpha-Beta depth 2)
    # Verify that the opponent cannot win on their immediate next turn
    top_n = min(len(scored_candidates), 28)
    refined_best_score = -float('inf')

    for i in range(top_n):
        if time.time() - start_time > time_limit:
            break

        score, bit, r, c, q, d, next_my, next_opp = scored_candidates[i]
        next_occ = next_my | next_opp
        opp_moves = [b for b in range(36) if not ((next_occ >> b) & 1)]
        opp_moves.sort(key=placement_priority, reverse=True)

        opponent_can_win = False
        worst_opp_eval = float('inf')

        # Check opponent counter-moves
        for o_bit in opp_moves:
            for o_q in range(4):
                for o_d in ('L', 'R'):
                    after_opp_opp = rotate_board(next_opp | (1 << o_bit), o_q, o_d)
                    if check_win(after_opp_opp):
                        opponent_can_win = True
                        break
                if opponent_can_win:
                    break
            if opponent_can_win:
                break

        if opponent_can_win:
            # Candidate leaves an open winning response for opponent
            candidate_val = -8000.0
        else:
            candidate_val = score

        if candidate_val > refined_best_score:
            refined_best_score = candidate_val
            best_move_str = f"{r},{c},{q},{d}"

    return best_move_str
