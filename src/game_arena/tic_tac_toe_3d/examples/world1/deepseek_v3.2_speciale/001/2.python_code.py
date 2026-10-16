
import time

# ---------- precompute all winning lines ----------
def idx(i, j, k):
    return i * 9 + j * 3 + k

LINES = []               # bit masks of the three cells
LINE_INDICES = []        # list of three indices per line (for building CELL_LINES)

# Rows (x varies)
for j in range(3):
    for k in range(3):
        mask = 0
        indices = []
        for i in range(3):
            ix = idx(i, j, k)
            mask |= 1 << ix
            indices.append(ix)
        LINES.append(mask)
        LINE_INDICES.append(indices)

# Columns (y varies)
for i in range(3):
    for k in range(3):
        mask = 0
        indices = []
        for j in range(3):
            ix = idx(i, j, k)
            mask |= 1 << ix
            indices.append(ix)
        LINES.append(mask)
        LINE_INDICES.append(indices)

# Pillars (z varies)
for i in range(3):
    for j in range(3):
        mask = 0
        indices = []
        for k in range(3):
            ix = idx(i, j, k)
            mask |= 1 << ix
            indices.append(ix)
        LINES.append(mask)
        LINE_INDICES.append(indices)

# Face diagonals (z constant)
for z in range(3):
    # main diagonal
    mask = (1 << idx(0, 0, z)) | (1 << idx(1, 1, z)) | (1 << idx(2, 2, z))
    indices = [idx(0, 0, z), idx(1, 1, z), idx(2, 2, z)]
    LINES.append(mask)
    LINE_INDICES.append(indices)
    # anti diagonal
    mask = (1 << idx(0, 2, z)) | (1 << idx(1, 1, z)) | (1 << idx(2, 0, z))
    indices = [idx(0, 2, z), idx(1, 1, z), idx(2, 0, z)]
    LINES.append(mask)
    LINE_INDICES.append(indices)

# Face diagonals (y constant)
for y in range(3):
    mask = (1 << idx(0, y, 0)) | (1 << idx(1, y, 1)) | (1 << idx(2, y, 2))
    indices = [idx(0, y, 0), idx(1, y, 1), idx(2, y, 2)]
    LINES.append(mask)
    LINE_INDICES.append(indices)
    mask = (1 << idx(0, y, 2)) | (1 << idx(1, y, 1)) | (1 << idx(2, y, 0))
    indices = [idx(0, y, 2), idx(1, y, 1), idx(2, y, 0)]
    LINES.append(mask)
    LINE_INDICES.append(indices)

# Face diagonals (x constant)
for x in range(3):
    mask = (1 << idx(x, 0, 0)) | (1 << idx(x, 1, 1)) | (1 << idx(x, 2, 2))
    indices = [idx(x, 0, 0), idx(x, 1, 1), idx(x, 2, 2)]
    LINES.append(mask)
    LINE_INDICES.append(indices)
    mask = (1 << idx(x, 0, 2)) | (1 << idx(x, 1, 1)) | (1 << idx(x, 2, 0))
    indices = [idx(x, 0, 2), idx(x, 1, 1), idx(x, 2, 0)]
    LINES.append(mask)
    LINE_INDICES.append(indices)

# Space diagonals
mask = (1 << idx(0, 0, 0)) | (1 << idx(1, 1, 1)) | (1 << idx(2, 2, 2))
indices = [idx(0, 0, 0), idx(1, 1, 1), idx(2, 2, 2)]
LINES.append(mask)
LINE_INDICES.append(indices)
mask = (1 << idx(0, 0, 2)) | (1 << idx(1, 1, 1)) | (1 << idx(2, 2, 0))
indices = [idx(0, 0, 2), idx(1, 1, 1), idx(2, 2, 0)]
LINES.append(mask)
LINE_INDICES.append(indices)
mask = (1 << idx(0, 2, 0)) | (1 << idx(1, 1, 1)) | (1 << idx(2, 0, 2))
indices = [idx(0, 2, 0), idx(1, 1, 1), idx(2, 0, 2)]
LINES.append(mask)
LINE_INDICES.append(indices)
mask = (1 << idx(0, 2, 2)) | (1 << idx(1, 1, 1)) | (1 << idx(2, 0, 0))
indices = [idx(0, 2, 2), idx(1, 1, 1), idx(2, 0, 0)]
LINES.append(mask)
LINE_INDICES.append(indices)

