
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.85

    # Check legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Transposition table: state -> (depth, flag, score, best_move)
    # flag: 0: EXACT, 1: LOWERBOUND, 2: UPPERBOUND
    tt = {}

    def simulate_move(y, o, pit):
        # 13 pits: 0..5 (y houses), 6 (y store), 7..12 (o houses)
        p = [y[0], y[1], y[2], y[3], y[4], y[5], y[6], o[0], o[1], o[2], o[3], o[4], o[5]]
        seeds = p[pit]
        p[pit] = 0
        idx = pit
        while seeds > 0:
            idx = (idx + 1) % 13
            p[idx] += 1
            seeds -= 1

        extra_turn = (idx == 6)
        os = o[6]

        # Capture check
        if 0 <= idx <= 5 and p[idx] == 1:
            opp_idx = 12 - idx
            if p[opp_idx] > 0:
                p[6] += 1 + p[opp_idx]
                p[idx] = 0
                p[opp_idx] = 0

        # Check game over
        sum_y = p[0] + p[1] + p[2] + p[3] + p[4] + p[5]
        sum_o = p[7] + p[8] + p[9] + p[10] + p[11] + p[12]

        if sum_y == 0 or sum_o == 0:
            p[6] += sum_y
            os += sum_o
            for k in range(6):
                p[k] = 0
                p[7 + k] = 0
            # Terminal state
            if extra_turn:
                next_y = (0, 0, 0, 0, 0, 0, p[6])
                next_o = (0, 0, 0, 0, 0, 0, os)
                return next_y, next_o, True, True
            else:
                # Board flipped from opponent's view
                next_y = (0, 0, 0, 0, 0, 0, os)
                next_o = (0, 0, 0, 0, 0, 0, p[6])
                return next_y, next_o, False, True

        if extra_turn:
            next_y = (p[0], p[1], p[2], p[3], p[4], p[5], p[6])
            next_o = (p[7], p[8], p[9], p[10], p[11], p[12], os)
            return next_y, next_o, True, False
        else:
            # Flip perspective
            next_y = (p[7], p[8], p[9], p[10], p[11], p[12], os)
            next_o = (p[0], p[1], p[2], p[3], p[4], p[5], p[6])
            return next_y, next_o, False, False

    def evaluate(y, o):
        diff_store = y[6] - o[6]
        diff_seeds = sum(y[:6]) - sum(o[:6])
        bonus = 0
        for i in range(6):
            if y[i] == 6 - i:
                bonus += 2  # potential extra turn
            if o[i] == 6 - i:
                bonus -= 2
        return diff_store * 100 + diff_seeds * 10 + bonus

    def order_moves(y, o, moves, tt_move):
        def move_score(m):
            if m == tt_move:
                return 10000
            score = 0
            if y[m] == 6 - m:
                score += 500  # Extra turn is very strong
            dest = (m + y[m]) % 13
            if dest <= 5:
                # Land in own pit
                if y[dest] == 0 and o[5 - dest] > 0:
                    score += 200 + o[5 - dest] * 10  # Capture
            score += y[m]
            return score

        return sorted(moves, key=move_score, reverse=True)

    class TimeoutException(Exception):
        pass

    def negamax(y, o, depth, alpha, beta):
        if time.time() - start_time > time_limit:
            raise TimeoutException()

        state_key = (y, o)
        tt_entry = tt.get(state_key)
        tt_move = None
        if tt_entry is not None:
            tt_depth, tt_flag, tt_score, tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score, tt_move
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score, tt_move

        moves = [i for i in range(6) if y[i] > 0]
        if not moves:
            # No moves: game over
            return (y[6] - o[6]) * 10000, None

        if depth <= 0:
            return evaluate(y, o), None

        ordered_moves = order_moves(y, o, moves, tt_move)
        best_score = -float('inf')
        best_move = ordered_moves[0]
        orig_alpha = alpha

        for m in ordered_moves:
            next_y, next_o, extra_turn, terminal = simulate_move(y, o, m)
            if terminal:
                score = (next_y[6] - next_o[6]) * 10000
                if not extra_turn:
                    score = -score
            elif extra_turn:
                # Same player continues, do not negate
                score, _ = negamax(next_y, next_o, depth, alpha, beta)
            else:
                score_child, _ = negamax(next_y, next_o, depth - 1, -beta, -alpha)
                score = -score_child

            if score > best_score:
                best_score = score
                best_move = m
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        if best_score <= orig_alpha:
            flag = 2  # UPPERBOUND
        elif best_score >= beta:
            flag = 1  # LOWERBOUND
        else:
            flag = 0  # EXACT
        tt[state_key] = (depth, flag, best_score, best_move)

        return best_score, best_move

    init_y = tuple(you)
    init_o = tuple(opponent)
    best_move = legal_moves[0]

    # Iterative deepening
    for depth in range(1, 30):
        try:
            _, m = negamax(init_y, init_o, depth, -float('inf'), float('inf'))
            if m is not None:
                best_move = m
        except TimeoutException:
            break

    return best_move
