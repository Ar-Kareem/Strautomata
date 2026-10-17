
import numpy as np

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Helper function to check if a square is occupied
    def is_occupied(square, pieces):
        return square in pieces
    
    # Helper function to generate all possible capture moves
    def generate_captures(my_pieces, opp_pieces, color):
        captures = []
        directions = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
        for piece in my_pieces:
            r, c = piece
            for dr, dc in directions:
                # Check if opponent piece exists in the diagonal direction
                opp_r, opp_c = r + dr, c + dc
                if 0 <= opp_r < 8 and 0 <= opp_c < 8 and is_occupied((opp_r, opp_c), opp_pieces):
                    # Check if the landing square is empty
                    land_r, land_c = opp_r + dr, opp_c + dc
                    if 0 <= land_r < 8 and 0 <= land_c < 8 and not is_occupied((land_r, land_c), my_pieces + opp_pieces):
                        captures.append(((r, c), (land_r, land_c)))
        return captures
    
    # Helper function to generate non-capture moves
    def generate_non_captures(my_pieces, color):
        moves = []
        directions = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
        for piece in my_pieces:
            r, c = piece
            for dr, dc in directions:
                land_r, land_c = r + dr, c + dc
                if 0 <= land_r < 8 and 0 <= land_c < 8 and not is_occupied((land_r, land_c), my_pieces + opp_pieces):
                    moves.append(((r, c), (land_r, land_c)))
        return moves
    
    # Check for captures first
    captures = generate_captures(my_men + my_kings, opp_men + opp_kings, color)
    if captures:
        # Prefer captures that remove more opponent pieces
        best_capture = max(captures, key=lambda move: sum(1 for _, (r, c) in move if (r, c) in opp_men + opp_kings))
        return best_capture
    
    # Generate non-capture moves
    non_captures = generate_non_captures(my_men + my_kings, color)
    if non_captures:
        # Prefer moving kings forward
        best_non_capture = max(non_captures, key=lambda move: 1 if move[1][0] in my_kings else 0)
        return best_non_capture
    
    # Fallback: return any valid move if none found
    return non_captures[0] if non_captures else ((0, 0), (0, 0))
