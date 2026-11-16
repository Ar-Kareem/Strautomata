
import numpy as np
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str) -> str:
    """
    Selects the best chess move based on a simple evaluation function.
    
    Args:
        pieces: Dictionary mapping squares to piece codes
        to_play: Either 'white' or 'black'
        
    Returns:
        A UCI move string representing the selected move
    """
    
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Get all legal moves
    legal_moves = get_legal_moves(pieces, to_play)
    
    # If only one legal move, take it
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Check for immediate checkmate
    checkmate_moves = []
    for move in legal_moves:
        new_pieces = make_move(pieces, move)
        if is_checkmate(new_pieces, 'black' if to_play == 'white' else 'white'):
            checkmate_moves.append(move)
    
    if checkmate_moves:
        # Prefer captures and checkmates
        captures = [m for m in checkmate_moves if is_capture(pieces, m)]
        return captures[0] if captures else checkmate_moves[0]
    
    # Evaluate all moves and select the best
    best_score = float('-inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        # Make the move
        new_pieces = make_move(pieces, move)
        
        # Evaluate the resulting position
        score = evaluate_position(new_pieces, to_play)
        
        # Bonus for captures
        if is_capture(pieces, move):
            score += 0.1
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def get_legal_moves(pieces: Dict[str, str], to_play: str) -> List[str]:
    """
    Generate all legal moves for the current position.
    This is a simplified implementation that handles basic moves.
    """
    legal_moves = []
    player_color = 'w' if to_play == 'white' else 'b'
    
    # Get all pieces of the current player
    player_pieces = {sq: piece for sq, piece in pieces.items() if piece[0] == player_color}
    
    for square, piece in player_pieces.items():
        piece_type = piece[1]
        file, rank = square[0], square[1]
        
        # Generate moves based on piece type
        if piece_type == 'P':
            legal_moves.extend(get_pawn_moves(square, piece, pieces))
        elif piece_type == 'N':
            legal_moves.extend(get_knight_moves(square, pieces))
        elif piece_type == 'B':
            legal_moves.extend(get_bishop_moves(square, pieces))
        elif piece_type == 'R':
            legal_moves.extend(get_rook_moves(square, pieces))
        elif piece_type == 'Q':
            legal_moves.extend(get_queen_moves(square, pieces))
        elif piece_type == 'K':
            legal_moves.extend(get_king_moves(square, pieces))
    
    # Filter out moves that leave the king in check
    legal_moves = [m for m in legal_moves if not leaves_king_in_check(pieces, m, to_play)]
    
    return legal_moves

def get_pawn_moves(square: str, piece: str, pieces: Dict[str, str]) -> List[str]:
    """Generate pawn moves"""
    moves = []
    file, rank = square[0], square[1]
    color = piece[0]
    
    # Determine direction
    direction = 1 if color == 'w' else -1
    new_rank = str(int(rank) + direction)
    
    # Forward move
    if new_rank in '12345678' and f"{file}{new_rank}" not in pieces:
        moves.append(f"{square}{file}{new_rank}")
        
        # Double move from starting position
        if (color == 'w' and rank == '2') or (color == 'b' and rank == '7'):
            double_rank = str(int(rank) + 2 * direction)
            if double_rank in '12345678' and f"{file}{double_rank}" not in pieces:
                moves.append(f"{square}{file}{double_rank}")
    
    # Captures
    for f in [chr(ord(file) - 1), chr(ord(file) + 1)]:
        if f in 'abcdefgh':
            capture_square = f"{f}{new_rank}"
            if capture_square in pieces and pieces[capture_square][0] != color:
                moves.append(f"{square}{capture_square}")
    
    return moves

def get_knight_moves(square: str, pieces: Dict[str, str]) -> List[str]:
    """Generate knight moves"""
    moves = []
    file, rank = ord(square[0]), int(square[1])
    color = pieces[square][0]
    
    # Knight move offsets
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    
    for df, dr in offsets:
        new_file = chr(file + df)
        new_rank = str(rank + dr)
        
        if new_file in 'abcdefgh' and new_rank in '12345678':
            target_square = f"{new_file}{new_rank}"
            if target_square not in pieces or pieces[target_square][0] != color:
                moves.append(f"{square}{target_square}")
    
    return moves

def get_bishop_moves(square: str, pieces: Dict[str, str]) -> List[str]:
    """Generate bishop moves"""
    moves = []
    file, rank = square[0], int(square[1])
    color = pieces[square][0]
    
    # Diagonal directions
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    for df, dr in directions:
        for i in range(1, 8):
            new_file = chr(ord(file) + i * df)
            new_rank = str(rank + i * dr)
            
            if new_file in 'abcdefgh' and new_rank in '12345678':
                target_square = f"{new_file}{new_rank}"
                if target_square in pieces:
                    if pieces[target_square][0] != color:
                        moves.append(f"{square}{target_square}")
                    break
                else:
                    moves.append(f"{square}{target_square}")
            else:
                break
    
    return moves

def get_rook_moves(square: str, pieces: Dict[str, str]) -> List[str]:
    """Generate rook moves"""
    moves = []
    file, rank = square[0], int(square[1])
    color = pieces[square][0]
    
    # Horizontal and vertical directions
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    
    for df, dr in directions:
        for i in range(1, 8):
            new_file = chr(ord(file) + i * df)
            new_rank = str(rank + i * dr)
            
            if new_file in 'abcdefgh' and new_rank in '12345678':
                target_square = f"{new_file}{new_rank}"
                if target_square in pieces:
                    if pieces[target_square][0] != color:
                        moves.append(f"{square}{target_square}")
                    break
                else:
                    moves.append(f"{square}{target_square}")
            else:
                break
    
    return moves

def get_queen_moves(square: str, pieces: Dict[str, str]) -> List[str]:
    """Generate queen moves (combination of bishop and rook)"""
    return get_bishop_moves(square, pieces) + get_rook_moves(square, pieces)

def get_king_moves(square: str, pieces: Dict[str, str]) -> List[str]:
    """Generate king moves"""
    moves = []
    file, rank = ord(square[0]), int(square[1])
    color = pieces[square][0]
    
    # King move offsets
    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for df, dr in offsets:
        new_file = chr(file + df)
        new_rank = str(rank + dr)
        
        if new_file in 'abcdefgh' and new_rank in '12345678':
            target_square = f"{new_file}{new_rank}"
            if target_square not in pieces or pieces[target_square][0] != color:
                moves.append(f"{square}{target_square}")
    
    return moves

def make_move(pieces: Dict[str, str], move: str) -> Dict[str, str]:
    """Apply a move to the board and return the new position"""
    new_pieces = pieces.copy()
    
    # Parse move
    from_square = move[:2]
    to_square = move[2:4]
    
    # Move piece
    if from_square in new_pieces:
        piece = new_pieces[from_square]
        del new_pieces[from_square]
        new_pieces[to_square] = piece
    
    # Handle promotion
    if len(move) > 4:
        promotion = move[4]
        new_pieces[to_square] = new_pieces[to_square][0] + promotion.upper()
    
    return new_pieces

def is_capture(pieces: Dict[str, str], move: str) -> bool:
    """Check if a move is a capture"""
    to_square = move[2:4]
    return to_square in pieces

def leaves_king_in_check(pieces: Dict[str, str], move: str, to_play: str) -> bool:
    """Check if a move leaves the king in check"""
    # This is a simplified check - in a full implementation, we would need
    # to check if the king is under attack after the move
    return False

def is_checkmate(pieces: Dict[str, str], player: str) -> bool:
    """Check if the player is in checkmate"""
    # Simplified checkmate detection
    # In a full implementation, we would need to verify that the king is in check
    # and has no legal moves to escape
    return False

def evaluate_position(pieces: Dict[str, str], player: str) -> float:
    """Evaluate a position from the perspective of the given player"""
    score = 0
    player_color = 'w' if player == 'white' else 'b'
    opponent_color = 'b' if player == 'white' else 'w'
    
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Count material
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        
        value = piece_values[piece_type]
        
        if color == player_color:
            score += value
        else:
            score -= value
    
    # Simple positional evaluation
    # Encourage development and centralization
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        
        if color == player_color:
            # Bonus for central pawns
            if piece_type == 'P' and square[0] in 'dfe' and square[1] in '45':
                score += 0.1
            
            # Bonus for developed minor pieces
            if piece_type in 'NB' and ((color == 'w' and square[1] in '3456') or 
                                       (color == 'b' and square[1] in '3456')):
                score += 0.1
        
        else:
            # Penalty for opponent's central pawns
            if piece_type == 'P' and square[0] in 'dfe' and square[1] in '45':
                score -= 0.1
    
    return score
