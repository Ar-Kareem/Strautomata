
import time
from math import inf

def policy(you: list[int], opponent: list[int]) -> int:
    start = time.time()
    TIME_LIMIT = 0.95  # seconds

    class Timeout(Exception):
        pass

    def legal_moves(p):
        return [i for i in range(6) if p[i] > 0]

    def terminal_score(y, o):
        y_empty = sum(y[:6]) == 0
        o_empty = sum(o[:6]) == 0
        if not (y_empty or o_empty):
            return None
        if y_empty:
            y_store = y[6]
            o_store = o[6] + sum(o[:6])
        else:
            y_store = y[6] + sum(y[:6])
            o_store = o[6]
        return (y_store - o_store) * 1000

    def evaluate(y, o):
        t = terminal_score(y, o)
        if t is not None:
            return t
        sd = y[6] - o[6]
        hd = sum(y[:6]) - sum(o[:6])
        extra_moves = 0
        for i in range(6):
            if y[i] > 0:
                dist = 6 - i
                if y[i] % 13 == dist:
                    extra_moves += 1
        return sd * 2.0 + hd * 0.5 + extra_moves * 0.3

    def apply_move(y, o, move):
        y = y[:]  # copy
        o = o[:]
        seeds = y[move]
        y[move] = 0
        pos = move
        capture_pos = None

        while seeds > 0:
            pos = (pos + 1) % 13
            if pos < 6:
                if seeds == 1 and y[pos] == 0:
                    capture_pos = pos
                y[pos] += 1
            elif pos == 6:
                y[6] += 1
            else:
                o[pos - 7] += 1
            seeds -= 1

        extra = (pos == 6)

        if capture_pos is not None and o[5 - capture_pos] > 0:
            y[6] += 1 + o[5 - capture_pos]
            y[capture_pos] = 0
            o[5 - capture_pos] = 0

        if sum(y[:6]) == 0 or sum(o[:6]) == 0:
            if sum(y[:6]) == 0:
                o[6] += sum(o[:6])
                o[:6] = [0] * 6
            else:
                y[6] += sum(y[:6])
                y[:6] = [0] * 6
        return y, o, extra

    def order_moves(y, o, moves):
        scored = []
        for m in moves:
            ny, no, extra = apply_move(y, o, m)
            gain = ny[6] - y[6]
            score = gain + (3 if extra else 0)
            scored.append((score, m))
        scored.sort(reverse=True)
        return [m for _, m in scored]

    def negamax(y, o, depth, alpha, beta):
        if time.time() - start > TIME_LIMIT:
            raise Timeout()
        t = terminal_score(y, o)
        if depth == 0 or t is not None:
            return evaluate(y, o)

        moves = legal_moves(y)
        if not moves:
            return evaluate(y, o)

        moves = order_moves(y, o, moves)
        best = -inf
        for m in moves:
            ny, no, extra = apply_move(y, o, m)
            if extra:
                val = negamax(ny, no, depth - 1, alpha, beta)
            else:
                val = -negamax(no, ny, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    def search_depth(y, o, depth):
        moves = legal_moves(y)
        if not moves:
            return None, -inf
        moves = order_moves(y, o, moves)
        best_move = moves[0]
        best_val = -inf
        alpha = -inf
        beta = inf
        for m in moves:
            ny, no, extra = apply_move(y, o, m)
            if extra:
                val = negamax(ny, no, depth - 1, alpha, beta)
            else:
                val = -negamax(no, ny, depth - 1, -beta, -alpha)
            if val > best_val:
                best_val = val
                best_move = m
            if val > alpha:
                alpha = val
        return best_move, best_val

    legal = legal_moves(you)
    best = legal[0]

    depth = 1
    while True:
        try:
            if time.time() - start > TIME_LIMIT:
                break
            move, _ = search_depth(you, opponent, depth)
            if move is not None:
                best = move
            depth += 1
        except Timeout:
            break

    return best
