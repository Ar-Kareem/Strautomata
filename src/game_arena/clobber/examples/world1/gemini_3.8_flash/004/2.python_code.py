
import time

# Precompute board geometry and valid directed edges for 5x6 grid
ROWS = 5
COLS = 6
NUM_SQUARES = 30

# Each entry: (from_sq, to_sq, dir_str, from_mask, to_mask)
ALL_EDGES = []
for r in range(ROWS):
    for c in range(COLS):
        sq = r * COLS + c
        from_mask = 1 << sq
        if r > 0:
            to_sq = sq - COLS
            ALL_EDGES.append((sq, to_sq, 'U', from_mask, 1 << to_sq))
        if r < ROWS - 1:
            to_sq = sq + COLS
            ALL_EDGES.append((sq, to_sq, 'D', from_mask, 1 << to_sq))
        if c > 0:
            to_sq = sq - 1
            ALL_EDGES.append((sq, to_sq, 'L', from_mask, 1 << to_sq))
        if c < COLS - 1:
            to_sq = sq + 1
            ALL_EDGES.append((sq, to_sq, 'R', from_mask, 1 << to_sq))


def get_legal_moves(player_bb: int, opp_bb: int):
    """Generate all legal moves for player_bb against opp_bb."""
    moves = []
    for from_sq, to_sq, d, from_mask, to_mask in ALL_EDGES:
        if (player_bb & from_mask) and (opp_bb & to_mask):
            moves.append((from_sq, to_sq, d, from_mask, to_mask))
    return moves


def count_moves(player_bb: int, opp_bb: int) -> int:
    """Fast mobility count."""
    cnt = 0
    for _, _, _, from_mask, to_mask in ALL_EDGES:
        if (player_bb & from_mask) and (opp_bb & to_mask):
            cnt += 1
    return cnt


def evaluate(player_bb: int, opp_bb: int) -> int:
    """
    Heuristic evaluation from player_bb's perspective.
    Emphasizes mobility difference and active pieces.
    """
    p_moves = 0
    o_moves = 0
    p_active = 0
    o_active = 0

    for _, _, _, f_mask, t_mask in ALL_EDGES:
        if (player_bb & f_mask) and (opp_bb & t_mask):
            p_moves += 1
            p_active |= f_mask
        if (opp_bb & f_mask) and (player_bb & t_mask):
            o_moves += 1
            o_active |= f_mask

    if p_moves == 0:
        return -50000
    if o_moves == 0:
        return 50000

    p_active_count = bin(p_active).count('1')
    o_active_count = bin(o_active).count('1')

    return (p_moves - o_moves) * 100 + (p_active_count - o_active_count) * 20


class SearchTimeout(Exception):
    pass


def policy(you, opponent) -> str:
    start_time = time.time()
    time_limit = 0.82  # Target within 1.0s limit

    # Parse input into 30-bit integers
    flat_you = []
    flat_opp = []

    # Flatten inputs regardless of format (list of lists, flat list, numpy array)
    try:
        flat_you = [int(v) for row in you for v in row]
    except TypeError:
        flat_you = [int(v) for v in you]

    try:
        flat_opp = [int(v) for row in opponent for v in row]
    except TypeError:
        flat_opp = [int(v) for v in opponent]

    you_bb = 0
    opp_bb = 0
    for i in range(NUM_SQUARES):
        if flat_you[i]:
            you_bb |= 1 << i
        if flat_opp[i]:
            opp_bb |= 1 << i

    moves = get_legal_moves(you_bb, opp_bb)
    if not moves:
        return "0,0,U"  # Fallback if no moves possible

    if len(moves) == 1:
        f_sq, _, d, _, _ = moves[0]
        return f"{f_sq // COLS},{f_sq % COLS},{d}"

    # Check for immediate winning move (leaves opponent with 0 moves)
    for m in moves:
        f_sq, t_sq, d, f_mask, t_mask = m
        next_you = (you_bb ^ f_mask) | t_mask
        next_opp = opp_bb ^ t_mask
        if count_moves(next_opp, next_you) == 0:
            return f"{f_sq // COLS},{f_sq % COLS},{d}"

    # Transposition Table: (player_bb, opp_bb) -> (depth, score, flag, best_move)
    # flag: 0 = EXACT, 1 = LOWERBOUND (alpha), 2 = UPPERBOUND (beta)
    tt = {}

    def negamax(p_bb: int, o_bb: int, depth: int, alpha: int, beta: int) -> int:
        if time.time() - start_time > time_limit:
            raise SearchTimeout()

        alpha_orig = alpha
        state_key = (p_bb, o_bb)
        tt_entry = tt.get(state_key)
        tt_move = None

        if tt_entry is not None:
            tt_depth, tt_score, tt_flag, tt_best = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score
            tt_move = tt_best

        legal = get_legal_moves(p_bb, o_bb)
        if not legal:
            return -50000 - depth  # Loss for current player

        if depth <= 0:
            return evaluate(p_bb, o_bb)

        # Move ordering: TT move first, then moves capturing active opponent pieces
        if tt_move is not None:
            legal.sort(key=lambda m: 1000 if (m[0] == tt_move[0] and m[1] == tt_move[1]) else 0, reverse=True)

        best_score = -100000
        best_m = legal[0]

        for m in legal:
            f_sq, t_sq, d, f_mask, t_mask = m
            nxt_p = (p_bb ^ f_mask) | t_mask
            nxt_o = o_bb ^ t_mask

            score = -negamax(nxt_o, nxt_p, depth - 1, -beta, -alpha)

            if score > best_score:
                best_score = score
                best_m = m

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        # Store in TT
        if best_score <= alpha_orig:
            flag = 2  # UPPERBOUND
        elif best_score >= beta:
            flag = 1  # LOWERBOUND
        else:
            flag = 0  # EXACT
        tt[state_key] = (depth, best_score, flag, best_m)

        return best_score

    best_move_found = moves[0]

    # Iterative deepening
    try:
        for depth in range(1, 25):
            current_best_move = None
            current_best_score = -100000
            alpha = -100000
            beta = 100000

            # Order root moves using previous TT information if available
            root_key = (you_bb, opp_bb)
            tt_entry = tt.get(root_key)
            if tt_entry is not None and tt_entry[3] is not None:
                prev_best = tt_entry[3]
                moves.sort(key=lambda m: 1000 if (m[0] == prev_best[0] and m[1] == prev_best[1]) else 0, reverse=True)

            for m in moves:
                if time.time() - start_time > time_limit:
                    raise SearchTimeout()

                f_sq, t_sq, d, f_mask, t_mask = m
                nxt_you = (you_bb ^ f_mask) | t_mask
                nxt_opp = opp_bb ^ t_mask

                score = -negamax(nxt_opp, nxt_you, depth - 1, -beta, -alpha)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = m

                alpha = max(alpha, score)

            if current_best_move is not None:
                best_move_found = current_best_move
                tt[root_key] = (depth, current_best_score, 0, current_best_move)

            # If proven win found, no need to search deeper
            if current_best_score >= 40000:
                break

    except SearchTimeout:
        pass

    f_sq, _, d, _, _ = best_move_found
    r = f_sq // COLS
    c = f_sq % COLS
    return f"{r},{c},{d}"
