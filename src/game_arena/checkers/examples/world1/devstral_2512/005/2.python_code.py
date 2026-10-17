
import random
from typing import List, Tuple

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Combine all pieces
    my_pieces = my_men + my_kings
    opp_pieces = opp_men + opp_kings
    all_pieces = my_pieces + opp_pieces

    # Determine direction based on color
    direction = 1 if color == 'w' else -1

    # Get all possible moves (including captures)
    possible_moves = get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color, direction)

    # Separate captures and regular moves
    captures = [move for move in possible_moves if is_capture(move, my_pieces, opp_pieces)]
    regular_moves = [move for move in possible_moves if not is_capture(move, my_pieces, opp_pieces)]

    # Captures are mandatory if available
    if captures:
        # Evaluate all capture sequences
        best_capture = evaluate_captures(captures, my_men, my_kings, opp_men, opp_kings, color, direction)
        return best_capture
    else:
        # Evaluate regular moves
        best_move = evaluate_regular_moves(regular_moves, my_men, my_kings, opp_men, opp_kings, color, direction)
        return best_move

def get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color, direction):
    moves = []
    all_my_pieces = my_men + my_kings
    all_opp_pieces = opp_men + opp_kings

    for piece in all_my_pieces:
        if piece in my_kings:
            # Kings can move in all directions
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    moves.extend(get_moves_for_piece(piece, dr, dc, all_my_pieces, all_opp_pieces, color, is_king=True))
        else:
            # Regular pieces move in one direction
            for dc in [-1, 1]:
                moves.extend(get_moves_for_piece(piece, direction, dc, all_my_pieces, all_opp_pieces, color, is_king=False))

    return moves

def get_moves_for_piece(piece, dr, dc, my_pieces, opp_pieces, color, is_king):
    moves = []
    r, c = piece
    new_r, new_c = r + dr, c + dc

    # Check if new position is on the board and empty
    if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in my_pieces and (new_r, new_c) not in opp_pieces:
        # Check if it's a dark square
        if (new_r + new_c) % 2 == 1:
            moves.append(((r, c), (new_r, new_c)))

    # Check for captures
    capture_r, capture_c = r + 2*dr, c + 2*dc
    if 0 <= capture_r < 8 and 0 <= capture_c < 8:
        # Check if the square to capture is opponent's piece
        if (r + dr, c + dc) in opp_pieces and (capture_r, capture_c) not in my_pieces and (capture_r, capture_c) not in opp_pieces:
            # Check if it's a dark square
            if (capture_r + capture_c) % 2 == 1:
                moves.append(((r, c), (capture_r, capture_c)))

    return moves

def is_capture(move, my_pieces, opp_pieces):
    (r1, c1), (r2, c2) = move
    # A capture is when the move is more than 1 square in any direction
    return abs(r2 - r1) > 1 or abs(c2 - c1) > 1

def evaluate_captures(captures, my_men, my_kings, opp_men, opp_kings, color, direction):
    if not captures:
        return None

    # For now, just return a random capture (in a real implementation, we'd evaluate which capture is best)
    # This is a simplified version - a full implementation would evaluate multi-jumps and material advantage
    return random.choice(captures)

def evaluate_regular_moves(moves, my_men, my_kings, opp_men, opp_kings, color, direction):
    if not moves:
        return None

    # Evaluate each move based on several factors
    best_move = None
    best_score = -float('inf')

    for move in moves:
        score = evaluate_move(move, my_men, my_kings, opp_men, opp_kings, color, direction)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(moves)

def evaluate_move(move, my_men, my_kings, opp_men, opp_kings, color, direction):
    (r1, c1), (r2, c2) = move
    score = 0

    # 1. Promotion potential (if moving to the last row)
    if (color == 'w' and r2 == 7) or (color == 'b' and r2 == 0):
        score += 100  # High value for promotion

    # 2. Center control (distance from center)
    center_distance = abs(r2 - 3.5) + abs(c2 - 3.5)
    score += (7 - center_distance) * 2  # Max 14 points for center

    # 3. Forward movement (for regular pieces)
    if (r1, c1) in my_men:
        if (color == 'w' and r2 > r1) or (color == 'b' and r2 < r1):
            score += 5

    # 4. Mobility (number of possible moves from new position)
    # This is a simplified version - in a full implementation we'd calculate actual mobility
    if (r2 + c2) % 2 == 1:  # Dark square
        score += 3

    # 5. Safety (not moving into a position where we can be immediately captured)
    # This would require looking at opponent's possible moves - simplified here
    if not is_vulnerable((r2, c2), my_men, my_kings, opp_men, opp_kings, color):
        score += 5

    return score

def is_vulnerable(position, my_men, my_kings, opp_men, opp_kings, color):
    # Simplified vulnerability check - in a full implementation we'd check if opponent can capture this piece
    r, c = position
    opp_direction = -1 if color == 'w' else 1

    # Check adjacent squares for opponent pieces that could capture
    for dr in [-1, 1]:
        for dc in [-1, 1]:
            # Check if there's an opponent piece that could jump over us
            opp_r, opp_c = r + opp_direction, c + dc
            if (opp_r, opp_c) in opp_men or (opp_r, opp_c) in opp_kings:
                # Check if the square behind us is empty
                behind_r, behind_c = r - opp_direction, c - dc
                if 0 <= behind_r < 8 and 0 <= behind_c < 8:
                    if (behind_r, behind_c) not in my_men and (behind_r, behind_c) not in my_kings:
                        if (behind_r, behind_c) not in opp_men and (behind_r, behind_c) not in opp_kings:
                            return True
    return False
