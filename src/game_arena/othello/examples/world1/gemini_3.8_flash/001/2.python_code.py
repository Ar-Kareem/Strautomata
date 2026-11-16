
import time
import numpy as np

# Board constants & masks
MASK64 = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
NOT_AB = 0xFCFCFCFCFCFCFCFC
NOT_GH = 0x3F3F3F3F3F3F3F3F

DIRECTIONS = [
    (1, NOT_H, lambda b: (b << 1) & NOT_A, lambda b: (b >> 1) & NOT_H),       # E / W
    (8, MASK64, lambda b: b << 8, lambda b: b >> 8),                          # S / N
    (7, NOT_A, lambda b: (b << 7) & NOT_H, lambda b: (b >> 7) & NOT_A),       # SW / NE
    (9, NOT_H, lambda b: (b << 9) & NOT_A, lambda b: (b >> 9) & NOT_H),       # SE / NW
]

# Static position evaluation table (row-major order)
WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

# Corner indices and adjacent squares (X and C squares)
CORNERS = [0, 7, 56, 63]
X_SQUARES = {
    0: 9,
    7: 14,
    56: 49,
    63: 54
}
C_SQUARES = {
    0: (1, 8),
    7: (6, 15),
    56: (48, 57),
    63: (55, 62)
}


def get_moves(own: int, opp: int) -> int:
    """Generate bitmask of legal moves for 'own' against 'opp'."""
    empty = ~(own | opp) & MASK64
    moves = 0
    
    # 8 directional shifts
    shifts = [
        (1, NOT_A),   # East
        (7, NOT_H),   # South-West
        (8, MASK64),  # South
        (9, NOT_A),   # South-East
    ]
    
    for shift, mask in shifts:
        # Positive shift directions
        w = (own << shift) & mask & opp
        w |= (w << shift) & mask & opp
        w |= (w << shift) & mask & opp
        w |= (w << shift) & mask & opp
        w |= (w << shift) & mask & opp
        w |= (w << shift) & mask & opp
        moves |= (w << shift) & mask & empty

        # Negative shift directions
        w = (own >> shift) & (~mask if shift == 1 or shift == 9 else (NOT_H if shift == 7 else MASK64)) & opp
        # Direct clean mask for right shifts:
        # East opposite is West (>> 1, NOT_H)
        # SW opposite is NE (>> 7, NOT_A)
        # S opposite is N (>> 8, MASK64)
        # SE opposite is NW (>> 9, NOT_H)

    # Clean explicit 8-direction pass for safety and correctness
    moves = 0
    # Left / Right
    for d, m_in, m_out in [
        (1, NOT_H, NOT_A),  # E (<< 1)
        (8, MASK64, MASK64), # S (<< 8)
        (7, NOT_A, NOT_H),  # SW (<< 7)
        (9, NOT_H, NOT_A),  # SE (<< 9)
    ]:
        # Forward (<< d)
        candidates = (own << d) & m_out & opp
        for _ in range(5):
            candidates |= (candidates << d) & m_out & opp
        moves |= (candidates << d) & m_out & empty

        # Backward (>> d)
        candidates = (own >> d) & m_in & opp
        for _ in range(5):
            candidates |= (candidates >> d) & m_in & opp
        moves |= (candidates >> d) & m_in & empty

    return moves & MASK64


def make_flips(sq: int, own: int, opp: int) -> int:
    """Return the bitmask of opponent discs flipped by placing at sq."""
    move_bit = 1 << sq
    flips = 0

    shifts_masks = [
        (1, NOT_A, True),    # E: << 1
        (1, NOT_H, False),   # W: >> 1
        (8, MASK64, True),   # S: << 8
        (8, MASK64, False),  # N: >> 8
        (7, NOT_H, True),    # SW: << 7
        (7, NOT_A, False),   # NE: >> 7
        (9, NOT_A, True),    # SE: << 9
        (9, NOT_H, False),   # NW: >> 9
    ]

    for d, mask, is_left in shifts_masks:
        curr_flips = 0
        if is_left:
            cursor = (move_bit << d) & mask
            while cursor and (cursor & opp):
                curr_flips |= cursor
                cursor = (cursor << d) & mask
            if cursor and (cursor & own):
                flips |= curr_flips
        else:
            cursor = (move_bit >> d) & mask
            while cursor and (cursor & opp):
                curr_flips |= cursor
                cursor = (cursor >> d) & mask
            if cursor and (cursor & own):
                flips |= curr_flips

    return flips


def popcount(b: int) -> int:
    return bin(b).count('1')


