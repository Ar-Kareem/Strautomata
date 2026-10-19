
import copy
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Select the next move for a 3x3 Tic Tac Toe board.
    board: 3x3 list of lists with values 0 (empty), 1 (us), -1 (opponent)
    returns: (row, col) tuple with 0..2 indices
    """
    # Defensive copy
    b = [row[:] for row in board]

    # Precomputed preference order for tie-breaking: center, corners, edges
    pref = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    rank = {pos: i for i, pos in enumerate(pref)}

    def winner(board_state: List[List[int]]) -> int:
        # returns 1 if we win, -1 if opponent wins, 0 otherwise
        for i in range(3):
            s = board_state[i][0] + board_state[i][1] + board_state[i][2]
            if s == 3: return 1
            if s == -3: return -1
        for j in range(3):
            s = board_state[0][j] + board_state[1][j] + board_state[2][j]
            if s == 3: return 1
            if s == -3: return -1
        s = board_state[0][0] + board_state[1][1] + board_state[2][2]
        if s == 3: return 1
        if s == -3: return -1
        s = board_state[0][2] + board_state[1][1] + board_state[2][0]
        if s == 3: return 1
        if s == -3: return -1
        return 0

    def legal_moves(board_state: List[List[int]]) -> List[Tuple[int, int]]:
        return [(i, j) for i in range(3) for j in range(3) if board_state[i][j] == 0]

    def pref_index(move: Optional[Tuple[int, int]]) -> int:
        if move is None:
            return len(pref)
        return rank.get(move, len(pref))

    def minimax(board_state: List[List[int]], turn: int, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[Tuple[int, int]]]:
        """
        Returns (score, move) where score is higher-is-better for us (1).
        Uses depth to prefer quicker wins / slower losses.
        turn: 1 for us (maximizer), -1 for opponent (minimizer)
        """
        w = winner(board_state)
        if w != 0:
            # Larger magnitude for quicker wins; positive for our win, negative for opponent win
            return (100 - depth) * w, None
        moves = legal_moves(board_state)
        if not moves:
            return 0, None  # draw

        best_move: Optional[Tuple[int, int]] = None
        if turn == 1:
            best_score = -10_000
            for mv in moves:
                i, j = mv
                board_state[i][j] = turn
                score, _ = minimax(board_state, -turn, depth + 1, alpha, beta)
                board_state[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = mv
                elif score == best_score:
                    # tie-break by preference order
                    if pref_index(mv) < pref_index(best_move):
                        best_move = mv
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            best_score = 10_000
            for mv in moves:
                i, j = mv
                board_state[i][j] = turn
                score, _ = minimax(board_state, -turn, depth + 1, alpha, beta)
                board_state[i][j] = 0
                if score < best_score:
                    best_score = score
                    best_move = mv
                elif score == best_score:
                    # for opponent minimizing, prefer moves with worse preference for us (not necessary, keep stable)
                    if pref_index(mv) < pref_index(best_move):
                        best_move = mv
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move

    score, move = minimax(b, 1, 0, -100000, 100000)
    if move is None:
        # Either terminal or no moves; return first empty if possible, else (0,0)
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    return (i, j)
        return (0, 0)
    return move

# For simple local testing (not executed in the arena), you could do:
# if __name__ == "__main__":
#     print(policy([[0,0,0],[0,0,0],[0,0,0]]))
