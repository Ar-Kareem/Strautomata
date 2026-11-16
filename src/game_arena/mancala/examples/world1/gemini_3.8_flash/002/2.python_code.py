
import time

def apply_move(p1: tuple, p2: tuple, move: int):
    """
    Applies move for p1 against p2.
    p1: tuple of 7 ints (0..5 houses, 6 store)
    p2: tuple of 7 ints (0..5 houses, 6 store)
    Returns: (new_p1, new_p2, extra_turn, game_over)
    """
    # 13-pit circular track: pits 0..5 (p1 houses), 6 (p1 store), 7..12 (p2 houses)
    board = [p1[0], p1[1], p1[2], p1[3], p1[4], p1[5], p1[6],
             p2[0], p2[1], p2[2], p2[3], p2[4], p2[5]]
    seeds = board[move]
    board[move] = 0

    full_laps, rem = divmod(seeds, 13)
    if full_laps:
        for i in range(13):
            board[i] += full_laps
    for i in range(1, rem + 1):
        board[(move + i) % 13] += 1

    last_pos = (move + seeds) % 13
    extra_turn = (last_pos == 6)

    # Capture check: landed in p1's house, which was empty before this drop, and opp opposite pit has seeds
    if last_pos < 6 and board[last_pos] == 1:
        opp_pit = 12 - last_pos
        if board[opp_pit] > 0:
            board[6] += 1 + board[opp_pit]
            board[last_pos] = 0
            board[opp_pit] = 0

    p1_store = board[6]
    p2_store = p2[6]

    # Check game over
    p1_seeds = sum(board[0:6])
    p2_seeds = sum(board[7:13])
    if p1_seeds == 0 or p2_seeds == 0:
        p1_store += p1_seeds
        p2_store += p2_seeds
        return ((0, 0, 0, 0, 0, 0, p1_store),
                (0, 0, 0, 0, 0, 0, p2_store),
                False, True)

    new_p1 = (board[0], board[1], board[2], board[3], board[4], board[5], p1_store)
    new_p2 = (board[7], board[8], board[9], board[10], board[11], board[12], p2_store)
    return new_p1, new_p2, extra_turn, False

def evaluate(p1: tuple, p2: tuple) -> int:
    # Evaluation from perspective of p1
    store_diff = p1[6] - p2[6]
    side_seeds_diff = sum(p1[:6]) - sum(p2[:6])
    return store_diff * 100 + side_seeds_diff * 8

def order_moves(p1: tuple, p2: tuple, tt_move: int = -1):
    legal_moves = [i for i in range(6) if p1[i] > 0]
    
    def score_move(m):
        if m == tt_move:
            return 10000
        seeds = p1[m]
        # Extra turn move
        if (m + seeds) % 13 == 6:
            return 5000 + m
        # Capture potential
        last_pos = (m + seeds) % 13
        if last_pos < 6:
            # Empty before drop or will receive exact 1 seed
            curr = p1[last_pos] if last_pos != m else 0
            if (curr == 0 and seeds < 13) or (curr + seeds // 13 == 0):
                opp_pit = 5 - last_pos
                if p2[opp_pit] > 0:
                    return 2000 + p2[opp_pit]
        return m

    legal_moves.sort(key=score_move, reverse=True)
    return legal_moves


def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.82  # Target completion within ~0.82s

    p1_state = tuple(you)
    p2_state = tuple(opponent)
    
    legal_moves = [i for i in range(6) if p1_state[i] > 0]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    tt = {}  # state -> (depth, score, flag, best_move)
    FLAG_EXACT = 0
    FLAG_LOWER = 1
    FLAG_UPPER = 2

    best_move_overall = legal_moves[0]
    nodes_visited = 0

    def alphabeta(p1, p2, depth, alpha, beta, is_p1):
        nonlocal nodes_visited
        nodes_visited += 1

        if (nodes_visited & 511) == 0:
            if time.time() - start_time > time_limit:
                raise TimeoutError

        state_key = (p1, p2, is_p1)
        tt_entry = tt.get(state_key)
        tt_move = -1

        if tt_entry is not None:
            entry_depth, entry_score, entry_flag, entry_best_move = tt_entry
            tt_move = entry_best_move
            if entry_depth >= depth:
                if entry_flag == FLAG_EXACT:
                    return entry_score, tt_move
                elif entry_flag == FLAG_LOWER and entry_score > alpha:
                    alpha = entry_score
                elif entry_flag == FLAG_UPPER and entry_score < beta:
                    beta = entry_score
                if alpha >= beta:
                    return entry_score, tt_move

        if depth <= 0:
            val = evaluate(p1, p2) if is_p1 else evaluate(p2, p1)
            return (val if is_p1 else -val), -1

        curr_p = p1 if is_p1 else p2
        opp_p = p2 if is_p1 else p1
        moves = order_moves(curr_p, opp_p, tt_move)

        if not moves:
            # No legal moves, evaluate
            val = evaluate(p1, p2)
            return val, -1

        orig_alpha = alpha
        best_local_move = moves[0]

        if is_p1:
            max_eval = -1000000
            for m in moves:
                np1, np2, extra, over = apply_move(p1, p2, m)
                if over:
                    score = evaluate(np1, np2)
                elif extra:
                    score, _ = alphabeta(np1, np2, depth - 1, alpha, beta, True)
                else:
                    score, _ = alphabeta(np1, np2, depth - 1, alpha, beta, False)

                if score > max_eval:
                    max_eval = score
                    best_local_move = m
                alpha = max(alpha, max_eval)
                if alpha >= beta:
                    break

            flag = FLAG_EXACT
            if max_eval <= orig_alpha:
                flag = FLAG_UPPER
            elif max_eval >= beta:
                flag = FLAG_LOWER
            tt[state_key] = (depth, max_eval, flag, best_local_move)
            return max_eval, best_local_move
        else:
            min_eval = 1000000
            for m in moves:
                np2, np1, extra, over = apply_move(p2, p1, m)
                if over:
                    score = evaluate(np1, np2)
                elif extra:
                    score, _ = alphabeta(np1, np2, depth - 1, alpha, beta, False)
                else:
                    score, _ = alphabeta(np1, np2, depth - 1, alpha, beta, True)

                if score < min_eval:
                    min_eval = score
                    best_local_move = m
                beta = min(beta, min_eval)
                if alpha >= beta:
                    break

            flag = FLAG_EXACT
            if min_eval <= orig_alpha:
                flag = FLAG_UPPER
            elif min_eval >= beta:
                flag = FLAG_LOWER
            tt[state_key] = (depth, min_eval, flag, best_local_move)
            return min_eval, best_local_move

    # Iterative deepening
    for depth in range(1, 40):
        try:
            score, move = alphabeta(p1_state, p2_state, depth, -1000000, 1000000, True)
            if move in legal_moves:
                best_move_overall = move
        except TimeoutError:
            break

        if time.time() - start_time > time_limit:
            break

    return best_move_overall
