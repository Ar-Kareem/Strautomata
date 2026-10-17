
import random
from typing import List, Tuple

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Checkers policy that prioritizes captures, promotes kings, and controls the center.
    """
    # Directions: down-left, down-right, up-left, up-right (for black/white)
    directions = {
        'b': [(-1, -1), (-1, 1)],  # Black moves downward
        'w': [(1, -1), (1, 1)]     # White moves upward
    }
    king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Kings can move in all 4 diagonal directions

    # Get all legal moves (captures first, then regular moves)
    legal_moves = get_legal_moves(my_men, my_kings, opp_men, opp_kings, color, directions[color], king_directions)

    if not legal_moves:
        # Fallback: return a dummy move (should not happen in valid games)
        return ((0, 0), (1, 1))

    # Separate captures and regular moves
    captures = [move for move in legal_moves if is_capture(move, directions[color])]
    regular_moves = [move for move in legal_moves if not is_capture(move, directions[color])]

    # If captures exist, choose the best one
    if captures:
        best_capture = max(captures, key=lambda move: evaluate_capture(move, my_men, my_kings, opp_men, opp_kings, color, directions[color]))
        return best_capture
    # Else, choose the best regular move
    else:
        best_move = max(regular_moves, key=lambda move: evaluate_move(move, my_men, my_kings, opp_men, opp_kings, color, directions[color]))
        return best_move

def get_legal_moves(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                     opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
                     color: str, directions: List[Tuple[int, int]], king_directions: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Generate all legal moves (captures and regular) for the given color.
    """
    legal_moves = []
    all_my_pieces = my_men + my_kings
    opponent_pieces = opp_men + opp_kings

    for piece in all_my_pieces:
        row, col = piece
        if color == 'b' and row == 0 or color == 'w' and row == 7:
            continue  # Piece is already promoted (or at edge, no move possible)

        # Determine possible moves based on whether the piece is a king
        possible_directions = king_directions if piece in my_kings else directions

        for dr, dc in possible_directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8 and is_dark_square(new_row, new_col):
                # Check if the square is empty (regular move)
                if (new_row, new_col) not in all_my_pieces and (new_row, new_col) not in opponent_pieces:
                    legal_moves.append(((row, col), (new_row, new_col)))

                # Check for captures
                else:
                    # Capture requires jumping over an opponent's piece
                    jump_row, jump_col = row + dr, col + dc
                    capture_row, capture_col = new_row, new_col
                    if (jump_row, jump_col) in opponent_pieces:
                        # Check if the landing square is empty
                        if (capture_row, capture_col) not in all_my_pieces and (capture_row, capture_col) not in opponent_pieces:
                            legal_moves.append(((row, col), (capture_row, capture_col)))

    return legal_moves

def is_capture(move: Tuple[Tuple[int, int], Tuple[int, int]], directions: List[Tuple[int, int]]) -> bool:
    """
    Check if a move is a capture (i.e., the destination is two squares away in a diagonal direction).
    """
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    row_diff = to_row - from_row
    col_diff = to_col - from_col
    return abs(row_diff) == 2 and abs(col_diff) == 2

def evaluate_capture(move: Tuple[Tuple[int, int], Tuple[int, int]], my_men: List[Tuple[int, int]],
                     my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]],
                     opp_kings: List[Tuple[int, int]], color: str, directions: List[Tuple[int, int]]) -> float:
    """
    Evaluate the quality of a capture move.
    Higher score = better move.
    """
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    is_king = (from_row, from_col) in my_kings

    # Score based on captured piece type
    captured_piece = None
    for piece in opp_men + opp_kings:
        if (to_row - from_row) // 2 == (piece[0] - from_row) and (to_col - from_col) // 2 == (piece[1] - from_col):
            captured_piece = piece
            break
    if captured_piece in opp_kings:
        score = 3.0  # Capturing a king is very valuable
    else:
        score = 1.0  # Capturing a regular piece

    # Bonus for multi-captures (if the move leads to another capture)
    next_moves = get_legal_moves(
        my_men + [to_row, to_col] if (to_row, to_col) not in my_kings else my_kings,
        my_kings if (to_row, to_col) in my_kings else my_kings + [(to_row, to_col)],
        opp_men if captured_piece in opp_men else opp_men - [captured_piece],
        opp_kings if captured_piece in opp_kings else opp_kings - [captured_piece],
        color, directions, king_directions
    )
    if any(is_capture(m, directions) for m in next_moves):
        score += 2.0  # Multi-capture bonus

    # Positional score: prefer central captures
    center_score = 1.0 - (abs(to_row - 3.5) + abs(to_col - 3.5)) / 5.0
    score += center_score

    return score

def evaluate_move(move: Tuple[Tuple[int, int], Tuple[int, int]], my_men: List[Tuple[int, int]],
                  my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]],
                  opp_kings: List[Tuple[int, int]], color: str, directions: List[Tuple[int, int]]) -> float:
    """
    Evaluate the quality of a non-capture move.
    Higher score = better move.
    """
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    is_king = (from_row, from_col) in my_kings

    # Score based on piece type (kings are more valuable)
    piece_score = 2.0 if is_king else 1.0

    # Positional score: prefer moving toward center or promotion
    center_score = 1.0 - (abs(to_row - 3.5) + abs(to_col - 3.5)) / 5.0
    promotion_score = 0.0
    if color == 'b' and to_row < from_row:  # Black moving toward row 0
        promotion_score = (from_row - to_row) / 7.0
    elif color == 'w' and to_row > from_row:  # White moving toward row 7
        promotion_score = (to_row - from_row) / 7.0

    # Mobility score: how many new moves does this create?
    mobility_score = 0.0
    new_my_men = my_men.copy()
    new_my_kings = my_kings.copy()
    if (from_row, from_col) in my_men:
        new_my_men.remove((from_row, from_col))
        new_my_men.append((to_row, to_col))
    else:
        new_my_kings.remove((from_row, from_col))
        new_my_kings.append((to_row, to_col))

    new_legal_moves = get_legal_moves(new_my_men, new_my_kings, opp_men, opp_kings, color, directions, king_directions)
    mobility_score = len(new_legal_moves) / 10.0  # Normalize

    # King safety: avoid moving kings into corners
    if is_king:
        corner_penalty = 0.0
        if (to_row in [0, 7] and to_col in [0, 7]):
            corner_penalty = -1.0
        score = piece_score + center_score + promotion_score + mobility_score + corner_penalty
    else:
        score = piece_score + center_score + promotion_score + mobility_score

    return score

def is_dark_square(row: int, col: int) -> bool:
    """
    Check if a square is dark (playable in checkers).
    """
    return (row + col) % 2 == 1
