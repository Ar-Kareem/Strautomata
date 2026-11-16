
import time

# ------------------------------------------------------------
#  Board geometry
# ------------------------------------------------------------
ROWS = 5
COLS = 6
SIZE = ROWS * COLS                     # 30

# ------------------------------------------------------------
#  Pre‑computed helpers
# ------------------------------------------------------------
# (row, col) for every index 0‑29
_index_to_rowcol = [(i // COLS, i % COLS) for i in range(SIZE)]

# neighbours for every cell – list of (direction_char, neighbour_index)
_neighbours = [[] for _ in range(SIZE)]
for idx in range(SIZE):
    r, c = _index_to_rowcol[idx]
    if r > 0:      _neighbours[idx].append(('U', idx - COLS))        # up
    if r < ROWS - 1: _neighbours[idx].append(('D', idx + COLS))      # down
    if c > 0:      _neighbours[idx].append(('L', idx - 1))          # left
    if c < COLS - 1: _neighbours[idx].append(('R', idx + 1))        # right

# central‑square bonuses
_central = [1] * SIZE
_center_rows = [2, 3]
_center_cols = [2, 3]
for idx in range(SIZE):
    r, c = _index_to_rowcol[idx]
    d = min(abs(r - cr) + abs(c - cc) for cr in _center_rows for cc in _center_cols)
    if d == 0:
        _central[idx] = 3
    elif d == 1:
        _central[idx] = 2
    else:
        _central[idx] = 1

# ------------------------------------------------------------
#  Bit‑board utilities
# ------------------------------------------------------------
def _popcount(m: int) -> int:
    """number of set bits (Python ≥3.8 can use m.bit_count())"""
    return m.bit_count()                     # fast built‑in

def _generate_moves(my_mask: int, opp_mask: int):
    """return list of legal moves (start_idx, dest_idx, dir_char)"""
    moves = []
    mm = my_mask
    while mm:
        lsb = mm & -mm
        i = lsb.bit_length() - 1
        mm ^= lsb
        for d, j in _neighbours[i]:
            if (opp_mask >> j) & 1:
                moves.append((i, j, d))
    return moves

def _apply_move(my_mask: int, opp_mask: int, move):
    """return (new_my_mask, new_opp_mask) after executing move"""
    s, d, _ = move
    start_bit = 1 << s
    dest_bit = 1 << d
    new_my = (my_mask ^ start_bit) | dest_bit          # remove start, add destination
    new_opp = opp_mask ^ dest_bit                      # remove captured piece
    return new_my, new_opp

# ------------------------------------------------------------
#  Evaluation (heuristic)
# ------------------------------------------------------------
def _evaluate(my_mask: int, opp_mask: int) -> int:
    """score from the viewpoint of the player that owns my_mask"""
    # material
    my_pc = _popcount(my_mask)
    opp_pc = _popcount(opp_mask)
    score = (my_pc - opp_pc) * 100

    # mobility
    my_mob = len(_generate_moves(my_mask, opp_mask))
    opp_mob = len(_generate_moves(opp_mask, my_mask))
    score += (my_mob - opp_mob) * 10

    # central control
    my_cent = 0
    m = my_mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb
        my_cent += _central[i]
    opp_cent = 0
    m = opp_mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb
        opp_cent += _central[i]
    score += my_cent - opp_cent

    return score

# ------------------------------------------------------------
#  Exact solver (≤ 10 pieces)
# ------------------------------------------------------------
_exact_tt = {}                     # (my_mask, opp_mask) → (value, best_move)

def _solve_exact(my_mask: int, opp_mask: int):
    """return (+inf, move) if win, (-inf, move) if lose, move is always legal"""
    key = (my_mask, opp_mask)
    if key in _exact_tt:
        return _exact_tt[key]

    moves = _generate_moves(my_mask, opp_mask)
    if not moves:                                 # no legal move → lose
        result = (-float('inf'), None)
        _exact_tt[key] = result
        return result

    best_move = None
    for mv in moves:
        n_my, n_opp = _apply_move(my_mask, opp_mask, mv)
        child_val, _ = _solve_exact(n_opp, n_my)  # opponent to move
        if child_val == -float('inf'):            # opponent loses → we win
            result = (float('inf'), mv)
            _exact_tt[key] = result
            return result
        if best_move is None:
            best_move = mv

    # No winning move → losing position
    result = (-float('inf'), best_move)
    _exact_tt[key] = result
    return result

# ------------------------------------------------------------
#  Alpha‑beta searcher (depth limit, heuristic evaluation)
# ------------------------------------------------------------
def _search_alpha_beta(my_mask: int, opp_mask: int, depth: int,
                       alpha: float, beta: float):
    """return (value, best_move) for player that owns my_mask"""
    moves = _generate_moves(my_mask, opp_mask)
    if not moves:
        return -float('inf'), None
    if depth == 0:
        return _evaluate(my_mask, opp_mask), None

    # simple move ordering – captures of more central squares first
    scored = [(_central[dest], mv) for mv in moves]
    scored.sort(reverse=True)
    moves = [mv for _, mv in scored]

    best_val = -float('inf')
    best_move = moves[0]                     # guaranteed at least one move exists

    for mv in moves:
        n_my, n_opp = _apply_move(my_mask, opp_mask, mv)
        child_val, _ = _search_alpha_beta(opp_mask=n_opp, my_mask=n_my,
                                          depth=depth - 1,
                                          alpha=-beta, beta=-alpha)
        val = -child_val
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best_val, best_move

# ------------------------------------------------------------
#  Public API – the only function that must be present
# ------------------------------------------------------------
def policy(you, opponent):
    """
    you      – list of 30 ints (0/1), you[row*6+col] == 1 ⇔ you own the square
    opponent – same for the opponent
    return   – move string "row,col,dir"
    """
    # build bit‑boards
    my_mask = 0
    opp_mask = 0
    for i in range(SIZE):
        if you[i]:
            my_mask |= (1 << i)
        if opponent[i]:
            opp_mask |= (1 << i)

    # all legal moves for the side to move
    moves = _generate_moves(my_mask, opp_mask)
    if not moves:                     # should never happen (game already over)
        return "0,0,U"

    total_pieces = _popcount(my_mask) + _popcount(opp_mask)

    # --------------------------------------------------------
    #  End‑game – solve exactly (very fast for ≤ 10 pieces)
    # --------------------------------------------------------
    if total_pieces <= 10:
        _, move = _solve_exact(my_mask, opp_mask)
        # move is always legal when at least one move exists
        r, c = _index_to_rowcol[move[0]]
        return f"{r},{c},{move[2]}"

    # --------------------------------------------------------
    #  Mid‑game – depth‑limited α‑β search with heuristic eval
    # --------------------------------------------------------
    # choose depth according to remaining material (keeps total time < 1 s)
    if total_pieces <= 20:
        max_depth = 5
    else:
        max_depth = 4

    start = time.time()
    TIME_LIMIT = 0.95                     # leave a little safety margin
    best_move = moves[0]                  # fallback

    for depth in range(1, max_depth + 1):
        if time.time() - start > TIME_LIMIT:
            break
        val, move = _search_alpha_beta(my_mask, opp_mask,
                                        depth,
                                        -float('inf'), float('inf'))
        if move is not None:
            best_move = move
        # if we already see a forced win we can stop early
        if val == float('inf'):
            break

    r, c = _index_to_rowcol[best_move[0]]
    return f"{r},{c},{best_move[2]}"
