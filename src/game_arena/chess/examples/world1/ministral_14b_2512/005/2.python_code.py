
import re
from collections import defaultdict

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Determine our color and opponent's color
    our_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    # Precompute piece values (material)
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }

    # Precompute center squares (d4, d5, e4, e5)
    center_squares = {'d4', 'd5', 'e4', 'e5'}

    # Parse the board to find our and opponent's pieces
    our_pieces = {sq: piece for sq, piece in pieces.items() if piece[0] == our_color}
    opponent_pieces = {sq: piece for sq, piece in pieces.items() if piece[0] == opponent_color}

    # Find our king position
    our_king_pos = None
    for sq, piece in our_pieces.items():
        if piece[1] == 'K':
            our_king_pos = sq
            break

    # Find opponent's king position
    opponent_king_pos = None
    for sq, piece in opponent_pieces.items():
        if piece[1] == 'K':
            opponent_king_pos = sq
            break

    # Evaluate each legal move
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(move, pieces, our_color, opponent_color, our_pieces, opponent_pieces, our_king_pos, opponent_king_pos, center_squares, piece_values)
        move_scores.append((move, score))

    # Sort moves by score (descending) and pick the best
    move_scores.sort(key=lambda x: -x[1])
    best_move = move_scores[0][0]

    return best_move

def evaluate_move(move: str, pieces: dict[str, str], our_color: str, opponent_color: str,
                  our_pieces: dict[str, str], opponent_pieces: dict[str, str],
                  our_king_pos: str, opponent_king_pos: str, center_squares: set[str],
                  piece_values: dict[str, int]) -> int:
    # Check if the move is a checkmate (highest priority)
    if '+' in move and '#' in move:
        return float('inf')

    # Check if the move is a check (high priority)
    if '+' in move:
        return 10000

    # Parse the move to extract from, to, and promotion (if any)
    from_sq, to_sq = parse_move(move)
    promotion = None
    if '=' in move:
        promotion = move.split('=')[1][0]

    # Check if the move captures (and what is captured)
    captured_piece = None
    if 'x' in move:
        captured_sq = move.split('x')[1].split('+')[0].split('#')[0].split('=')[0][:2]
        if captured_sq in opponent_pieces:
            captured_piece = opponent_pieces[captured_sq][1]

    # Score for capturing opponent's pieces (material gain)
    capture_score = 0
    if captured_piece:
        capture_score = piece_values[captured_piece] * 100

    # Score for promoting a pawn (high value)
    promote_score = 0
    if promotion:
        promote_score = piece_values[promotion] * 100

    # Score for moving pieces to center squares (knights and bishops)
    center_score = 0
    if from_sq in our_pieces:
        piece_type = our_pieces[from_sq][1]
        if piece_type in ['N', 'B'] and to_sq in center_squares:
            center_score = 50

    # Score for castling (king safety)
    castle_score = 0
    if move in ['O-O', 'O-O-O']:
        castle_score = 100

    # Score for moving pawns to center (e4, d4, e5, d5)
    pawn_center_score = 0
    if from_sq in our_pieces and our_pieces[from_sq][1] == 'P' and to_sq in center_squares:
        pawn_center_score = 30

    # Score for avoiding moves that expose the king (e.g., moving king into check)
    king_safety_score = 0
    if our_king_pos and to_sq == our_king_pos:
        # Check if the move leaves the king in a worse position (simplified)
        # For now, just avoid moving king into check (handled by legal moves)
        pass

    # Score for developing pieces (knights and bishops)
    develop_score = 0
    if from_sq in our_pieces:
        piece_type = our_pieces[from_sq][1]
        if piece_type in ['N', 'B'] and not is_piece_developed(from_sq, our_color):
            develop_score = 20

    # Combine all scores
    total_score = (
        capture_score +
        promote_score +
        center_score +
        castle_score +
        pawn_center_score +
        develop_score
    )

    return total_score

def parse_move(move: str) -> tuple[str, str]:
    # Handle castling
    if move in ['O-O', 'O-O-O']:
        if move == 'O-O':
            return ('e1', 'g1') if our_color == 'w' else ('e8', 'g8')
        else:
            return ('e1', 'c1') if our_color == 'w' else ('e8', 'c8')

    # Handle promotions
    if '=' in move:
        move = move.split('=')[0]

    # Handle captures
    if 'x' in move:
        parts = move.split('x')
        from_sq = parts[0]
        to_sq = parts[1].split('+')[0].split('#')[0]
    else:
        from_sq = move[:-2]
        to_sq = move[-2:]

    return from_sq, to_sq

def is_piece_developed(sq: str, color: str) -> bool:
    # Simplified: a knight or bishop is developed if it's not on its starting square
    if color == 'w':
        if sq in ['g1', 'b1', 'a1', 'h1']:
            return False
    else:
        if sq in ['g8', 'b8', 'a8', 'h8']:
            return False
    return True
