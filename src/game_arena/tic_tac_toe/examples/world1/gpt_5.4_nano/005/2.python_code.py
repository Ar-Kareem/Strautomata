
from __future__ import annotations

from typing import List, Tuple, Optional

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Optimal Tic Tac Toe move using minimax with alpha-beta pruning.
    board: 3x3 with 0 empty, 1 self, -1 opponent.
    returns: (row, col) for an empty cell.
    """
    N = 3

    def winner(b: List[List[int]]) -> int:
        # Returns 1 if self wins, -1 if opponent wins, 0 otherwise (including draw not detected here)
        lines = []
        # rows and cols
        for i in range(N):
            lines.append(b[i][0] + b[i][1] + b[i][2])
            lines.append(b[0][i] + b[1][i] + b[2][i])
        # diagonals
        lines.append(b[0][0] + b[1][1] + b[2][2])
        lines.append(b[0][2] + b[1][1] + b[2][0])
        if 3 in lines:
            return 1
        if -3 in lines:
            return -1
        return 0

    def is_full(b: List[List[int]]) -> bool:
        for r in range(N):
            for c in range(N):
                if b[r][c] == 0:
                    return False
        return True

    def legal_moves(b: List[List[int]]) -> List[Tuple[int, int]]:
        moves = []
        for r in range(N):
            for c in range(N):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    def next_player(b: List[List[int]]) -> int:
        # self=1, opponent=-1. Determine whose turn from counts.
        count_self = sum(1 for r in range(N) for c in range(N) if b[r][c] == 1)
        count_opp = sum(1 for r in range(N) for c in range(N) if b[r][c] == -1)
        # If equal, it's self's turn; otherwise opponent's.
        return 1 if count_self == count_opp else -1

    def score_terminal(b: List[List[int]], depth: int) -> Optional[int]:
        w = winner(b)
        if w != 0:
            # Prefer faster wins / slower losses
            # self win => higher, opp win => lower
            return 10 - depth if w == 1 else -10 + depth
        if is_full(b):
            return 0
        return None

    def minimax(b: List[List[int]], depth: int, alpha: int, beta: int) -> int:
        term = score_terminal(b, depth)
        if term is not None:
            return term

        player = next_player(b)
        # If it's self's turn, we maximize; opponent's turn, we minimize
        if player == 1:
            best = -10**9
            for (r, c) in legal_moves(b):
                b[r][c] = 1
                val = minimax(b, depth + 1, alpha, beta)
                b[r][c] = 0
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = 10**9
            for (r, c) in legal_moves(b):
                b[r][c] = -1
                val = minimax(b, depth + 1, alpha, beta)
                b[r][c] = 0
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    # Work on a copy to avoid mutating input
    b = [row[:] for row in board]

    moves = legal_moves(b)
    if not moves:
        # No legal moves; should not happen in valid games. Return something legal anyway.
        return (0, 0)

    # Choose the best move for self
    # If it's opponent's turn (shouldn't happen given API expectation), we still return a legal move.
    player = next_player(b)
    best_move = moves[0]

    if player == 1:
        best_val = -10**9
        alpha, beta = -10**9, 10**9
        for (r, c) in moves:
            b[r][c] = 1
            val = minimax(b, depth=1, alpha=alpha, beta=beta)
            b[r][c] = 0
            if val > best_val:
                best_val = val
                best_move = (r, c)
            if best_val > alpha:
                alpha = best_val
    else:
        # If somehow it's opponent's turn, choose move that minimizes their outcome
        best_val = 10**9
        alpha, beta = -10**9, 10**9
        for (r, c) in moves:
            b[r][c] = -1
            val = minimax(b, depth=1, alpha=alpha, beta=beta)
            b[r][c] = 0
            if val < best_val:
                best_val = val
                best_move = (r, c)
            if best_val < beta:
                beta = best_val

    return best_move
