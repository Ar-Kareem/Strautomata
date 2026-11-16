
from functools import lru_cache
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a move for player '1' on a 3x3 tic-tac-toe board.
    board: 3x3 list of lists with 0 (empty), 1 (us), -1 (opponent)
    returns: (row, col) with 0 <= row,col <= 2
    """

    # Flatten board to tuple of length 9 for easy hashing/caching
    flat = tuple(board[r][c] for r in range(3) for c in range(3))

    # Winning line index triples
    LINES = (
        (0,1,2), (3,4,5), (6,7,8),  # rows
        (0,3,6), (1,4,7), (2,5,8),  # cols
        (0,4,8), (2,4,6)            # diags
    )

    def winner_of(state: Tuple[int, ...]) -> int:
        for a,b,c in LINES:
            s = state[a] + state[b] + state[c]
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    # Preferred move order: center, corners, edges (deterministic)
    PREFERRED = [4, 0, 2, 6, 8, 1, 3, 5, 7]

    @lru_cache(maxsize=None)
    def minimax(state: Tuple[int, ...], player: int) -> Tuple[int, int]:
        """
        Return (score, best_move_index) from this state for 'player' to move.
        score is from perspective of player 1 (us); higher is better for us.
        """
        w = winner_of(state)
        if w != 0:
            # Terminal: someone has won
            # Use magnitude to favor quicker wins: but because cached per state,
            # depth not explicit; we will use fixed utilities.
            return (100 if w == 1 else -100, -1)

        if all(x != 0 for x in state):
            # Draw
            return (0, -1)

        # Maximizer is player 1, minimizer is -1
        if player == 1:
            best_score = -10**9
            best_move = -1
            for idx in PREFERRED:
                if state[idx] == 0:
                    lst = list(state)
                    lst[idx] = player
                    new_state = tuple(lst)
                    sc, _ = minimax(new_state, -player)
                    # sc is always from perspective of player 1.
                    if sc > best_score or (sc == best_score and best_move == -1):
                        best_score = sc
                        best_move = idx
                        # immediate win short-circuit
                        if best_score == 100:
                            break
            return (best_score, best_move)
        else:
            # opponent move: choose move that minimizes our score
            best_score = 10**9
            best_move = -1
            for idx in PREFERRED:
                if state[idx] == 0:
                    lst = list(state)
                    lst[idx] = player
                    new_state = tuple(lst)
                    sc, _ = minimax(new_state, -player)
                    if sc < best_score or (sc == best_score and best_move == -1):
                        best_score = sc
                        best_move = idx
                        if best_score == -100:
                            break
            return (best_score, best_move)

    # If board already terminal or full, just pick a valid empty cell deterministically
    w0 = winner_of(flat)
    if w0 != 0 or all(x != 0 for x in flat):
        for idx in PREFERRED:
            if flat[idx] == 0:
                return (idx // 3, idx % 3)
        return (0,0)

    # Determine whose turn it is by counts
    count_us = sum(1 for x in flat if x == 1)
    count_them = sum(1 for x in flat if x == -1)
    to_move = 1 if count_us == count_them else -1  # we move if equal counts

    # If it's opponent's turn in the given board, we should still return a legal move
    # but to be consistent, compute result as if we are to play next (i.e., assume it's our turn).
    # However, the minimax routine expects the correct to_move. We'll compute the best move for the side to move,
    # then if it's opponent to move we shouldn't play; but since the task requires returning "the row and column you choose",
    # we will compute the best move for us assuming it's our turn. This is the usual expectation.
    # So override to_move to 1 to pick our move.
    to_move_for_choice = 1

    _, move_idx = minimax(flat, to_move_for_choice)
    if move_idx == -1:
        # fallback: pick first empty
        for idx in PREFERRED:
            if flat[idx] == 0:
                move_idx = idx
                break
    return (move_idx // 3, move_idx % 3)
