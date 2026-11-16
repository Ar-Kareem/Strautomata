
import time

def policy(you: list[int], opponent: list[int]) -> int:
    # Flatten board: indices 0-5 your houses, 6 your store, 7-12 opponent houses, 13 opponent store.
    board = you[:6] + [you[6]] + opponent[:6] + [opponent[6]]
    player_us = 0

    legal_moves = [i for i in range(6) if board[i] > 0]
    if len(legal_moves) == 1:
        return legal_moves[0]

    deadline = time.time() + 0.9
    nodes = [0]
    abort = [False]

    class TimeOut(Exception):
        pass

    def get_legal_moves(b, p):
        start = 0 if p == 0 else 7
        return [i for i in range(6) if b[start + i] > 0]

    def is_terminal(b):
        return sum(b[0:6]) == 0 or sum(b[7:13]) == 0

    def evaluate(b, p):
        if is_terminal(b):
            our_rem = sum(b[0:6])
            opp_rem = sum(b[7:13])
            if our_rem == 0:
                our_score = b[6]
                opp_score = b[13] + opp_rem
            elif opp_rem == 0:
                our_score = b[6] + our_rem
                opp_score = b[13]
            else:
                our_score = b[6]
                opp_score = b[13]
            diff = our_score - opp_score
            return diff if p == 0 else -diff
        else:
            store_diff = b[6] - b[13]
            house_diff = sum(b[0:6]) - sum(b[7:13])
            val = store_diff + 0.2 * house_diff
            return val if p == 0 else -val

    def quick_eval(b, p):
        store_diff = b[6] - b[13]
        house_diff = sum(b[0:6]) - sum(b[7:13])
        val = store_diff + 0.2 * house_diff
        return val if p == 0 else -val

    def make_move(b, p, pit):
        new_b = b[:]
        start = 0 if p == 0 else 7
        store = 6 if p == 0 else 13
        opp_store = 13 if p == 0 else 6
        idx = start + pit
        seeds = new_b[idx]
        new_b[idx] = 0
        pos = idx
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == opp_store:
                continue
            new_b[pos] += 1
            seeds -= 1
        next_p = p if pos == store else 1 - p
        # Capture
        if p == 0:
            if 0 <= pos <= 5 and b[pos] == 0:
                opp_pos = 12 - pos
                if new_b[opp_pos] > 0:
                    new_b[store] += new_b[pos] + new_b[opp_pos]
                    new_b[pos] = 0
                    new_b[opp_pos] = 0
        else:
            if 7 <= pos <= 12 and b[pos] == 0:
                opp_pos = 12 - pos
                if new_b[opp_pos] > 0:
                    new_b[store] += new_b[pos] + new_b[opp_pos]
                    new_b[pos] = 0
                    new_b[opp_pos] = 0
        return new_b, next_p

    def negamax(b, depth, alpha, beta, p):
        nodes[0] += 1
        if nodes[0] % 500 == 0 and time.time() > deadline:
            abort[0] = True
            raise TimeOut()
        if depth == 0 or is_terminal(b):
            return evaluate(b, p)
        legal = get_legal_moves(b, p)
        if not legal:
            return evaluate(b, p)
        # Move ordering
        children = []
        for pit in legal:
            new_b, next_p = make_move(b, p, pit)
            sc = quick_eval(new_b, p)
            children.append((sc, new_b, next_p, pit))
        children.sort(reverse=True, key=lambda x: x[0])
        value = -float('inf')
        for _, new_b, next_p, pit in children:
            if abort[0]:
                raise TimeOut()
            child_val = -negamax(new_b, depth - 1, -beta, -alpha, next_p)
            if child_val > value:
                value = child_val
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    best_move = legal_moves[0]
    try:
        for depth in range(1, 50):
            if abort[0] or time.time() > deadline:
                break
            alpha = -float('inf')
            beta = float('inf')
            value = -float('inf')
            legal = get_legal_moves(board, player_us)
            children = []
            for pit in legal:
                new_b, next_p = make_move(board, player_us, pit)
                sc = quick_eval(new_b, player_us)
                children.append((sc, new_b, next_p, pit))
            children.sort(reverse=True, key=lambda x: x[0])
            current_best = best_move
            for _, new_b, next_p, pit in children:
                if abort[0]:
                    break
                child_val = -negamax(new_b, depth - 1, -beta, -alpha, next_p)
                if child_val > value:
                    value = child_val
                    current_best = pit
                alpha = max(alpha, value)
            if not abort[0]:
                best_move = current_best
    except TimeOut:
        pass

    return best_move
