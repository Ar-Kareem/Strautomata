
import time

LINES = (
    0x000F, 0x00F0, 0x0F00, 0xF000,  # Rows
    0x1111, 0x2222, 0x4444, 0x8888,  # Columns
    0x8421, 0x1248                   # Diagonals
)

# Cell weights to prioritize promising moves early during search
CELL_WEIGHTS = [
    3, 2, 2, 3,
    2, 4, 4, 2,
    2, 4, 4, 2,
    3, 2, 2, 3
]

INF = 1000000

def check_win(bitmask: int) -> bool:
    for line in LINES:
        if (bitmask & line) == line:
            return True
    return False

def evaluate(my_bits: int, opp_bits: int) -> int:
    score = 0
    for line in LINES:
        has_my = (my_bits & line) != 0
        has_opp = (opp_bits & line) != 0

        if has_my and has_opp:
            continue

        if has_my:
            count = bin(my_bits & line).count("1")
            if count == 4:
                return INF
            elif count == 3:
                score += 500
            elif count == 2:
                score += 40
            elif count == 1:
                score += 5
        elif has_opp:
            count = bin(opp_bits & line).count("1")
            if count == 4:
                return -INF
            elif count == 3:
                score -= 500
            elif count == 2:
                score -= 40
            elif count == 1:
                score -= 5

    return score

def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.time()
    time_limit = 0.85  # Reserve margin within 1.0s limit

    my_bits = 0
    opp_bits = 0
    empty_cells = []

    for r in range(4):
        for c in range(4):
            idx = r * 4 + c
            val = board[r][c]
            if val == 1:
                my_bits |= (1 << idx)
            elif val == -1:
                opp_bits |= (1 << idx)
            else:
                empty_cells.append(idx)

    if not empty_cells:
        return (0, 0)

    # Fast-path: Win immediately or block immediate opponent win
    for idx in empty_cells:
        if check_win(my_bits | (1 << idx)):
            return (idx // 4, idx % 4)

    block_move = None
    for idx in empty_cells:
        if check_win(opp_bits | (1 << idx)):
            block_move = idx
            break
    if block_move is not None:
        # If there's an immediate block, prioritize it unless deeper search refines it
        best_overall_move = block_move
    else:
        best_overall_move = max(empty_cells, key=lambda idx: CELL_WEIGHTS[idx])

    tt = {}

    def alpha_beta(my_b: int, opp_b: int, depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
        nonlocal time_limit, start_time
        if (time.time() - start_time) > time_limit:
            raise TimeoutError

        state_key = (my_b, opp_b, is_maximizing)
        if state_key in tt and tt[state_key][0] >= depth:
            entry_depth, entry_val = tt[state_key]
            return entry_val

        if check_win(opp_b):
            return -100000 - depth
        if check_win(my_b):
            return 100000 + depth

        occ = my_b | opp_b
        if occ == 0xFFFF or depth == 0:
            return evaluate(my_b, opp_b)

        free_bits = (~occ) & 0xFFFF
        moves = []
        for i in range(16):
            if (free_bits >> i) & 1:
                moves.append(i)

        # Move ordering based on strategic square weights
        moves.sort(key=lambda m: CELL_WEIGHTS[m], reverse=True)

        if is_maximizing:
            max_eval = -INF
            for m in moves:
                val = alpha_beta(my_b | (1 << m), opp_b, depth - 1, alpha, beta, False)
                if val > max_eval:
                    max_eval = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            tt[state_key] = (depth, max_eval)
            return max_eval
        else:
            min_eval = INF
            for m in moves:
                val = alpha_beta(my_b, opp_b | (1 << m), depth - 1, alpha, beta, True)
                if val < min_eval:
                    min_eval = val
                beta = min(beta, val)
                if beta <= alpha:
                    break
            tt[state_key] = (depth, min_eval)
            return min_eval

    # Iterative Deepening
    max_depth = min(len(empty_cells), 10)
    ordered_moves = sorted(empty_cells, key=lambda idx: CELL_WEIGHTS[idx], reverse=True)

    try:
        for current_depth in range(1, max_depth + 1):
            best_val = -INF
            best_move_at_depth = None

            for m in ordered_moves:
                val = alpha_beta(my_bits | (1 << m), opp_bits, current_depth - 1, -INF, INF, False)
                if val > best_val:
                    best_val = val
                    best_move_at_depth = m

            if best_move_at_depth is not None:
                best_overall_move = best_move_at_depth

            # If a guaranteed winning sequence is found, finish early
            if best_val >= 90000:
                break
    except TimeoutError:
        pass

    return (best_overall_move // 4, best_overall_move % 4)
