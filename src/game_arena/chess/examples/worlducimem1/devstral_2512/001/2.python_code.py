
import random
from typing import Dict, Tuple, List

# Piece values for evaluation
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

# Center squares for evaluation
CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}

def evaluate_board(pieces: Dict[str, str], to_play: str) -> float:
    """
    Evaluate the current board position.
    Positive values favor white, negative values favor black.
    """
    score = 0.0

    # Material balance
    white_material = 0
    black_material = 0

    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]

        if color == 'w':
            white_material += PIECE_VALUES[piece_type]
        else:
            black_material += PIECE_VALUES[piece_type]

    score += (white_material - black_material)

    # Piece activity (center control)
    white_center = 0
    black_center = 0

    for square in CENTER_SQUARES:
        if square in pieces:
            piece = pieces[square]
            if piece[0] == 'w':
                white_center += 0.1
            else:
                black_center += 0.1

    score += (white_center - black_center)

    # King safety (penalize exposed kings)
    white_king_square = None
    black_king_square = None

    for square, piece in pieces.items():
        if piece == 'wK':
            white_king_square = square
        elif piece == 'bK':
            black_king_square = square

    if white_king_square:
        # Penalize white king in center or on open files
        if white_king_square in CENTER_SQUARES:
            score -= 0.5
        # Check if king is on an open file (no pawns in front)
        file = white_king_square[0]
        rank = int(white_king_square[1])
        if rank < 8:
            if f"{file}{rank+1}" not in pieces or pieces[f"{file}{rank+1}"][1] != 'P':
                score -= 0.2

    if black_king_square:
        # Penalize black king in center or on open files
        if black_king_square in CENTER_SQUARES:
            score += 0.5
        # Check if king is on an open file (no pawns in front)
        file = black_king_square[0]
        rank = int(black_king_square[1])
        if rank > 1:
            if f"{file}{rank-1}" not in pieces or pieces[f"{file}{rank-1}"][1] != 'P':
                score += 0.2

    # Adjust score based on whose turn it is
    if to_play == 'black':
        score = -score

    return score

def is_capture(move: str, pieces: Dict[str, str]) -> bool:
    """Check if a move is a capture."""
    dest_square = move[2:4]
    return dest_square in pieces

def get_piece_type(piece_code: str) -> str:
    """Get the piece type from a piece code."""
    return piece_code[1]

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    """
    Select the best move based on the current board position.
    """
    # Get legal moves (in a real implementation, these would be provided)
    # For this example, we'll assume legal_moves is available in memory
    if 'legal_moves' not in memory:
        # This is just for the example - in reality, legal moves would be provided
        memory['legal_moves'] = generate_legal_moves(pieces, to_play)

    legal_moves = memory['legal_moves']

    if not legal_moves:
        # No legal moves - should not happen in a real game
        return random.choice(list(legal_moves)), memory

    # Evaluate each move
    best_move = None
    best_score = -float('inf')
    best_capture = None
    best_capture_score = -float('inf')

    # First pass: look for captures and checkmate
    for move in legal_moves:
        # Make a copy of the board to simulate the move
        new_pieces = pieces.copy()

        # Remove the piece from the source square
        source_square = move[:2]
        del new_pieces[source_square]

        # Handle the destination square
        dest_square = move[2:4]
        if dest_square in new_pieces:
            # Capture - remove the captured piece
            del new_pieces[dest_square]

        # Add the moving piece to the destination square
        moving_piece = pieces[source_square]
        new_pieces[dest_square] = moving_piece

        # Handle pawn promotion if needed
        if len(move) == 5 and moving_piece[1] == 'P':
            promotion_piece = move[4].upper()
            new_pieces[dest_square] = moving_piece[0] + promotion_piece

        # Evaluate the new position
        score = evaluate_board(new_pieces, 'black' if to_play == 'white' else 'white')

        # Check if this is a capture
        if is_capture(move, pieces):
            if score > best_capture_score:
                best_capture_score = score
                best_capture = move
        else:
            if score > best_score:
                best_score = score
                best_move = move

    # Second pass: if we found a good capture, use it
    if best_capture and best_capture_score > best_score + 1:  # Capture threshold
        return best_capture, memory

    # If no good captures, return the best move
    if best_move:
        return best_move, memory

    # Fallback: return a random move (shouldn't happen if we have legal moves)
    return random.choice(legal_moves), memory

