
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert stone positions to a 19x19 board (1-based indexing)
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1

    # Check if opponent has a single stone with 1 liberty (capture opportunity)
    for r, c in opponent:
        if is_single_stone_with_one_liberty(board, r-1, c-1):
            return (r, c)

    # Check for ko (simplified: avoid repeating the last opponent's move)
    last_opponent_move = None
    if opponent:
        last_opponent_move = opponent[-1]
    if me and me[-1] == last_opponent_move:
        return (0, 0)  # Pass to avoid ko (simplified)

    # Evaluate influence and liberties for all possible moves
    best_move = None
    best_score = -float('inf')

    # Check all legal moves (including pass)
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0:
                continue  # Skip occupied points
            # Simulate placing a stone here
            temp_board = board.copy()
            temp_board[r, c] = 1
            # Calculate influence and liberties
            score = evaluate_move(temp_board, r, c, me, opponent)
            if score > best_score:
                best_score = score
                best_move = (r+1, c+1)  # Convert back to 1-based

    # If no good move found, pass
    if best_move is None:
        return (0, 0)

    return best_move

def evaluate_move(board: np.ndarray, r: int, c: int, me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> float:
    """Evaluates a move based on liberties, influence, and basic Go heuristics."""
    # Place the stone
    board[r, c] = 1

    # Calculate liberties for my stones and opponent's stones
    my_liberties = count_liberties(board, me)
    opp_liberties = count_liberties(board, opponent)

    # Influence score (higher near edges/corners)
    influence = calculate_influence(r, c)

    # Stone placement efficiency (prefer moves that secure liberties)
    placement_efficiency = 0
    # Check if this move reduces opponent's liberties significantly
    if r > 0 and board[r-1, c] == -1:
        placement_efficiency += 1
    if r < 18 and board[r+1, c] == -1:
        placement_efficiency += 1
    if c > 0 and board[r, c-1] == -1:
        placement_efficiency += 1
    if c < 18 and board[r, c+1] == -1:
        placement_efficiency += 1

    # Total score (weighted combination)
    total_score = (
        influence * 0.5 +
        sum(my_liberties) * 0.3 -
        sum(opp_liberties) * 0.2 +
        placement_efficiency * 0.4
    )

    # Remove the stone (undo simulation)
    board[r, c] = 0
    return total_score

def count_liberties(board: np.ndarray, stones: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    """Counts liberties for each stone in the given list."""
    liberties = {}
    for (r, c) in stones:
        if board[r, c] != 1:  # Skip if not my stone
            continue
        # Check adjacent points (including diagonals)
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue  # Skip self
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    count += 1
        liberties[(r, c)] = count
    return liberties

def calculate_influence(r: int, c: int) -> float:
    """Estimates influence of a point (higher near edges/corners)."""
    # Distance from edges (1-based)
    dist_from_edge = min(r, 18 - r, c, 18 - c)
    # Corners have highest influence
    if (r == 0 or r == 18) and (c == 0 or c == 18):
        return 10.0
    # Sides have moderate influence
    elif r == 0 or r == 18 or c == 0 or c == 18:
        return 5.0 - dist_from_edge * 0.1
    # Center has low influence
    else:
        return 2.0 - dist_from_edge * 0.2
    return max(0.0, influence_score)

def is_single_stone_with_one_liberty(board: np.ndarray, r: int, c: int) -> bool:
    """Checks if a stone is isolated and has only 1 liberty."""
    # Check if it's a single stone (no adjacent opponent stones)
    adjacent_opponent = False
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == -1:
                adjacent_opponent = True
                break
        if adjacent_opponent:
            break

    if adjacent_opponent:
        return False

    # Count liberties (only empty adjacent points)
    liberties = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                liberties += 1

    return liberties == 1
