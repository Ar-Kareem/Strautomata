
import time

WIN_MASKS = (
    # Rows
    0x000F, 0x00F0, 0x0F00, 0xF000,
    # Columns
    0x1111, 0x2222, 0x4444, 0x8888,
    # Diagonals
    0x8421, 0x1248
)

# Strategic cell priorities based on line intersections
CELL_WEIGHTS = [
    3, 2, 2, 3,
    2, 3, 3, 2,
    2, 3, 3, 2,
    3, 2, 2, 3
]

def check_win(mask: int) -> bool:
    for w in WIN_MASKS:
        if (mask & w) == w:
            return True
    return False

def evaluate(my_mask: int, opp_mask: int) -> int:
    score = 0
    for w in WIN_MASKS:
        has_my = (my_mask & w)
        has_opp = (opp_mask & w)
        
        if has_my and has_opp:
            continue
        
        if has_my:
            cnt = bin(has_my).count('1')
            if cnt == 4:
                return 100000
            elif cnt == 3:
                score += 150
            elif cnt == 2:
                score += 15
            else:
                score += 2
        elif has_opp:
            cnt = bin(has_opp).count('1')
            if cnt == 4:
                return -100000
            elif cnt == 3:
                score -= 150
            elif cnt == 2:
                score -= 15
            else:
                score -= 2

    return score

class SearchTimeout(Exception):
    pass

def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.perf_counter()
    time_limit = 0.85  # Reserve margin within the 1-second constraint

    my_mask = 0
    opp_mask = 0
    empty_cells = []

    for r in range(4):
        for c in range(4):
            val = board[r][c]
            bit = 1 << (r * 4 + c)
            if val == 1:
                my_mask |= bit
            elif val == -1:
                opp_mask |= bit
            else:
                empty_cells.append(r * 4 + c)

    if not empty_cells:
        return (0, 0)

    # Immediate win check
    for cell in empty_cells:
        bit = 1 << cell
        if check_win(my_mask | bit):
            return (cell // 4, cell % 4)

    # Immediate block check
    block_move = None
    for cell in empty_cells:
        bit = 1 << cell
        if check_win(opp_mask | bit):
            block_move = (cell // 4, cell % 4)
            break
    if block_move is not None and len(empty_cells) > 13:
        return block_move

    # Order initial moves by positional heuristic
    empty_cells.sort(key=lambda idx: CELL_WEIGHTS[idx], reverse=True)
    best_move_idx = empty_cells[0]

    tt = {}
    nodes_searched = 0

    def minimax(my_m: int, opp_m: int, depth: int, alpha: int, beta: int, is_max: bool) -> int:
        nonlocal nodes_searched
        nodes_searched += 1
        if nodes_searched & 127 == 0:
            if time.perf_counter() - start_time > time_limit:
                raise SearchTimeout()

        state_key = (my_m, opp_m, is_max)
        if state_key in tt:
            cached_depth, cached_val = tt[state_key]
            if cached_depth >= depth:
                return cached_val

        if is_max:
            if check_win(opp_m):
                return -100000 - depth
        else:
            if check_win(my_m):
                return 100000 + depth

        occ = my_m | opp_m
        if occ == 0xFFFF or depth == 0:
            val = evaluate(my_m, opp_m)
            tt[state_key] = (depth, val)
            return val

        moves = [i for i in range(16) if not (occ & (1 << i))]
        moves.sort(key=lambda idx: CELL_WEIGHTS[idx], reverse=True)

        if is_max:
            max_eval = -999999
            for m in moves:
                b = 1 << m
                ev = minimax(my_m | b, opp_m, depth - 1, alpha, beta, False)
                if ev > max_eval:
                    max_eval = ev
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            tt[state_key] = (depth, max_eval)
            return max_eval
        else:
            min_eval = 999999
            for m in moves:
                b = 1 << m
                ev = minimax(my_m, opp_m | b, depth - 1, alpha, beta, True)
                if ev < min_eval:
                    min_eval = ev
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            tt[state_key] = (depth, min_eval)
            return min_eval

    # Iterative deepening search
    max_search_depth = min(16, len(empty_cells))
    for depth in range(1, max_search_depth + 1):
        best_eval_depth = -999999
        current_best = best_move_idx
        try:
            for cell in empty_cells:
                bit = 1 << cell
                ev = minimax(my_mask | bit, opp_mask, depth - 1, -999999, 999999, False)
                if ev > best_eval_depth:
                    best_eval_depth = ev
                    current_best = cell

            best_move_idx = current_best
            if best_eval_depth >= 90000:  # Found forced win
                break
        except SearchTimeout:
            break

    return (best_move_idx // 4, best_move_idx % 4)
