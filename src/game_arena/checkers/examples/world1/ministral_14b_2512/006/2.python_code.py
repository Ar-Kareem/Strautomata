
import numpy as np
from collections import deque

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine direction based on color
    direction = 1 if color == 'w' else -1
    opponent_direction = -direction

    # Combine all pieces for easier access
    my_pieces = my_men + my_kings
    opp_pieces = opp_men + opp_kings

    # Check for captures first (mandatory)
    captures = find_captures(my_pieces, opp_pieces, direction, opponent_direction)
    if captures:
        # Evaluate captures and choose the best one
        best_capture = evaluate_captures(captures, my_pieces, opp_pieces, direction, opponent_direction)
        return best_capture

    # If no captures, make a non-capture move
    best_move = None
    best_score = -float('inf')

    # Generate all possible non-capture moves
    for piece in my_pieces:
        for move in generate_non_capture_moves(piece, my_pieces, direction):
            score = evaluate_move(move, my_pieces, opp_pieces, direction, opponent_direction)
            if score > best_score:
                best_score = score
                best_move = move

    # If no moves found (shouldn't happen in valid positions), return a dummy move
    if best_move is None:
        return ((0, 0), (0, 0))  # This is a fallback and should not occur in practice

    return best_move

def find_captures(my_pieces, opp_pieces, direction, opponent_direction):
    captures = []
    for piece in my_pieces:
        row, col = piece
        # Check diagonal captures
        for dr, dc in [(direction, direction), (direction, -direction)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                # Check if the jump lands on an opponent's piece
                if (new_row, new_col) in opp_pieces:
                    # Check if the landing square is empty (after capture)
                    landing_row, landing_col = row + 2 * dr, col + 2 * dc
                    if 0 <= landing_row < 8 and 0 <= landing_col < 8:
                        if (landing_row, landing_col) not in my_pieces and (landing_row, landing_col) not in opp_pieces:
                            captures.append(((row, col), (landing_row, landing_col)))
    return captures

def evaluate_captures(captures, my_pieces, opp_pieces, direction, opponent_direction):
    best_capture = None
    best_score = -float('inf')

    for capture in captures:
        from_row, from_col = capture[0]
        to_row, to_col = capture[1]
        # Check if the capturing piece is a king or man
        is_king = (from_row, from_col) in my_kings
        # Check if the captured piece is a king or man
        captured_piece = None
        for piece in opp_pieces:
            if piece == (from_row + direction, from_col + direction) or piece == (from_row + direction, from_col - direction):
                captured_piece = piece
                break
        is_captured_king = captured_piece in opp_kings

        # Score the capture
        score = 0
        # Prefer capturing kings
        if is_captured_king:
            score += 2
        else:
            score += 1
        # Prefer moving kings
        if is_king:
            score += 1
        # Prefer captures that leave the opponent with fewer moves
        # Simulate the capture and count opponent's moves
        temp_my_pieces = my_pieces.copy()
        temp_opp_pieces = opp_pieces.copy()
        # Remove captured piece
        temp_opp_pieces.remove(captured_piece)
        # Remove capturing piece from original position
        temp_my_pieces.remove((from_row, from_col))
        # Add capturing piece to new position
        temp_my_pieces.append((to_row, to_col))
        # Count opponent's possible captures after this move
        opp_captures = find_captures(temp_opp_pieces, temp_my_pieces, opponent_direction, direction)
        if not opp_captures:
            score += 1  # Opponent has no captures after this move
        # Prefer captures that open the opponent's back rank
        if (to_row == 0 and color == 'w') or (to_row == 7 and color == 'b'):
            score += 1

        if score > best_score:
            best_score = score
            best_capture = capture

    return best_capture

def generate_non_capture_moves(piece, my_pieces, direction):
    moves = []
    row, col = piece
    # Check diagonal moves
    for dr, dc in [(direction, direction), (direction, -direction)]:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if (new_row, new_col) not in my_pieces:
                moves.append(((row, col), (new_row, new_col)))
    return moves

def evaluate_move(move, my_pieces, opp_pieces, direction, opponent_direction):
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    # Check if the moving piece is a king or man
    is_king = (from_row, from_col) in my_kings
    # Score based on piece type
    score = 0
    if is_king:
        score += 1
    # Score based on position (closer to opponent's back rank is better)
    if color == 'w':
        score += (8 - to_row)  # White wants to reach row 7
    else:
        score += to_row  # Black wants to reach row 0
    # Score based on mobility (pieces with more moves are better)
    mobility_score = 0
    for piece in my_pieces:
        if piece == (from_row, from_col):
            mobility_score += len(generate_non_capture_moves(piece, my_pieces, direction))
    score += mobility_score * 0.1
    # Score based on blocking opponent's pieces
    # Check if the move blocks opponent's potential captures
    blocked = False
    for opp_piece in opp_pieces:
        opp_row, opp_col = opp_piece
        for dr, dc in [(-opponent_direction, opponent_direction), (-opponent_direction, -opponent_direction)]:
            new_row, new_col = opp_row + dr, opp_col + dc
            if (new_row, new_col) == (to_row, to_col):
                blocked = True
                break
    if blocked:
        score += 1
    return score
