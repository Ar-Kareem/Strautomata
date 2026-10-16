
import numpy as np
from collections import defaultdict

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Convert sets to lists for easier manipulation
    my_men = [tuple(pos) for pos in my_men]
    my_kings = [tuple(pos) for pos in my_kings]
    opp_men = [tuple(pos) for pos in opp_men]
    opp_kings = [tuple(pos) for pos in opp_kings]

    # Get all possible moves
    moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)

    # If no moves available, return None (indicates game over)
    if not moves:
        return None

    # Choose the best move based on our evaluation function
    best_move = None
    best_score = float('-inf')

    for move in moves:
        # Make the move
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = make_move(
            my_men, my_kings, opp_men, opp_kings, move, color)

        # Evaluate the resulting position
        score = evaluate_position(new_my_men, new_my_kings, new_opp_men, new_opp_kings, color)

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def get_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    moves = []
    occupied = set(my_men + my_kings + opp_men + opp_kings)

    # Check for captures first (captures are mandatory)
    for piece in my_men + my_kings:
        piece_moves = get_piece_moves(piece, my_men, my_kings, opp_men, opp_kings, color, occupied)
        for move in piece_moves:
            if is_capture(move):
                moves.append(move)

    # If no captures, get all regular moves
    if not moves:
        for piece in my_men + my_kings:
            piece_moves = get_piece_moves(piece, my_men, my_kings, opp_men, opp_kings, color, occupied)
            moves.extend(piece_moves)

    return moves

def get_piece_moves(piece, my_men, my_kings, opp_men, opp_kings, color, occupied):
    moves = []
    row, col = piece

    # Determine if this is a king
    is_king = piece in my_kings

    # Define possible directions
    directions = []
    if color == 'b' or is_king:
        directions.extend([(-1, -1), (-1, 1)])  # Move up-left and up-right
    if color == 'w' or is_king:
        directions.extend([(1, -1), (1, 1)])    # Move down-left and down-right

    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc

        # Check if the square is within bounds and empty
        if 0 <= new_row < 8 and 0 <= new_col < 8 and (new_row, new_col) not in occupied:
            moves.append((piece, (new_row, new_col)))

        # Check for captures
        elif 0 <= new_row < 8 and 0 <= new_col < 8:
            # Check if there's an opponent piece to capture
            if (new_row, new_col) in opp_men or (new_row, new_col) in opp_kings:
                jump_row, jump_col = new_row + dr, new_col + dc
                if 0 <= jump_row < 8 and 0 <= jump_col < 8 and (jump_row, jump_col) not in occupied:
                    moves.append((piece, (jump_row, jump_col)))

    return moves

def is_capture(move):
    from_pos, to_pos = move
    return abs(from_pos[0] - to_pos[0]) == 2

def make_move(my_men, my_kings, opp_men, opp_kings, move, color):
    from_pos, to_pos = move
    new_my_men = my_men[:]
    new_my_kings = my_kings[:]
    new_opp_men = opp_men[:]
    new_opp_kings = opp_kings[:]

    # Remove the moved piece from its original position
    if from_pos in new_my_men:
        new_my_men.remove(from_pos)
    elif from_pos in new_my_kings:
        new_my_kings.remove(from_pos)

    # Check for captures
    if is_capture(move):
        mid_pos = ((from_pos[0] + to_pos[0]) // 2, (from_pos[1] + to_pos[1]) // 2)
        if mid_pos in new_opp_men:
            new_opp_men.remove(mid_pos)
        elif mid_pos in new_opp_kings:
            new_opp_kings.remove(mid_pos)

    # Add the piece to its new position
    if to_pos[0] == 0 and color == 'b':
        new_my_kings.append(to_pos)
    elif to_pos[0] == 7 and color == 'w':
        new_my_kings.append(to_pos)
    else:
        if from_pos in my_kings:
            new_my_kings.append(to_pos)
        else:
            new_my_men.append(to_pos)

    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

def evaluate_position(my_men, my_kings, opp_men, opp_kings, color):
    score = 0

    # Piece values
    man_value = 1
    king_value = 1.5

    # Count pieces
    my_piece_count = len(my_men) + len(my_kings)
    opp_piece_count = len(opp_men) + len(opp_kings)

    # Calculate score based on piece count
    score += my_piece_count * man_value
    score += len(my_kings) * king_value
    score -= opp_piece_count * man_value
    score -= len(opp_kings) * king_value

    # Add bonus for kings
    score += len(my_kings) * 0.5
    score -= len(opp_kings) * 0.5

    # Add positional bonus for being closer to promotion
    for row, col in my_men:
        if color == 'b':
            score += (7 - row) * 0.1
        else:
            score += row * 0.1

    for row, col in opp_men:
        if color == 'b':
            score -= row * 0.1
        else:
            score -= (7 - row) * 0.1

    return score
