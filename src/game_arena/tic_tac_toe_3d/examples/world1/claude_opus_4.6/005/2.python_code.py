
import numpy as np

def policy(board):
    # All 49 winning lines
    lines = []
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])
            lines.append([(i, k, j) for k in range(3)])
            lines.append([(k, i, j) for k in range(3)])
    for i in range(3):
        lines.append([(i, k, k) for k in range(3)])
        lines.append([(i, k, 2-k) for k in range(3)])
        lines.append([(k, i, k) for k in range(3)])
        lines.append([(k, i, 2-k) for k in range(3)])
        lines.append([(k, k, i) for k in range(3)])
        lines.append([(k, 2-k, i) for k in range(3)])
    lines.append([(k, k, k) for k in range(3)])
    lines.append([(k, k, 2-k) for k in range(3)])
    lines.append([(k, 2-k, k) for k in range(3)])
    lines.append([(2-k, k, k) for k in range(3)])

    b = np.array(board, dtype=np.int8)

    def check_win(b, player):
        for line in lines:
            if all(b[c] == player for c in line):
                return True
        return False

    def get_empty(b):
        return list(zip(*np.where(b == 0)))

    def evaluate(b):
        score = 0
        for line in lines:
            vals = [b[c] for c in line]
            s1 = vals.count(1)
            s2 = vals.count(-1)
            if s2 == 0 and s1 > 0:
                score += [0, 1, 10, 1000][s1]
            if s1 == 0 and s2 > 0:
                score -= [0, 1, 10, 1000][s2]
        return score

    def minimax(b, depth, alpha, beta, maximizing):
        if check_win(b, 1):
            return 10000 + depth
        if check_win(b, -1):
            return -10000 - depth
        empty = get_empty(b)
        if not empty:
            return 0
        if depth <= 0:
            return evaluate(b)

        # Move ordering
        def move_priority(m):
            ci = sum(abs(x - 1) for x in m)
            return ci
        empty.sort(key=move_priority)

        if maximizing:
            val = -100000
            for m in empty:
                b[m] = 1
                val = max(val, minimax(b, depth - 1, alpha, beta, False))
                b[m] = 0
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            val = 100000
            for m in empty:
                b[m] = -1
                val = min(val, minimax(b, depth - 1, alpha, beta, True))
                b[m] = 0
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val

    empty = get_empty(b)
    if not empty:
        return (0, 0, 0)

    # Determine search depth based on empty cells
    n_empty = len(empty)
    if n_empty > 20:
        max_depth = 4
    elif n_empty > 15:
        max_depth = 5
    elif n_empty > 10:
        max_depth = 6
    else:
        max_depth = 20  # solve to end

    best_move = empty[0]
    best_val = -200000

    def move_priority(m):
        return sum(abs(x - 1) for x in m)
    empty.sort(key=move_priority)

    for m in empty:
        b[m] = 1
        if check_win(b, 1):
            b[m] = 0
            return tuple(m)
        b[m] = 0

    for m in empty:
        b[m] = -1
        if check_win(b, -1):
            b[m] = 0
            return tuple(m)
        b[m] = 0

    for m in empty:
        b[m] = 1
        val = minimax(b, max_depth - 1, best_val, 200000, False)
        b[m] = 0
        if val > best_val:
            best_val = val
            best_move = m

    return tuple(best_move)
