
import time

# Precompute winning lines and board metadata
LINES = []
for _dx in (-1, 0, 1):
    for _dy in (-1, 0, 1):
        for _dz in (-1, 0, 1):
            _first = _dx if _dx != 0 else (_dy if _dy != 0 else _dz)
            if _first <= 0:
                continue
            for _x in range(3):
                for _y in range(3):
                    for _z in range(3):
                        _x2, _y2, _z2 = _x + 2 * _dx, _y + 2 * _dy, _z + 2 * _dz
                        if 0 <= _x2 < 3 and 0 <= _y2 < 3 and 0 <= _z2 < 3:
                            _p1 = _x * 9 + _y * 3 + _z
                            _p2 = (_x + _dx) * 9 + (_y + _dy) * 3 + (_z + _dz)
                            _p3 = _x2 * 9 + _y2 * 3 + _z2
                            LINES.append((_p1, _p2, _p3))

LINE_MASKS = [((1 << p1) | (1 << p2) | (1 << p3)) for p1, p2, p3 in LINES]

CELL_LINES = [[] for _ in range(27)]
for _line_idx, (p1, p2, p3) in enumerate(LINES):
    CELL_LINES[p1].append(_line_idx)
    CELL_LINES[p2].append(_line_idx)
    CELL_LINES[p3].append(_line_idx)

CELL_WEIGHTS = [len(CELL_LINES[i]) for i in range(27)]

EXACT, LOWERBOUND, UPPERBOUND = 0, 1, 2


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start_time = time.time()
    time_limit = 0.82

    # Flatten board and compute bitmasks
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

    # If completely empty, center is theoretically optimal
    if len(empty_cells) == 27:
        return (1, 1, 1)

    # If center is available, it is the highest-value opening cell
    if 13 in empty_cells and len(empty_cells) >= 25:
        return (1, 1, 1)

    # Immediate win check
    for cell in empty_cells:
        m = my_mask | (1 << cell)
        for line_mask in LINE_MASKS:
            if (m & line_mask) == line_mask:
                return (cell // 9, (cell // 3) % 3, cell % 3)

    # Immediate block check
    block_move = None
    for cell in empty_cells:
        o = opp_mask | (1 << cell)
        for line_mask in LINE_MASKS:
            if (o & line_mask) == line_mask:
                block_move = cell
                break
        if block_move is not None:
            break

    tt = {}

    def evaluate(p_mask: int, o_mask: int) -> int:
        score = 0
        for p1, p2, p3 in LINES:
            p_count = ((p_mask >> p1) & 1) + ((p_mask >> p2) & 1) + ((p_mask >> p3) & 1)
            o_count = ((o_mask >> p1) & 1) + ((o_mask >> p2) & 1) + ((o_mask >> p3) & 1)

            if o_count == 0:
                if p_count == 2:
                    score += 65
                elif p_count == 1:
                    score += 6
            elif p_count == 0:
                if o_count == 2:
                    score -= 65
                elif o_count == 1:
                    score -= 6

        # Positional control bonus
        for c in range(27):
            if (p_mask >> c) & 1:
                score += CELL_WEIGHTS[c]
            elif (o_mask >> c) & 1:
                score -= CELL_WEIGHTS[c]

        return score

    def negamax(p_mask: int, o_mask: int, depth: int, alpha: int, beta: int) -> int:
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        alpha_orig = alpha
        tt_entry = tt.get((p_mask, o_mask))
        if tt_entry and tt_entry[0] >= depth:
            entry_depth, entry_flag, entry_val, _ = tt_entry
            if entry_flag == EXACT:
                return entry_val
            elif entry_flag == LOWERBOUND:
                alpha = max(alpha, entry_val)
            elif entry_flag == UPPERBOUND:
                beta = min(beta, entry_val)
            if alpha >= beta:
                return entry_val

        # Check win for previous player (opponent)
        for line_mask in LINE_MASKS:
            if (o_mask & line_mask) == line_mask:
                return -100000 - depth

        occ = p_mask | o_mask
        legal_moves = [c for c in range(27) if not ((occ >> c) & 1)]

        if not legal_moves:
            return 0

        if depth == 0:
            return evaluate(p_mask, o_mask)

        # Move ordering
        best_tt_move = tt_entry[3] if tt_entry else None

        def move_score(cell: int) -> int:
            if cell == best_tt_move:
                return 10000
            s = CELL_WEIGHTS[cell]
            # Prioritize winning or blocking lines
            m = p_mask | (1 << cell)
            for lm in LINE_MASKS:
                if (m & lm) == lm:
                    return 5000
            o = o_mask | (1 << cell)
            for lm in LINE_MASKS:
                if (o & lm) == lm:
                    return 2500
            return s

        legal_moves.sort(key=move_score, reverse=True)

        best_val = -200000
        best_move = legal_moves[0]

        for move in legal_moves:
            next_p = p_mask | (1 << move)
            val = -negamax(o_mask, next_p, depth - 1, -beta, -alpha)
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        flag = EXACT
        if best_val <= alpha_orig:
            flag = UPPERBOUND
        elif best_val >= beta:
            flag = LOWERBOUND

        tt[(p_mask, o_mask)] = (depth, flag, best_val, best_move)
        return best_val

    # Iterative Deepening
    best_overall_move = block_move if block_move is not None else empty_cells[0]
    max_search_depth = min(len(empty_cells), 8)

    try:
        for depth in range(1, max_search_depth + 1):
            occ = my_mask | opp_mask
            candidates = [c for c in empty_cells]
            if block_move is not None and block_move in candidates:
                candidates.remove(block_move)
                candidates.insert(0, block_move)

            current_best_val = -200000
            current_best_move = best_overall_move
            alpha = -200000
            beta = 200000

            for move in candidates:
                val = -negamax(opp_mask, my_mask | (1 << move), depth - 1, -beta, -alpha)
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = move
                alpha = max(alpha, val)

            best_overall_move = current_best_move
            if current_best_val > 50000:  # Forced win found
                break
    except TimeoutError:
        pass

    chosen = best_overall_move
    return (chosen // 9, (chosen // 3) % 3, chosen % 3)
