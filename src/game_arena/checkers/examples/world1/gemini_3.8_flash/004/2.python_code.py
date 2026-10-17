
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.85  # Reserve safety margin within the 1.0 second limit

    # Board orientation & promotion ranks
    is_white = (color == 'w')
    my_dir = 1 if is_white else -1
    opp_dir = -my_dir
    my_promo_row = 7 if is_white else 0
    opp_promo_row = 0 if is_white else 7

    # Represent state as sets of (r, c)
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)

    def get_moves(p_men, p_kings, o_men, o_kings, p_dir):
        all_p = p_men | p_kings
        all_o = o_men | o_kings
        occupied = all_p | all_o

        jumps = []
        regular = []

        # Check jumps for men
        for r, c in p_men:
            for dc in (-1, 1):
                mr, mc = r + p_dir, c + dc
                lr, lc = r + 2 * p_dir, c + 2 * dc
                if 0 <= lr <= 7 and 0 <= lc <= 7:
                    if (mr, mc) in all_o and (lr, lc) not in occupied:
                        jumps.append(((r, c), (lr, lc), (mr, mc), False))

        # Check jumps for kings
        for r, c in p_kings:
            for dr in (-1, 1):
                for dc in (-1, 1):
                    mr, mc = r + dr, c + dc
                    lr, lc = r + 2 * dr, c + 2 * dc
                    if 0 <= lr <= 7 and 0 <= lc <= 7:
                        if (mr, mc) in all_o and (lr, lc) not in occupied:
                            jumps.append(((r, c), (lr, lc), (mr, mc), True))

        if jumps:
            return jumps, True

        # Regular moves
        for r, c in p_men:
            for dc in (-1, 1):
                nr, nc = r + p_dir, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in occupied:
                    regular.append(((r, c), (nr, nc), None, False))

        for r, c in p_kings:
            for dr in (-1, 1):
                for dc in (-1, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in occupied:
                        regular.append(((r, c), (nr, nc), None, True))

        return regular, False

    def apply_move(p_men, p_kings, o_men, o_kings, move, p_promo_row):
        start, end, captured, is_king = move
        new_p_men = set(p_men)
        new_p_kings = set(p_kings)
        new_o_men = set(o_men)
        new_o_kings = set(o_kings)

        if is_king:
            new_p_kings.remove(start)
            new_p_kings.add(end)
        else:
            new_p_men.remove(start)
            if end[0] == p_promo_row:
                new_p_kings.add(end)
            else:
                new_p_men.add(end)

        if captured:
            if captured in new_o_men:
                new_o_men.remove(captured)
            elif captured in new_o_kings:
                new_o_kings.remove(captured)

        return new_p_men, new_p_kings, new_o_men, new_o_kings

    # Positional evaluation tables
    def evaluate(p_men, p_kings, o_men, o_kings):
        # Material
        score = (len(p_men) * 100 + len(p_kings) * 160) - (len(o_men) * 100 + len(o_kings) * 160)

        # Positional bonuses
        for r, c in p_men:
            # Advancement bonus
            adv = r if is_white else (7 - r)
            score += adv * 5
            # Back-rank defense
            if (is_white and r == 0) or (not is_white and r == 7):
                score += 15
            # Center control
            if 2 <= r <= 5 and 2 <= c <= 5:
                score += 8
            # Edge penalty
            if c == 0 or c == 7:
                score -= 6

        for r, c in p_kings:
            # Kings prefer center
            if 2 <= r <= 5 and 2 <= c <= 5:
                score += 12
            if c == 0 or c == 7:
                score -= 4

        for r, c in o_men:
            adv = (7 - r) if is_white else r
            score -= adv * 5
            if (not is_white and r == 0) or (is_white and r == 7):
                score -= 15
            if 2 <= r <= 5 and 2 <= c <= 5:
                score -= 8
            if c == 0 or c == 7:
                score += 6

        for r, c in o_kings:
            if 2 <= r <= 5 and 2 <= c <= 5:
                score -= 12
            if c == 0 or c == 7:
                score += 4

        return score

    legal_moves, is_capture = get_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, my_dir)
    if not legal_moves:
        return ((0, 0), (0, 0))
    if len(legal_moves) == 1:
        return (legal_moves[0][0], legal_moves[0][1])

    # Move ordering heuristic
    def move_priority(m):
        _, end, captured, is_king = m
        prio = 0
        if captured:
            prio += 1000
        if not is_king and end[0] == my_promo_row:
            prio += 500
        if 2 <= end[0] <= 5 and 2 <= end[1] <= 5:
            prio += 50
        return prio

    legal_moves.sort(key=move_priority, reverse=True)

    def minimax(p_men, p_kings, o_men, o_kings, depth, alpha, beta, maximizing, p_dir, o_dir, p_promo, o_promo):
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        if maximizing:
            moves, _ = get_moves(p_men, p_kings, o_men, o_kings, p_dir)
            if not moves:
                return -20000 + (10 - depth)
            if depth == 0:
                return evaluate(p_men, p_kings, o_men, o_kings)

            moves.sort(key=move_priority, reverse=True)
            max_eval = -999999
            for m in moves:
                np_m, np_k, no_m, no_k = apply_move(p_men, p_kings, o_men, o_kings, m, p_promo)
                val = minimax(np_m, np_k, no_m, no_k, depth - 1, alpha, beta, False, p_dir, o_dir, p_promo, o_promo)
                if val > max_eval:
                    max_eval = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            moves, _ = get_moves(o_men, o_kings, p_men, p_kings, o_dir)
            if not moves:
                return 20000 - (10 - depth)
            if depth == 0:
                return evaluate(p_men, p_kings, o_men, o_kings)

            moves.sort(key=move_priority, reverse=True)
            min_eval = 999999
            for m in moves:
                no_m, no_k, np_m, np_k = apply_move(o_men, o_kings, p_men, p_kings, m, o_promo)
                val = minimax(np_m, np_k, no_m, no_k, depth - 1, alpha, beta, True, p_dir, o_dir, p_promo, o_promo)
                if val < min_eval:
                    min_eval = val
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval

    # Iterative deepening
    best_move = legal_moves[0]
    for depth in range(1, 12):
        best_at_depth = None
        best_val = -999999
        alpha = -999999
        beta = 999999
        try:
            for m in legal_moves:
                np_m, np_k, no_m, no_k = apply_move(my_men_set, my_kings_set, opp_men_set, opp_kings_set, m, my_promo_row)
                val = minimax(np_m, np_k, no_m, no_k, depth - 1, alpha, beta, False, my_dir, opp_dir, my_promo_row, opp_promo_row)
                if val > best_val:
                    best_val = val
                    best_at_depth = m
                alpha = max(alpha, val)

            if best_at_depth:
                best_move = best_at_depth
                # Reorder top moves for next depth
                legal_moves.remove(best_move)
                legal_moves.insert(0, best_move)
        except TimeoutError:
            break

    return (best_move[0], best_move[1])
