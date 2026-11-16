
import time

# --- PRECOMPUTED TABLES & MASKS ---

ROW_MASK = [0xFF << (r * 8) for r in range(8)]
COL_MASK = [0x0101010101010101 << c for c in range(8)]

NOT_COL_0 = ~COL_MASK[0] & 0xFFFFFFFFFFFFFFFF
NOT_COL_7 = ~COL_MASK[7] & 0xFFFFFFFFFFFFFFFF

DIAG1_MASK = [0] * 15  # r - c + 7
DIAG2_MASK = [0] * 15  # r + c
for r in range(8):
    for c in range(8):
        DIAG1_MASK[r - c + 7] |= 1 << (r * 8 + c)
        DIAG2_MASK[r + c] |= 1 << (r * 8 + c)

DIRS = [
    (0, 1),   # 0: Right
    (0, -1),  # 1: Left
    (1, 0),   # 2: Down
    (-1, 0),  # 3: Up
    (1, 1),   # 4: Down-Right
    (-1, -1), # 5: Up-Left
    (1, -1),  # 6: Down-Left
    (-1, 1),  # 7: Up-Right
]

# MOVE_TABLE[sq][d_idx][k] = (target_idx, path_mask, target_mask) or None
MOVE_TABLE = [[[None for _ in range(9)] for _ in range(8)] for _ in range(64)]

for sq in range(64):
    r = sq >> 3
    c = sq & 7
    for d_idx, (dr, dc) in enumerate(DIRS):
        for k in range(1, 9):
            tr = r + k * dr
            tc = c + k * dc
            if 0 <= tr < 8 and 0 <= tc < 8:
                t_idx = tr * 8 + tc
                path = 0
                for s in range(1, k):
                    path |= 1 << ((r + s * dr) * 8 + (c + s * dc))
                MOVE_TABLE[sq][d_idx][k] = (t_idx, path, 1 << t_idx)

CENTER_DIST = [0] * 64
for sq in range(64):
    r = sq >> 3
    c = sq & 7
    CENTER_DIST[sq] = abs(r - 3.5) + abs(c - 3.5)


def is_connected(bb: int) -> bool:
    """Checks if all bits in bb form a single 8-connected component."""
    if bb == 0:
        return False
    if (bb & (bb - 1)) == 0:
        return True

    seed = bb & -bb
    while True:
        exp = seed | ((seed & NOT_COL_0) >> 1) | ((seed & NOT_COL_7) << 1)
        exp |= (exp >> 8) | (exp << 8)
        exp &= bb
        if exp == seed:
            break
        seed = exp
    return seed == bb


def get_stats(bb: int):
    """Computes (num_components, max_component_size, dispersion) for pieces in bb."""
    if bb == 0:
        return 0, 0, 0.0
    n = bb.bit_count()
    if (bb & (bb - 1)) == 0:
        return 1, 1, 0.0

    sum_r = 0
    sum_c = 0
    temp = bb
    pts = []
    while temp:
        lsb = temp & -temp
        sq = lsb.bit_length() - 1
        pts.append(sq)
        sum_r += sq >> 3
        sum_c += sq & 7
        temp ^= lsb

    mr = sum_r / n
    mc = sum_c / n
    disp = 0.0
    for sq in pts:
        disp += max(abs((sq >> 3) - mr), abs((sq & 7) - mc))

    rem = bb
    max_c = 0
    comps = 0
    while rem:
        comps += 1
        seed = rem & -rem
        while True:
            exp = seed | ((seed & NOT_COL_0) >> 1) | ((seed & NOT_COL_7) << 1)
            exp |= (exp >> 8) | (exp << 8)
            exp &= bb
            if exp == seed:
                break
            seed = exp
        c_size = seed.bit_count()
        if c_size > max_c:
            max_c = c_size
        rem &= ~seed

    return comps, max_c, disp


def evaluate(P: int, O: int) -> float:
    """Heuristic static evaluation from perspective of player P."""
    comps_p, max_c_p, disp_p = get_stats(P)
    comps_o, max_c_o, disp_o = get_stats(O)

    n_p = P.bit_count()
    n_o = O.bit_count()

    score = (max_c_p / n_p - max_c_o / n_o) * 45.0
    score += (comps_o - comps_p) * 20.0
    score += (disp_o / n_o - disp_p / n_p) * 12.0
    return score


