
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

    def board_to_tuple(b):
        return tuple(tuple(row) for row in b)

    @lru_cache(maxsize=None)
    def solve(state):
        b = [list(row) for row in state]
        w = winner(b)
        if w != 0:
            return w
        moves = legal_moves(b)
        if not moves:
            return 0

        best = -2
        for r, c in moves:
            b[r][c] = 1
            next_state = tuple(tuple(-cell for cell in row) for row in b)
            score = -solve(next_state)
            b[r][c] = 0
            if score > best:
                best = score
                if best == 1:
                    break
        return best

    moves = legal_moves(board)
    if not moves:
        return (0, 0)

    for r, c in moves:
        if board[r][c] == 0:
            board[r][c] = 1
            if winner(board) == 1:
                board[r][c] = 0
                return (r, c)
            board[r][c] = 0

    for r, c in moves:
        if board[r][c] == 0:
            board[r][c] = -1
            if winner(board) == -1:
                board[r][c] = 0
                return (r, c)
            board[r][c] = 0

    best_score = -2
    best_move = moves[0]

    preferred_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    move_set = set(moves)
    ordered_moves = [m for m in preferred_order if m in move_set]

    for r, c in ordered_moves:
        board[r][c] = 1
        next_state = tuple(tuple(-cell for cell in row) for row in board)
        score = -solve(next_state)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
