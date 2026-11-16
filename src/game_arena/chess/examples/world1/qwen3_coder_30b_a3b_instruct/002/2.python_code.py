
import random
from collections import defaultdict

def is_capture(move: str) -> bool:
    return 'x' in move

def is_checkmate(move: str) -> bool:
    return move.endswith('#')

def is_check(move: str) -> bool:
    return move.endswith('+')

def get_piece_value(piece: str) -> int:
    piece_type = piece[1]
    if piece_type == 'P':
        return 1
    elif piece_type == 'N' or piece_type == 'B':
        return 3
    elif piece_type == 'R':
        return 5
    elif piece_type == 'Q':
        return 9
    elif piece_type == 'K':
        return 1000  # Very high value
    return 0

def evaluate_move(move: str, pieces: dict[str, str], to_play: str) -> int:
    score = 0
    
    # Checkmate has highest priority
    if is_checkmate(move):
        return 100000
    
    # Check is also important
    if is_check(move):
        score += 1000
    
    # Captures are valuable
    if is_capture(move):
        # Find the captured piece
        capture_square = move[move.index('x')+1:move.index('x')+3]  # This is a simple approach
        if capture_square in pieces:
            captured_piece = pieces[capture_square]
            captured_value = get_piece_value(captured_piece)
            # Prefer capturing higher value pieces
            score += captured_value * 100
        
        # Prefer captures that don't lose material
        moving_piece = None
        if move[0].isupper():
            piece_type = move[0]
            if len([p for p in pieces.values() if p[1] == piece_type and p[0] == to_play[0]]) > 0:
                moving_piece = to_play[0] + piece_type
        else:
            # pawn capture
            moving_piece = to_play[0] + 'P'
            
        # Prefer captures on squares that aren't defended by opponent
        # This is a very simplified check - would involve full board analysis for more accuracy
        score += 50  # simple bonus for captures
    
    # Prefer moves that develop pieces (knights and bishops)
    if move[0] in 'BN':
        score += 20
    
    # Prefer center control (moves to d4, d5, e4, e5)
    if len(move) >= 2 and move[1] in '45' and move[2] in 'de':
        score += 10
        
    # Prefer moves that put pieces in the center
    if 'e4' in move or 'd4' in move or 'e5' in move or 'd5' in move:
        score += 15
    
    # Prefer castling
    if move == 'O-O' or move == 'O-O-O':
        score += 200
    
    return score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return random.choice(legal_moves)
    
    # Filter for checkmate moves
    checkmate_moves = [move for move in legal_moves if is_checkmate(move)]
    if checkmate_moves:
        return checkmate_moves[0]
    
    # Filter for capture moves
    capture_moves = [move for move in legal_moves if is_capture(move)]
    if capture_moves:
        # Prefer captures of high-value pieces, and avoid captures that lose material
        max_score = -1
        best_move = capture_moves[0]
        for move in capture_moves:
            score = evaluate_move(move, pieces, to_play)
            if score > max_score:
                max_score = score
                best_move = move
        return best_move
    
    # Filter for check moves
    check_moves = [move for move in legal_moves if is_check(move)]
    if check_moves:
        return check_moves[0]
    
    # Prefer castling if available
    castling_moves = [move for move in legal_moves if move in ['O-O', 'O-O-O']]
    if castling_moves:
        return castling_moves[0]
    
    # Prefer central pawn moves
    central_moves = [move for move in legal_moves if move[0].islower() and len(move) >= 2 and move[1] in '3456']
    if central_moves:
        return central_moves[0]
    
    # Prioritize development of pieces
    development_moves = [move for move in legal_moves if move[0] in 'BN' and len(move) == 3]
    if development_moves:
        return development_moves[0]
    
    # Fallback to any legal move
    return legal_moves[0]
