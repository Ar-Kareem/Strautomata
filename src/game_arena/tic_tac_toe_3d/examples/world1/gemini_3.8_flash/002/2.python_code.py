
import time

# Precompute all 49 winning lines as bitmasks and tuples of cell indices
def _generate_lines():
    lines = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                first = dx if dx != 0 else (dy if dy != 0 else dz)
                if first < 0:
                    continue
                rx = range(3) if dx == 0 else ([0] if dx == 1 else [2])
                ry = range(3) if dy == 0 else ([0] if dy == 1 else [2])
                rz = range(3) if dz == 0 else ([0] if dz == 1 else [2])
                for x in rx:
                    for y in ry:
                        for z in rz:
                            line = tuple(
                                (x + s * dx) * 9 + (y + s * dy) * 3 + (z + s * dz)
                                for s in range(3)
                            )
                            lines.append(line)
    return lines

LINES = _generate_lines()
LINE_MASKS = [(1 << c0) | (1 << c1) | (1 << c2) for c0, c1, c2 in LINES]

# For each cell, precompute the line masks it participates in
CELL_LINE_MASKS = [[] for _ in range(27)]
for lmask in LINE_MASKS:
    for c in range(27):
        if (lmask >> c) & 1:
            CELL_LINE_MASKS[c].append(lmask)

# Static cell priority based on line participation count
CELL_WEIGHTS = [len(CELL_LINE_MASKS[c]) for c in range(27)]


class SearchTimeout(Exception):
    pass


def _bit_count(n: int) -> int:
    return n.bit_count() if hasattr(n, "bit_count") else bin(n).count("1")


def _evaluate(my_mask: int, opp_mask: int) -> int:
    score = 0
    for lmask in LINE_MASKS:
        m = my_mask & lmask
        o = opp_mask & lmask
        if m != 0 and o != 0:
            continue
        if m != 0:
            cnt = _bit_count(m)
            if cnt == 3:
                return 100000
            score += 55 if cnt == 2 else 4
        elif o != 0:
            cnt = _bit_count(o)
            if cnt == 3:
                return -100000
            score -= 55 if cnt == 2 else 4
    return score


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start_time = time.perf_counter()
    time_limit = 0.85

    # Parse board to bitboards
    my_mask = 0
    opp_mask = 0
    empty_cells = []

    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = i * 9 + j * 3 + k
                val = board[i][j][k]
                if val == 1:
                    my_mask |= 1 << idx
                elif val == -1:
                    opp_mask |= 1 << idx
                else:
                    empty_cells.append(idx)

    # If only one move left or board is full, return directly
    if not empty_cells:
        return (0, 0, 0)
    if len(empty_cells) == 1:
        c = empty_cells[0]
        return (c // 9, (c % 9) // 3, c % 3)

    # Center is index 13: if empty on turn 1, take center immediately
    if len(empty_cells) >= 26 and (13 in empty_cells):
        return (1, 1, 1)

    # 1. Immediate Win Check
    for c in empty_cells:
        m = 1 << c
        for lmask in CELL_LINE_MASKS[c]:
            if ((my_mask | m) & lmask) == lmask:
                return (c // 9, (c % 9) // 3, c % 3)

    # 2. Immediate Block Check
    blocking_moves = []
    for c in empty_cells:
        m = 1 << c
        for lmask in CELL_LINE_MASKS[c]:
            if ((opp_mask | m) & lmask) == lmask:
                blocking_moves.append(c)
                break
    if len(blocking_moves) == 1:
        c = blocking_moves[0]
        return (c // 9, (c % 9) // 3, c % 3)

    # 3. Iterative Deepening Minimax with Alpha-Beta Pruning
    tt = {}

    def alpha_beta(my_m: int, opp_m: int, depth: int, alpha: int, beta: int, is_max: bool) -> int:
        if time.perf_counter() - start_time > time_limit:
            raise SearchTimeout()

        occupied = my_m | opp_m
        available = [c for c in range(27) if not ((occupied >> c) & 1)]

        if depth == 0 or not available:
            return _evaluate(my_m, opp_m)

        tt_key = (my_m, opp_m, is_max)
        if tt_key in tt:
            entry_depth, entry_val = tt[tt_key]
            if entry_depth >= depth:
                return entry_val

        if is_max:
            # Check for immediate win moves
            for c in available:
                m = 1 << c
                for lmask in CELL_LINE_MASKS[c]:
                    if ((my_m | m) & lmask) == lmask:
                        return 90000 + depth

            # Sort moves: prioritize cells with more potential lines
            available.sort(key=lambda c: CELL_WEIGHTS[c], reverse=True)

            val = -1000000
            for c in available:
                score = alpha_beta(my_m | (1 << c), opp_m, depth - 1, alpha, beta, False)
                if score > val:
                    val = score
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break
            tt[tt_key] = (depth, val)
            return val
        else:
            # Check for immediate opponent win moves
            for c in available:
                m = 1 << c
                for lmask in CELL_LINE_MASKS[c]:
                    if ((opp_m | m) & lmask) == lmask:
                        return -90000 - depth

            available.sort(key=lambda c: CELL_WEIGHTS[c], reverse=True)

            val = 1000000
            for c in available:
                score = alpha_beta(my_m, opp_m | (1 << c), depth - 1, alpha, beta, True)
                if score < val:
                    val = score
                if val < beta:
                    beta = val
                if alpha >= beta:
                    break
            tt[tt_key] = (depth, val)
            return val

    # Order root candidates
    candidates = list(empty_cells)
    candidates.sort(key=lambda c: CELL_WEIGHTS[c], reverse=True)

    best_cell = candidates[0]

    try:
        max_depth = min(6, len(empty_cells))
        for d in range(1, max_depth + 1):
            current_best_cell = best_cell
            best_score = -1000000
            alpha = -1000000
            beta = 1000000

            for c in candidates:
                score = alpha_beta(my_mask | (1 << c), opp_mask, d - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    current_best_cell = c
                if score > alpha:
                    alpha = score

            best_cell = current_best_cell
            if best_score >= 80000:
                break
    except SearchTimeout:
        pass

    return (best_cell // 9, (best_cell % 9) // 3, best_cell % 3)
