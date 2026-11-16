
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Checkers policy returning the best legal move as ((from_r, from_c), (to_r, to_c)).
    """
    start_time = time.time()
    time_limit = 0.85  # Safe buffer under 1.0 second

    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)

    def get_moves(m_men, m_kings, o_men, o_kings, col):
        """
        Generate all legal moves for the current player.
        If any captures are available, only captures are returned.
        """
        fwd_dr = 1 if col == 'w' else -1
        occupied = m_men | m_kings | o_men | o_kings
        opp_all = o_men | o_kings

        captures = []
        quiet_moves = []

        # 1. Check man captures & quiet moves
        for (r, c) in m_men:
            for dc in (-1, 1):
                mid_r, mid_c = r + fwd_dr, c + dc
                land_r, land_c = r + 2 * fwd_dr, c + 2 * dc

                # Capture check
                if (mid_r, mid_c) in opp_all and 0 <= land_r < 8 and 0 <= land_c < 8:
                    if (land_r, land_c) not in occupied:
                        captures.append(((r, c), (land_r, land_c), (mid_r, mid_c), False))

                # Quiet move check
                if 0 <= mid_r < 8 and 0 <= mid_c < 8 and (mid_r, mid_c) not in occupied:
                    quiet_moves.append(((r, c), (mid_r, mid_c), None, False))

        # 2. Check king captures & quiet moves
        for (r, c) in m_kings:
            for dr in (-1, 1):
                for dc in (-1, 1):
                    mid_r, mid_c = r + dr, c + dc
                    land_r, land_c = r + 2 * dr, c + 2 * dc

                    # Capture check
                    if (mid_r, mid_c) in opp_all and 0 <= land_r < 8 and 0 <= land_c < 8:
                        if (land_r, land_c) not in occupied:
                            captures.append(((r, c), (land_r, land_c), (mid_r, mid_c), True))

                    # Quiet move check
                    if 0 <= mid_r < 8 and 0 <= mid_c < 8 and (mid_r, mid_c) not in occupied:
                        quiet_moves.append(((r, c), (mid_r, mid_c), None, True))

        if captures:
            return captures, True
        return quiet_moves, False

    def apply_move(m_men, m_kings, o_men, o_kings, move, col):
        """
        Applies a move and returns new sets for: (next_my_men, next_my_kings, next_opp_men, next_opp_kings)
        From the perspective of the next player (so roles swap).
        """
        (fr, fc), (tr, tc), cap, is_king = move
        promo_row = 7 if col == 'w' else 0

        new_m_men = set(m_men)
        new_m_kings = set(m_kings)
        new_o_men = set(o_men)
        new_o_kings = set(o_kings)

        if is_king:
            new_m_kings.remove((fr, fc))
            new_m_kings.add((tr, tc))
        else:
            new_m_men.remove((fr, fc))
            if tr == promo_row:
                new_m_kings.add((tr, tc))
            else:
                new_m_men.add((tr, tc))

        if cap:
            new_o_men.discard(cap)
            new_o_kings.discard(cap)

        # Swapped perspective for next player
        return new_o_men, new_o_kings, new_m_men, new_m_kings

    # Evaluation weights
    def evaluate(m_men, m_kings, o_men, o_kings, col):
        if not m_men and not m_kings:
            return -100000
        if not o_men and not o_kings:
            return 100000

        score = 0
        score += 100 * (len(m_men) - len(o_men))
        score += 175 * (len(m_kings) - len(o_kings))

        # Positional bonuses for current player
        base_row = 0 if col == 'w' else 7
        for r, c in m_men:
            # Advancement bonus
            adv = r if col == 'w' else (7 - r)
            score += adv * 5
            # Center control bonus
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 4
            # Back row defense
            if r == base_row:
                score += 8

        # Subtract positional bonuses for opponent
        opp_base_row = 7 if col == 'w' else 0
        for r, c in o_men:
            adv = (7 - r) if col == 'w' else r
            score -= adv * 5
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 4
            if r == opp_base_row:
                score -= 8

        return score

    # Check root moves
    legal_moves, is_capture = get_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
    if not legal_moves:
        # Fallback to prevent disqualification (e.g. game already lost)
        all_my = list(my_men_set | my_kings_set)
        if all_my:
            return (all_my[0], all_my[0])
        return ((0, 0), (0, 0))

    if len(legal_moves) == 1:
        move = legal_moves[0]
        return (move[0], move[1])

    opp_color = 'b' if color == 'w' else 'w'

    def alpha_beta(m_men, m_kings, o_men, o_kings, depth, alpha, beta, col):
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        if depth == 0:
            return evaluate(m_men, m_kings, o_men, o_kings, col)

        moves, _ = get_moves(m_men, m_kings, o_men, o_kings, col)
        if not moves:
            # Player has no legal moves: lost
            return -100000 + (10 - depth)

        # Move ordering: captures first
        moves.sort(key=lambda m: (m[2] is not None), reverse=True)

        nxt_col = 'b' if col == 'w' else 'w'
        for m in moves:
            nm_men, nm_kings, no_men, no_kings = apply_move(m_men, m_kings, o_men, o_kings, m, col)
            val = -alpha_beta(nm_men, nm_kings, no_men, no_kings, depth - 1, -beta, -alpha, nxt_col)
            if val >= beta:
                return beta
            if val > alpha:
                alpha = val

        return alpha

    # Iterative deepening
    best_move = legal_moves[0]
    try:
        # Order root moves (captures prioritized)
        legal_moves.sort(key=lambda m: (m[2] is not None), reverse=True)

        for depth in range(1, 16):
            current_best_move = None
            current_best_score = -float('inf')
            alpha = -float('inf')
            beta = float('inf')

            for m in legal_moves:
                nm_men, nm_kings, no_men, no_kings = apply_move(
                    my_men_set, my_kings_set, opp_men_set, opp_kings_set, m, color
                )
                score = -alpha_beta(nm_men, nm_kings, no_men, no_kings, depth - 1, -beta, -alpha, opp_color)
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = m
                alpha = max(alpha, current_best_score)

            if current_best_move is not None:
                best_move = current_best_move

            # If forced win detected, stop early
            if current_best_score > 90000:
                break
    except TimeoutError:
        pass

    return (best_move[0], best_move[1])
