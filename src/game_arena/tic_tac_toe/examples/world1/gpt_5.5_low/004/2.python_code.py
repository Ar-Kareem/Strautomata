
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy for player 1.
    board:
        0  = empty
        1  = our move
        -1 = opponent move
    returns:
        (row, col) legal empty position
    """

    preferred_order = [
        (1, 1),              # center
        (0, 0), (0, 2),      # corners
        (2, 0), (2, 2),
        (0, 1), (1, 0),      # edges
        (1, 2), (2, 1),
    ]

    def legal_moves(b):
        return [(r, c) for r, c in preferred_order if b[r][c] == 0]

    def winner(b):
        lines = []

        # Rows and columns
        for i in range(3):
            lines.append(b[i][0] + b[i][1] + b[i][2])
            lines.append(b[0][i] + b[1][i] + b[2][i])

        # Diagonals
        lines.append(b[0][0] + b[1][1] + b[2][2])
        lines.append(b[0][2] + b[1][1] + b[2][0])

        if 3 in lines:
            return 1
        if -3 in lines:
            return -1
        return 0

    def board_key(b):
        return tuple(tuple(row) for row in b)

    @lru_cache(None)
    def minimax(key, turn):
        b = [list(row) for row in key]

        w = winner(b)
        if w == 1:
            return 10
        if w == -1:
            return -10

        moves = legal_moves(b)
        if not moves:
            return 0

        if turn == 1:
            best = -100
            for r, c in moves:
                b[r][c] = 1
                score = minimax(board_key(b), -1)
                b[r][c] = 0

                # Prefer quicker wins.
                if score > 0:
                    score -= 1
                elif score < 0:
                    score += 1

                best = max(best, score)
            return best
        else:
            best = 100
            for r, c in moves:
                b[r][c] = -1
                score = minimax(board_key(b), 1)
                b[r][c] = 0

                # Opponent also prefers quicker wins for itself,
                # which are worse for us.
                if score > 0:
                    score -= 1
                elif score < 0:
                    score += 1

                best = min(best, score)
            return best

    moves = legal_moves(board)

    # Safety fallback for invalid/full terminal boards.
    if not moves:
        return (0, 0)

    # 1. Take immediate win.
    for r, c in moves:
        board[r][c] = 1
        if winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2. Block opponent immediate win.
    for r, c in moves:
        board[r][c] = -1
        if winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3. Full minimax search.
    best_move = moves[0]
    best_score = -100

    for r, c in moves:
        board[r][c] = 1
        score = minimax(board_key(board), -1)
        board[r][c] = 0

        if score > 0:
            score -= 1
        elif score < 0:
            score += 1

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