def generate_legal_moves(pieces: Dict[str, str], to_play: str) -> List[str]:
    """
    Generate all legal moves for the current position.
    This is a simplified version - in a real implementation, you would use a proper move generator.
    """
    moves = []
    color = 'w' if to_play == 'white' else 'b'

    for square, piece in pieces.items():
        if piece[0] != color:
            continue

        piece_type = piece[1]

        if piece_type == 'P':  # Pawn moves
            # Forward moves
            rank = int(square[1])
            new_rank = rank + 1 if color == 'w' else rank - 1
            if new_rank >= 1 and new_rank <= 8:
                new_square = square[0] + str(new_rank)
                if new_square not in pieces:
                    moves.append(square + new_square)
                    # Double move from starting position
                    if (rank == 2 and color == 'w') or (rank == 7 and color == 'b'):
                        new_square2 = square[0] + str(new_rank + (1 if color == 'w' else -1))
                        if new_square2 not in pieces:
                            moves.append(square + new_square2)
                # Captures
                for file_offset in [-1, 1]:
                    new_file = chr(ord(square[0]) + file_offset)
                    if 'a' <= new_file <= 'h':
                        capture_square = new_file + str(new_rank)
                        if capture_square in pieces and pieces[capture_square][0] != color:
                            moves.append(square + capture_square)
                            # Promotion
                            if (new_rank == 8 and color == 'w') or (new_rank == 1 and color == 'b'):
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(square + capture_square + promo)

        elif piece_type == 'N':  # Knight moves
            file = square[0]
            rank = int(square[1])
            for df, dr in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                          (1, -2), (1, 2), (2, -1), (2, 1)]:
                new_file = chr(ord(file) + df)
                new_rank = rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    new_square = new_file + str(new_rank)
                    if new_square not in pieces or pieces[new_square][0] != color:
                        moves.append(square + new_square)

        elif piece_type == 'B':  # Bishop moves
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for df, dr in directions:
                file = square[0]
                rank = int(square[1])
                for i in range(1, 8):
                    new_file = chr(ord(file) + df * i)
                    new_rank = rank + dr * i
                    if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                        break
                    new_square = new_file + str(new_rank)
                    if new_square in pieces:
                        if pieces[new_square][0] != color:
                            moves.append(square + new_square)
                        break
                    moves.append(square + new_square)

        elif piece_type == 'R':  # Rook moves
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for df, dr in directions:
                file = square[0]
                rank = int(square[1])
                for i in range(1, 8):
                    new_file = chr(ord(file) + df * i)
                    new_rank = rank + dr * i
                    if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                        break
                    new_square = new_file + str(new_rank)
                    if new_square in pieces:
                        if pieces[new_square][0] != color:
                            moves.append(square + new_square)
                        break
                    moves.append(square + new_square)

        elif piece_type == 'Q':  # Queen moves
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                          (0, 1), (1, -1), (1, 0), (1, 1)]
            for df, dr in directions:
                file = square[0]
                rank = int(square[1])
                for i in range(1, 8):
                    new_file = chr(ord(file) + df * i)
                    new_rank = rank + dr * i
                    if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                        break
                    new_square = new_file + str(new_rank)
                    if new_square in pieces:
                        if pieces[new_square][0] != color:
                            moves.append(square + new_square)
                        break
                    moves.append(square + new_square)

        elif piece_type == 'K':  # King moves
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                          (0, 1), (1, -1), (1, 0), (1, 1)]
            for df, dr in directions:
                new_file = chr(ord(square[0]) + df)
                new_rank = int(square[1]) + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    new_square = new_file + str(new_rank)
                    if new_square not in pieces or pieces[new_square][0] != color:
                        moves.append(square + new_square)

            # Castling (simplified - in reality would need to check more conditions)
            if color == 'w' and square == 'e1':
                if 'f1' not in pieces and 'g1' not in pieces and 'h1' in pieces and pieces['h1'] == 'wR':
                    moves.append('e1g1')
                if 'd1' not in pieces and 'c1' not in pieces and 'b1' not in pieces and 'a1' in pieces and pieces['a1'] == 'wR':
                    moves.append('e1c1')
            elif color == 'b' and square == 'e8':
                if 'f8' not in pieces and 'g8' not in pieces and 'h8' in pieces and pieces['h8'] == 'bR':
                    moves.append('e8g8')
                if 'd8' not in pieces and 'c8' not in pieces and 'b8' not in pieces and 'a8' in pieces and pieces['a8'] == 'bR':
                    moves.append('e8c8')

    return moves
