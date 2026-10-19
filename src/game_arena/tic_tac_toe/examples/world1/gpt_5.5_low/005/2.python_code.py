
from typing import List, Tuple

Board = List[List[int]]


def policy(board: Board) -> Tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy.

    Board representation:
        0  = empty
        1  = this policy's mark
        -1 = opponent's mark

    Returns:
        (row, col) for a legal empty cell.
    """

    def winner(b: Board) -> int:
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

    def empty_cells(b: Board) -> List[Tuple[int, int]]:
        # Strong move ordering improves alpha-beta pruning and tie-breaking.
        preferred = [
            (1, 1),
            (0, 0), (0, 2), (2, 0), (2, 2),
            (0, 1), (1, 0), (1, 2), (2, 1),
        ]
        return [(r, c) for r, c in preferred if b[r][c] == 0]

    def board_full(b: Board) -> bool:
        return all(b[r][c] != 0 for r in range(3) for c in range(3))

    def minimax(b: Board, turn: int, alpha: int, beta: int, depth: int) -> int:
        """
        Returns score from this policy's perspective:
            positive = good for us
            negative = good for opponent

        Depth is used to prefer faster wins and slower losses.
        """
        w = winner(b)
        if w == 1:
            return 10 - depth
        if w == -1:
            return depth - 10
        if board_full(b):
            return 0

        moves = empty_cells(b)

        if turn == 1:
            best = -100
            for r, c in moves:
                b[r][c] = 1
                score = minimax(b, -1, alpha, beta, depth + 1)
                b[r][c] = 0

                if score > best:
                    best = score
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best

        else:
            best = 100
            for r, c in moves:
                b[r][c] = -1
                score = minimax(b, 1, alpha, beta, depth + 1)
                b[r][c] = 0

                if score < best:
                    best = score
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    legal_moves = empty_cells(board)

    # Absolute safety fallback: always return a legal move if one exists.
    if not legal_moves:
        return (0, 0)

    best_score = -100
    best_move = legal_moves[0]

    for r, c in legal_moves:
        board[r][c] = 1
        score = minimax(board, -1, -100, 100, 1)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
