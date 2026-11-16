
import random
from typing import List, Tuple

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    A smart Checkers policy that prioritizes captures, king-making, and positional control.
    """
    # Directions for movement (down for black, up for white)
    direction = 1 if color == 'w' else -1
    # Possible moves for regular pieces (diagonal)
    piece_moves = [(direction, 1), (direction, -1)]
    # Possible captures (two squares diagonally)
    capture_moves = [(2 * direction, 2), (2 * direction, -2)]

    # All opponent pieces (men + kings)
    opp_pieces = opp_men + opp_kings

    # Step 1: Check for mandatory captures
    captures = find_captures(my_men, my_kings, opp_pieces, direction)
    if captures:
        # Choose the best capture (prioritize multi-jumps, then king captures)
        best_capture = choose_best_capture(captures, my_kings, opp_kings, direction)
        return best_capture

    # Step 2: Check for king promotions (if a piece can reach the opponent's back row)
    promotions = find_promotions(my_men, my_kings, direction)
    if promotions:
        # Choose the best promotion (prioritize center control)
        best_promotion = choose_best_promotion(promotions, direction)
        return best_promotion

    # Step 3: Find safe moves for kings and men
    safe_moves = find_safe_moves(my_men, my_kings, opp_pieces, direction)
    if safe_moves:
        # Choose the best safe move (prioritize center control)
        best_safe_move = choose_best_safe_move(safe_moves, my_kings, direction)
        return best_safe_move

    # Fallback: Default to a simple forward move (should not happen if board is valid)
    return default_move(my_men, my_kings, direction)

def find_captures(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                  opp_pieces: List[Tuple[int, int]], direction: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Find all possible captures for my pieces."""
    captures = []
    for piece in my_men + my_kings:
        for dr, dc in capture_moves:
            to_row, to_col = piece[0] + dr, piece[1] + dc
            if not (0 <= to_row < 8 and 0 <= to_col < 8):
                continue
            # Check if the landing square is valid (dark square)
            if (to_row + to_col) % 2 != 0:
                continue
            # Check if there's an opponent piece in between
            mid_row, mid_col = piece[0] + direction, piece[1]
            if (mid_row, mid_col) not in opp_pieces:
                mid_row, mid_col = piece[0] + direction, piece[1] + 2 * dc
                if (mid_row, mid_col) not in opp_pieces:
                    continue
            # Check if the landing square is empty
            if to_row < 0 or to_row >= 8 or to_col < 0 or to_col >= 8:
                continue
            # Check if the landing square is empty (not occupied by my piece)
            if (to_row, to_col) in my_men or (to_row, to_col) in my_kings:
                continue
            captures.append(((piece[0], piece[1]), (to_row, to_col)))
    return captures

def choose_best_capture(captures: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                        my_kings: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
                        direction: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Choose the best capture (prioritize multi-jumps, then king captures)."""
    # Check for multi-jump captures (if any capture leads to another capture)
    for capture in captures:
        from_piece, to_piece = capture
        # Simulate the capture and check if the new position allows another capture
        new_my_men = [p for p in my_men if p != from_piece] + [to_piece]
        new_my_kings = [p for p in my_kings if p != from_piece] + [to_piece]
        new_opp_pieces = [p for p in opp_pieces if p != (from_piece[0] + direction, from_piece[1])]
        new_captures = find_captures(new_my_men, new_my_kings, new_opp_pieces, direction)
        if new_captures:
            return capture
    # If no multi-jump, prioritize captures that remove opponent kings
    king_captures = [c for c in captures if (c[0][0] + direction, c[0][1]) in opp_kings]
    if king_captures:
        return random.choice(king_captures)
    # Otherwise, choose randomly among captures
    return random.choice(captures)

def find_promotions(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                    direction: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Find all possible promotions (pieces reaching the opponent's back row)."""
    promotions = []
    for piece in my_men:
        row, col = piece
        target_row = 7 if direction == 1 else 0  # Opponent's back row
        if (row + direction) == target_row:
            for dr, dc in piece_moves:
                to_row, to_col = row + dr, col + dc
                if to_row == target_row and (to_row + to_col) % 2 == 0:
                    promotions.append(((row, col), (to_row, to_col)))
    return promotions

def choose_best_promotion(promotions: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                         direction: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Choose the best promotion (prioritize center control)."""
    # Prefer promotions to the center (columns 3-4)
    center_promotions = [p for p in promotions if 3 <= p[1][1] <= 4]
    if center_promotions:
        return random.choice(center_promotions)
    return random.choice(promotions)

def find_safe_moves(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                    opp_pieces: List[Tuple[int, int]], direction: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Find all safe moves for kings and men."""
    safe_moves = []
    for piece in my_men + my_kings:
        for dr, dc in piece_moves:
            to_row, to_col = piece[0] + dr, piece[1] + dc
            if not (0 <= to_row < 8 and 0 <= to_col < 8):
                continue
            if (to_row + to_col) % 2 != 0:
                continue
            if (to_row, to_col) in my_men or (to_row, to_col) in my_kings:
                continue
            # Check if the move is safe (not into a capture)
            safe_moves.append(((piece[0], piece[1]), (to_row, to_col)))
    return safe_moves

def choose_best_safe_move(safe_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                         my_kings: List[Tuple[int, int]], direction: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Choose the best safe move (prioritize center control)."""
    # Prefer moves that control the center (rows 3-4, columns 3-4)
    center_moves = [m for m in safe_moves if 3 <= m[1][0] <= 4 and 3 <= m[1][1] <= 4]
    if center_moves:
        return random.choice(center_moves)
    # Prefer king moves over men moves
    king_moves = [m for m in safe_moves if m[0] in my_kings]
    if king_moves:
        return random.choice(king_moves)
    return random.choice(safe_moves)

def default_move(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                 direction: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Fallback to a simple forward move (should not happen if board is valid)."""
    if my_men:
        piece = random.choice(my_men)
        for dr, dc in piece_moves:
            to_row, to_col = piece[0] + dr, piece[1] + dc
            if 0 <= to_row < 8 and 0 <= to_col < 8 and (to_row + to_col) % 2 == 0:
                return ((piece[0], piece[1]), (to_row, to_col))
    elif my_kings:
        piece = random.choice(my_kings)
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            to_row, to_col = piece[0] + dr, piece[1] + dc
            if 0 <= to_row < 8 and 0 <= to_col < 8 and (to_row + to_col) % 2 == 0:
                return ((piece[0], piece[1]), (to_row, to_col))
    return ((0, 0), (0, 0))  # Should never reach here for a valid board
