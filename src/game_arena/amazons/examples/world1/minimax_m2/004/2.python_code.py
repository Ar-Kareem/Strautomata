
# Amazons policy for a 6x6 board.
# Implements a greedy one‑ply search with mobility‑difference evaluation.
# Returns a move string formatted as: "from_r,from_col:to_r,to_col:arrow_r,arrow_col"

import numpy as np
import random

# ----------------------------------------------------------------------
# Global constants
N = 6  # board dimension
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1)]

# ----------------------------------------------------------------------
def queen_reachable(board: np.ndarray, r: int, c: int):
    """
    Yield all empty squares that a queen‑like piece on (r,c) can reach,
    moving any number of steps in the 8 orthogonal/diagonal directions
    without crossing any non‑empty square.
    """
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc

# ----------------------------------------------------------------------
def count_moves(board: np.ndarray, player: int) -> int:
    """
    Count the total number of legal moves (move + arrow) the side `player`
    (1 = our amazons, 2 = opponent) has on `board`.
    """
    cnt = 0
    # Iterate over all amazons of the player
    for r, c in np.argwhere(board == player):
        # For each possible move destination
        for nr, nc in queen_reachable(board, r, c):
            # Simulate the move (no arrow yet)
            new_board = board.copy()
            new_board[r, c] = 0
            new_board[nr, nc] = player
            # Count every possible arrow target from the destination
            for ar, ac in queen_reachable(new_board, nr, nc):
                cnt += 1
    return cnt

# ----------------------------------------------------------------------
def policy(board: np.ndarray) -> str:
    """
    Main entry point – receives a 6x6 numpy array describing the board.
    Returns a legal move string for the player whose amazons are marked with `1`.
    """
    # Player identifiers
    ME = 1
    OPP = 2

    # Gather our amazons
    my_positions = np.argwhere(board == ME)
    best_move = None
    best_score = -float('inf')

    # Random jitter to break ties
    random_jitter = random.random() * 1e-6

    # ------------------------------------------------------------------
    # Explore all possible moves
    for from_r, from_c in my_positions:
        # All squares we can move the amazon to
        for to_r, to_c in queen_reachable(board, from_r, from_c):
            # Board after the amazon has been moved (before arrow)
            board_after_move = board.copy()
            board_after_move[from_r, from_c] = 0
            board_after_move[to_r, to_c] = ME

            # All possible arrow landing squares
            for ar, ac in queen_reachable(board_after_move, to_r, to_c):
                # Final board after arrow placement
                board_after_arrow = board_after_move.copy()
                board_after_arrow[ar, ac] = -1

                # Quick winning check: opponent has no moves
                opp_moves = count_moves(board_after_arrow, OPP)
                if opp_moves == 0:
                    # Immediate win – return immediately
                    return f"{from_r},{from_c}:{to_r},{to_c}:{ar},{ac}"

                # Compute mobility difference as heuristic
                my_moves = count_moves(board_after_arrow, ME)
                score = my_moves - opp_moves + random_jitter

                if score > best_score:
                    best_score = score
                    best_move = (from_r, from_c, to_r, to_c, ar, ac)

    # ------------------------------------------------------------------
    # In theory we should always have found at least one move.
    if best_move is None:
        # Fallback: pick the first legal move (should never happen)
        # Find any legal move without further evaluation
        for from_r, from_c in my_positions:
            for to_r, to_c in queen_reachable(board, from_r, from_c):
                board_after_move = board.copy()
                board_after_move[from_r, from_c] = 0
                board_after_move[to_r, to_c] = ME
                for ar, ac in queen_reachable(board_after_move, to_r, to_c):
                    return f"{from_r},{from_c}:{to_r},{to_c}:{ar},{ac}"

    # Return the chosen move formatted as required
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
