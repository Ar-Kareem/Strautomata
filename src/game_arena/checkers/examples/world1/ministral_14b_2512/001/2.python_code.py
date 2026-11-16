
import random
from collections import defaultdict

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Directions: up-left, up-right, down-left, down-right (for white/black)
    directions = {
        'w': [(-1, -1), (-1, 1)],  # White moves up (row increases)
        'b': [(1, 1), (1, -1)]     # Black moves down (row decreases)
    }
    opp_color = 'b' if color == 'w' else 'w'

    # Check if captures are available
    captures = find_all_captures(my_men, my_kings, opp_men, opp_kings, color, directions)
    if captures:
        # Evaluate captures and pick the best one
        best_capture = max(captures, key=lambda move: evaluate_capture(move, my_men, my_kings, opp_men, opp_kings, color, directions))
        return best_capture

    # No captures: find best regular move
    all_moves = find_all_regular_moves(my_men, my_kings, color, directions)
    if not all_moves:
        return None  # Should not happen per problem statement

    # Evaluate regular moves
    best_move = max(all_moves, key=lambda move: evaluate_regular_move(move, my_men, my_kings, opp_men, opp_kings, color, directions))
    return best_move

def find_all_captures(my_men, my_kings, opp_men, opp_kings, color, directions):
    captures = []
    for piece in my_men + my_kings:
        row, col = piece
        for dr, dc in directions[color]:
            # Check for single jump (capture)
            jump_row, jump_col = row + 2 * dr, col + 2 * dc
            if 0 <= jump_row < 8 and 0 <= jump_col < 8:
                # Check if the jump lands on a dark square (valid)
                if (jump_row + jump_col) % 2 == 1:
                    # Check if the square in between is an opponent piece
                    mid_row, mid_col = row + dr, col + dc
                    if (mid_row, mid_col) in opp_men or (mid_row, mid_col) in opp_kings:
                        captures.append(((row, col), (jump_row, jump_col)))
    return captures

def find_all_regular_moves(my_men, my_kings, color, directions):
    moves = []
    for piece in my_men + my_kings:
        row, col = piece
        for dr, dc in directions[color]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8 and (new_row + new_col) % 2 == 1:
                moves.append(((row, col), (new_row, new_col)))
    return moves

def evaluate_capture(move, my_men, my_kings, opp_men, opp_kings, color, directions):
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    is_king = (from_row, from_col) in my_kings
    opp_color = 'b' if color == 'w' else 'w'

    # Mid-square is the captured piece
    mid_row, mid_col = (from_row + to_row) // 2, (from_row + to_col) // 2
    captured_is_king = (mid_row, mid_col) in opp_kings

    # Base score: capturing a king is better
    score = 100 if captured_is_king else 50

    # Bonus for capturing near opponent's back row
    if color == 'w':
        score += (7 - to_row) * 5  # Closer to row 7 (white's back row)
    else:
        score += to_row * 5        # Closer to row 0 (black's back row)

    # Bonus for mobility after capture (how many new captures are possible from the new position)
    new_piece_pos = (to_row, to_col)
    new_captures = find_all_captures([new_piece_pos], [], opp_men, opp_kings, color, directions)
    score += len(new_captures) * 20

    # Penalty for blocking own pieces (simplified)
    if is_king:
        score += 10  # Kings are more valuable

    return score

def evaluate_regular_move(move, my_men, my_kings, opp_men, opp_kings, color, directions):
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    is_king = (from_row, from_col) in my_kings

    # Base score: moving kings is better
    score = 20 if is_king else 10

    # Bonus for moving toward opponent's back row
    if color == 'w':
        score += (to_row - from_row) * 5  # Moving up (toward row 7)
    else:
        score += (from_row - to_row) * 5  # Moving down (toward row 0)

    # Bonus for reaching opponent's back row (promotion potential)
    if color == 'w' and to_row == 7:
        score += 100
    elif color == 'b' and to_row == 0:
        score += 100

    # Penalty for moving away from opponent's back row
    if color == 'w' and to_row < from_row:
        score -= 10
    elif color == 'b' and to_row > from_row:
        score -= 10

    # Bonus for mobility after move (how many new captures/regular moves are possible)
    new_my_men = [p for p in my_men if p != (from_row, from_col)] + [(to_row, to_col)] if not is_king else my_men
    new_my_kings = [p for p in my_kings if p != (from_row, from_col)] + [(to_row, to_col)] if is_king else my_kings
    new_captures = find_all_captures(new_my_men, new_my_kings, opp_men, opp_kings, color, directions)
    new_regular_moves = find_all_regular_moves(new_my_men, new_my_kings, color, directions)
    score += (len(new_captures) + len(new_regular_moves)) * 2

    return score
