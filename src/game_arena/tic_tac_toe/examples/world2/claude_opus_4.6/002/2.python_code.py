
import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    WIN_LINES = []
    # Rows
    for r in range(4):
        WIN_LINES.append([(r, c) for c in range(4)])
    # Cols
    for c in range(4):
        WIN_LINES.append([(r, c) for r in range(4)])
    # Diagonals
    WIN_LINES.append([(i, i) for i in range(4)])
    WIN_LINES.append([(i, 3 - i) for i in range(4)])

    def check_winner(bd):
        for line in WIN_LINES:
            vals = [bd[r][c] for r, c in line]
            if vals[0] != 0 and all(v == vals[0] for v in vals):
                return vals[0]
        return 0

    def get_moves(bd):
        moves = []
        # Prioritize center, then corners, then edges
        order = [(1,1),(1,2),(2,1),(2,2),(0,0),(0,3),(3,0),(3,3),(0,1),(0,2),(1,0),(1,3),(2,0),(2,3),(3,1),(3,2)]
        for r, c in order:
            if bd[r][c] == 0:
                moves.append((r, c))
        return moves

    def evaluate(bd):
        w = check_winner(bd)
        if w != 0:
            return w * 100000
        score = 0
        for line in WIN_LINES:
            vals = [bd[r][c] for r, c in line]
            s1 = vals.count(1)
            s2 = vals.count(-1)
            if s2 == 0 and s1 > 0:
                if s1 == 3:
                    score += 500
                elif s1 == 2:
                    score += 10
                elif s1 == 1:
                    score += 1
            if s1 == 0 and s2 > 0:
                if s2 == 3:
                    score -= 500
                elif s2 == 2:
                    score -= 10
                elif s2 == 1:
                    score -= 1
        return score

    def minimax(bd, depth, alpha, beta, maximizing, deadline):
        w = check_winner(bd)
        if w != 0:
            return w * (100000 + depth), None
        moves = get_moves(bd)
        if not moves:
            return 0, None
        if depth == 0 or time.time() > deadline:
            return evaluate(bd), None

        best_move = moves[0]
        if maximizing:
            max_eval = -float('inf')
            for r, c in moves:
                bd[r][c] = 1
                val, _ = minimax(bd, depth - 1, alpha, beta, False, deadline)
                bd[r][c] = 0
                if val > max_eval:
                    max_eval = val
                    best_move = (r, c)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for r, c in moves:
                bd[r][c] = -1
                val, _ = minimax(bd, depth - 1, alpha, beta, True, deadline)
                bd[r][c] = 0
                if val < min_eval:
                    min_eval = val
                    best_move = (r, c)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    bd = [row[:] for row in board]
    deadline = time.time() + 0.85
    best_move = None

    for depth in range(1, 17):
        if time.time() > deadline:
            break
        val, move = minimax(bd, depth, -float('inf'), float('inf'), True, deadline)
        if move is not None:
            best_move = move
        if abs(val) >= 100000:
            break

    if best_move is None:
        best_move = get_moves(bd)[0]
    return best_move