def evaluate(own: int, opp: int, empty_count: int) -> int:
    """Static evaluation from perspective of 'own'."""
    own_count = popcount(own)
    opp_count = popcount(opp)
    
    # Endgame evaluation
    if empty_count <= 8:
        return (own_count - opp_count) * 1000

    # Positional weights
    score = 0
    o_b = own
    p_b = opp
    for i in range(64):
        bit = 1 << i
        if o_b & bit:
            score += WEIGHTS[i]
        elif p_b & bit:
            score -= WEIGHTS[i]

    # Dynamic corner & neighbor safety adjustment
    for c in CORNERS:
        c_bit = 1 << c
        x_sq = X_SQUARES[c]
        x_bit = 1 << x_sq
        if not ((own | opp) & c_bit):
            # Corner is empty: holding X-square or C-square is dangerous
            if own & x_bit:
                score -= 30
            elif opp & x_bit:
                score += 30
            for c_sq in C_SQUARES[c]:
                cs_bit = 1 << c_sq
                if own & cs_bit:
                    score -= 15
                elif opp & cs_bit:
                    score += 15
        else:
            # Corner is occupied: X-square is no longer dangerous
            if own & c_bit:
                if own & x_bit:
                    score += 25
            elif opp & c_bit:
                if opp & x_bit:
                    score -= 25

    # Mobility
    own_moves = get_moves(own, opp)
    opp_moves = get_moves(opp, own)
    own_mob = popcount(own_moves)
    opp_mob = popcount(opp_moves)
    
    mob_weight = 15 if empty_count > 20 else 8
    score += (own_mob - opp_mob) * mob_weight

    return score


class TimeoutException(Exception):
    pass


def search(own: int, opp: int, depth: int, alpha: int, beta: int, deadline: float, tt: dict) -> int:
    if time.time() > deadline:
        raise TimeoutException()

    tt_entry = tt.get((own, opp, depth))
    if tt_entry is not None:
        return tt_entry

    legal_moves = get_moves(own, opp)
    empty_count = popcount(~(own | opp) & MASK64)

    if depth == 0 or empty_count == 0:
        return evaluate(own, opp, empty_count)

    if not legal_moves:
        # Own passes
        opp_moves = get_moves(opp, own)
        if not opp_moves:
            # Game over
            own_count = popcount(own)
            opp_count = popcount(opp)
            if own_count > opp_count:
                return 100000 + (own_count - opp_count)
            elif own_count < opp_count:
                return -100000 + (own_count - opp_count)
            else:
                return 0
        # Single pass
        val = -search(opp, own, depth - 1, -beta, -alpha, deadline, tt)
        tt[(own, opp, depth)] = val
        return val

    # Move ordering
    move_list = []
    moves_bits = legal_moves
    while moves_bits:
        sq = (moves_bits & -moves_bits).bit_length() - 1
        moves_bits &= moves_bits - 1
        move_list.append((WEIGHTS[sq], sq))
    move_list.sort(key=lambda x: x[0], reverse=True)

    best_val = -10000000
    for _, sq in move_list:
        flips = make_flips(sq, own, opp)
        new_own = own | (1 << sq) | flips
        new_opp = opp & ~flips
        val = -search(new_opp, new_own, depth - 1, -beta, -alpha, deadline, tt)
        
        if val > best_val:
            best_val = val
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    tt[(own, opp, depth)] = best_val
    return best_val


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start_time = time.time()
    deadline = start_time + 0.85  # Reserve margin within 1.0s limit

    # Convert 8x8 numpy arrays to 64-bit integers
    own = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            if you[r][c] == 1:
                own |= (1 << sq)
            elif opponent[r][c] == 1:
                opp |= (1 << sq)

    legal_moves = get_moves(own, opp)
    if not legal_moves:
        return "pass"

    # Extract legal move squares
    move_candidates = []
    moves_bits = legal_moves
    while moves_bits:
        sq = (moves_bits & -moves_bits).bit_length() - 1
        moves_bits &= moves_bits - 1
        move_candidates.append(sq)

    # Single legal move: return immediately
    if len(move_candidates) == 1:
        sq = move_candidates[0]
        r, c = sq // 8, sq % 8
        return chr(ord('a') + c) + str(r + 1)

    # Prioritize corners immediately if available
    for sq in move_candidates:
        if sq in CORNERS:
            r, c = sq // 8, sq % 8
            return chr(ord('a') + c) + str(r + 1)

    # Sort initial moves by static weight
    move_candidates.sort(key=lambda s: WEIGHTS[s], reverse=True)

    best_move = move_candidates[0]
    empty_count = popcount(~(own | opp) & MASK64)
    max_search_depth = min(empty_count, 14 if empty_count <= 14 else 8)

    tt = {}

    # Iterative deepening alpha-beta search
    for depth in range(1, max_search_depth + 1):
        if time.time() > deadline:
            break

        current_best_move = best_move
        current_best_val = -10000000
        alpha = -10000000
        beta = 10000000

        # Try previous iteration's best move first
        ordered_moves = [best_move] + [sq for sq in move_candidates if sq != best_move]
        interrupted = False

        for sq in ordered_moves:
            flips = make_flips(sq, own, opp)
            new_own = own | (1 << sq) | flips
            new_opp = opp & ~flips

            try:
                val = -search(new_opp, new_own, depth - 1, -beta, -alpha, deadline, tt)
            except TimeoutException:
                interrupted = True
                break

            if val > current_best_val:
                current_best_val = val
                current_best_move = sq
            if current_best_val > alpha:
                alpha = current_best_val

        if not interrupted:
            best_move = current_best_move
            # If win is guaranteed in endgame search
            if best_move in CORNERS or current_best_val >= 90000:
                break
        else:
            break

    r = best_move // 8
    c = best_move % 8
    return chr(ord('a') + c) + str(r + 1)