# Build CELL_LINES: for each cell, list of line indices it belongs to
CELL_LINES = [[] for _ in range(27)]
for li, indices in enumerate(LINE_INDICES):
    for ix in indices:
        CELL_LINES[ix].append(li)

# Static importance of each cell = number of lines it is part of
CELL_IMPORTANCE = [len(lst) for lst in CELL_LINES]

INF = 10**7

class Timeout(Exception):
    pass

# ---------- policy ----------
def policy(board):
    start_time = time.perf_counter()
    deadline = start_time + 0.9   # leave 0.1 s margin

    # Convert board to bit masks
    my_mask = 0
    opp_mask = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                val = board[i][j][k]
                if val != 0:
                    ix = idx(i, j, k)
                    if val == 1:
                        my_mask |= 1 << ix
                    else:  # -1
                        opp_mask |= 1 << ix

    # Helper: does a mask contain a winning line?
    def is_win(mask):
        for line in LINES:
            if (line & mask) == line:
                return True
        return False

    # Immediate winning move
    occupied = my_mask | opp_mask
    for ix in range(27):
        if (occupied >> ix) & 1 == 0:
            if is_win(my_mask | (1 << ix)):
                i = ix // 9
                j = (ix // 3) % 3
                k = ix % 3
                return (i, j, k)

    # Heuristic evaluation from the perspective of player `p_mask`
    def evaluate(p_mask, o_mask):
        score = 0
        for line in LINES:
            p_cnt = (line & p_mask).bit_count()
            o_cnt = (line & o_mask).bit_count()
            if p_cnt > 0 and o_cnt > 0:
                continue
            if p_cnt == 2:
                score += 100
            elif p_cnt == 1:
                score += 1
            if o_cnt == 2:
                score -= 100
            elif o_cnt == 1:
                score -= 1
        return score

    # Generate ordered moves for the player to move (p_mask)
    def get_ordered_moves(p_mask, o_mask):
        occupied = p_mask | o_mask
        moves = []
        for ix in range(27):
            if (occupied >> ix) & 1 == 0:
                win = False
                block_cnt = 0
                for li in CELL_LINES[ix]:
                    line = LINES[li]
                    p_cnt = (line & p_mask).bit_count()
                    o_cnt = (line & o_mask).bit_count()
                    if p_cnt == 2 and o_cnt == 0:
                        win = True
                        break
                    if o_cnt == 2 and p_cnt == 0:
                        block_cnt += 1
                if win:
                    priority = 1000000 + CELL_IMPORTANCE[ix]
                elif block_cnt > 0:
                    priority = 500000 + (block_cnt * 100) + CELL_IMPORTANCE[ix]
                else:
                    priority = CELL_IMPORTANCE[ix]
                moves.append((priority, ix))
        moves.sort(reverse=True)
        return [ix for _, ix in moves]

    # Negamax with alpha-beta
    def negamax(p_mask, o_mask, depth, alpha, beta):
        if time.perf_counter() > deadline:
            raise Timeout

        if depth == 0:
            return evaluate(p_mask, o_mask)

        moves = get_ordered_moves(p_mask, o_mask)
        if not moves:
            return 0  # draw

        best = -INF
        for move in moves:
            new_p_mask = p_mask | (1 << move)
            if is_win(new_p_mask):
                score = INF
            else:
                score = -negamax(o_mask, new_p_mask, depth - 1, -beta, -alpha)
            if score > best:
                best = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break
        return best

    # Root search for a given depth; updates `best_move`
    def root_search(depth):
        nonlocal best_move
        best_val = -INF
        alpha = -INF
        beta = INF
        moves = get_ordered_moves(my_mask, opp_mask)
        if not moves:
            return
        current_best_move = moves[0]
        for move in moves:
            new_my_mask = my_mask | (1 << move)
            if is_win(new_my_mask):
                val = INF
            else:
                val = -negamax(opp_mask, new_my_mask, depth - 1, -beta, -alpha)
            if val > best_val:
                best_val = val
                current_best_move = move
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break
        best_move = current_best_move

    # Iterative deepening
    empty_cnt = 27 - (my_mask.bit_count() + opp_mask.bit_count())
    # fallback move (first empty cell)
    occupied = my_mask | opp_mask
    for ix in range(27):
        if (occupied >> ix) & 1 == 0:
            best_move = ix
            break

    try:
        for depth in range(1, empty_cnt + 1):
            root_search(depth)
    except Timeout:
        # use best_move from the last fully completed depth
        pass

    i = best_move // 9
    j = (best_move // 3) % 3
    k = best_move % 3
    return (i, j, k)
