
import time

def _coord_to_idx(x: int, y: int, z: int) -> int:
    return x * 9 + y * 3 + z

def _idx_to_coord(idx: int) -> tuple[int, int, int]:
    return idx // 9, (idx % 9) // 3, idx % 3

# Precompute all 49 winning lines
def _init_lines():
    lines = []
    # 27 axis-parallel lines
    for i in range(3):
        for j in range(3):
            lines.append((_coord_to_idx(i, j, 0), _coord_to_idx(i, j, 1), _coord_to_idx(i, j, 2)))
            lines.append((_coord_to_idx(i, 0, j), _coord_to_idx(i, 1, j), _coord_to_idx(i, 2, j)))
            lines.append((_coord_to_idx(0, i, j), _coord_to_idx(1, i, j), _coord_to_idx(2, i, j)))

    # 18 planar diagonals
    for i in range(3):
        # x = i plane
        lines.append((_coord_to_idx(i, 0, 0), _coord_to_idx(i, 1, 1), _coord_to_idx(i, 2, 2)))
        lines.append((_coord_to_idx(i, 0, 2), _coord_to_idx(i, 1, 1), _coord_to_idx(i, 2, 0)))
        # y = i plane
        lines.append((_coord_to_idx(0, i, 0), _coord_to_idx(1, i, 1), _coord_to_idx(2, i, 2)))
        lines.append((_coord_to_idx(0, i, 2), _coord_to_idx(1, i, 1), _coord_to_idx(2, i, 0)))
        # z = i plane
        lines.append((_coord_to_idx(0, 0, i), _coord_to_idx(1, 1, i), _coord_to_idx(2, 2, i)))
        lines.append((_coord_to_idx(0, 2, i), _coord_to_idx(1, 1, i), _coord_to_idx(2, 0, i)))

    # 4 space diagonals
    lines.append((_coord_to_idx(0, 0, 0), _coord_to_idx(1, 1, 1), _coord_to_idx(2, 2, 2)))
    lines.append((_coord_to_idx(0, 0, 2), _coord_to_idx(1, 1, 1), _coord_to_idx(2, 2, 0)))
    lines.append((_coord_to_idx(0, 2, 0), _coord_to_idx(1, 1, 1), _coord_to_idx(2, 0, 2)))
    lines.append((_coord_to_idx(0, 2, 2), _coord_to_idx(1, 1, 1), _coord_to_idx(2, 0, 0)))

    # Build cell-to-lines mapping
    cell_lines = [[] for _ in range(27)]
    for line_idx, line in enumerate(lines):
        for cell in line:
            cell_lines[cell].append(line_idx)

    return lines, cell_lines

ALL_LINES, CELL_LINES = _init_lines()

# Intrinsic static priority: center (13 lines), corners (7 lines), face centers (5 lines), edge centers (4 lines)
CELL_WEIGHTS = [len(CELL_LINES[i]) for i in range(27)]

