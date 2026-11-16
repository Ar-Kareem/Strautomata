
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    def legal_moves(b):
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    def winner(b):
        lines = []

        for i in range(3):
            lines.append(b[i])
            lines.append([b[0][i], b[1][i], b[2][i]])

        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])

        for line in lines:
            s = sum(line)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def board_key(b):
        return tuple(tuple(row) for row in b)

    @lru_cache(maxsize=None)
    def minimax(state, turn):
        b = [list(row) for row in state]
        w = winner(b)
        if w == 1:
            return 1
        if w == -1:
            return -1

        moves = legal_moves(b)
        if not moves:
            return 0

        if turn == 1:
            best = -2
            for r, c in moves:
                b[r][c] = 1
                val = minimax(board_key(b), -1)
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
                val = minimax(board_key(b), 1)
                b[r][c] = 0
                if val < best:
                    best = val
                if best == -1:
                    break
            return best

    moves = legal_moves(board)
    if not moves:
        return (0, 0)

    # Strong move ordering for deterministic play.
    preferred_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    move_set = set(moves)
    ordered_moves = [m for m in preferred_order if m in move_set]

    best_move = ordered_moves[0]
    best_score = -2

    for r, c in ordered_moves:
        board[r][c] = 1
        score = minimax(board_key(board), -1)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

        if best_score == 1:
            break

    # Guaranteed legal fallback
    if board[best_move[0]][best_move[1]] == 0:
        return best_move

    for move in moves:
        if board[move[0]][move[1]] == 0:
            return move

    return (0, 0)
