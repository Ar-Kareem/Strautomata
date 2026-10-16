
import numpy as np
from typing import List, Tuple

def is_dark_square(row: int, col: int) -> bool:
    """Check if a square is dark (playable)."""
    return (row + col) % 2 == 1

def is_valid_square(row: int, col: int) -> bool:
    """Check if a square is within the board (0..7)."""
    return 0 <= row <= 7 and 0 <= col <= 7

def get_legal_moves(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Generate all legal moves (non-captures) for the given color.
    Kings can move any number of squares diagonally.
    """
    legal_moves = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if color == 'b' else [(1, -1), (1, 1), (-1, -1), (-1, 1)]
    king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if color == 'b' else [(1, -1), (1, 1), (-1, -1), (-1, 1)]

    # Generate moves for men
    for (r, c) in my_men:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_valid_square(nr, nc) and is_dark_square(nr, nc) and (nr, nc) not in opp_men + opp_kings:
                legal_moves.append(((r, c), (nr, nc)))

    # Generate moves for kings (can move any number of squares)
    for (r, c) in my_kings:
        for dr, dc in king_directions:
            nr, nc = r + dr, c + dc
            while is_valid_square(nr, nc) and is_dark_square(nr, nc):
                if (nr, nc) not in opp_men + opp_kings:
                    legal_moves.append(((r, c), (nr, nc)))
                nr, nc = nr + dr, nc + dc

    return legal_moves

def get_legal_captures(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
    """
    Generate all legal captures (including jumps).
    Returns a list of ((from_row, from_col), (to_row, to_col), (captured_row, captured_col)).
    Kings can capture multiple pieces in a single move.
    """
    legal_captures = []
    directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)] if color == 'b' else [(2, -2), (2, 2), (-2, -2), (-2, 2)]
    king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if color == 'b' else [(1, -1), (1, 1), (-1, -1), (-1, 1)]

    # Check for regular captures (men only)
    for (r, c) in my_men:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_valid_square(nr, nc) and is_dark_square(nr, nc) and (nr, nc) in opp_men + opp_kings:
                captured = (r + dr//2, c + dc//2)  # Middle square
                if is_valid_square(*captured) and is_dark_square(*captured):
                    legal_captures.append(((r, c), (nr, nc), captured))

    # Check for king jumps (multiple captures)
    for (r, c) in my_kings:
        for dr, dc in king_directions:
            nr, nc = r + dr, c + dc
            while is_valid_square(nr, nc) and is_dark_square(nr, nc):
                if (nr, nc) in opp_men + opp_kings:
                    captured = (r + dr, c + dc)  # Previous square (since king jumps over)
                    if is_valid_square(*captured) and is_dark_square(*captured):
                        # Check if the next square is also capturable (for multiple jumps)
                        next_nr, next_nc = nr + dr, nc + dc
                        if is_valid_square(next_nr, next_nc) and is_dark_square(next_nr, next_nc) and (next_nr, next_nc) in opp_men + opp_kings:
                            # Multiple jump: store the first jump and let the loop handle the rest
                            legal_captures.append(((r, c), (next_nr, next_nc), captured))
                            break
                        else:
                            # Single jump: add to captures
                            legal_captures.append(((r, c), (nr, nc), captured))
                            break
                r, c = nr, nc  # Move to the new position for next jump

    return legal_captures

def evaluate_capture(capture: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> float:
    """
    Evaluate the quality of a capture.
    Higher score = better capture.
    """
    (from_r, from_c), (to_r, to_c), captured = capture
    score = 0.0

    # Check if the capture is a jump (multiple squares)
    if abs(to_r - from_r) > 1:
        score += 1.0  # Bonus for jumps

    # Check if the captured piece is a king
    if captured in opp_kings:
        score += 1.5  # Bonus for capturing a king

    # Check if the destination is near the opponent's back rank (promotion potential)
    if color == 'b' and to_r == 7:
        score += 1.0
    elif color == 'w' and to_r == 0:
        score += 1.0

    # Check if the destination is central (better mobility)
    central_bonus = 1.0 - (min(abs(to_r - 3), abs(to_r - 4)) + min(abs(to_c - 3), abs(to_c - 4))) / 4.0
    score += central_bonus

    # Check if the capture blocks opponent mobility
    blocked_opp = 0
    for opp_piece in opp_men + opp_kings:
        opp_r, opp_c = opp_piece
        if color == 'b':
            if (opp_r + 1, opp_c + 1) == captured or (opp_r + 1, opp_c - 1) == captured:
                blocked_opp += 1
        else:
            if (opp_r - 1, opp_c + 1) == captured or (opp_r - 1, opp_c - 1) == captured:
                blocked_opp += 1
    score += blocked_opp * 0.5

    return score

def evaluate_move(move: Tuple[Tuple[int, int], Tuple[int, int]], my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> float:
    """
    Evaluate the quality of a non-capture move.
    Higher score = better move.
    """
    (from_r, from_c), (to_r, to_c) = move
    score = 0.0

    # Check if the move promotes a man to king
    if color == 'b' and to_r == 7 and (from_r, from_c) in my_men:
        score += 2.0  # Big bonus for king promotion
    elif color == 'w' and to_r == 0 and (from_r, from_c) in my_men:
        score += 2.0

    # Check if the move is toward the center (better mobility)
    central_bonus = 1.0 - (min(abs(to_r - 3), abs(to_r - 4)) + min(abs(to_c - 3), abs(to_c - 4))) / 4.0
    score += central_bonus

    # Check if the move improves control over opponent's pieces
    controlled_squares = 0
    for opp_piece in opp_men + opp_kings:
        opp_r, opp_c = opp_piece
        if color == 'b':
            if (opp_r + 1, opp_c + 1) == (to_r, to_c) or (opp_r + 1, opp_c - 1) == (to_r, to_c):
                controlled_squares += 1
        else:
            if (opp_r - 1, opp_c + 1) == (to_r, to_c) or (opp_r - 1, opp_c - 1) == (to_r, to_c):
                controlled_squares += 1
    score += controlled_squares * 0.3

    return score

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Main policy function.
    Returns the best move (either a capture or a regular move).
    Captures are mandatory when available.
    """
    # Step 1: Check if any captures are available (mandatory)
    captures = get_legal_captures(my_men, my_kings, opp_men, opp_kings, color)
    if captures:
        # Evaluate all captures and pick the best one
        best_capture = max(captures, key=lambda x: evaluate_capture(x, opp_men, opp_kings, color))
        return (best_capture[0], best_capture[1])  # Return the capture move

    # Step 2: No captures available, generate all legal moves
    moves = get_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        # No legal moves (shouldn't happen in normal checkers)
        return ((0, 0), (0, 0))  # Default to a safe square (disqualification risk, but unlikely)

    # Step 3: Evaluate all moves and pick the best one
    best_move = max(moves, key=lambda x: evaluate_move(x, my_men, my_kings, opp_men, opp_kings, color))

    return best_move
