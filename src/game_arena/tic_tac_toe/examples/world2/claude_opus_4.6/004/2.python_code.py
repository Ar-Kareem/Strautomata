
import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    lines = []
    for r in range(4):
        lines.append([(r, c) for c in range(4)])
    for c in range(4):
        lines.append([(r, c) for r in range(4)])
    lines.append([(i, i) for i in range(4)])
    lines.append([(i, 3 - i) for i in range(4)])

    def check_winner(bd):
        for line in lines:
            s = sum(bd[r][c] for r, c in line)
            if s == 4: return 1
            if s == -4: return -1
        return 0

    def get_moves(bd):
        return [(r, c) for r in range(4) for c in range(4) if bd[r][c] == 0]

    def evaluate(bd):
        w = check_winner(bd)
        if w != 0:
            return w * 100000
        score = 0
        for line in lines:
            vals = [bd[r][c] for r, c in line]
            s = sum(vals)
            zeros = vals.count(0)
            if -1 not in vals and 1 in vals:
                if s == 3 and zeros == 1:
                    score += 5000
                elif s == 2 and zeros == 2:
                    score += 200
                elif s == 1 and zeros == 3:
                    score += 10
            if 1 not in vals and -1 in vals:
                if s == -3 and zeros == 1:
                    score -= 5000
                elif s == -2 and zeros == 2:
                    score -= 200
                elif s == -1 and zeros == 3:
                    score -= 10
        return score

    def order_moves(bd, moves, maximizing):
        scored = []
        for m in moves:
            r, c = m
            bd[r][c] = 1 if maximizing else -1
            scored.append((evaluate(bd), m))
            bd[r][c] = 0
        scored.sort(key=lambda x: x[0], reverse=maximizing)
        return [m for _, m in scored]

    def minimax(bd, depth, alpha, beta, maximizing, deadline):
        w = check_winner(bd)
        if w != 0:
            return w * (100000 + depth), None
        moves = get_moves(bd)
        if not moves:
            return 0, None
        if depth == 0 or time.time() > deadline:
            return evaluate(bd), None
        moves = order_moves(bd, moves, maximizing)
        best_move = moves[0]
        if maximizing:
            val = -float('inf')
            for m in moves:
                bd[m[0]][m[1]] = 1
                v, _ = minimax(bd, depth - 1, alpha, beta, False, deadline)
                bd[m[0]][m[1]] = 0
                if v > val:
                    val = v
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta or time.time() > deadline:
                    break
            return val, best_move
        else:
            val = float('inf')
            for m in moves:
                bd[m[0]][m[1]] = -1
                v, _ = minimax(bd, depth - 1, alpha, beta, True, deadline)
                bd[m[0]][m[1]] = 0
                if v < val:
                    val = v
                    best_move = m
                beta = min(beta, val)
                if alpha >= beta or time.time() > deadline:
                    break
            return val, best_move

    bd = [row[:] for row in board]
    deadline = time.time() + 0.85
    best_move = None
    moves = get_moves(bd)
    if not moves:
        return (0, 0)
    best_move = moves[0]
    for depth in range(1, 17):
        if time.time() > deadline:
            break
        val, move = minimax(bd, depth, -float('inf'), float('inf'), True, deadline)
        if move is not None:
            best_move = move
        if abs(val) >= 100000:
            break
    return best_move
