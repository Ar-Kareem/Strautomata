
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.85  # safety margin under 1.0s

    is_white = (color == 'w')

    # Convert coordinates to bitboard
    # Square: row * 8 + col (0 <= row, col <= 7)
    my_bb = 0
    for r, c in me:
        my_bb |= (1 << (r * 8 + c))
    
    opp_bb = 0
    for r, c in opp:
        opp_bb |= (1 << (r * 8 + c))

    # Helper: Check immediate win
    # White moves to row 7 (squares 56..63)
    # Black moves to row 0 (squares 0..7)
    target_row = 7 if is_white else 0

    def generate_moves(p_bb, o_bb, white):
        moves = []
        occ = p_bb | o_bb
        if white:
            # White moves: +8 (straight), +7 (diag left), +9 (diag right)
            # From row 0..6
            b = p_bb
            while b:
                lsb = b & -b
                from_sq = lsb.bit_length() - 1
                b ^= lsb
                r = from_sq >> 3
                c = from_sq & 7
                if r == 7:
                    continue
                # Straight forward: empty
                to_sq = from_sq + 8
                if not (occ & (1 << to_sq)):
                    moves.append((from_sq, to_sq, False))
                # Diag left (c - 1)
                if c > 0:
                    to_sq = from_sq + 7
                    is_opp = bool(o_bb & (1 << to_sq))
                    if is_opp or not (occ & (1 << to_sq)):
                        moves.append((from_sq, to_sq, is_opp))
                # Diag right (c + 1)
                if c < 7:
                    to_sq = from_sq + 9
                    is_opp = bool(o_bb & (1 << to_sq))
                    if is_opp or not (occ & (1 << to_sq)):
                        moves.append((from_sq, to_sq, is_opp))
        else:
            # Black moves: -8 (straight), -9 (diag left), -7 (diag right)
            b = p_bb
            while b:
                lsb = b & -b
                from_sq = lsb.bit_length() - 1
                b ^= lsb
                r = from_sq >> 3
                c = from_sq & 7
                if r == 0:
                    continue
                # Straight forward: empty
                to_sq = from_sq - 8
                if not (occ & (1 << to_sq)):
                    moves.append((from_sq, to_sq, False))
                # Diag left (c - 1)
                if c > 0:
                    to_sq = from_sq - 9
                    is_opp = bool(o_bb & (1 << to_sq))
                    if is_opp or not (occ & (1 << to_sq)):
                        moves.append((from_sq, to_sq, is_opp))
                # Diag right (c + 1)
                if c < 7:
                    to_sq = from_sq - 7
                    is_opp = bool(o_bb & (1 << to_sq))
                    if is_opp or not (occ & (1 << to_sq)):
                        moves.append((from_sq, to_sq, is_opp))
        return moves

    # Check for immediate win
    root_moves = generate_moves(my_bb, opp_bb, is_white)
    if not root_moves:
        # Fallback (should not happen in legal game)
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))

    for m in root_moves:
        if (m[1] >> 3) == target_row:
            f, t = m[0], m[1]
            return ((f >> 3, f & 7), (t >> 3, t & 7))

    # Static Evaluation weights
    ROW_WEIGHTS_W = [0, 10, 25, 50, 100, 220, 600, 100000]
    ROW_WEIGHTS_B = [100000, 600, 220, 100, 50, 25, 10, 0]

    def evaluate(p_bb, o_bb, turn_white):
        # Count and score pieces
        p_score = 0
        o_score = 0
        
        b = p_bb
        p_count = 0
        while b:
            lsb = b & -b
            sq = lsb.bit_length() - 1
            b ^= lsb
            p_count += 1
            r = sq >> 3
            p_score += (ROW_WEIGHTS_W[r] if turn_white else ROW_WEIGHTS_B[r])
            # Protection bonus
            c = sq & 7
            if turn_white:
                if r > 0:
                    if c > 0 and (p_bb & (1 << (sq - 9))):
                        p_score += 15
                    if c < 7 and (p_bb & (1 << (sq - 7))):
                        p_score += 15
            else:
                if r < 7:
                    if c > 0 and (p_bb & (1 << (sq + 7))):
                        p_score += 15
                    if c < 7 and (p_bb & (1 << (sq + 9))):
                        p_score += 15

        b = o_bb
        o_count = 0
        while b:
            lsb = b & -b
            sq = lsb.bit_length() - 1
            b ^= lsb
            o_count += 1
            r = sq >> 3
            o_score += (ROW_WEIGHTS_B[r] if turn_white else ROW_WEIGHTS_W[r])
            c = sq & 7
            if not turn_white:
                if r > 0:
                    if c > 0 and (o_bb & (1 << (sq - 9))):
                        o_score += 15
                    if c < 7 and (o_bb & (1 << (sq - 7))):
                        o_score += 15
            else:
                if r < 7:
                    if c > 0 and (o_bb & (1 << (sq + 7))):
                        o_score += 15
                    if c < 7 and (o_bb & (1 << (sq + 9))):
                        o_score += 15

        return (p_score - o_score) + (p_count - o_count) * 80

    tt = {}

    def score_move(m, white):
        f, t, is_cap = m
        tr = t >> 3
        dist_score = (tr if white else (7 - tr)) * 50
        return (1000 if is_cap else 0) + dist_score

    best_move = root_moves[0]

    # Iterative Deepening
    max_depth = 12
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break

        def alphabeta(p_bb, o_bb, d, alpha, beta, cur_white):
            # Check terminal states
            if cur_white:
                if p_bb & 0xFF00000000000000:  # White reached row 7
                    return 500000 + d * 1000
                if o_bb & 0x00000000000000FF:  # Black reached row 0
                    return -500000 - d * 1000
            else:
                if p_bb & 0x00000000000000FF:  # Black reached row 0
                    return 500000 + d * 1000
                if o_bb & 0xFF00000000000000:  # White reached row 7
                    return -500000 - d * 1000

            if not o_bb:
                return 500000 + d * 1000
            if not p_bb:
                return -500000 - d * 1000

            if d == 0:
                return evaluate(p_bb, o_bb, cur_white)

            state_key = (p_bb, o_bb, cur_white)
            if state_key in tt:
                tt_d, tt_val, tt_flag = tt[state_key]
                if tt_d >= d:
                    if tt_flag == 0:  # EXACT
                        return tt_val
                    elif tt_flag == 1 and tt_val <= alpha:  # UPPERBOUND
                        return tt_val
                    elif tt_flag == 2 and tt_val >= beta:  # LOWERBOUND
                        return tt_val

            moves = generate_moves(p_bb, o_bb, cur_white)
            if not moves:
                return -500000 - d * 1000

            # Sort moves
            moves.sort(key=lambda m: score_move(m, cur_white), reverse=True)

            orig_alpha = alpha
            value = -99999999

            for f, t, is_cap in moves:
                np_bb = (p_bb ^ (1 << f)) | (1 << t)
                no_bb = o_bb & ~(1 << t) if is_cap else o_bb

                val = -alphabeta(no_bb, np_bb, d - 1, -beta, -alpha, not cur_white)
                if val > value:
                    value = val
                alpha = max(alpha, value)
                if alpha >= beta:
                    break

            flag = 0 if (orig_alpha < value < beta) else (2 if value >= beta else 1)
            tt[state_key] = (d, value, flag)
            return value

        # Root search
        root_moves.sort(key=lambda m: score_move(m, is_white), reverse=True)
        cur_best_move = best_move
        alpha = -10000000
        beta = 10000000
        aborted = False

        for m in root_moves:
            if time.time() - start_time > time_limit:
                aborted = True
                break
            f, t, is_cap = m
            np_bb = (my_bb ^ (1 << f)) | (1 << t)
            no_bb = opp_bb & ~(1 << t) if is_cap else opp_bb

            val = -alphabeta(no_bb, np_bb, depth - 1, -beta, -alpha, not is_white)
            if val > alpha:
                alpha = val
                cur_best_move = m

        if not aborted:
            best_move = cur_best_move
            if alpha > 400000:
                # Forced win found
                break

    f, t, _ = best_move
    return ((f >> 3, f & 7), (t >> 3, t & 7))
