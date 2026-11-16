
import numpy as np
from typing import List, Tuple

def policy(board: np.ndarray) -> str:
    """
    Heuristic-based policy for Amazons on a 6x6 board.
    Priorities:
    1. Capture opponent amazon (move to square attacking it).
    2. Move toward center (2,2)-(3,3) to control space.
    3. Shoot arrows to block opponent or open own paths.
    4. Avoid self-blocking.
    """
    # Directions: queen-like (8 possible)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    # Find all our amazons (1)
    our_amazons = np.argwhere(board == 1)
    if len(our_amazons) == 0:
        raise ValueError("No amazons to move!")

    # Find all opponent amazons (2)
    opponent_amazons = np.argwhere(board == 2)
    if len(opponent_amazons) == 0:
        raise ValueError("No opponent amazons left!")

    # Generate all legal moves
    legal_moves = []
    for from_pos in our_amazons:
        from_row, from_col = from_pos
        for to_row in range(6):
            for to_col in range(6):
                if board[to_row, to_col] != 0:
                    continue  # target must be empty
                # Check if path from (from_row, from_col) to (to_row, to_col) is valid
                if not is_valid_path(board, from_row, from_col, to_row, to_col):
                    continue
                # Now check all possible arrow directions from (to_row, to_col)
                for d_row, d_col in directions:
                    arrow_row, arrow_col = to_row + d_row, to_col + d_col
                    # Arrow must be within bounds and not occupied (after move)
                    if 0 <= arrow_row < 6 and 0 <= arrow_col < 6:
                        # Simulate the move and check if arrow is valid
                        temp_board = board.copy()
                        temp_board[from_row, from_col] = 0  # amazon moved
                        temp_board[to_row, to_col] = 1  # amazon landed
                        if temp_board[arrow_row, arrow_col] == 0:  # arrow target empty
                            if is_valid_arrow_path(temp_board, to_row, to_col, arrow_row, arrow_col):
                                legal_moves.append((from_row, from_col, to_row, to_col, arrow_row, arrow_col))

    if not legal_moves:
        raise ValueError("No legal moves found!")

    # Evaluate moves based on heuristics
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        from_row, from_col, to_row, to_col, arrow_row, arrow_col = move
        score = evaluate_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is None:
        # Fallback: pick first legal move (should not happen if legal_moves is non-empty)
        best_move = legal_moves[0]

    from_row, from_col, to_row, to_col, arrow_row, arrow_col = best_move
    return f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"

def is_valid_path(board: np.ndarray, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
    """Check if the path from (from_row, from_col) to (to_row, to_col) is unobstructed."""
    if from_row == to_row and from_col == to_col:
        return False  # cannot move to same square

    row_step = 0 if from_row == to_row else (1 if to_row > from_row else -1)
    col_step = 0 if from_col == to_col else (1 if to_col > from_col else -1)

    # If moving diagonally, steps must be equal
    if row_step != 0 and col_step != 0:
        if abs(to_row - from_row) != abs(to_col - from_col):
            return False

    # Check path
    row, col = from_row + row_step, from_col + col_step
    while row != to_row or col != to_col:
        if board[row, col] != 0:
            return False  # path blocked
        row += row_step
        col += col_step
    return True

def is_valid_arrow_path(board: np.ndarray, to_row: int, to_col: int, arrow_row: int, arrow_col: int) -> bool:
    """Check if arrow path from (to_row, to_col) to (arrow_row, arrow_col) is valid after move."""
    if to_row == arrow_row and to_col == arrow_col:
        return False  # cannot shoot to same square

    # Simulate amazon at (to_row, to_col) and no amazon at (from_row, from_col)
    # (Note: board is already updated for this case in policy())
    row_step = 0 if to_row == arrow_row else (1 if arrow_row > to_row else -1)
    col_step = 0 if to_col == arrow_col else (1 if arrow_col > to_col else -1)

    if row_step != 0 and col_step != 0:
        if abs(arrow_row - to_row) != abs(arrow_col - to_col):
            return False

    row, col = to_row + row_step, to_col + col_step
    while row != arrow_row or col != arrow_col:
        if board[row, col] != 0 and board[row, col] != -1:
            return False  # path blocked (by amazon or arrow)
        row += row_step
        col += col_step
    return True

def evaluate_move(board: np.ndarray, from_row: int, from_col: int, to_row: int, to_col: int,
                arrow_row: int, arrow_col: int) -> float:
    """
    Evaluate a move based on heuristics:
    1. Capture opponent amazon (highest score).
    2. Move toward center (moderate score).
    3. Arrow blocks opponent or opens own paths (bonus).
    4. Avoid self-blocking (penalty).
    """
    score = 0.0

    # Check if this move captures an opponent amazon
    if board[arrow_row, arrow_col] == 2:
        score += 100.0  # capture is highest priority

    # Move toward center (2,2)-(3,3) is preferred
    center_distance = np.abs(np.array([to_row, to_col]) - np.array([2.5, 2.5])).sum()
    score += 10.0 / center_distance  # higher score for moves closer to center

    # Arrow blocks opponent amazons (bonus)
    opponent_amazons = np.argwhere(board == 2)
    for opp_row, opp_col in opponent_amazons:
        if is_attacked(board, arrow_row, arrow_col, opp_row, opp_col):
            score += 5.0  # arrow blocks opponent amazon

    # Avoid self-blocking (penalty)
    our_amazons = np.argwhere(board == 1)
    for our_row, our_col in our_amazons:
        if is_attacked(board, our_row, our_col, arrow_row, arrow_col):
            score -= 3.0  # arrow blocks our own amazon

    # Prefer moves that don't leave our amazons in vulnerable positions
    # (e.g., where they can be easily attacked by opponent arrows)
    if board[to_row, to_col] == 1:  # redundant, but just in case
        # Count how many opponent arrows can attack this amazon
        opponent_arrows = np.argwhere(board == -1)
        for arrow_r, arrow_c in opponent_arrows:
            if is_attacked(board, to_row, to_col, arrow_r, arrow_c):
                score -= 1.0

    return score

def is_attacked(board: np.ndarray, row: int, col: int, attacker_row: int, attacker_col: int) -> bool:
    """Check if (row, col) is attacked by (attacker_row, attacker_col) (queen-like)."""
    if row == attacker_row and col == attacker_col:
        return False

    row_step = 0 if row == attacker_row else (1 if attacker_row > row else -1)
    col_step = 0 if col == attacker_col else (1 if attacker_col > col else -1)

    if row_step != 0 and col_step != 0:
        if abs(attacker_row - row) != abs(attacker_col - col):
            return False

    # Check path (ignoring arrows, since they are already placed)
    temp_row, temp_col = row + row_step, col + col_step
    while temp_row != attacker_row or temp_col != attacker_col:
        if board[temp_row, temp_col] != 0:
            return False  # path blocked
        temp_row += row_step
        temp_col += col_step
    return True

# Example usage (not part of the policy):
if __name__ == "__main__":
    # Test board: simple case
    test_board = np.array([
        [0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, 0],
        [0, 0, 0, 0, 0, 0]
    ])
    print(policy(test_board))  # Expected: capture move like "1,1:4,4:4,4"
