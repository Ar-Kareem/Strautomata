
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    def legal_moves(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    def winner(b):
        lines = []
        lines.extend(b)
        lines.extend([[b[0][c], b[1][c], b[2][c]] for c in range(3)])
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for line in lines:
            s = sum(line)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def is_full(b):
        return all(b[r][c] != 0 for r in range(3) for c in range(3))

    def to_key(b):
        return tuple(tuple(row) for row in b)

    @lru_cache(maxsize=None)
    def solve(state, player):
        b = [list(row) for row in state]
        w = winner(b)
        if w != 0:
            return w
        if is_full(b):
            return 0

        moves = legal_moves(b)
        if player == 1:
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

    def move_priority(move):
        r, c = move
        if (r, c) == (1, 1):
            return 3
        if (r, c) in ((0, 0), (0, 2), (2, 0), (2, 2)):
            return 2
        return 1

    b = [row[:] for row in board]
    moves = legal_moves(b)

    # Always return a legal move if possible.
    if not moves:
        return (0, 0)

    # Immediate win
    for r, c in moves:
        b[r][c] = 1
        if winner(b) == 1:
            return (r, c)
        b[r][c] = 0

    # Immediate block
    for r, c in moves:
        b[r][c] = -1
        if winner(b) == -1:
            b[r][c] = 0
            return (r, c)
        b[r][c] = 0

    # Minimax over all legal moves
    best_score = -2
    best_moves = []

    for r, c in moves:
        b[r][c] = 1
        score = solve(to_key(b), -1)
        b[r][c] = 0

        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))

    # Tie-break by board preference: center > corners > edges
    best_moves.sort(key=lambda mv: (-move_priority(mv), mv[0], mv[1]))
    return best_moves[0] if best_moves else moves[0]
