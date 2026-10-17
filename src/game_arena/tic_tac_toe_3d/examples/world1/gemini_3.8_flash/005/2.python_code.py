
import time

# --- Precomputed 3D Tic-Tac-Toe Geometry ---

def _coord_to_idx(x: int, y: int, z: int) -> int:
    return x * 9 + y * 3 + z

def _idx_to_coord(idx: int) -> tuple[int, int, int]:
    return (idx // 9, (idx % 9) // 3, idx % 3)

# Generate all 49 unique winning lines in 3x3x3
_LINES = []
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx == 0 and dy == 0 and dz == 0:
                continue
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                        if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                            p0 = (x, y, z)
                            p1 = (x + dx, y + dy, z + dz)
                            p2 = (x2, y2, z2)
                            line = tuple(sorted([p0, p1, p2]))
                            if line not in _LINES:
                                _LINES.append(line)

LINE_MASKS: tuple[int, ...] = tuple(
    (1 << _coord_to_idx(*p0)) | (1 << _coord_to_idx(*p1)) | (1 << _coord_to_idx(*p2))
    for p0, p1, p2 in _LINES
)

# For each of the 27 cells, store the line masks passing through it
CELL_LINES: tuple[tuple[int, ...], ...] = tuple(
    tuple(lm for lm in LINE_MASKS if (lm & (1 << idx)))
    for idx in range(27)
)

# Static score multiplier for cells based on line participation count
CELL_WEIGHTS: tuple[int, ...] = tuple(len(CELL_LINES[idx]) for idx in range(27))

WIN_SCORE = 100_000
TIME_LIMIT = 0.85  # Execution safety margin within 1.0s limit


def _evaluate(m1: int, m2: int) -> int:
    score = 0
    for lm in LINE_MASKS:
        b1 = (m1 & lm).bit_count()
        b2 = (m2 & lm).bit_count()
        if b1 > 0 and b2 > 0:
            continue
        if b1 == 2:
            score += 50
        elif b1 == 1:
            score += 4
        elif b2 == 2:
            score -= 55
        elif b2 == 1:
            score -= 4
    return score


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start_time = time.time()

    # Convert 3D list to bitmasks
    m1 = 0  # player 1 (our stones)
    m2 = 0  # player -1 (opponent stones)
    empty_indices = []

    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = _coord_to_idx(i, j, k)
                val = board[i][j][k]
                if val == 1:
                    m1 |= (1 << idx)
                elif val == -1:
                    m2 |= (1 << idx)
                else:
                    empty_indices.append(idx)

    # Base case: no legal moves left
    if not empty_indices:
        return (0, 0, 0)

    # Opening book: Center cell (1, 1, 1) has 13 winning lines, optimal first move
    center_idx = _coord_to_idx(1, 1, 1)
    if (m1 | m2) == 0:
        return _idx_to_coord(center_idx)

    # 1. Immediate Win Check
    for idx in empty_indices:
        bit = 1 << idx
        for lm in CELL_LINES[idx]:
            if (m1 | bit) & lm == lm:
                return _idx_to_coord(idx)

    # 2. Immediate Block Check
    block_indices = []
    for idx in empty_indices:
        bit = 1 << idx
        for lm in CELL_LINES[idx]:
            if (m2 | bit) & lm == lm:
                block_indices.append(idx)
                break

    if len(block_indices) == 1:
        # Must block immediate win
        return _idx_to_coord(block_indices[0])

    # Transposition table: (depth, flag, score, best_move)
    tt: dict[tuple[int, int, bool], tuple[int, int, int, int | None]] = {}

    def get_ordered_moves(cur_m1: int, cur_m2: int, is_max: bool, tt_move: int | None) -> list[int]:
        occupied = cur_m1 | cur_m2
        moves = [i for i in range(27) if not (occupied & (1 << i))]

        def move_priority(idx: int) -> int:
            if idx == tt_move:
                return 10_000
            bit = 1 << idx
            my_mask = cur_m1 if is_max else cur_m2
            opp_mask = cur_m2 if is_max else cur_m1
            # Check immediate win
            for lm in CELL_LINES[idx]:
                if (my_mask | bit) & lm == lm:
                    return 5_000
            # Check immediate block
            for lm in CELL_LINES[idx]:
                if (opp_mask | bit) & lm == lm:
                    return 2_500
            return CELL_WEIGHTS[idx]

        moves.sort(key=move_priority, reverse=True)
        return moves

    def alpha_beta(
        cur_m1: int,
        cur_m2: int,
        depth: int,
        alpha: int,
        beta: int,
        is_max: bool,
        last_move: int | None,
    ) -> int:
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError

        # Check win from previous move
        if last_move is not None:
            if not is_max:  # Last move was made by MAX (player 1)
                for lm in CELL_LINES[last_move]:
                    if (cur_m1 & lm) == lm:
                        return WIN_SCORE + depth
            else:  # Last move was made by MIN (player 2)
                for lm in CELL_LINES[last_move]:
                    if (cur_m2 & lm) == lm:
                        return -WIN_SCORE - depth

        occupied = cur_m1 | cur_m2
        if occupied == 0x7FFFFFF:  # All 27 cells full
            return 0

        if depth == 0:
            return _evaluate(cur_m1, cur_m2)

        tt_entry = tt.get((cur_m1, cur_m2, is_max))
        tt_move = None
        if tt_entry is not None:
            entry_depth, entry_flag, entry_score, tt_move = tt_entry
            if entry_depth >= depth:
                if entry_flag == 0:  # EXACT
                    return entry_score
                elif entry_flag == 1 and entry_score >= beta:  # LOWERBOUND
                    return entry_score
                elif entry_flag == 2 and entry_score <= alpha:  # UPPERBOUND
                    return entry_score

        moves = get_ordered_moves(cur_m1, cur_m2, is_max, tt_move)
        best_local_move = moves[0]

        if is_max:
            value = -1_000_000
            for mv in moves:
                score = alpha_beta(
                    cur_m1 | (1 << mv), cur_m2, depth - 1, alpha, beta, False, mv
                )
                if score > value:
                    value = score
                    best_local_move = mv
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = 1_000_000
            for mv in moves:
                score = alpha_beta(
                    cur_m1, cur_m2 | (1 << mv), depth - 1, alpha, beta, True, mv
                )
                if score < value:
                    value = score
                    best_local_move = mv
                beta = min(beta, value)
                if alpha >= beta:
                    break

        # Save to transposition table
        flag = 0
        if value <= alpha:
            flag = 2  # UPPERBOUND
        elif value >= beta:
            flag = 1  # LOWERBOUND
        tt[(cur_m1, cur_m2, is_max)] = (depth, flag, value, best_local_move)

        return value

    # Iterative Deepening
    best_overall_move = empty_indices[0]
    if block_indices:
        best_overall_move = block_indices[0]

    max_search_depth = min(len(empty_indices), 8)

    for depth in range(1, max_search_depth + 1):
        try:
            alpha = -1_000_000
            beta = 1_000_000
            best_depth_move = None
            best_depth_val = -1_000_000

            ordered = get_ordered_moves(m1, m2, True, best_overall_move)
            for mv in ordered:
                val = alpha_beta(
                    m1 | (1 << mv), m2, depth - 1, alpha, beta, False, mv
                )
                if val > best_depth_val:
                    best_depth_val = val
                    best_depth_move = mv
                alpha = max(alpha, best_depth_val)

            if best_depth_move is not None:
                best_overall_move = best_depth_move

            # Proven win found: take it immediately
            if best_depth_val >= WIN_SCORE:
                break

        except TimeoutError:
            break

    return _idx_to_coord(best_overall_move)
