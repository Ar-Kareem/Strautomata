
from typing import List, Tuple, Optional, Dict

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Given a 3x3 Tic-Tac-Toe board (0 empty, 1 = us, -1 = opponent),
    return the row,col (0-2) for our next move.
    Uses minimax with alpha-beta pruning to play optimally.
    """
    # Helper functions
    def winner(b: List[List[int]]) -> int:
        # return 1 if we win, -1 if opponent wins, 0 otherwise
        for i in range(3):
            s = b[i][0] + b[i][1] + b[i][2]
            if s == 3: return 1
            if s == -3: return -1
            s = b[0][i] + b[1][i] + b[2][i]
            if s == 3: return 1
            if s == -3: return -1
        s = b[0][0] + b[1][1] + b[2][2]
        if s == 3: return 1
        if s == -3: return -1
        s = b[0][2] + b[1][1] + b[2][0]
        if s == 3: return 1
        if s == -3: return -1
        return 0

    def board_key(b: List[List[int]]) -> Tuple[Tuple[int, ...], ...]:
        return tuple(tuple(row) for row in b)

    # Count pieces to determine whose turn it is
    cnt_us = sum(cell == 1 for row in board for cell in row)
    cnt_op = sum(cell == -1 for row in board for cell in row)
    our_turn = (cnt_us == cnt_op)  # if equal, it's our turn (we start the game)

    # If the board is already terminal, just return the first empty cell (or (0,0) if none)
    if winner(board) != 0 or all(cell != 0 for row in board for cell in row):
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)

    # Minimax with alpha-beta and memoization
    memo: Dict[Tuple[Tuple[int, ...], ...], int] = {}

    def minimax(b: List[List[int]], player: int, alpha: int, beta: int) -> int:
        """
        player: current mover (1 for us, -1 for opponent)
        returns evaluation: 1 = win for us, 0 = draw, -1 = loss for us
        """
        k = board_key(b)
        if k in memo:
            return memo[k]

        w = winner(b)
        if w != 0:
            memo[k] = w
            return w
        # check for draw (no moves)
        moves = [(i, j) for i in range(3) for j in range(3) if b[i][j] == 0]
        if not moves:
            memo[k] = 0
            return 0

        if player == 1:
            # maximize
            best = -2
            for i, j in moves:
                b[i][j] = 1
                val = minimax(b, -1, alpha, beta)
                b[i][j] = 0
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            memo[k] = best
            return best
        else:
            # minimize (opponent tries to minimize our score)
            best = 2
            for i, j in moves:
                b[i][j] = -1
                val = minimax(b, 1, alpha, beta)
                b[i][j] = 0
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            memo[k] = best
            return best

    # If it's our turn, choose the move that maximizes minimax outcome.
    # If it's not our turn (shouldn't normally happen), we still return the best move
    # as if we were to move now (deterministic choice).
    best_move: Optional[Tuple[int, int]] = None
    best_score = -2  # worse than the worst possible (-1)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # try move
                board[i][j] = 1
                score = minimax(board, -1, -2, 2)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
                # immediate win short-circuit
                if best_score == 1:
                    return best_move  # type: ignore

    # Fallback: if no best_move found (shouldn't happen), select first empty
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)

    return best_move  # type: ignore
