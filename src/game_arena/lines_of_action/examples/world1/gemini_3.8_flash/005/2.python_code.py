
import time
import math

# Bitboard helpers
# Square index: r * 8 + c (r from 0 to 7, c from 0 to 7)
MASK64 = 0xFFFFFFFFFFFFFFFF
COL0 = 0x0101010101010101
COL7 = 0x8080808080808080

DIRECTIONS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
]

# Axis for each direction:
# 0: vertical, 1: horizontal, 2: main-diagonal (\), 3: anti-diagonal (/)
AXIS_FOR_DIR = [0, 0, 1, 1, 2, 2, 3, 3]

# Precompute tables
LINE_MASKS = [[0] * 4 for _ in range(64)]
BETWEEN_MASKS = [[0] * 64 for _ in range(64)]
TARGET_SQUARES = [[[] for _ in range(8)] for _ in range(64)]

def _init_tables():
    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            # Axis 0: vertical
            v_mask = 0
            for i in range(8):
                v_mask |= (1 << (i * 8 + c))
            LINE_MASKS[sq][0] = v_mask

            # Axis 1: horizontal
            h_mask = 0
            for i in range(8):
                h_mask |= (1 << (r * 8 + i))
            LINE_MASKS[sq][1] = h_mask

            # Axis 2: main diagonal (dr = dc)
            d1_mask = 0
            for i in range(-7, 8):
                nr, nc = r + i, c + i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    d1_mask |= (1 << (nr * 8 + nc))
            LINE_MASKS[sq][2] = d1_mask

            # Axis 3: anti diagonal (dr = -dc)
            d2_mask = 0
            for i in range(-7, 8):
                nr, nc = r + i, c - i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    d2_mask |= (1 << (nr * 8 + nc))
            LINE_MASKS[sq][3] = d2_mask

    for sq1 in range(64):
        r1, c1 = sq1 // 8, sq1 % 8
        for d_idx, (dr, dc) in enumerate(DIRECTIONS):
            for step in range(1, 8):
                r2, c2 = r1 + dr * step, c1 + dc * step
                if 0 <= r2 < 8 and 0 <= c2 < 8:
                    sq2 = r2 * 8 + c2
                    b_mask = 0
                    for s in range(1, step):
                        b_mask |= (1 << ((r1 + dr * s) * 8 + (c1 + dc * s)))
                    BETWEEN_MASKS[sq1][sq2] = b_mask
                    TARGET_SQUARES[sq1][d_idx].append((step, sq2))

_init_tables()


def is_connected(bb: int) -> bool:
    """Returns True if all pieces in bb form a single 8-connected group."""
    if bb == 0:
        return False
    # Only 1 piece is trivially connected
    if (bb & (bb - 1)) == 0:
        return True

    # Pick the lowest set bit as seed
    seed = bb & -bb
    visited = seed

    while True:
        # Expand visited 8-ways
        h = visited | ((visited & ~COL0) >> 1) | ((visited & ~COL7) << 1)
        expanded = (h | (h >> 8) | (h << 8)) & MASK64
        new_visited = expanded & bb
        if new_visited == visited:
            break
        visited = new_visited

    return visited == bb


def count_components(bb: int) -> int:
    """Returns the number of connected components."""
    if bb == 0:
        return 0
    rem = bb
    comps = 0
    while rem:
        comps += 1
        seed = rem & -rem
        visited = seed
        while True:
            h = visited | ((visited & ~COL0) >> 1) | ((visited & ~COL7) << 1)
            expanded = (h | (h >> 8) | (h << 8)) & MASK64
            new_visited = expanded & rem
            if new_visited == visited:
                break
            visited = new_visited
        rem &= ~visited
    return comps


def get_legal_moves(friendly_bb: int, enemy_bb: int):
    """Generates all legal moves for the friendly player as (sq_from, sq_to)."""
    occupied = friendly_bb | enemy_bb
    moves = []

    f = friendly_bb
    while f:
        sq = (f & -f).bit_length() - 1
        f &= f - 1

        for d_idx in range(8):
            axis = AXIS_FOR_DIR[d_idx]
            count = (occupied & LINE_MASKS[sq][axis]).bit_count()

            # Target step is exactly `count`
            targets = TARGET_SQUARES[sq][d_idx]
            if count <= len(targets):
                _, target_sq = targets[count - 1]
                # Can't land on friendly piece
                if not (friendly_bb & (1 << target_sq)):
                    # Can't jump over enemy pieces
                    if not (enemy_bb & BETWEEN_MASKS[sq][target_sq]):
                        moves.append((sq, target_sq))
    return moves


