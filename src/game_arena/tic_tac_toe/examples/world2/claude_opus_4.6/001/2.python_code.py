
import functools

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
            if s == 4:
                return 1
            if s == -4:
                return -1
        return 0

    def get_empty(bd):
        return [(r, c) for r in range(4) for c in range(4) if bd[r][c] == 0]

    def evaluate(bd):
        w = check_winner(bd)
        if w != 0:
            return w * 100000
        score = 0
        for line in lines:
            vals = [bd[r][c] for r, c in line]
            s = sum(vals)
            has1 = any(v == 1 for v in vals)
            has_neg1 = any(v == -1 for v in vals)
            if has_neg1 and has1:
                continue
            if has1:
                score += s * s * s  # cubic to heavily weight 3-in-a-row
            elif has_neg1:
                score += s * abs(s) * abs(s)  # negative cubic
        return score

    def board_key(bd, player):
        return (tuple(tuple(row) for row in bd), player)

    trans = {}

    def minimax(bd, player, alpha, beta, depth, max_depth):
        key = board_key(bd, player)
        if key in trans:
            stored_depth, stored_val = trans[key]
            if stored_depth >= max_depth - depth:
                return stored_val

        w = check_winner(bd)
        if w != 0:
            val = w * (100000 + depth)  # prefer faster wins
            return val

        empty = get_empty(bd)
        if not empty:
            return 0

        if depth >= max_depth:
            return evaluate(bd)

        # Move ordering: center-ish first
        empty.sort(key=lambda pos: -((pos[0] - 1.5)**2 + (pos[1] - 1.5)**2))
        empty.sort(key=lambda pos: abs(sum(bd[r][c] for r, c in line) for line in lines if pos in line).__class__(0))

        # Simple move ordering by center distance
        empty.sort(key=lambda pos: (pos[0] - 1.5)**2 + (pos[1] - 1.5)**2)

        if player == 1:
            best = -999999
            for r, c in empty:
                bd[r][c] = 1
                val = minimax(bd, -1, alpha, beta, depth + 1, max_depth)
                bd[r][c] = 0
                best = max(best, val)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            trans[key] = (max_depth - depth, best)
            return best
        else:
            best = 999999
            for r, c in empty:
                bd[r][c] = -1
                val = minimax(bd, 1, alpha, beta, depth + 1, max_depth)
                bd[r][c] = 0
                best = min(best, val)
                beta = min(beta, val)
                if alpha >= beta:
                    break
            trans[key] = (max_depth - depth, best)
            return best

    empty = get_empty(board)
    if not empty:
        return (0, 0)

    best_move = empty[0]
    # Iterative deepening
    for max_d in range(1, 17):
        best_val = -999999
        moves = sorted(empty, key=lambda pos: (pos[0] - 1.5)**2 + (pos[1] - 1.5)**2)
        for r, c in moves:
            board[r][c] = 1
            val = minimax(board, -1, -999999, 999999, 1, max_d)
            board[r][c] = 0
            if val > best_val:
                best_val = val
                best_move = (r, c)

    return best_move