def generate_moves(P: int, O: int):
    """Generates all legal moves for current player P."""
    occ = P | O
    moves = []
    temp = P
    while temp:
        lsb = temp & -temp
        sq = lsb.bit_length() - 1
        temp ^= lsb

        r = sq >> 3
        c = sq & 7

        k_h = (occ & ROW_MASK[r]).bit_count()
        k_v = (occ & COL_MASK[c]).bit_count()
        k_d1 = (occ & DIAG1_MASK[r - c + 7]).bit_count()
        k_d2 = (occ & DIAG2_MASK[r + c]).bit_count()

        d_k = (
            (0, k_h), (1, k_h),
            (2, k_v), (3, k_v),
            (4, k_d1), (5, k_d1),
            (6, k_d2), (7, k_d2)
        )
        table_sq = MOVE_TABLE[sq]
        for d_idx, k in d_k:
            entry = table_sq[d_idx][k]
            if entry is not None:
                to_idx, path_mask, to_mask = entry
                if not (O & path_mask) and not (P & to_mask):
                    is_capture = bool(O & to_mask)
                    moves.append((sq, to_idx, to_mask, is_capture))

    moves.sort(key=lambda m: (m[3], -CENTER_DIST[m[1]]), reverse=True)
    return moves


class TimeoutException(Exception):
    pass


class Searcher:
    def __init__(self, time_limit=0.88):
        self.time_limit = time_limit
        self.start_time = 0
        self.tt = {}
        self.node_count = 0

    def negamax(self, P: int, O: int, depth: int, alpha: float, beta: float, ply: int) -> float:
        self.node_count += 1
        if (self.node_count & 127) == 0:
            if time.perf_counter() - self.start_time > self.time_limit:
                raise TimeoutException()

        tt_entry = self.tt.get((P, O))
        if tt_entry is not None:
            tt_depth, tt_alpha, tt_beta, tt_val = tt_entry
            if tt_depth >= depth:
                if tt_val <= tt_alpha:
                    return tt_alpha
                if tt_val >= tt_beta:
                    return tt_beta
                return tt_val

        moves = generate_moves(P, O)
        if not moves:
            return -50000.0

        if depth <= 0:
            return evaluate(P, O)

        orig_alpha = alpha
        best_val = -1000000.0

        for sq, to_idx, to_mask, _ in moves:
            new_P = (P ^ (1 << sq)) | to_mask
            new_O = O & ~to_mask

            if is_connected(new_P):
                return 100000.0 - ply

            if is_connected(new_O):
                val = -100000.0 + ply
            else:
                val = -self.negamax(new_O, new_P, depth - 1, -beta, -alpha, ply + 1)

            if val > best_val:
                best_val = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if len(self.tt) < 150000:
            self.tt[(P, O)] = (depth, orig_alpha, beta, best_val)

        return best_val


def policy(board) -> str:
    """
    Given an 8x8 LOA board where:
      1  = player to move
     -1  = opponent
      0  = empty
    Returns next move string formatted as: 'from_row,from_col:to_row,to_col'
    """
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            val = board[r][c]
            if val == 1:
                P |= 1 << (r * 8 + c)
            elif val == -1:
                O |= 1 << (r * 8 + c)

    moves = generate_moves(P, O)
    if not moves:
        return "0,0:0,0"

    # Immediate win check
    for sq, to_idx, to_mask, _ in moves:
        new_P = (P ^ (1 << sq)) | to_mask
        if is_connected(new_P):
            fr, fc = sq >> 3, sq & 7
            tr, tc = to_idx >> 3, to_idx & 7
            return f"{fr},{fc}:{tr},{tc}"

    searcher = Searcher(time_limit=0.85)
    searcher.start_time = time.perf_counter()

    best_move = moves[0]

    for depth in range(1, 10):
        current_best = None
        best_val = -1000000.0
        alpha = -1000000.0
        beta = 1000000.0

        try:
            for sq, to_idx, to_mask, _ in moves:
                new_P = (P ^ (1 << sq)) | to_mask
                new_O = O & ~to_mask

                if is_connected(new_P):
                    val = 100000.0
                elif is_connected(new_O):
                    val = -100000.0
                else:
                    val = -searcher.negamax(new_O, new_P, depth - 1, -beta, -alpha, 1)

                if val > best_val:
                    best_val = val
                    current_best = (sq, to_idx, to_mask, _)
                if val > alpha:
                    alpha = val

            if current_best is not None:
                best_move = current_best

            if best_val >= 90000.0 or best_val <= -90000.0:
                break
        except TimeoutException:
            break

    fr, fc = best_move[0] >> 3, best_move[0] & 7
    tr, tc = best_move[1] >> 3, best_move[1] & 7
    return f"{fr},{fc}:{tr},{tc}"
