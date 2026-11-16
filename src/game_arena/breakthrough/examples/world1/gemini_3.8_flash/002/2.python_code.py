
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.85  # Safe margin under 1.0s limit

    is_white = (color == 'w')

    # Convert coordinates to bitboards (sq = r * 8 + c)
    my_bb = 0
    for r, c in me:
        my_bb |= (1 << (r * 8 + c))

    opp_bb = 0
    for r, c in opp:
        opp_bb |= (1 << (r * 8 + c))

    NOT_A_FILE = 0xFEFEFEFEFEFEFEFE
    NOT_H_FILE = 0x7F7F7F7F7F7F7F7F
    ROW_7 = 0xFF00000000000000
    ROW_0 = 0x00000000000000FF

    def generate_moves(p_bb: int, o_bb: int, white: bool):
        empty = ~(p_bb | o_bb) & 0xFFFFFFFFFFFFFFFF
        moves = []
        if white:
            # Straight (+8)
            straight_targets = (p_bb << 8) & empty & 0xFFFFFFFFFFFFFFFF
            # Diag left (+7, c > 0)
            diag_l_targets = ((p_bb & NOT_A_FILE) << 7) & (empty | o_bb) & 0xFFFFFFFFFFFFFFFF
            # Diag right (+9, c < 7)
            diag_r_targets = ((p_bb & NOT_H_FILE) << 9) & (empty | o_bb) & 0xFFFFFFFFFFFFFFFF

            # Check instant wins first
            w_straight = straight_targets & ROW_7
            if w_straight:
                to_sq = (w_straight & -w_straight).bit_length() - 1
                return [(to_sq - 8, to_sq)]
            w_dl = diag_l_targets & ROW_7
            if w_dl:
                to_sq = (w_dl & -w_dl).bit_length() - 1
                return [(to_sq - 7, to_sq)]
            w_dr = diag_r_targets & ROW_7
            if w_dr:
                to_sq = (w_dr & -w_dr).bit_length() - 1
                return [(to_sq - 9, to_sq)]

            # Captures
            capt_l = diag_l_targets & o_bb
            capt_r = diag_r_targets & o_bb
            temp = capt_l
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq - 7, to_sq, 2))  # priority 2: capture
                temp &= temp - 1
            temp = capt_r
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq - 9, to_sq, 2))
                temp &= temp - 1

            # Non-captures
            non_capt_l = diag_l_targets & empty
            non_capt_r = diag_r_targets & empty
            temp = non_capt_l
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq - 7, to_sq, 1))  # priority 1: forward diagonal
                temp &= temp - 1
            temp = non_capt_r
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq - 9, to_sq, 1))
                temp &= temp - 1
            temp = straight_targets
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq - 8, to_sq, 0))  # priority 0: forward straight
                temp &= temp - 1
        else:
            # Straight (-8)
            straight_targets = (p_bb >> 8) & empty
            # Diag left (-9, c > 0)
            diag_l_targets = ((p_bb & NOT_A_FILE) >> 9) & (empty | o_bb)
            # Diag right (-7, c < 7)
            diag_r_targets = ((p_bb & NOT_H_FILE) >> 7) & (empty | o_bb)

            # Check instant wins first
            b_straight = straight_targets & ROW_0
            if b_straight:
                to_sq = (b_straight & -b_straight).bit_length() - 1
                return [(to_sq + 8, to_sq)]
            b_dl = diag_l_targets & ROW_0
            if b_dl:
                to_sq = (b_dl & -b_dl).bit_length() - 1
                return [(to_sq + 9, to_sq)]
            b_dr = diag_r_targets & ROW_0
            if b_dr:
                to_sq = (b_dr & -b_dr).bit_length() - 1
                return [(to_sq + 7, to_sq)]

            # Captures
            capt_l = diag_l_targets & o_bb
            capt_r = diag_r_targets & o_bb
            temp = capt_l
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq + 9, to_sq, 2))
                temp &= temp - 1
            temp = capt_r
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq + 7, to_sq, 2))
                temp &= temp - 1

            # Non-captures
            non_capt_l = diag_l_targets & empty
            non_capt_r = diag_r_targets & empty
            temp = non_capt_l
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq + 9, to_sq, 1))
                temp &= temp - 1
            temp = non_capt_r
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq + 7, to_sq, 1))
                temp &= temp - 1
            temp = straight_targets
            while temp:
                to_sq = (temp & -temp).bit_length() - 1
                moves.append((to_sq + 8, to_sq, 0))
                temp &= temp - 1

        # Sort moves: higher priority (captures) first, then deeper advances
        if white:
            moves.sort(key=lambda m: (m[2], m[1] // 8), reverse=True)
        else:
            moves.sort(key=lambda m: (m[2], 7 - (m[1] // 8)), reverse=True)

        return [(m[0], m[1]) for m in moves]

    def evaluate(p_bb: int, o_bb: int, white: bool) -> int:
        if white:
            if p_bb & ROW_7:
                return 100000
            if o_bb & ROW_0:
                return -100000
        else:
            if p_bb & ROW_0:
                return 100000
            if o_bb & ROW_7:
                return -100000

        p_count = bin(p_bb).count('1')
        o_count = bin(o_bb).count('1')
        if o_count == 0:
            return 100000
        if p_count == 0:
            return -100000

        score = (p_count - o_count) * 150

        # Positional progress weights per row
        row_weights_w = [0, 5, 15, 35, 75, 160, 400, 10000]
        row_weights_b = [10000, 400, 160, 75, 35, 15, 5, 0]

        weights_me = row_weights_w if white else row_weights_b
        weights_opp = row_weights_b if white else row_weights_w

        temp = p_bb
        while temp:
            sq = (temp & -temp).bit_length() - 1
            r = sq >> 3
            score += weights_me[r]
            temp &= temp - 1

        temp = o_bb
        while temp:
            sq = (temp & -temp).bit_length() - 1
            r = sq >> 3
            score -= weights_opp[r]
            temp &= temp - 1

        return score

    initial_moves = generate_moves(my_bb, opp_bb, is_white)
    if not initial_moves:
        # Fallback if no moves are found (should not happen in valid state)
        m = me[0]
        return (m, m)

    # Check for immediate win
    for frm, to in initial_moves:
        target_row = to >> 3
        if (is_white and target_row == 7) or (not is_white and target_row == 0):
            return ((frm >> 3, frm & 7), (to >> 3, to & 7))

    best_move = initial_moves[0]
    tt = {}

    def negamax(p_bb: int, o_bb: int, white: bool, depth: int, alpha: int, beta: int) -> int:
        nonlocal best_iter_move
        if time.time() - start_time > time_limit:
            raise TimeoutError

        state_key = (p_bb, o_bb, white)
        if state_key in tt:
            tt_depth, tt_val, tt_flag, tt_best = tt[state_key]
            if tt_depth >= depth:
                if tt_flag == 'EXACT':
                    return tt_val
                elif tt_flag == 'LOWERBOUND':
                    alpha = max(alpha, tt_val)
                elif tt_flag == 'UPPERBOUND':
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

        if depth == 0:
            return evaluate(p_bb, o_bb, white)

        moves = generate_moves(p_bb, o_bb, white)
        if not moves:
            return -100000

        # Prioritize TT move if available
        if state_key in tt and tt[state_key][3] in moves:
            tt_m = tt[state_key][3]
            moves.remove(tt_m)
            moves.insert(0, tt_m)

        best_val = -999999
        local_best = moves[0]
        alpha_orig = alpha

        for frm, to in moves:
            to_row = to >> 3
            if (white and to_row == 7) or (not white and to_row == 0):
                # Winning terminal move
                return 90000 + depth

            # Apply move
            new_p = (p_bb & ~(1 << frm)) | (1 << to)
            new_o = o_bb & ~(1 << to)

            if new_o == 0:
                val = 90000 + depth
            else:
                val = -negamax(new_o, new_p, not white, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
                local_best = (frm, to)
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # TT store
        flag = 'EXACT'
        if best_val <= alpha_orig:
            flag = 'UPPERBOUND'
        elif best_val >= beta:
            flag = 'LOWERBOUND'
        tt[state_key] = (depth, best_val, flag, local_best)

        return best_val

    # Iterative deepening
    max_depth = 12
    for depth in range(1, max_depth + 1):
        try:
            moves = initial_moves[:]
            if best_move in moves:
                moves.remove(best_move)
                moves.insert(0, best_move)

            best_iter_move = moves[0]
            alpha = -999999
            beta = 999999
            best_val = -999999

            for frm, to in moves:
                new_p = (my_bb & ~(1 << frm)) | (1 << to)
                new_o = opp_bb & ~(1 << to)
                if new_o == 0:
                    val = 90000
                else:
                    val = -negamax(new_o, new_p, not is_white, depth - 1, -beta, -alpha)

                if val > best_val:
                    best_val = val
                    best_iter_move = (frm, to)
                alpha = max(alpha, val)

            best_move = best_iter_move
            if best_val >= 80000:
                # Forced win found
                break
        except TimeoutError:
            break

    frm, to = best_move
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))
