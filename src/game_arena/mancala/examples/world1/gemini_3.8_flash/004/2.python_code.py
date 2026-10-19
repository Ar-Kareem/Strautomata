
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.88  # Safe margin within 1.0 second limit

    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Initial state representation: 14 elements
    # [you_0..5, you_store, opp_0..5, opp_store]
    initial_state = tuple(you + opponent)

    tt = {}

    def apply_move(state: tuple, move: int):
        b = list(state)
        seeds = b[move]
        b[move] = 0

        pos = move
        while seeds > 1:
            pos = (pos + 1) % 13
            b[pos] += 1
            seeds -= 1

        # Final seed
        pos = (pos + 1) % 13
        # Check capture
        if pos <= 5 and b[pos] == 0 and b[12 - pos] > 0:
            captured = 1 + b[12 - pos]
            b[12 - pos] = 0
            b[6] += captured
        else:
            b[pos] += 1

        extra_turn = (pos == 6)

        # Check terminal condition
        sum_you = sum(b[0:6])
        sum_opp = sum(b[7:13])

        if sum_you == 0 or sum_opp == 0:
            if sum_you == 0 and sum_opp > 0:
                b[13] += sum_opp
                for i in range(7, 13):
                    b[i] = 0
            elif sum_opp == 0 and sum_you > 0:
                b[6] += sum_you
                for i in range(6):
                    b[i] = 0
            return tuple(b), False, True

        if extra_turn:
            return tuple(b), True, False
        else:
            # Switch sides: player to move is always indices 0..6
            swapped = (
                b[7], b[8], b[9], b[10], b[11], b[12], b[13],
                b[0], b[1], b[2], b[3], b[4], b[5], b[6]
            )
            return swapped, False, False

    def evaluate(state: tuple, is_terminal: bool) -> int:
        if is_terminal:
            diff = state[6] - state[13]
            if diff > 0:
                return 10000 + diff * 100
            elif diff < 0:
                return -10000 + diff * 100
            return 0

        score = (state[6] - state[13]) * 100
        score += (sum(state[0:6]) - sum(state[7:13])) * 10

        # Heuristic bonuses
        for i in range(6):
            # Extra turn potential
            if state[i] > 0 and (state[i] % 13 == 6 - i):
                score += 18
            # Capture threats
            if state[i] == 0 and state[12 - i] > 0:
                score += state[12 - i] * 4

        return score

    def order_moves(state: tuple, moves: list[int], tt_move: int | None) -> list[int]:
        def move_priority(m: int) -> int:
            if m == tt_move:
                return 1000
            p = 0
            seeds = state[m]
            if seeds % 13 == 6 - m:
                p += 200
            # Sowing lands on empty pit on our side
            last_pit = (m + seeds) % 13
            if last_pit <= 5 and (state[last_pit] == 0 or last_pit == m):
                if state[12 - last_pit] > 0:
                    p += 100 + state[12 - last_pit] * 2
            return p + seeds

        return sorted(moves, key=move_priority, reverse=True)

    def negamax(state: tuple, depth: int, alpha: int, beta: int) -> int:
        if time.time() - start_time > time_limit:
            raise TimeoutError

        tt_entry = tt.get(state)
        tt_move = None
        if tt_entry is not None:
            entry_depth, entry_flag, entry_val, entry_move = tt_entry
            tt_move = entry_move
            if entry_depth >= depth:
                if entry_flag == 0:  # EXACT
                    return entry_val
                elif entry_flag == 1:  # LOWERBOUND
                    alpha = max(alpha, entry_val)
                elif entry_flag == 2:  # UPPERBOUND
                    beta = min(beta, entry_val)
                if alpha >= beta:
                    return entry_val

        moves = [i for i in range(6) if state[i] > 0]
        if not moves:
            return evaluate(state, True)

        if depth == 0:
            return evaluate(state, False)

        ordered = order_moves(state, moves, tt_move)
        best_val = -1000000
        best_move = ordered[0]
        orig_alpha = alpha

        for m in ordered:
            next_state, extra_turn, is_term = apply_move(state, m)
            if is_term:
                val = evaluate(next_state, True)
            elif extra_turn:
                val = negamax(next_state, depth, alpha, beta)
            else:
                val = -negamax(next_state, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_move = m

            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # Save to transposition table
        flag = 0
        if best_val <= orig_alpha:
            flag = 2  # UPPERBOUND
        elif best_val >= beta:
            flag = 1  # LOWERBOUND

        tt[state] = (depth, flag, best_val, best_move)
        return best_val

    best_action = legal_moves[0]
    depth = 1

    try:
        while True:
            current_best_action = None
            current_best_val = -1000000
            alpha = -1000000
            beta = 1000000

            tt_entry = tt.get(initial_state)
            tt_move = tt_entry[3] if tt_entry else None
            ordered = order_moves(initial_state, legal_moves, tt_move)

            for m in ordered:
                next_state, extra_turn, is_term = apply_move(initial_state, m)
                if is_term:
                    val = evaluate(next_state, True)
                elif extra_turn:
                    val = negamax(next_state, depth, alpha, beta)
                else:
                    val = -negamax(next_state, depth - 1, -beta, -alpha)

                if val > current_best_val:
                    current_best_val = val
                    current_best_action = m

                alpha = max(alpha, val)

            if current_best_action is not None:
                best_action = current_best_action

            if current_best_val >= 9000 or current_best_val <= -9000:
                break

            depth += 1
            if depth > 30:
                break
    except TimeoutError:
        pass

    return best_action
