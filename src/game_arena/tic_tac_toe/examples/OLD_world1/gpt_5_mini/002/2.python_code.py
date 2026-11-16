import math
from functools import lru_cache
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the best move for player 1 on a 3x3 Tic-Tac-Toe board.
    board: 3x3 list of lists with values {0: empty, 1: us, -1: opponent}
    Returns (row, col) with 0 <= row,col <= 2.
    """

    # Helper to flatten and create an immutable key for caching
    def board_key(b):
        return tuple(b[0] + b[1] + b[2])

    # Determine winner: return 1 (we), -1 (opponent), or 0 (no winner yet)
    def winner_of_key(key):
        # key is tuple of 9 ints in row-major order
        k = key
        lines = (
            (k[0], k[1], k[2]),
            (k[3], k[4], k[5]),
            (k[6], k[7], k[8]),
            (k[0], k[3], k[6]),
            (k[1], k[4], k[7]),
            (k[2], k[5], k[8]),
            (k[0], k[4], k[8]),
            (k[2], k[4], k[6]),
        )
        for a, b, c in lines:
            s = a + b + c
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    # Count pieces and find empty squares
    flat = board[0] + board[1] + board[2]
    our_count = flat.count(1)
    opp_count = flat.count(-1)
    empties = [i for i, v in enumerate(flat) if v == 0]

    # If no empties, return any valid index (game over)
    if not empties:
        return (0, 0)

    # Decide whose turn it is. Normally this function is called when it's our turn.
    # If counts equal -> our turn (1). If our_count > opp_count -> opponent (-1).
    current_turn = 1 if our_count == opp_count else -1

    # If it's not our turn, just return a reasonable move (first prioritized empty)
    if current_turn != 1:
        # prefer center, then corners, then edges
        priorities = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        for idx in priorities:
            if flat[idx] == 0:
                return divmod(idx, 3)
        # fallback
        idx = empties[0]
        return divmod(idx, 3)

    # Preferred move ordering: center, corners, edges
    move_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]

    # Minimax with alpha-beta and memoization.
    # Score convention: larger is better for us.
    # Terminal scores incorporate depth to prefer quicker wins / delay losses.
    @lru_cache(maxsize=None)
    def minimax(key: Tuple[int, ...], turn: int) -> int:
        w = winner_of_key(key)
        filled = sum(1 for x in key if x != 0)
        if w == 1:
            # we already won
            return 100 - filled  # prefer quicker win
        if w == -1:
            return -100 + filled  # prefer to delay loss
        if filled == 9:
            return 0  # draw

        # Generate moves in preferred order
        best = -math.inf if turn == 1 else math.inf

        for idx in move_order:
            if key[idx] != 0:
                continue
            new_list = list(key)
            new_list[idx] = turn
            new_key = tuple(new_list)
            val = minimax(new_key, -turn)
            if turn == 1:
                if val > best:
                    best = val
                # alpha-beta pruning isn't strictly necessary here due to small state,
                # but we keep the structure simple without separate alpha/beta params.
                if best == 100 - (filled + 1):  # best possible immediate win
                    return best
            else:
                if val < best:
                    best = val
                if best == -100 + (filled + 1):
                    return best
        return best

    # Evaluate best move
    root_key = board_key(board)
    best_score = -math.inf
    best_move_idx = None

    # First check immediate winning moves or blocks quickly
    for idx in move_order:
        if flat[idx] != 0:
            continue
        # try move
        new = list(flat)
        new[idx] = 1
        k = tuple(new)
        if winner_of_key(k) == 1:
            return divmod(idx, 3)  # immediate win

    # Block opponent immediate win
    for idx in move_order:
        if flat[idx] != 0:
            continue
        new = list(flat)
        new[idx] = -1
        k = tuple(new)
        if winner_of_key(k) == -1:
            # placing our mark here blocks opponent's immediate win
            return divmod(idx, 3)

    # Otherwise use minimax to pick best move
    for idx in move_order:
        if flat[idx] != 0:
            continue
        new = list(flat)
        new[idx] = 1
        k = tuple(new)
        val = minimax(k, -1)
        if val > best_score:
            best_score = val
            best_move_idx = idx

    if best_move_idx is None:
        # Fallback: pick first empty
        return divmod(empties[0], 3)
    return divmod(best_move_idx, 3)