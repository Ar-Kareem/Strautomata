
import time

class TimeoutException(Exception):
    pass

# Global transposition table preserved across turns
TT = {}

def make_move(p0, p1, m):
    """
    Simulate move m (0 <= m <= 5) for player p0 against p1.
    Returns: (next_p0, next_p1, extra_turn, game_over)
    """
    p0 = list(p0)
    p1 = list(p1)
    seeds = p0[m]
    p0[m] = 0

    curr = m
    while seeds > 0:
        curr = (curr + 1) % 13
        if curr <= 5:
            p0[curr] += 1
        elif curr == 6:
            p0[6] += 1
        else:
            p1[curr - 7] += 1
        seeds -= 1

    extra_turn = False
    if curr == 6:
        extra_turn = True
    elif curr <= 5 and p0[curr] == 1 and p1[5 - curr] > 0:
        p0[6] += 1 + p1[5 - curr]
        p0[curr] = 0
        p1[5 - curr] = 0

    s0 = sum(p0[:6])
    s1 = sum(p1[:6])
    if s0 == 0 or s1 == 0:
        p0[6] += s0
        p1[6] += s1
        for i in range(6):
            p0[i] = 0
            p1[i] = 0
        return p0, p1, False, True

    return p0, p1, extra_turn, False

def evaluate(p0, p1):
    """Heuristic evaluation from p0's perspective."""
    store_diff = p0[6] - p1[6]
    pits_diff = sum(p0[:6]) - sum(p1[:6])

    extra_turns_p0 = 0
    captures_p0 = 0
    for i in range(6):
        if p0[i] == 6 - i:
            extra_turns_p0 += 1
        if p0[i] == 0 and p1[5 - i] > 0:
            for j in range(i):
                if p0[j] == i - j:
                    captures_p0 += p1[5 - i] + 1
                    break

    extra_turns_p1 = 0
    for i in range(6):
        if p1[i] == 6 - i:
            extra_turns_p1 += 1

    return store_diff * 100 + pits_diff * 10 + extra_turns_p0 * 15 - extra_turns_p1 * 15 + captures_p0 * 5

def order_moves(p0, p1, legal_moves, tt_move):
    def score_move(m):
        if m == tt_move:
            return 10000
        score = 0
        seeds = p0[m]
        if seeds == 6 - m:
            score += 500
        # Capture estimation
        last_pit = (m + seeds) % 13
        if last_pit <= 5:
            if (p0[last_pit] == 0 or (last_pit == m and seeds == 13)) and p1[5 - last_pit] > 0:
                score += 300 + p1[5 - last_pit]
        score += seeds
        return score

    return sorted(legal_moves, key=score_move, reverse=True)

nodes_count = 0

def negamax(p0, p1, depth, alpha, beta, deadline):
    global nodes_count
    nodes_count += 1
    if (nodes_count & 511) == 0:
        if time.perf_counter() >= deadline:
            raise TimeoutException()

    state_key = (tuple(p0), tuple(p1))
    tt_entry = TT.get(state_key)
    tt_move = None
    if tt_entry is not None:
        tt_depth, tt_flag, tt_val, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == 0:  # EXACT
                return tt_val
            elif tt_flag == 1:  # LOWERBOUND
                alpha = max(alpha, tt_val)
            elif tt_flag == 2:  # UPPERBOUND
                beta = min(beta, tt_val)
            if alpha >= beta:
                return tt_val

    if depth <= 0:
        return evaluate(p0, p1)

    legal_moves = [i for i in range(6) if p0[i] > 0]
    if not legal_moves:
        return evaluate(p0, p1)

    ordered_moves = order_moves(p0, p1, legal_moves, tt_move)

    orig_alpha = alpha
    best_val = -float('inf')
    best_m = ordered_moves[0]

    for m in ordered_moves:
        next_p0, next_p1, extra_turn, game_over = make_move(p0, p1, m)
        if game_over:
            diff = next_p0[6] - next_p1[6]
            if diff > 0:
                val = 100000 + diff * 100 + depth
            elif diff < 0:
                val = -100000 + diff * 100 - depth
            else:
                val = 0
        elif extra_turn:
            val = negamax(next_p0, next_p1, depth - 1, alpha, beta, deadline)
        else:
            val = -negamax(next_p1, next_p0, depth - 1, -beta, -alpha, deadline)

        if val > best_val:
            best_val = val
            best_m = m
        alpha = max(alpha, val)
        if alpha >= beta:
            break

    if best_val <= orig_alpha:
        flag = 2  # UPPERBOUND
    elif best_val >= beta:
        flag = 1  # LOWERBOUND
    else:
        flag = 0  # EXACT

    if len(TT) < 500000:
        TT[state_key] = (depth, flag, best_val, best_m)

    return best_val

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.perf_counter()
    deadline = start_time + 0.85

    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    best_move = legal_moves[0]
    state_key = (tuple(you), tuple(opponent))
    tt_entry = TT.get(state_key)
    tt_move = tt_entry[3] if tt_entry is not None else None

    # Iterative deepening
    try:
        for depth in range(1, 40):
            ordered = order_moves(you, opponent, legal_moves, tt_move)
            cur_best_move = ordered[0]
            cur_best_val = -float('inf')
            alpha = -float('inf')
            beta = float('inf')

            for m in ordered:
                next_p0, next_p1, extra_turn, game_over = make_move(you, opponent, m)
                if game_over:
                    diff = next_p0[6] - next_p1[6]
                    if diff > 0:
                        val = 100000 + diff * 100 + depth
                    elif diff < 0:
                        val = -100000 + diff * 100 - depth
                    else:
                        val = 0
                elif extra_turn:
                    val = negamax(next_p0, next_p1, depth - 1, alpha, beta, deadline)
                else:
                    val = -negamax(next_p1, next_p0, depth - 1, -beta, -alpha, deadline)

                if val > cur_best_val:
                    cur_best_val = val
                    cur_best_move = m
                alpha = max(alpha, val)

            best_move = cur_best_move
            tt_move = best_move

            # If a decisive win or loss is found, stop searching deeper
            if abs(cur_best_val) >= 90000:
                break
    except TimeoutException:
        pass

    return best_move
