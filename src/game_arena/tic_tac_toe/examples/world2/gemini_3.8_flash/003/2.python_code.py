
import time

# Precomputed winning line bitmasks for 4x4 grid (16 cells: 0 to 15)
WIN_MASKS = [
    # Rows
    0x000F, 0x00F0, 0x0F00, 0xF000,
    # Columns
    0x1111, 0x2222, 0x4444, 0x8888,
    # Diagonals
    0x8421, 0x1248
]

# Positional weights: preference for central cells (indices 5, 6, 9, 10)
CELL_WEIGHTS = [
    2, 3, 3, 2,
    3, 5, 5, 3,
    3, 5, 5, 3,
    2, 3, 3, 2
]

INF = 10**8
WIN_SCORE = 10**6

LINE_WEIGHTS = [0, 3, 35, 600, WIN_SCORE]


def bit_count(n: int) -> int:
    return bin(n).count("1")


def check_win(mask: int) -> bool:
    for m in WIN_MASKS:
        if (mask & m) == m:
            return True
    return False


def evaluate(my_mask: int, opp_mask: int) -> int:
    score = 0
    # Evaluate lines
    for m in WIN_MASKS:
        my_has = bit_count(my_mask & m)
        opp_has = bit_count(opp_mask & m)
        if my_has > 0 and opp_has > 0:
            continue
        if my_has > 0:
            score += LINE_WEIGHTS[my_has]
        elif opp_has > 0:
            score -= LINE_WEIGHTS[opp_has]

    # Positional bonus
    temp = my_mask
    while temp:
        lsb = temp & -temp
        idx = lsb.bit_length() - 1
        score += CELL_WEIGHTS[idx]
        temp ^= lsb

    temp = opp_mask
    while temp:
        lsb = temp & -temp
        idx = lsb.bit_length() - 1
        score -= CELL_WEIGHTS[idx]
        temp ^= lsb

    return score


def get_empty_indices(occupied: int) -> list[int]:
    empty = (~occupied) & 0xFFFF
    indices = []
    while empty:
        lsb = empty & -empty
        indices.append(lsb.bit_length() - 1)
        empty ^= lsb
    return indices


class SearchTimeout(Exception):
    pass


def minimax(
    my_mask: int,
    opp_mask: int,
    depth: int,
    alpha: int,
    beta: int,
    is_max: bool,
    deadline: float,
) -> int:
    if time.time() > deadline:
        raise SearchTimeout()

    if is_max:
        if check_win(opp_mask):
            return -WIN_SCORE - depth
    else:
        if check_win(my_mask):
            return WIN_SCORE + depth

    occupied = my_mask | opp_mask
    if occupied == 0xFFFF or depth == 0:
        return evaluate(my_mask, opp_mask)

    empty_cells = get_empty_indices(occupied)

    if is_max:
        # Move ordering: prioritize cells with higher positional weight
        empty_cells.sort(key=lambda idx: -CELL_WEIGHTS[idx])
        val = -INF
        for idx in empty_cells:
            nxt = my_mask | (1 << idx)
            # Immediate win cutoff
            if check_win(nxt):
                return WIN_SCORE + depth
            res = minimax(nxt, opp_mask, depth - 1, alpha, beta, False, deadline)
            if res > val:
                val = res
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        return val
    else:
        empty_cells.sort(key=lambda idx: -CELL_WEIGHTS[idx])
        val = INF
        for idx in empty_cells:
            nxt = opp_mask | (1 << idx)
            # Immediate opponent win
            if check_win(nxt):
                return -WIN_SCORE - depth
            res = minimax(my_mask, nxt, depth - 1, alpha, beta, True, deadline)
            if res < val:
                val = res
            if val < beta:
                beta = val
            if alpha >= beta:
                break
        return val


def policy(board: list[list[int]]) -> tuple[int, int]:
    deadline = time.time() + 0.85

    my_mask = 0
    opp_mask = 0
    empty_positions = []

    for r in range(4):
        for c in range(4):
            idx = r * 4 + c
            if board[r][c] == 1:
                my_mask |= 1 << idx
            elif board[r][c] == -1:
                opp_mask |= 1 << idx
            else:
                empty_positions.append((r, c))

    # Safety: fallback move if something goes wrong
    if not empty_positions:
        return (0, 0)
    best_move = empty_positions[0]

    # Quick check: 1) Can we win immediately?
    for r, c in empty_positions:
        idx = r * 4 + c
        if check_win(my_mask | (1 << idx)):
            return (r, c)

    # Quick check: 2) Can opponent win immediately? Block them!
    for r, c in empty_positions:
        idx = r * 4 + c
        if check_win(opp_mask | (1 << idx)):
            return (r, c)

    # If first move on an empty board, take a center square
    if not my_mask and not opp_mask:
        return (1, 1)

    # Order moves by positional heuristics for initial search
    empty_cells = [(r * 4 + c, (r, c)) for (r, c) in empty_positions]
    empty_cells.sort(key=lambda item: -CELL_WEIGHTS[item[0]])

    best_move = empty_cells[0][1]

    # Iterative deepening search
    max_depth = len(empty_positions)
    for depth in range(1, max_depth + 1):
        current_best_move = best_move
        best_val = -INF
        alpha = -INF
        beta = INF

        try:
            for idx, coord in empty_cells:
                val = minimax(
                    my_mask | (1 << idx),
                    opp_mask,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    deadline,
                )
                if val > best_val:
                    best_val = val
                    current_best_move = coord
                if val > alpha:
                    alpha = val
            best_move = current_best_move
            # If win is guaranteed, no need to search deeper
            if best_val >= WIN_SCORE:
                break
        except SearchTimeout:
            break

    return best_move