class TimeoutException(Exception):
    pass

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Flatten the board into a 27-element list: 1 for self, -1 for opponent, 0 for empty
    flat_board = [0] * 27
    empty_cells = []
    my_cells = []
    opp_cells = []

    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = _coord_to_idx(i, j, k)
                val = board[i][j][k]
                flat_board[idx] = val
                if val == 0:
                    empty_cells.append(idx)
                elif val == 1:
                    my_cells.append(idx)
                else:
                    opp_cells.append(idx)

    if not empty_cells:
        return (0, 0, 0)
    if len(empty_cells) == 1:
        return _idx_to_coord(empty_cells[0])

    # Opening book: Center is optimal first move
    center_idx = _coord_to_idx(1, 1, 1)
    if len(empty_cells) == 27:
        return (1, 1, 1)
    if len(empty_cells) == 26 and center_idx in empty_cells:
        return (1, 1, 1)

    # Line occupancy counters: counts for player 1 (my_count) and -1 (opp_count)
    my_counts = [0] * len(ALL_LINES)
    opp_counts = [0] * len(ALL_LINES)

    for cell in my_cells:
        for l_idx in CELL_LINES[cell]:
            my_counts[l_idx] += 1
    for cell in opp_cells:
        for l_idx in CELL_LINES[cell]:
            opp_counts[l_idx] += 1

    # 1. Immediate Win Check
    for cell in empty_cells:
        for l_idx in CELL_LINES[cell]:
            if my_counts[l_idx] == 2 and opp_counts[l_idx] == 0:
                return _idx_to_coord(cell)

    # 2. Immediate Block Check
    block_moves = []
    for cell in empty_cells:
        for l_idx in CELL_LINES[cell]:
            if opp_counts[l_idx] == 2 and my_counts[l_idx] == 0:
                if cell not in block_moves:
                    block_moves.append(cell)
    if len(block_moves) == 1:
        return _idx_to_coord(block_moves[0])

    start_time = time.perf_counter()
    time_limit = 0.80  # Stay safely within the 1-second budget

    def evaluate() -> int:
        score = 0
        for l_idx in range(len(ALL_LINES)):
            mc = my_counts[l_idx]
            oc = opp_counts[l_idx]
            if mc > 0 and oc > 0:
                continue
            if mc == 2:
                score += 150
            elif mc == 1:
                score += 8
            elif oc == 2:
                score -= 150
            elif oc == 1:
                score -= 8
        return score

    def move_priority(cell: int, player: int) -> int:
        p_counts = my_counts if player == 1 else opp_counts
        o_counts = opp_counts if player == 1 else my_counts
        score = CELL_WEIGHTS[cell]
        for l_idx in CELL_LINES[cell]:
            if o_counts[l_idx] == 0:
                if p_counts[l_idx] == 2:
                    score += 10000  # Winning line
                elif p_counts[l_idx] == 1:
                    score += 50     # Threat line
            if p_counts[l_idx] == 0 and o_counts[l_idx] == 2:
                score += 2000       # Block opponent threat
        return score

    def negamax(depth: int, alpha: int, beta: int, player: int, empties: list[int]) -> int:
        if (time.perf_counter() - start_time) > time_limit:
            raise TimeoutException()

        # Immediate winning or blocking at current node
        p_counts = my_counts if player == 1 else opp_counts
        o_counts = opp_counts if player == 1 else my_counts

        # Check for immediate win for current player
        for cell in empties:
            for l_idx in CELL_LINES[cell]:
                if p_counts[l_idx] == 2 and o_counts[l_idx] == 0:
                    return 50000 + depth

        if depth == 0 or not empties:
            val = evaluate()
            return val if player == 1 else -val

        # Sort moves
        empties_sorted = sorted(empties, key=lambda c: move_priority(c, player), reverse=True)

        for cell in empties_sorted:
            # Make move
            for l_idx in CELL_LINES[cell]:
                p_counts[l_idx] += 1
            empties.remove(cell)

            score = -negamax(depth - 1, -beta, -alpha, -player, empties)

            # Undo move
            empties.append(cell)
            for l_idx in CELL_LINES[cell]:
                p_counts[l_idx] -= 1

            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return alpha

    # Iterative deepening
    best_move = block_moves[0] if block_moves else max(empty_cells, key=lambda c: CELL_WEIGHTS[c])

    try:
        max_depth = min(len(empty_cells), 6)
        candidates = block_moves if block_moves else empty_cells

        for depth in range(1, max_depth + 1):
            curr_best_move = None
            curr_best_val = -float('inf')
            candidates_sorted = sorted(candidates, key=lambda c: move_priority(c, 1), reverse=True)

            for cell in candidates_sorted:
                # Play cell for player 1
                for l_idx in CELL_LINES[cell]:
                    my_counts[l_idx] += 1
                rem = [c for c in empty_cells if c != cell]

                val = -negamax(depth - 1, -float('inf'), -curr_best_val, -1, rem)

                # Undo move
                for l_idx in CELL_LINES[cell]:
                    my_counts[l_idx] -= 1

                if val > curr_best_val:
                    curr_best_val = val
                    curr_best_move = cell

                if curr_best_val >= 50000:
                    break

            if curr_best_move is not None:
                best_move = curr_best_move
            if curr_best_val >= 50000:
                break
    except TimeoutException:
        pass

    return _idx_to_coord(best_move)
