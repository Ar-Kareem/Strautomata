
import numpy as np
import random
from typing import List, Tuple

# 8 queen directions
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

BOARD_SIZE = 6
SIMS_PER_MOVE = 30   # number of random playouts per candidate move


def policy(board: np.ndarray) -> str:
    """Return the best move for player 1 (value 1) as a string."""
    moves = generate_all_moves(board, player=1)
    if not moves:
        # Should never happen in the arena, but return a dummy legal move anyway.
        # Pick any empty square for a dummy move (will be illegal but never used).
        empty = tuple(map(int, np.argwhere(board == 0)[0]))
        return f"{empty[0]},{empty[1]}:{empty[0]},{empty[1]}:{empty[0]},{empty[1]}"

    best_move = None
    best_score = -1.0

    for move in moves:
        wins = 0
        for _ in range(SIMS_PER_MOVE):
            nb = apply_move(board, move, player=1)
            if random_playout(nb, next_player=2):
                wins += 1
        score = wins / SIMS_PER_MOVE
        if score > best_score:
            best_score = score
            best_move = move
            # early exit on a guaranteed win
            if best_score == 1.0:
                break

    return move_to_string(best_move)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def generate_all_moves(board: np.ndarray, player: int) -> List[Tuple[Tuple[int, int],
                                                                   Tuple[int, int],
                                                                   Tuple[int, int]]]:
    """Return list of all legal moves for the given player."""
    moves = []
    amazons = np.argwhere(board == player)
    for (fr, fc) in amazons:
        for (tr, tc) in sliding_squares(board, (fr, fc)):
            # temporary board after moving the amazon (arrow not placed yet)
            tmp = board.copy()
            tmp[fr, fc] = 0
            tmp[tr, tc] = player
            for (ar, ac) in sliding_squares(tmp, (tr, tc)):
                moves.append(((fr, fc), (tr, tc), (ar, ac)))
    return moves


def sliding_squares(board: np.ndarray, start: Tuple[int, int]) -> List[Tuple[int, int]]:
    """All reachable empty squares from start moving like a queen."""
    reachable = []
    sr, sc = start
    for dr, dc in DIRS:
        r, c = sr + dr, sc + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r, c] == 0:
            reachable.append((r, c))
            r += dr
            c += dc
    return reachable


def apply_move(board: np.ndarray,
               move: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]],
               player: int) -> np.ndarray:
    """Return a new board after applying the given move for `player`."""
    (fr, fc), (tr, tc), (ar, ac) = move
    newb = board.copy()
    newb[fr, fc] = 0          # vacate original amazon square
    newb[tr, tc] = player    # place amazon at destination
    newb[ar, ac] = -1         # arrow becomes a blocker
    return newb


def move_to_string(move: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]) -> str:
    (fr, fc), (tr, tc), (ar, ac) = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def random_playout(board: np.ndarray, next_player: int) -> bool:
    """
    Simulate a random game from the current board.
    Returns True if the original player (player 1) wins, False otherwise.
    `next_player` is the player who must move now (1 or 2).
    """
    cur = next_player
    while True:
        moves = generate_all_moves(board, cur)
        if not moves:                # current player cannot move → loses
            return cur != 1          # player 1 wins iff it is NOT his turn
        move = random.choice(moves)
        board = apply_move(board, move, cur)
        cur = 2 if cur == 1 else 1   # switch player


# ----------------------------------------------------------------------
# End of policy file
# ----------------------------------------------------------------------
