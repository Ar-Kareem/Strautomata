
import time

class TimeoutError(Exception):
    pass

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    TIME_LIMIT = 0.95  # seconds

    # Convert to a flat tuple of length 14:
    # [my_houses 0..5, my_store, opp_houses 0..5, opp_store]
    state = tuple(you[:6]) + (you[6],) + tuple(opponent[:6]) + (opponent[6],)

    # Quick exit if only one legal move
    legal = [i for i in range(6) if state[i] > 0]
    if len(legal) == 1:
        return legal[0]

    trans_table = {}

    def evaluate(st: tuple) -> int:
        # Heuristic: store difference
        return st[6] - st[13]

    def legal_moves(st: tuple) -> list:
        return [i for i in range(6) if st[i] > 0]

    def simulate_move(st: tuple, move: int):
        """Return (new_state, extra_turn) or (None, terminal_value) if game over."""
        my = list(st[0:6])
        my_store = st[6]
        opp = list(st[7:13])
        opp_store = st[13]

        seeds = my[move]
        my[move] = 0
        pos = move

        # Sow seeds
        while seeds:
            pos = (pos + 1) % 14
            if pos == 13:       # skip opponent's store
                continue
            if pos <= 5:
                my[pos] += 1
            elif pos == 6:
                my_store += 1
            else:  # 7..12
                opp[pos - 7] += 1
            seeds -= 1

        # Capture
        if 0 <= pos <= 5 and my[pos] == 1 and opp[5 - pos] > 0:
            my_store += 1 + opp[5 - pos]
            my[pos] = 0
            opp[5 - pos] = 0

        # Check game end
        if all(h == 0 for h in my):
            return None, my_store - (opp_store + sum(opp))
        if all(h == 0 for h in opp):
            return None, (my_store + sum(my)) - opp_store

        extra_turn = (pos == 6)
        if extra_turn:
            return tuple(my + [my_store] + opp + [opp_store]), True
        else:
            # Flip perspective
            return tuple(opp + [opp_store] + my + [my_store]), False

    def negamax(st: tuple, depth: int, alpha: float, beta: float) -> float:
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError()

        orig_alpha = alpha
        key = st

        # Transposition table lookup
        if key in trans_table:
            tt_val, tt_depth, tt_flag = trans_table[key]
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_val
                elif tt_flag == 1:
                    alpha = max(alpha, tt_val)
                elif tt_flag == 2:
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

        moves = legal_moves(st)
        if not moves:
            # Game over at start of turn (should not happen with correct simulation)
            return st[6] - (st[13] + sum(st[7:13]))

        if depth == 0:
            return evaluate(st)

        # Generate all children
        children = []
        for m in moves:
            new_st, extra = simulate_move(st, m)
            children.append((m, new_st, extra))

        # Move ordering: 1-ply static evaluation
        def priority(item):
            _, new_st, extra = item
            if new_st is None:
                return extra  # terminal value from current perspective
            elif extra:
                return evaluate(new_st)
            else:
                return -evaluate(new_st)

        children.sort(reverse=True, key=priority)

        best_val = -float('inf')
        for m, new_st, extra in children:
            if new_st is None:
                child_val = extra
            else:
                if extra:
                    child_val = negamax(new_st, depth - 1, alpha, beta)
                else:
                    child_val = -negamax(new_st, depth - 1, -beta, -alpha)

            if child_val > best_val:
                best_val = child_val
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break

        # Store in transposition table
        flag = 0
        if best_val <= orig_alpha:
            flag = 2
        elif best_val >= beta:
            flag = 1
        trans_table[key] = (best_val, depth, flag)
        return best_val

    best_move = legal[0]  # fallback

    try:
        for depth in range(1, 100):
            if time.time() - start_time > TIME_LIMIT:
                break

            moves = legal_moves(state)
            children = []
            for m in moves:
                new_st, extra = simulate_move(state, m)
                children.append((m, new_st, extra))

            def priority(item):
                _, new_st, extra = item
                if new_st is None:
                    return extra
                elif extra:
                    return evaluate(new_st)
                else:
                    return -evaluate(new_st)

            children.sort(reverse=True, key=priority)

            best_val = -float('inf')
            current_best = children[0][0]
            alpha = -float('inf')
            beta = float('inf')

            for m, new_st, extra in children:
                if new_st is None:
                    val = extra
                else:
                    if extra:
                        val = negamax(new_st, depth - 1, alpha, beta)
                    else:
                        val = -negamax(new_st, depth - 1, -beta, -alpha)

                if val > best_val:
                    best_val = val
                    current_best = m
                alpha = max(alpha, val)

                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError()

            best_move = current_best

    except TimeoutError:
        pass

    return best_move
