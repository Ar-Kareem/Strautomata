
import time

TIMEOUT = object()

def make_move(my_houses, my_store, opp_houses, opp_store, move):
    """Return (my_houses, my_store, opp_houses, opp_store, extra_turn) after move."""
    seeds = my_houses[move]
    my_houses = list(my_houses)
    opp_houses = list(opp_houses)
    my_houses[move] = 0

    pos = move + 1
    while seeds > 0:
        if pos <= 5:
            my_houses[pos] += 1
        elif pos == 6:
            my_store += 1
        elif pos <= 12:
            opp_houses[pos - 7] += 1
        elif pos == 13:
            pos = 0
            continue
        seeds -= 1
        pos += 1
        if pos == 14:
            pos = 0

    last_pos = (pos - 1) % 14
    extra = (last_pos == 6)

    if not extra and 0 <= last_pos <= 5:
        if my_houses[last_pos] == 1 and opp_houses[5 - last_pos] > 0:
            my_store += my_houses[last_pos] + opp_houses[5 - last_pos]
            my_houses[last_pos] = 0
            opp_houses[5 - last_pos] = 0

    return my_houses, my_store, opp_houses, opp_store, extra


def evaluate(my_h, my_s, opp_h, opp_s):
    """Heuristic: final score difference if game ended now."""
    return (my_s + sum(my_h)) - (opp_s + sum(opp_h))


def alphabeta(my_h, my_s, opp_h, opp_s, depth, alpha, beta, maximizing, start_time, limit):
    if time.time() - start_time > limit:
        return TIMEOUT, None

    if sum(my_h) == 0 or sum(opp_h) == 0:
        return evaluate(my_h, my_s, opp_h, opp_s), None

    if depth == 0:
        return evaluate(my_h, my_s, opp_h, opp_s), None

    if maximizing:
        moves = [i for i in range(6) if my_h[i] > 0]
        if not moves:
            return evaluate(my_h, my_s, opp_h, opp_s), None

        # Generate children with ordering info
        children = []
        for move in moves:
            n_my_h, n_my_s, n_opp_h, n_opp_s, extra = make_move(my_h, my_s, opp_h, opp_s, move)
            score = evaluate(n_my_h, n_my_s, n_opp_h, n_opp_s)
            children.append((move, n_my_h, n_my_s, n_opp_h, n_opp_s, extra, score))

        # Prefer extra-turn moves, then higher scores
        children.sort(key=lambda c: (c[5], c[6]), reverse=True)

        best_val = -float('inf')
        best_move = children[0][0]
        for move, n_my_h, n_my_s, n_opp_h, n_opp_s, extra, _ in children:
            if sum(n_my_h) == 0 or sum(n_opp_h) == 0:
                val = evaluate(n_my_h, n_my_s, n_opp_h, n_opp_s)
            else:
                if extra:
                    # Same player continues, depth unchanged
                    val, _ = alphabeta(n_my_h, n_my_s, n_opp_h, n_opp_s, depth, alpha, beta, True, start_time, limit)
                else:
                    val, _ = alphabeta(n_opp_h, n_opp_s, n_my_h, n_my_s, depth - 1, alpha, beta, False, start_time, limit)
            if val is TIMEOUT:
                return TIMEOUT, None
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best_val, best_move

    else:  # minimizing (opponent's turn)
        moves = [i for i in range(6) if opp_h[i] > 0]
        if not moves:
            return evaluate(my_h, my_s, opp_h, opp_s), None

        children = []
        for move in moves:
            n_opp_h, n_opp_s, n_my_h, n_my_s, extra = make_move(opp_h, opp_s, my_h, my_s, move)
            score = evaluate(n_my_h, n_my_s, n_opp_h, n_opp_s)
            children.append((move, n_my_h, n_my_s, n_opp_h, n_opp_s, extra, score))

        # Opponent wants low scores; prefer extra-turn moves (bad for us), then lower scores
        children.sort(key=lambda c: (-c[5], c[6]))

        best_val = float('inf')
        best_move = children[0][0] if children else None
        for move, n_my_h, n_my_s, n_opp_h, n_opp_s, extra, _ in children:
            if sum(n_my_h) == 0 or sum(n_opp_h) == 0:
                val = evaluate(n_my_h, n_my_s, n_opp_h, n_opp_s)
            else:
                if extra:
                    val, _ = alphabeta(n_opp_h, n_opp_s, n_my_h, n_my_s, depth, alpha, beta, False, start_time, limit)
                else:
                    val, _ = alphabeta(n_my_h, n_my_s, n_opp_h, n_opp_s, depth - 1, alpha, beta, True, start_time, limit)
            if val is TIMEOUT:
                return TIMEOUT, None
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, val)
            if alpha >= beta:
                break
        return best_val, best_move


def policy(you, opponent):
    start = time.time()
    limit = 0.95

    legal = [i for i in range(6) if you[i] > 0]
    best_move = legal[0] if legal else 0
    depth = 1

    while True:
        if time.time() - start > limit:
            break
        val, move = alphabeta(
            you[0:6], you[6], opponent[0:6], opponent[6],
            depth, -float('inf'), float('inf'), True,
            start, limit
        )
        if val is TIMEOUT:
            break
        if move is not None:
            best_move = move
        depth += 1

    return best_move
