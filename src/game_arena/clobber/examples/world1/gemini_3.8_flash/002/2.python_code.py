
import time

MASK30 = (1 << 30) - 1
COL0_MASK = sum(1 << (r * 6) for r in range(5))
COL5_MASK = sum(1 << (r * 6 + 5) for r in range(5))
NOT_COL0 = MASK30 ^ COL0_MASK
NOT_COL5 = MASK30 ^ COL5_MASK

TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2


def to_bitboard(grid) -> int:
    """Converts 2D list, 1D list, or numpy array to a 30-bit integer."""
    if hasattr(grid, "flatten"):
        flat = grid.flatten()
    elif isinstance(grid, (list, tuple)) and len(grid) > 0 and isinstance(grid[0], (list, tuple)):
        flat = [cell for row in grid for cell in row]
    else:
        flat = grid

    b = 0
    for i, v in enumerate(flat):
        if v:
            b |= 1 << i
    return b


def count_moves(b_p: int, b_o: int) -> int:
    """Computes total legal moves for player b_p against opponent b_o."""
    m_up = (b_p >> 6) & b_o
    m_down = (b_p << 6) & b_o & MASK30
    m_left = ((b_p & NOT_COL0) >> 1) & b_o
    m_right = ((b_p & NOT_COL5) << 1) & b_o
    return m_up.bit_count() + m_down.bit_count() + m_left.bit_count() + m_right.bit_count()


def get_moves(b_p: int, b_o: int):
    """Generates all legal moves as (start_idx, dest_idx, dir_str)."""
    moves = []

    # Up: player piece moves up onto opponent piece
    m = (b_p >> 6) & b_o
    while m:
        lsb = m & -m
        t = lsb.bit_length() - 1
        moves.append((t + 6, t, 'U'))
        m ^= lsb

    # Down: player piece moves down onto opponent piece
    m = (b_p << 6) & b_o & MASK30
    while m:
        lsb = m & -m
        t = lsb.bit_length() - 1
        moves.append((t - 6, t, 'D'))
        m ^= lsb

    # Left: player piece moves left onto opponent piece
    m = ((b_p & NOT_COL0) >> 1) & b_o
    while m:
        lsb = m & -m
        t = lsb.bit_length() - 1
        moves.append((t + 1, t, 'L'))
        m ^= lsb

    # Right: player piece moves right onto opponent piece
    m = ((b_p & NOT_COL5) << 1) & b_o
    while m:
        lsb = m & -m
        t = lsb.bit_length() - 1
        moves.append((t - 1, t, 'R'))
        m ^= lsb

    return moves


def evaluate(b_p: int, b_o: int, ply: int) -> int:
    """Heuristic static evaluation from perspective of player b_p."""
    my_moves = count_moves(b_p, b_o)
    if my_moves == 0:
        return -100000 + ply

    opp_moves = count_moves(b_o, b_p)
    if opp_moves == 0:
        return 100000 - ply

    my_pieces = b_p.bit_count()
    opp_pieces = b_o.bit_count()

    return (my_moves - opp_moves) * 25 + (my_pieces - opp_pieces) * 5


class SearchTimeout(Exception):
    pass


def negamax(b_p: int, b_o: int, depth: int, ply: int, alpha: int, beta: int,
            tt: dict, deadline: float):
    if time.perf_counter() > deadline:
        raise SearchTimeout()

    orig_alpha = alpha
    state_key = (b_p, b_o)

    if state_key in tt:
        tt_depth, tt_flag, tt_score, tt_move = tt[state_key]
        if tt_depth >= depth:
            if tt_flag == TT_EXACT:
                return tt_score, tt_move
            elif tt_flag == TT_LOWERBOUND:
                alpha = max(alpha, tt_score)
            elif tt_flag == TT_UPPERBOUND:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score, tt_move
    else:
        tt_move = None

    moves = get_moves(b_p, b_o)
    if not moves:
        return -100000 + ply, None

    if depth <= 0:
        return evaluate(b_p, b_o, ply), None

    if tt_move and tt_move in moves:
        moves.remove(tt_move)
        moves.insert(0, tt_move)

    best_score = -200000
    best_move = moves[0]

    for move in moves:
        u, v, _ = move
        # Execute move: b_p moves from u to v, capturing opponent at v
        next_bp = (b_p ^ (1 << u)) | (1 << v)
        next_bo = b_o ^ (1 << v)

        # Invert perspective for the opponent
        score, _ = negamax(next_bo, next_bp, depth - 1, ply + 1, -beta, -alpha, tt, deadline)
        score = -score

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)
        if alpha >= beta:
            break

    flag = TT_EXACT
    if best_score <= orig_alpha:
        flag = TT_UPPERBOUND
    elif best_score >= beta:
        flag = TT_LOWERBOUND

    if len(tt) < 500000:
        tt[state_key] = (depth, flag, best_score, best_move)

    return best_score, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    deadline = start_time + 0.90

    b_you = to_bitboard(you)
    b_opp = to_bitboard(opponent)

    legal_moves = get_moves(b_you, b_opp)
    if not legal_moves:
        return "0,0,U"

    best_move = legal_moves[0]
    tt = {}

    for depth in range(1, 35):
        try:
            _, move = negamax(b_you, b_opp, depth, 0, -200000, 200000, tt, deadline)
            if move is not None:
                best_move = move
        except SearchTimeout:
            break

    start_idx, _, direction = best_move
    row = start_idx // 6
    col = start_idx % 6
    return f"{row},{col},{direction}"