def evaluate(my_bb: int, opp_bb: int) -> float:
    """Heuristic evaluation of the board from perspective of `my_bb`."""
    my_conn = is_connected(my_bb)
    opp_conn = is_connected(opp_bb)

    if my_conn and not opp_conn:
        return 100000.0
    if opp_conn and not my_conn:
        return -100000.0
    if my_conn and opp_conn:
        # Simultaneous connection: current player to move wins
        return 100000.0

    # Dispersion / Center of mass heuristic
    def get_dispersion(bb: int):
        coords = []
        b = bb
        sr, sc = 0, 0
        n = 0
        while b:
            sq = (b & -b).bit_length() - 1
            b &= b - 1
            r, c = sq // 8, sq % 8
            coords.append((r, c))
            sr += r
            sc += c
            n += 1
        if n == 0:
            return 0.0
        mr, mc = sr / n, sc / n
        disp = 0.0
        for r, c in coords:
            disp += max(abs(r - mr), abs(c - mc))
        return disp / n

    my_disp = get_dispersion(my_bb)
    opp_disp = get_dispersion(opp_bb)

    my_comps = count_components(my_bb)
    opp_comps = count_components(opp_bb)

    # Score components:
    score = (opp_disp - my_disp) * 30.0
    score += (opp_comps - my_comps) * 50.0

    return score


class SearchTimeout(Exception):
    pass


def negamax(my_bb: int, opp_bb: int, depth: int, alpha: float, beta: float, end_time: float) -> tuple[float, tuple | None]:
    if time.time() > end_time:
        raise SearchTimeout()

    # Terminal checks
    if is_connected(my_bb):
        return 100000.0, None
    if is_connected(opp_bb):
        return -100000.0, None

    if depth == 0:
        return evaluate(my_bb, opp_bb), None

    moves = get_legal_moves(my_bb, opp_bb)
    if not moves:
        # No legal moves: lose
        return -100000.0, None

    # Move ordering heuristic: captures first, then moves toward center of mass
    sr, sc, cnt = 0, 0, 0
    b = my_bb
    while b:
        sq = (b & -b).bit_length() - 1
        b &= b - 1
        sr += sq // 8
        sc += sq % 8
        cnt += 1
    mr, mc = sr / max(1, cnt), sc / max(1, cnt)

    def move_priority(m):
        sq1, sq2 = m
        score = 0.0
        if opp_bb & (1 << sq2):
            score += 100.0  # Capture
        r2, c2 = sq2 // 8, sq2 % 8
        r1, c1 = sq1 // 8, sq1 % 8
        dist_before = abs(r1 - mr) + abs(c1 - mc)
        dist_after = abs(r2 - mr) + abs(c2 - mc)
        score += (dist_before - dist_after) * 5.0
        return score

    moves.sort(key=move_priority, reverse=True)

    best_val = -float('inf')
    best_move = moves[0]

    for m in moves:
        sq1, sq2 = m
        new_my_bb = (my_bb ^ (1 << sq1)) | (1 << sq2)
        new_opp_bb = opp_bb & ~(1 << sq2)

        # Immediate win after making move
        if is_connected(new_my_bb):
            return 90000.0 + depth, m

        # Opponent's turn: negamax recursion
        val, _ = negamax(new_opp_bb, new_my_bb, depth - 1, -beta, -alpha, end_time)
        val = -val

        if val > best_val:
            best_val = val
            best_move = m

        alpha = max(alpha, best_val)
        if alpha >= beta:
            break

    return best_val, best_move


def policy(board) -> str:
    """Lines of Action policy.
    Receives an 8x8 nested list/array of ints (1=us, -1=opponent, 0=empty).
    Returns string "from_row,from_col:to_row,to_col".
    """
    start_time = time.time()
    time_limit = 0.85  # Reserve margin within the 1-second constraint

    my_bb = 0
    opp_bb = 0
    for r in range(8):
        for c in range(8):
            val = board[r][c]
            if val == 1:
                my_bb |= (1 << (r * 8 + c))
            elif val == -1:
                opp_bb |= (1 << (r * 8 + c))

    legal_moves = get_legal_moves(my_bb, opp_bb)
    if not legal_moves:
        return "0,0:0,0"

    # Default to first legal move
    best_move = legal_moves[0]

    # Iterative deepening search
    depth = 1
    end_time = start_time + time_limit
    while depth <= 10:
        try:
            val, m = negamax(my_bb, opp_bb, depth, -float('inf'), float('inf'), end_time)
            if m is not None:
                best_move = m
            # If win is found, stop early
            if val >= 80000.0:
                break
        except SearchTimeout:
            break
        depth += 1

    sq1, sq2 = best_move
    r1, c1 = sq1 // 8, sq1 % 8
    r2, c2 = sq2 // 8, sq2 % 8
    return f"{r1},{c1}:{r2},{c2}"
