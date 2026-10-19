
import time
import numpy as np

# Direction definitions: (dr, dc, char_code, bit_shift)
# Bit layout: index = r * 6 + c
MOVES_CONFIG = [
    (-1, 0, 'U', -6),
    (1, 0, 'D', 6),
    (0, -1, 'L', -1),
    (0, 1, 'R', 1),
]

def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.time()
    time_limit = 0.85  # Conservative budget under 1.0s

    # Standardize input to 5x6 boolean arrays regardless of input dimension / container
    y_arr = np.array(you, dtype=bool).reshape((5, 6))
    o_arr = np.array(opponent, dtype=bool).reshape((5, 6))

    # Convert to 30-bit integers
    you_bits = 0
    opp_bits = 0
    for r in range(5):
        for c in range(6):
            idx = r * 6 + c
            if y_arr[r, c]:
                you_bits |= (1 << idx)
            if o_arr[r, c]:
                opp_bits |= (1 << idx)

    # Move generation helper
    def get_moves(p_bits, o_bits):
        moves = []
        for r in range(5):
            for c in range(6):
                src = r * 6 + c
                if not (p_bits & (1 << src)):
                    continue
                # Try all 4 directions
                if r > 0 and (o_bits & (1 << (src - 6))):
                    moves.append((r, c, 'U', src, src - 6))
                if r < 4 and (o_bits & (1 << (src + 6))):
                    moves.append((r, c, 'D', src, src + 6))
                if c > 0 and (o_bits & (1 << (src - 1))):
                    moves.append((r, c, 'L', src, src - 1))
                if c < 5 and (o_bits & (1 << (src + 1))):
                    moves.append((r, c, 'R', src, src + 1))
        return moves

    initial_moves = get_moves(you_bits, opp_bits)
    if not initial_moves:
        return "0,0,U"  # No moves available; return fallback
    if len(initial_moves) == 1:
        m = initial_moves[0]
        return f"{m[0]},{m[1]},{m[2]}"

    # Heuristic evaluation for non-terminal states
    def evaluate(p_bits, o_bits):
        my_m = get_moves(p_bits, o_bits)
        op_m = get_moves(o_bits, p_bits)

        len_my = len(my_m)
        len_op = len(op_m)

        if len_my == 0:
            return -20000
        if len_op == 0:
            return 20000

        # Mobility difference is paramount in Clobber
        score = (len_my - len_op) * 120

        # Material count difference
        my_count = bin(p_bits).count('1')
        op_count = bin(o_bits).count('1')
        score += (my_count - op_count) * 15

        return score

    # Transposition table: key -> (depth, flag, value, best_move)
    # flag: 0: EXACT, 1: LOWERBOUND, 2: UPPERBOUND
    tt = {}

    best_overall_move = initial_moves[0]

    def alphabeta(p_bits, o_bits, depth, alpha, beta, is_max):
        nonlocal best_overall_move
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        moves = get_moves(p_bits, o_bits) if is_max else get_moves(o_bits, p_bits)
        if not moves:
            # Current player cannot move -> loss
            return -25000 - depth if is_max else 25000 + depth

        if depth == 0:
            val = evaluate(p_bits, o_bits)
            return val if is_max else -val

        state_key = (p_bits, o_bits, is_max)
        tt_entry = tt.get(state_key)
        if tt_entry and tt_entry[0] >= depth:
            tdepth, tflag, tval, _ = tt_entry
            if tflag == 0:
                return tval
            elif tflag == 1:
                alpha = max(alpha, tval)
            elif tflag == 2:
                beta = min(beta, tval)
            if alpha >= beta:
                return tval

        # Move ordering: prioritize moves that reduce opponent responses
        def move_priority(m):
            # Apply move: p_bits loses m[3], gains m[4]; o_bits loses m[4]
            if is_max:
                n_p = (p_bits ^ (1 << m[3])) | (1 << m[4])
                n_o = o_bits ^ (1 << m[4])
                return -len(get_moves(n_o, n_p))
            else:
                n_o = (o_bits ^ (1 << m[3])) | (1 << m[4])
                n_p = p_bits ^ (1 << m[4])
                return -len(get_moves(n_p, n_o))

        moves.sort(key=move_priority, reverse=True)

        best_m = moves[0]
        if is_max:
            val = -100000
            for m in moves:
                n_p = (p_bits ^ (1 << m[3])) | (1 << m[4])
                n_o = o_bits ^ (1 << m[4])
                res = alphabeta(n_p, n_o, depth - 1, alpha, beta, False)
                if res > val:
                    val = res
                    best_m = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
        else:
            val = 100000
            for m in moves:
                n_o = (o_bits ^ (1 << m[3])) | (1 << m[4])
                n_p = p_bits ^ (1 << m[4])
                res = alphabeta(n_p, n_o, depth - 1, alpha, beta, True)
                if res < val:
                    val = res
                    best_m = m
                beta = min(beta, val)
                if alpha >= beta:
                    break

        flag = 0
        if val <= alpha:
            flag = 2
        elif val >= beta:
            flag = 1
        tt[state_key] = (depth, flag, val, best_m)
        return val

    # Iterative deepening search
    max_search_depth = 12
    try:
        for depth in range(1, max_search_depth + 1):
            cur_best = None
            cur_best_val = -100000
            alpha = -100000
            beta = 100000

            # Sort root moves using previous TT or heuristics
            for m in initial_moves:
                n_p = (you_bits ^ (1 << m[3])) | (1 << m[4])
                n_o = opp_bits ^ (1 << m[4])
                val = alphabeta(n_p, n_o, depth - 1, alpha, beta, False)
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best = m
                alpha = max(alpha, cur_best_val)

            if cur_best:
                best_overall_move = cur_best

            # If a guaranteed win is found, no need to search deeper
            if cur_best_val > 20000:
                break
    except TimeoutError:
        pass

    m = best_overall_move
    return f"{m[0]},{m[1]},{m[2]}"
