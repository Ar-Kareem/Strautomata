
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return a legal move (row, col) for Tic Tac Toe.
    Board encoding:
      0  = empty
      1  = our moves
      -1 = opponent moves
    """

    def legal_moves(b):
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    def winner(b):
        # Rows
        for r in range(3):
            s = b[r][0] + b[r][1] + b[r][2]
            if s == 3:
                return 1
            if s == -3:
                return -1

        # Cols
        for c in range(3):
            s = b[0][c] + b[1][c] + b[2][c]
            if s == 3:
                return 1
            if s == -3:
                return -1

        # Diagonals
        s = b[0][0] + b[1][1] + b[2][2]
        if s == 3:
            return 1
        if s == -3:
            return -1

        s = b[0][2] + b[1][1] + b[2][0]
        if s == 3:
            return 1
        if s == -3:
            return -1

        return 0

    def is_full(b):
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    # Preferred move order for tie-breaking
    preferred_order = [
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2),  # corners
        (0, 1), (1, 0), (1, 2), (2, 1),  # edges
    ]

    def ordered_moves(b):
        legal = set(legal_moves(b))
        return [mv for mv in preferred_order if mv in legal]

    memo = {}

    def encode(b):
        return tuple(tuple(row) for row in b)

    def minimax(b, turn, depth):
        """
        turn = 1 if it's our turn, -1 if opponent's turn.
        Returns score from our perspective:
          positive = good for us
          negative = good for opponent
        """
        key = (encode(b), turn)
        if key in memo:
            return memo[key]

        w = winner(b)
        if w == 1:
            return 10 - depth
        if w == -1:
            return depth - 10
        if is_full(b):
            return 0

        moves = ordered_moves(b)

        if turn == 1:
            best = -10**9
            for r, c in moves:
                b[r][c] = 1
                score = minimax(b, -1, depth + 1)
                b[r][c] = 0
                if score > best:
                    best = score
            memo[key] = best
            return best
        else:
            best = 10**9
            for r, c in moves:
                b[r][c] = -1
                score = minimax(b, 1, depth + 1)
                b[r][c] = 0
                if score < best:
                    best = score
            memo[key] = best
            return best

    moves = ordered_moves(board)

    # Guaranteed legal fallback, even for malformed edge cases.
    if not moves:
        for r in range(3):
            for c in range(3):
                if 0 <= r < 3 and 0 <= c < 3 and board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    best_move = moves[0]
    best_score = -10**9

    for r, c in moves:
        board[r][c] = 1
        score = minimax(board, -1, 1)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Final legality check
    r, c = best_move
    if 0 <= r < 3 and 0 <= c < 3 and board[r][c] == 0:
        return best_move

    for mv in moves:
        rr, cc = mv
        if board[rr][cc] == 0:
            return mv

    # Last-resort fallback
    for rr in range(3):
        for cc in range(3):
            if board[rr][cc] == 0:
                return (rr, cc)

    return (0, 0)
