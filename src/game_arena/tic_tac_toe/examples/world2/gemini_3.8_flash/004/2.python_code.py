
import time

# Precompute 10 winning lines for 4x4 grid (4 rows, 4 cols, 2 diagonals)
LINES = [
    0x000F, 0x00F0, 0x0F00, 0xF000,  # Rows
    0x1111, 0x2222, 0x4444, 0x8888,  # Columns
    0x8421, 0x1248                   # Diagonals: (0,5,10,15) and (3,6,9,12)
]

# Precompute win table for all 16-bit states
WIN_TABLE = [False] * 65536
for mask in range(65536):
    for line in LINES:
        if (mask & line) == line:
            WIN_TABLE[mask] = True
            break

# Precompute population count table
POP_COUNT = [bin(i).count('1') for i in range(65536)]

# Positional preference ordering (center cells and corners before edges)
PREFERRED_ORDER = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]

def evaluate(p_mask: int, o_mask: int) -> int:
    score = 0
    for line in LINES:
        p_bits = p_mask & line
        o_bits = o_mask & line

        if p_bits and o_bits:
            continue
        elif p_bits:
            cnt = POP_COUNT[p_bits]
            if cnt == 3:
                score += 120
            elif cnt == 2:
                score += 15
            elif cnt == 1:
                score += 2
        elif o_bits:
            cnt = POP_COUNT[o_bits]
            if cnt == 3:
                score -= 120
            elif cnt == 2:
                score -= 15
            elif cnt == 1:
                score -= 2
    return score

def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.time()
    time_limit = 0.85  # Reserve margin within the 1.0s total allowance

    # Convert board into bitboards
    my_mask = 0
    opp_mask = 0
    empty_cells = []

    for r in range(4):
        for c in range(4):
            idx = r * 4 + c
            val = board[r][c]
            if val == 1:
                my_mask |= (1 << idx)
            elif val == -1:
                opp_mask |= (1 << idx)
            else:
                empty_cells.append(idx)

    # Safety check: if no empty cells remain
    if not empty_cells:
        return (0, 0)

    # 1. Immediate Win Check
    for cell in empty_cells:
        if WIN_TABLE[my_mask | (1 << cell)]:
            return (cell // 4, cell % 4)

    # 2. Immediate Block Check
    blocking_moves = []
    for cell in empty_cells:
        if WIN_TABLE[opp_mask | (1 << cell)]:
            blocking_moves.append(cell)
    if len(blocking_moves) == 1:
        return (blocking_moves[0] // 4, blocking_moves[0] % 4)

    # Transposition Table: (my_mask, opp_mask, depth) -> (flag, score, best_move)
    tt = {}

    def get_ordered_moves(p_m, o_m, best_move=None):
        avail = [c for c in PREFERRED_ORDER if not ((p_m | o_m) & (1 << c))]
        if best_move is not None and best_move in avail:
            avail.remove(best_move)
            return [best_move] + avail
        return avail

    def alphabeta(p_mask, o_mask, depth, alpha, beta, is_max):
        # Time check
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        occupied = p_mask | o_mask
        if occupied == 0xFFFF:
            return 0

        state_key = (p_mask, o_mask)
        tt_entry = tt.get(state_key)
        if tt_entry and tt_entry[0] >= depth:
            entry_depth, entry_flag, entry_val, _ = tt_entry
            if entry_flag == 'EXACT':
                return entry_val
            elif entry_flag == 'LOWER' and entry_val > alpha:
                alpha = entry_val
            elif entry_flag == 'UPPER' and entry_val < beta:
                beta = entry_val
            if alpha >= beta:
                return entry_val

        if depth == 0:
            val = evaluate(p_mask, o_mask) if is_max else -evaluate(o_mask, p_mask)
            return val

        moves = get_ordered_moves(p_mask, o_mask, tt_entry[3] if tt_entry else None)
        best_local_move = moves[0]

        if is_max:
            max_eval = -999999
            for m in moves:
                next_p = p_mask | (1 << m)
                if WIN_TABLE[next_p]:
                    eval_score = 100000 + depth
                else:
                    eval_score = alphabeta(next_p, o_mask, depth - 1, alpha, beta, False)

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_local_move = m
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            flag = 'EXACT'
            if max_eval <= alpha:
                flag = 'UPPER'
            elif max_eval >= beta:
                flag = 'LOWER'
            tt[state_key] = (depth, flag, max_eval, best_local_move)
            return max_eval
        else:
            min_eval = 999999
            for m in moves:
                next_o = o_mask | (1 << m)
                if WIN_TABLE[next_o]:
                    eval_score = -100000 - depth
                else:
                    eval_score = alphabeta(p_mask, next_o, depth - 1, alpha, beta, True)

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_local_move = m
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break

            flag = 'EXACT'
            if min_eval <= alpha:
                flag = 'UPPER'
            elif min_eval >= beta:
                flag = 'LOWER'
            tt[state_key] = (depth, flag, min_eval, best_local_move)
            return min_eval

    # Iterative Deepening
    best_move = empty_cells[0]
    for cell in PREFERRED_ORDER:
        if cell in empty_cells:
            best_move = cell
            break

    max_possible_depth = len(empty_cells)
    try:
        for depth in range(1, max_possible_depth + 1):
            root_moves = get_ordered_moves(my_mask, opp_mask, best_move)
            current_best_move = root_moves[0]
            current_best_val = -999999
            alpha = -999999
            beta = 999999

            for m in root_moves:
                next_my = my_mask | (1 << m)
                if WIN_TABLE[next_my]:
                    return (m // 4, m % 4)
                val = alphabeta(next_my, opp_mask, depth - 1, alpha, beta, False)
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = m
                alpha = max(alpha, val)

            best_move = current_best_move
            if current_best_val >= 90000:
                # Guaranteed win found
                break
    except TimeoutError:
        pass

    return (best_move // 4, best_move % 4)
