
import time

# Column exploration order prioritizing central control
MOVE_ORDER = [3, 2, 4, 1, 5, 0, 6]

# Board bitmask (6 rows x 7 columns with 1 guard bit per column)
BOARD_MASK = 0
for _c in range(7):
    BOARD_MASK |= ((1 << 6) - 1) << (_c * 7)

# Precomputed weights for each board cell based on the number of
# 4-in-a-row winning combinations passing through that cell.
CELL_WEIGHTS = [0] * 49
for _c in range(7):
    for _r in range(6):
        w = 0
        # Horizontal
        for _x in range(4):
            if _x <= _c <= _x + 3:
                w += 1
        # Vertical
        for _y in range(3):
            if _y <= _r <= _y + 3:
                w += 1
        # Diagonal /
        for _x in range(4):
            for _y in range(3):
                if any(_x + k == _c and _y + k == _r for k in range(4)):
                    w += 1
        # Diagonal \
        for _x in range(4):
            for _y in range(3, 6):
                if any(_x + k == _c and _y - k == _r for k in range(4)):
                    w += 1
        CELL_WEIGHTS[_c * 7 + _r] = w


class SearchTimeout(Exception):
    pass


def is_win(pos: int) -> bool:
    """Checks if the bitboard contains any 4-in-a-row."""
    # Horizontal
    m = pos & (pos >> 7)
    if m & (m >> 14):
        return True
    # Vertical
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    # Diagonal /
    m = pos & (pos >> 8)
    if m & (m >> 16):
        return True
    # Diagonal \
    m = pos & (pos >> 6)
    if m & (m >> 12):
        return True
    return False


def compute_threats(pos: int) -> int:
    """Computes all potential 4th-cell win locations for the player."""
    r = (pos << 1) & (pos << 2) & (pos << 3)
    for s in (7, 8, 6):
        p1 = (pos << s) & (pos >> s)
        r |= p1 & (pos << (2 * s))
        r |= p1 & (pos >> (2 * s))
        r |= (pos << s) & (pos << (2 * s)) & (pos << (3 * s))
        r |= (pos >> s) & (pos >> (2 * s)) & (pos >> (3 * s))
    return r & BOARD_MASK


def evaluate(current: int, opponent: int, mask: int) -> int:
    """Heuristic evaluation of leaf positions."""
    score = 0
    c_temp = current
    while c_temp:
        lsb = c_temp & -c_temp
        score += CELL_WEIGHTS[lsb.bit_length() - 1]
        c_temp ^= lsb

    o_temp = opponent
    while o_temp:
        lsb = o_temp & -o_temp
        score -= CELL_WEIGHTS[lsb.bit_length() - 1]
        o_temp ^= lsb

    empty = BOARD_MASK ^ mask
    my_threats = compute_threats(current) & empty
    opp_threats = compute_threats(opponent) & empty

    my_threat_count = my_threats.bit_count() if hasattr(my_threats, "bit_count") else bin(my_threats).count("1")
    opp_threat_count = opp_threats.bit_count() if hasattr(opp_threats, "bit_count") else bin(opp_threats).count("1")

    score += (my_threat_count - opp_threat_count) * 28
    return score


node_count = 0


def negamax(current: int, opponent: int, mask: int, height: list[int],
            depth: int, alpha: int, beta: int, ply: int,
            deadline: float, tt: dict) -> tuple[int, int]:
    global node_count
    node_count += 1
    if (node_count & 1023) == 0:
        if time.time() >= deadline:
            raise SearchTimeout()

    # Transposition table lookup
    tt_key = current | (mask << 49)
    tt_entry = tt.get(tt_key)
    tt_move = None
    if tt_entry is not None:
        e_depth, e_flag, e_score, tt_move = tt_entry
        if e_depth >= depth:
            if e_flag == 0:  # EXACT
                return e_score, tt_move
            elif e_flag == 1 and e_score >= beta:  # LOWERBOUND
                return e_score, tt_move
            elif e_flag == 2 and e_score <= alpha:  # UPPERBOUND
                return e_score, tt_move

    # Leaf node evaluation
    if depth == 0:
        return evaluate(current, opponent, mask), -1

    if mask == BOARD_MASK:
        return 0, -1

    # Order moves: transposition table move first, then center-outward
    moves = []
    if tt_move is not None and height[tt_move] < tt_move * 7 + 6:
        moves.append(tt_move)
    for c in MOVE_ORDER:
        if c != tt_move and height[c] < c * 7 + 6:
            moves.append(c)

    if not moves:
        return 0, -1

    # Immediate win detection
    for c in moves:
        bit = 1 << height[c]
        if is_win(current | bit):
            return 100000 - ply, c

    orig_alpha = alpha
    best_score = -1000000
    best_col = moves[0]

    for c in moves:
        bit = 1 << height[c]
        height[c] += 1
        new_current = opponent
        new_opponent = current | bit
        new_mask = mask | bit

        score, _ = negamax(new_current, new_opponent, new_mask, height,
                           depth - 1, -beta, -alpha, ply + 1,
                           deadline, tt)
        score = -score

        height[c] -= 1

        if score > best_score:
            best_score = score
            best_col = c

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    # Store position evaluation in transposition table
    if best_score <= orig_alpha:
        flag = 2  # UPPERBOUND
    elif best_score >= beta:
        flag = 1  # LOWERBOUND
    else:
        flag = 0  # EXACT
    tt[tt_key] = (depth, flag, best_score, best_col)

    return best_score, best_col


def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy function.
    Returns the chosen column index (0-6).
    """
    global node_count
    node_count = 0

    # Parse board state into bitboards
    current = 0
    mask = 0
    height = [0] * 7

    for c in range(7):
        count = 0
        for r in range(5, -1, -1):
            val = board[r][c]
            if val == 0:
                break
            bit = 1 << (c * 7 + count)
            mask |= bit
            if val == 1:
                current |= bit
            count += 1
        height[c] = c * 7 + count

    opponent = mask ^ current

    legal_moves = [c for c in MOVE_ORDER if height[c] < c * 7 + 6]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    # 1. Take immediate win if available
    for c in legal_moves:
        bit = 1 << height[c]
        if is_win(current | bit):
            return c

    # 2. Block immediate opponent win if present
    opp_wins = []
    for c in legal_moves:
        bit = 1 << height[c]
        if is_win(opponent | bit):
            opp_wins.append(c)
    if opp_wins:
        return opp_wins[0]

    # 3. Iterative deepening search
    start_time = time.time()
    deadline = start_time + 0.85
    best_move = legal_moves[0]
    tt = {}

    for max_depth in range(1, 43):
        try:
            score, move = negamax(current, opponent, mask, height,
                                  max_depth, -1000000, 1000000, 0,
                                  deadline, tt)
            if move in legal_moves:
                best_move = move
            if score >= 90000:
                # Forced win confirmed
                break
            if time.time() >= deadline:
                break
        except SearchTimeout:
            break

    return best_move
