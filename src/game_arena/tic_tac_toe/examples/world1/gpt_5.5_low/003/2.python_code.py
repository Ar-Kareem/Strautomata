
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy for player 1.
    board: 3x3 list where 0 = empty, 1 = our mark, -1 = opponent mark.
    returns: (row, col) legal empty position.
    """

    # Preferred move order improves alpha-beta pruning and gives sensible play.
    preferred_moves = [
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2),  # corners
        (0, 1), (1, 0), (1, 2), (2, 1),  # edges
    ]

    def legal_moves(b):
        return [(r, c) for r, c in preferred_moves if b[r][c] == 0]

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

    def is_full(b):
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    def minimax(b, turn, alpha, beta, depth):
        """
        Returns score from our perspective.
        Higher is better for player 1.
        Scores include depth so faster wins and slower losses are preferred.
        """
        w = winner(b)
        if w == 1:
            return 10 - depth
        if w == -1:
            return depth - 10
        if is_full(b):
            return 0

        moves = legal_moves(b)
        if not moves:
            return 0

        if turn == 1:
            best = -999
            for r, c in moves:
                b[r][c] = 1
                score = minimax(b, -1, alpha, beta, depth + 1)
                b[r][c] = 0

                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
            return best
        else:
            best = 999
            for r, c in moves:
                b[r][c] = -1
                score = minimax(b, 1, alpha, beta, depth + 1)
                b[r][c] = 0

                if score < best:
                    best = score
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
            return best

    moves = legal_moves(board)

    # Absolute safety fallback: if no legal moves exist, return a valid-shaped tuple.
    # In normal arena play this should never happen because the game is already over.
    if not moves:
        return (0, 0)

    # First, take an immediate win if available.
    for r, c in moves:
        board[r][c] = 1
        if winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Then, block any immediate opponent win.
    for r, c in moves:
        board[r][c] = -1
        if winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Otherwise use minimax to choose the optimal move.
    best_score = -999
    best_move = moves[0]

    for r, c in moves:
        board[r][c] = 1
        score = minimax(board, -1, -999, 999, 1)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
