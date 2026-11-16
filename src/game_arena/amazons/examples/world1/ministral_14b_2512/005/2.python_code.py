
import numpy as np
from typing import List, Tuple, Optional

def policy(board: np.ndarray) -> str:
    """
    Policy for Amazons on a 6x6 board.
    Uses a combination of threat assessment, mobility, and central control.
    """
    # Find all legal moves
    legal_moves = generate_legal_moves(board)

    if not legal_moves:
        raise ValueError("No legal moves available (should not happen per problem statement)")

    # Evaluate moves using a combination of threat assessment and mobility
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def generate_legal_moves(board: np.ndarray) -> List[str]:
    """Generate all legal moves for the current board state."""
    legal_moves = []
    my_amazons = np.argwhere(board == 1)

    for (from_row, from_col) in my_amazons:
        # Generate all possible to positions
        to_positions = get_reachable_squares(board, from_row, from_col, 1)
        for (to_row, to_col) in to_positions:
            # Generate all possible arrow positions after moving to (to_row, to_col)
            temp_board = board.copy()
            temp_board[from_row, from_col] = 0
            temp_board[to_row, to_col] = 1
            arrow_positions = get_reachable_squares(temp_board, to_row, to_col, -1)
            for (arrow_row, arrow_col) in arrow_positions:
                legal_moves.append(f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}")

    return legal_moves

def get_reachable_squares(board: np.ndarray, row: int, col: int, value: int) -> List[Tuple[int, int]]:
    """Get all squares reachable from (row, col) in a straight line (queen-like)."""
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]
    reachable = []

    for dr, dc in directions:
        for step in range(1, 6):
            new_row, new_col = row + dr * step, col + dc * step
            if 0 <= new_row < 6 and 0 <= new_col < 6:
                if board[new_row, new_col] != 0:
                    break  # blocked
                reachable.append((new_row, new_col))
            else:
                break  # out of bounds

    return reachable

def evaluate_move(board: np.ndarray, move: str) -> float:
    """Evaluate a move using a combination of threat assessment and mobility."""
    from_row, from_col, to_row, to_col, arrow_row, arrow_col = parse_move(move)

    # Simulate the move
    temp_board = board.copy()
    temp_board[from_row, from_col] = 0
    temp_board[to_row, to_col] = 1
    temp_board[arrow_row, arrow_col] = -1

    # Evaluate the new board state
    my_mobility = count_mobility(temp_board, 1)
    opp_mobility = count_mobility(temp_board, 2)

    # Threat assessment: check if the opponent is in danger of being blocked
    threat_score = assess_threats(temp_board, 1, 2)  # my amazons vs opponent amazons
    opp_threat_score = assess_threats(temp_board, 2, 1)  # opponent amazons vs my amazons

    # Central control bonus
    center_control = (abs(to_row - 2.5) + abs(to_col - 2.5))  # prefer center
    center_control = 1.0 / (1.0 + center_control)  # higher for center

    # Arrow control: does the arrow block opponent's mobility?
    arrow_block = 0.0
    if temp_board[arrow_row, arrow_col] == -1:
        # Check if the arrow blocks opponent's potential moves
        opp_amazons = np.argwhere(temp_board == 2)
        for (opp_row, opp_col) in opp_amazons:
            reachable = get_reachable_squares(temp_board, opp_row, opp_col, 2)
            if (arrow_row, arrow_col) in reachable:
                arrow_block += 1.0

    # Combine scores
    score = (
        my_mobility * 0.5 +
        (my_mobility - opp_mobility) * 0.3 +
        threat_score * 0.4 +
        center_control * 0.2 +
        arrow_block * 0.1
    )

    return score

def count_mobility(board: np.ndarray, player: int) -> int:
    """Count the number of legal moves for a player."""
    count = 0
    amazons = np.argwhere(board == player)

    for (row, col) in amazons:
        to_positions = get_reachable_squares(board, row, col, player)
        for (to_row, to_col) in to_positions:
            temp_board = board.copy()
            temp_board[row, col] = 0
            temp_board[to_row, to_col] = player
            arrow_positions = get_reachable_squares(temp_board, to_row, to_col, -1)
            count += len(arrow_positions)

    return count

def assess_threats(board: np.ndarray, attacker: int, defender: int) -> float:
    """Assess if the attacker can threaten the defender's amazons."""
    threat_score = 0.0
    attacker_amazons = np.argwhere(board == attacker)

    for (attacker_row, attacker_col) in attacker_amazons:
        reachable = get_reachable_squares(board, attacker_row, attacker_col, attacker)
        defender_amazons = np.argwhere(board == defender)

        for (defender_row, defender_col) in defender_amazons:
            # Check if the defender is in line with the attacker and can be blocked
            if is_in_line(attacker_row, attacker_col, defender_row, defender_col):
                # Check if there's a square between them that can be blocked
                path = get_path(attacker_row, attacker_col, defender_row, defender_col)
                for (block_row, block_col) in path:
                    if board[block_row, block_col] == 0:
                        threat_score += 1.0  # potential to block

    return threat_score

def is_in_line(row1: int, col1: int, row2: int, col2: int) -> bool:
    """Check if two squares are in a straight line (queen-like)."""
    dr = row2 - row1
    dc = col2 - col1
    return abs(dr) == abs(dc) or dr == 0 or dc == 0

def get_path(row1: int, col1: int, row2: int, col2: int) -> List[Tuple[int, int]]:
    """Get the path between two squares (excluding endpoints)."""
    path = []
    dr = row2 - row1
    dc = col2 - col1
    steps = max(abs(dr), abs(dc))

    for step in range(1, steps):
        new_row = row1 + dr * step // steps
        new_col = col1 + dc * step // steps
        path.append((new_row, new_col))

    return path

def parse_move(move: str) -> Tuple[int, int, int, int, int, int]:
    """Parse a move string into coordinates."""
    parts = move.split(':')
    from_part, to_part, arrow_part = parts
    from_row, from_col = map(int, from_part.split(','))
    to_row, to_col = map(int, to_part.split(','))
    arrow_row, arrow_col = map(int, arrow_part.split(','))
    return from_row, from_col, to_row, to_col, arrow_row, arrow_col
