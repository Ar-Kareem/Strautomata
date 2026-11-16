
import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    # All lines of 4 on a 4x4 board
    lines = []
    for r in range(4):
        lines.append([(r, c) for c in range(4)])
    for c in range(4):
        lines.append([(r, c) for r in range(4)])
    lines.append([(i, i) for i in range(4)])
    lines.append([(i, 3 - i) for i in range(4)])

    def get_empty(b):
        return [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]

    def check_win(b, player):
        for line in lines:
            if all(b[r][c] == player for r, c in line):
                return True
        return False

    def evaluate(b):
        # Check terminal states
        if check_win(b, 1):
            return 10000
        if check_win(b, -1):
            return -10000

        score = 0
        for line in lines:
            vals = [b[r][c] for r, c in line]
            p1 = vals.count(1)
            p2 = vals.count(-1)
            if p2 == 0 and p1 > 0:
                score += [0, 1, 10, 100][p1]
            if p1 == 0 and p2 > 0:
                score -= [0, 1, 10, 100][p2]
        return score

    start_time = time.time()
    time_limit = 0.85

    def minimax(b, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(b), None

        if check_win(b, 1):
            return 10000 + depth, None
        if check_win(b, -1):
            return -10000 - depth, None

        empty = get_empty(b)
        if not empty or depth == 0:
            return evaluate(b), None

        # Move ordering: prioritize center-ish cells
        def move_score(m):
            r, c = m
            return -abs(r - 1.5) - abs(c - 1.5)
        empty.sort(key=move_score, reverse=True)

        best_move = empty[0]
        if maximizing:
            max_eval = -float('inf')
            for r, c in empty:
                b[r][c] = 1
                ev, _ = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                if ev > max_eval:
                    max_eval = ev
                    best_move = (r, c)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
                if time.time() - start_time > time_limit:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for r, c in empty:
                b[r][c] = -1
                ev, _ = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                if ev < min_eval:
                    min_eval = ev
                    best_move = (r, c)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
                if time.time() - start_time > time_limit:
                    break
            return min_eval, best_move

    # Make a copy to avoid mutating original
    b = [row[:] for row in board]
    empty = get_empty(b)

    if not empty:
        return (0, 0)  # shouldn't happen

    # Iterative deepening
    best_move = empty[0]
    for depth in range(1, len(empty) + 1):
        if time.time() - start_time > time_limit:
            break
        ev, move = minimax(b, depth, -float('inf'), float('inf'), True)
        if move is not None:
            best_move = move
        if abs(ev) >= 10000:
            break

    return best_move
