
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.85

    # 1. Immediate fallback legal move generator
    def get_raw_moves(my_pieces, opp_pieces, is_white):
        my_set = set(my_pieces)
        opp_set = set(opp_pieces)
        moves = []
        dr = 1 if is_white else -1
        target_row = 7 if is_white else 0

        for r, c in my_pieces:
            nr = r + dr
            # Straight forward (only if empty)
            if (nr, c) not in my_set and (nr, c) not in opp_set:
                moves.append(((r, c), (nr, c)))
            # Diagonal left
            if c > 0 and (nr, c - 1) not in my_set:
                moves.append(((r, c), (nr, c - 1)))
            # Diagonal right
            if c < 7 and (nr, c + 1) not in my_set:
                moves.append(((r, c), (nr, c + 1)))
        return moves

    is_white = (color == 'w')
    raw_moves = get_raw_moves(me, opp, is_white)
    if not raw_moves:
        return ((0, 0), (0, 0))

    # Immediate win check
    target_row = 7 if is_white else 0
    for m in raw_moves:
        if m[1][0] == target_row:
            return m

    # Bitboard representation: sq = r * 8 + c
    def to_bb(pieces):
        bb = 0
        for r, c in pieces:
            bb |= (1 << (r * 8 + c))
        return bb

    my_bb = to_bb(me)
    opp_bb = to_bb(opp)

    WIN_SCORE = 1_000_000

    def gen_moves_bb(bb_player, bb_enemy, white):
        moves = []
        occ = bb_player | bb_enemy
        if white:
            # White moves r + 1 (sq + 8, sq + 7 [if c > 0], sq + 9 [if c < 7])
            for sq in range(64):
                if not (bb_player & (1 << sq)):
                    continue
                r = sq >> 3
                c = sq & 7
                if r == 7:
                    continue

                # Forward
                dest_fwd = sq + 8
                if not (occ & (1 << dest_fwd)):
                    moves.append((sq, dest_fwd, (bb_enemy & (1 << dest_fwd)) != 0))

                # Diagonal left (c - 1)
                if c > 0:
                    dest_dl = sq + 7
                    if not (bb_player & (1 << dest_dl)):
                        moves.append((sq, dest_dl, (bb_enemy & (1 << dest_dl)) != 0))

                # Diagonal right (c + 1)
                if c < 7:
                    dest_dr = sq + 9
                    if not (bb_player & (1 << dest_dr)):
                        moves.append((sq, dest_dr, (bb_enemy & (1 << dest_dr)) != 0))
        else:
            # Black moves r - 1 (sq - 8, sq - 9 [if c > 0], sq - 7 [if c < 7])
            for sq in range(63, -1, -1):
                if not (bb_player & (1 << sq)):
                    continue
                r = sq >> 3
                c = sq & 7
                if r == 0:
                    continue

                # Forward
                dest_fwd = sq - 8
                if not (occ & (1 << dest_fwd)):
                    moves.append((sq, dest_fwd, (bb_enemy & (1 << dest_fwd)) != 0))

                # Diagonal left (c - 1)
                if c > 0:
                    dest_dl = sq - 9
                    if not (bb_player & (1 << dest_dl)):
                        moves.append((sq, dest_dl, (bb_enemy & (1 << dest_dl)) != 0))

                # Diagonal right (c + 1)
                if c < 7:
                    dest_dr = sq - 7
                    if not (bb_player & (1 << dest_dr)):
                        moves.append((sq, dest_dr, (bb_enemy & (1 << dest_dr)) != 0))

        # Move ordering: Winning moves first, then captures, then advancement
        def move_score(m):
            from_sq, to_sq, is_cap = m
            to_r = to_sq >> 3
            if (white and to_r == 7) or (not white and to_r == 0):
                return 100000
            score = 0
            if is_cap:
                score += 500
            adv = (to_r - (from_sq >> 3)) if white else ((from_sq >> 3) - to_r)
            score += adv * 50 + (to_r if white else (7 - to_r)) * 10
            return score

        moves.sort(key=move_score, reverse=True)
        return moves

    # Positional evaluation weights based on rank advancement
    WHITE_SQUARE_WEIGHTS = [0] * 64
    BLACK_SQUARE_WEIGHTS = [0] * 64
    for sq in range(64):
        r = sq >> 3
        WHITE_SQUARE_WEIGHTS[sq] = [5, 10, 20, 35, 60, 110, 250, 10000][r]
        BLACK_SQUARE_WEIGHTS[sq] = [10000, 250, 110, 60, 35, 20, 10, 5][r]

    def evaluate(bb_w, bb_b):
        score = 0
        w_curr = bb_w
        while w_curr:
            lsb = w_curr & -w_curr
            sq = (lsb.bit_length() - 1)
            score += WHITE_SQUARE_WEIGHTS[sq]
            w_curr ^= lsb

        b_curr = bb_b
        while b_curr:
            lsb = b_curr & -b_curr
            sq = (lsb.bit_length() - 1)
            score -= BLACK_SQUARE_WEIGHTS[sq]
            b_curr ^= lsb

        return score

    best_move = raw_moves[0]

    def minimax(bb_my, bb_opp, depth, alpha, beta, maximizing, is_w):
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        # Check win condition for opponent's previous move
        if not maximizing:
            # Maximizing player just moved
            if is_w and (bb_my & 0xFF00000000000000):
                return WIN_SCORE + depth
            if not is_w and (bb_my & 0x00000000000000FF):
                return WIN_SCORE + depth
            if bb_opp == 0:
                return WIN_SCORE + depth
        else:
            # Minimizing player just moved
            if not is_w and (bb_opp & 0xFF00000000000000):
                return -WIN_SCORE - depth
            if is_w and (bb_opp & 0x00000000000000FF):
                return -WIN_SCORE - depth
            if bb_my == 0:
                return -WIN_SCORE - depth

        if depth == 0:
            eval_score = evaluate(bb_my if is_w else bb_opp, bb_opp if is_w else bb_my)
            return eval_score if is_w else -eval_score

        if maximizing:
            moves = gen_moves_bb(bb_my, bb_opp, is_w)
            if not moves:
                return -WIN_SCORE
            val = -float('inf')
            for from_sq, to_sq, is_cap in moves:
                new_my = (bb_my ^ (1 << from_sq)) | (1 << to_sq)
                new_opp = (bb_opp ^ (1 << to_sq)) if is_cap else bb_opp
                res = minimax(new_my, new_opp, depth - 1, alpha, beta, False, is_w)
                if res > val:
                    val = res
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return val
        else:
            moves = gen_moves_bb(bb_opp, bb_my, not is_w)
            if not moves:
                return WIN_SCORE
            val = float('inf')
            for from_sq, to_sq, is_cap in moves:
                new_opp = (bb_opp ^ (1 << from_sq)) | (1 << to_sq)
                new_my = (bb_my ^ (1 << to_sq)) if is_cap else bb_my
                res = minimax(new_my, new_opp, depth - 1, alpha, beta, True, is_w)
                if res < val:
                    val = res
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return val

    # Iterative deepening search
    current_best_move = raw_moves[0]
    try:
        moves = gen_moves_bb(my_bb, opp_bb, is_white)
        for depth in range(1, 12):
            best_val = -float('inf')
            iteration_best = None

            for from_sq, to_sq, is_cap in moves:
                to_r = to_sq >> 3
                # Instant win
                if (is_white and to_r == 7) or (not is_white and to_r == 0):
                    f_row, f_col = from_sq >> 3, from_sq & 7
                    t_row, t_col = to_sq >> 3, to_sq & 7
                    return ((f_row, f_col), (t_row, t_col))

                new_my = (my_bb ^ (1 << from_sq)) | (1 << to_sq)
                new_opp = (opp_bb ^ (1 << to_sq)) if is_cap else opp_bb

                score = minimax(new_my, new_opp, depth - 1, -float('inf'), float('inf'), False, is_white)
                if score > best_val:
                    best_val = score
                    iteration_best = ((from_sq >> 3, from_sq & 7), (to_sq >> 3, to_sq & 7))

            if iteration_best:
                current_best_move = iteration_best
            if best_val >= WIN_SCORE - 50:
                break
    except TimeoutError:
        pass

    return current_best_move
