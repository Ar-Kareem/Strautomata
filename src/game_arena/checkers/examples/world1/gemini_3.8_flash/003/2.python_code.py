
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.75  # Safe margin under 1.0 second

    # Represent the board as a 64-element list
    # 0: Empty
    # 1: My Man, 2: My King
    # -1: Opp Man, -2: Opp King
    board = [0] * 64

    for r, c in my_men:
        board[r * 8 + c] = 1
    for r, c in my_kings:
        board[r * 8 + c] = 2
    for r, c in opp_men:
        board[r * 8 + c] = -1
    for r, c in opp_kings:
        board[r * 8 + c] = -2

    # Forward row directions
    # 'w' moves to higher row (+1), 'b' moves to lower row (-1)
    my_fwd = 1 if color == 'w' else -1
    opp_fwd = -my_fwd

    def get_legal_moves(b, is_my_turn):
        captures = []
        regular_moves = []

        fwd = my_fwd if is_my_turn else opp_fwd
        man_val = 1 if is_my_turn else -1
        king_val = 2 if is_my_turn else -2

        for idx in range(64):
            val = b[idx]
            if val != man_val and val != king_val:
                continue

            r = idx >> 3
            c = idx & 7

            if val == man_val:
                directions = [(fwd, -1), (fwd, 1)]
            else:
                directions = [(1, -1), (1, 1), (-1, -1), (-1, 1)]

            for dr, dc in directions:
                # Check jump
                jr, jc = r + 2 * dr, c + 2 * dc
                if 0 <= jr < 8 and 0 <= jc < 8:
                    mid_r, mid_c = r + dr, c + dc
                    mid_val = b[mid_r * 8 + mid_c]
                    # Opponent piece in the middle and empty destination
                    if is_my_turn:
                        is_opp = mid_val in (-1, -2)
                    else:
                        is_opp = mid_val in (1, 2)

                    if is_opp and b[jr * 8 + jc] == 0:
                        captures.append(((r, c), (jr, jc), (mid_r, mid_c)))

                # Check step (only if no captures found yet, to save work)
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and b[nr * 8 + nc] == 0:
                    regular_moves.append(((r, c), (nr, nc), None))

        if captures:
            return captures, True
        return regular_moves, False

    def apply_move(b, move, is_my_turn):
        nb = list(b)
        (r1, c1), (r2, c2), mid = move
        from_idx = r1 * 8 + c1
        to_idx = r2 * 8 + c2
        piece = nb[from_idx]
        nb[from_idx] = 0

        if mid is not None:
            mr, mc = mid
            nb[mr * 8 + mc] = 0

        # Promotion check
        if is_my_turn and piece == 1:
            crown_row = 7 if my_fwd == 1 else 0
            if r2 == crown_row:
                piece = 2
        elif not is_my_turn and piece == -1:
            crown_row = 7 if opp_fwd == 1 else 0
            if r2 == crown_row:
                piece = -2

        nb[to_idx] = piece
        return nb

    # Positional evaluation table for central control and advancement
    def evaluate(b):
        score = 0
        my_crown_row = 7 if my_fwd == 1 else 0
        my_home_row = 0 if my_fwd == 1 else 7
        opp_home_row = my_crown_row

        for idx in range(64):
            val = b[idx]
            if val == 0:
                continue

            r = idx >> 3
            c = idx & 7

            # Central bonus
            center_bonus = 0
            if 2 <= r <= 5 and 2 <= c <= 5:
                center_bonus = 6
                if 3 <= r <= 4 and 3 <= c <= 4:
                    center_bonus = 12

            if val == 1:  # My Man
                advancement = (r if my_fwd == 1 else (7 - r)) * 5
                home_def = 10 if r == my_home_row else 0
                score += 100 + advancement + center_bonus + home_def
            elif val == 2:  # My King
                score += 175 + center_bonus * 2
            elif val == -1:  # Opp Man
                advancement = (r if opp_fwd == 1 else (7 - r)) * 5
                home_def = 10 if r == opp_home_row else 0
                score -= 100 + advancement + center_bonus + home_def
            elif val == -2:  # Opp King
                score -= 175 + center_bonus * 2

        return score

    def alphabeta(b, depth, alpha, beta, is_my_turn):
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        moves, _ = get_legal_moves(b, is_my_turn)
        if not moves:
            # No moves: losing condition
            return -10000 if is_my_turn else 10000

        if depth == 0:
            return evaluate(b)

        if is_my_turn:
            val = -1000000
            for m in moves:
                nb = apply_move(b, m, True)
                score = alphabeta(nb, depth - 1, alpha, beta, False)
                val = max(val, score)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return val
        else:
            val = 1000000
            for m in moves:
                nb = apply_move(b, m, False)
                score = alphabeta(nb, depth - 1, alpha, beta, True)
                val = min(val, score)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return val

    # Primary move retrieval
    root_moves, _ = get_legal_moves(board, True)
    if not root_moves:
        # Fallback dummy move
        if my_men:
            return (my_men[0], my_men[0])
        elif my_kings:
            return (my_kings[0], my_kings[0])
        return ((0, 0), (0, 0))

    best_move = (root_moves[0][0], root_moves[0][1])

    # Iterative deepening
    for depth in range(1, 12):
        current_best_val = -1000000
        best_move_at_depth = None
        try:
            for m in root_moves:
                nb = apply_move(board, m, True)
                score = alphabeta(nb, depth - 1, current_best_val, 1000000, False)
                if score > current_best_val:
                    current_best_val = score
                    best_move_at_depth = (m[0], m[1])

                if time.time() - start_time > time_limit:
                    break

            if best_move_at_depth is not None:
                best_move = best_move_at_depth

            if time.time() - start_time > time_limit:
                break
        except TimeoutError:
            break

    return best_move
