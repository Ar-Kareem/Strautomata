
import time

class TimeoutException(Exception):
    pass

def simulate_move(you: list[int], opp: list[int], move: int):
    y = list(you)
    o = list(opp)
    seeds = y[move]
    y[move] = 0
    pos = move
    
    for _ in range(seeds):
        pos = (pos + 1) % 13
        if pos < 6:
            y[pos] += 1
        elif pos == 6:
            y[6] += 1
        else:
            o[pos - 7] += 1

    extra_turn = False
    if pos == 6:
        extra_turn = True
    elif pos < 6 and y[pos] == 1 and o[5 - pos] > 0:
        captured = 1 + o[5 - pos]
        y[6] += captured
        y[pos] = 0
        o[5 - pos] = 0

    y_sum = sum(y[:6])
    o_sum = sum(o[:6])
    if y_sum == 0 or o_sum == 0:
        y[6] += y_sum
        o[6] += o_sum
        for i in range(6):
            y[i] = 0
            o[i] = 0
        return y, o, False, True

    return y, o, extra_turn, False

def evaluate(you: list[int], opp: list[int], total_seeds: int) -> int:
    y_store, o_store = you[6], opp[6]
    half = total_seeds // 2
    if y_store > half:
        return 15000 + (y_store - o_store)
    if o_store > half:
        return -15000 + (y_store - o_store)

    store_diff = y_store - o_store
    house_diff = sum(you[:6]) - sum(opp[:6])
    
    extra_moves_y = sum(1 for i in range(6) if you[i] == 6 - i)
    extra_moves_o = sum(1 for i in range(6) if opp[i] == 6 - i)
    
    return store_diff * 100 + house_diff * 10 + (extra_moves_y - extra_moves_o) * 25

def get_move_score(m: int, you: list[int], opp: list[int], tt_best: int) -> int:
    if m == tt_best:
        return 2000
    seeds = you[m]
    if seeds == 6 - m:
        return 1000 + seeds
    landing = (m + seeds) % 13
    if landing < 6 and opp[5 - landing] > 0:
        if (landing != m and you[landing] == 0) or (landing == m and seeds == 13):
            return 500 + opp[5 - landing]
    return seeds

def policy(you: list[int], opponent: list[int]) -> int:
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    start_time = time.perf_counter()
    time_limit = 0.82
    total_seeds = sum(you) + sum(opponent)
    
    tt = {}
    nodes = 0
    best_move = legal_moves[0]

    def negamax(y: list[int], o: list[int], depth: int, alpha: int, beta: int) -> int:
        nonlocal nodes
        nodes += 1
        if (nodes & 63) == 0 and (time.perf_counter() - start_time) > time_limit:
            raise TimeoutException()

        state_key = (tuple(y), tuple(o))
        tt_move = -1
        if state_key in tt:
            tt_depth, tt_score, tt_move, tt_flag = tt[state_key]
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        moves = [i for i in range(6) if y[i] > 0]
        if not moves:
            diff = y[6] - o[6]
            if diff > 0:
                return 20000 + diff
            elif diff < 0:
                return -20000 + diff
            return 0

        if depth <= 0:
            return evaluate(y, o, total_seeds)

        moves.sort(key=lambda m: get_move_score(m, y, o, tt_move), reverse=True)

        orig_alpha = alpha
        best_val = -100000
        best_local_move = moves[0]

        for m in moves:
            ny, no, extra_turn, terminal = simulate_move(y, o, m)
            if terminal:
                diff = ny[6] - no[6]
                if diff > 0:
                    val = 20000 + diff
                elif diff < 0:
                    val = -20000 + diff
                else:
                    val = 0
            elif extra_turn:
                val = negamax(ny, no, depth, alpha, beta)
            else:
                val = -negamax(no, ny, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_local_move = m

            alpha = max(alpha, val)
            if alpha >= beta:
                break

        if best_val <= orig_alpha:
            flag = 2
        elif best_val >= beta:
            flag = 1
        else:
            flag = 0
        tt[state_key] = (depth, best_val, best_local_move, flag)

        return best_val

    # Iterative deepening
    for depth in range(1, 35):
        if time.perf_counter() - start_time > time_limit:
            break
        try:
            moves = list(legal_moves)
            tt_best = tt.get((tuple(you), tuple(opponent)), (0, 0, best_move, 0))[2]
            moves.sort(key=lambda m: get_move_score(m, you, opponent, tt_best), reverse=True)

            current_best_move = moves[0]
            alpha = -100000
            beta = 100000

            for m in moves:
                ny, no, extra_turn, terminal = simulate_move(you, opponent, m)
                if terminal:
                    diff = ny[6] - no[6]
                    if diff > 0:
                        score = 20000 + diff
                    elif diff < 0:
                        score = -20000 + diff
                    else:
                        score = 0
                elif extra_turn:
                    score = negamax(ny, no, depth, alpha, beta)
                else:
                    score = -negamax(no, ny, depth - 1, -beta, -alpha)

                if score > alpha:
                    alpha = score
                    current_best_move = m

            best_move = current_best_move
            if alpha >= 15000:
                break
        except TimeoutException:
            break

    return best_move
