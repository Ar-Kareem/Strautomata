
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    def legal_moves(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    def winner(b):
        lines = []

        for i in range(3):
            lines.append((b[i][0], b[i][1], b[i][2]))
            lines.append((b[0][i], b[1][i], b[2][i]))

        lines.append((b[0][0], b[1][1], b[2][2]))
        lines.append((b[0][2], b[1][1], b[2][0]))

        for line in lines:
            s = sum(line)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def to_key(b):
        return tuple(tuple(row) for row in b)

    @lru_cache(maxsize=None)
    def solve(state, turn):
        b = [list(row) for row in state]
        w = winner(b)
        if w != 0:
            return w
        moves = legal_moves(b)
        if not moves:
            return 0

        if turn == 1:
            best = -2
            for r, c in moves:
                b[r][c] = 1
                val = solve(to_key(b), -1)
                b[r][c] = 0
                if val > best:
                    best = val
                if best == 1:
                    break
            return best
        else:
            best = 2
            for r, c in moves:
                b[r][c] = -1
                val = solve(to_key(b), 1)
                b[r][c] = 0
                if val < best:
                    best = val
                if best == -1:
                    break
            return best

    moves = legal_moves(board)
    if not moves:
        return (0, 0)

    best_move = moves[0]
    best_score = -2

    # Mild tie-breaking for stronger practical play ordering:
    preferred_order = {
        (1, 1): 3,
        (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
        (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1,
    }

    state = to_key(board)

    ordered_moves = sorted(
        moves,
        key=lambda mv: preferred_order.get(mv, 0),
        reverse=True
    )

    for r, c in ordered_moves:
        board[r][c] = 1
        score = solve(to_key(board), -1)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)
        elif score == best_score:
            if preferred_order.get((r, c), 0) > preferred_order.get(best_move, 0):
                best_move = (r, c)

        if best_score == 1:
            break

    # Safety fallback: always return a legal move
    if board[best_move[0]][best_move[1]] == 0:
        return best_move
    for mv in moves:
        if board[mv[0]][mv[1]] == 0:
            return mv
    return (0, 0)
