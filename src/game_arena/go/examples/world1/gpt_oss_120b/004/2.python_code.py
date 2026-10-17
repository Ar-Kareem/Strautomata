
import random
from collections import deque
from typing import List, Tuple, Set

BOARD_SIZE = 19

# Directions: up, down, left, right
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def _in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def _neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    return [(r + dr, c + dc) for dr, dc in DIRS if _in_bounds(r + dr, c + dc)]

def _group_and_liberties(board: List[List[int]], start: Tuple[int, int]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    """Return the set of stones in the connected group containing start
    and the set of its liberties."""
    color = board[start[0] - 1][start[1] - 1]
    visited = set()
    liberties = set()
    q = deque([start])
    while q:
        r, c = q.popleft()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        for nr, nc in _neighbors(r, c):
            val = board[nr - 1][nc - 1]
            if val == 0:
                liberties.add((nr, nc))
            elif val == color and (nr, nc) not in visited:
                q.append((nr, nc))
    return visited, liberties

def _remove_group(board: List[List[int]], group: Set[Tuple[int, int]]):
    for r, c in group:
        board[r - 1][c - 1] = 0

def _apply_move(board: List[List[int]], move: Tuple[int, int], player: int) -> bool:
    """Place a stone for *player* (1 = us, 2 = opponent) at *move*.
    Returns True if the move is legal, otherwise leaves board unchanged."""
    r, c = move
    if board[r - 1][c - 1] != 0:
        return False

    # Tentatively place the stone
    board[r - 1][c - 1] = player

    opponent = 2 if player == 1 else 1
    # First, capture any opponent groups without liberties
    captured_any = False
    for nr, nc in _neighbors(r, c):
        if board[nr - 1][nc - 1] == opponent:
            group, libs = _group_and_liberties(board, (nr, nc))
            if not libs:
                _remove_group(board, group)
                captured_any = True

    # Now check our own group liberties
    group, libs = _group_and_liberties(board, (r, c))
    if libs:
        return True  # legal

    # Move is a suicide (unless it captured something)
    if captured_any:
        # Capturing move that results in zero liberties is still legal in Go.
        return True
    # Undo the move
    board[r - 1][c - 1] = 0
    return False

def _legal_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r - 1][c - 1] != 0:
                continue
            if _apply_move(board, (r, c), 1):
                # revert the temporary board changes
                # (the function already left the board in the post‑move state,
                # so we need to restore the original board)
                # We'll simply copy the board before testing in the caller.
                moves.append((r, c))
            # board will be restored by the caller (see policy implementation)
    return moves

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Return the selected move (row, col) or (0,0) to pass."""
    # Initialise board: 0 empty, 1 our stones, 2 opponent stones
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        board[r - 1][c - 1] = 1
    for r, c in opponent:
        board[r - 1][c - 1] = 2

    # Pre‑compute a simple influence score for every empty point
    best_score = float('-inf')
    best_moves = []

    # Pre‑store stone lists for faster distance computation
    my_stones = me
    opp_stones = opponent

    # If the board is empty, just play the centre.
    if not my_stones and not opp_stones:
        return (10, 10)

    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r - 1][c - 1] != 0:
                continue

            # Influence score: sum over stones of (+/-) 1 / d^2
            score = 0.0
            for mr, mc in my_stones:
                d2 = (mr - r) ** 2 + (mc - c) ** 2
                score += 1.0 / (d2 + 1)      # +1 avoids division by zero
            for orow, ocol in opp_stones:
                d2 = (orow - r) ** 2 + (ocol - c) ** 2
                score -= 1.0 / (d2 + 1)

            # Quick legality test using a copy of the board
            test_board = [row[:] for row in board]
            if not _apply_move(test_board, (r, c), 1):
                continue  # illegal move

            if score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))

    if not best_moves:
        # No legal moves found – pass.
        return (0, 0)

    # Choose randomly among equally good moves to add variety
    return random.choice(best_moves)
