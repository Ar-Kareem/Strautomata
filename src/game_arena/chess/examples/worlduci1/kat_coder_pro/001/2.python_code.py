
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Chess policy that evaluates legal moves and selects the best one.
    
    Args:
        pieces: Dictionary mapping squares to piece codes
        to_play: Either 'white' or 'black'
    
    Returns:
        A move string in UCI format
    """
    
    # Define piece values
    piece_values = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0
    }
    
    # Define color
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    # Find all legal moves (simplified - in real implementation this would be more complex)
    # For this example, we'll assume legal_moves is provided in the context
    # Since it's not, we'll need to generate it
    legal_moves = generate_legal_moves(pieces, color)
    
    if not legal_moves:
        # Fallback - should not happen in a real game
        return random.choice(list(pieces.keys())) + random.choice(list(pieces.keys()))
    
    # Evaluate each move
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(move, pieces, color, opponent_color, piece_values)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else legal_moves[0]


def generate_legal_moves(pieces: dict[str, str], color: str) -> list[str]:
    """
    Generate all legal moves for the given color.
    This is a simplified implementation for demonstration.
    """
    legal_moves = []
    
    # Find all pieces of the given color
    friendly_pieces = {sq: piece for sq, piece in pieces.items() if piece.startswith(color)}
    
    for square, piece in friendly_pieces.items():
        piece_type = piece[1]
        
        # Generate moves based on piece type (simplified)
        if piece_type == 'P':
            pawn_moves = generate_pawn_moves(square, color, pieces)
            legal_moves.extend(pawn_moves)
        elif piece_type == 'N':
            knight_moves = generate_knight_moves(square, color, pieces)
            legal_moves.extend(knight_moves)
        elif piece_type == 'B':
            bishop_moves = generate_bishop_moves(square, color, pieces)
            legal_moves.extend(bishop_moves)
        elif piece_type == 'R':
            rook_moves = generate_rook_moves(square, color, pieces)
            legal_moves.extend(rook_moves)
        elif piece_type == 'Q':
            bishop_moves = generate_bishop_moves(square, color, pieces)
            rook_moves = generate_rook_moves(square, color, pieces)
            legal_moves.extend(bishop_moves + rook_moves)
        elif piece_type == 'K':
            king_moves = generate_king_moves(square, color, pieces)
            legal_moves.extend(king_moves)
    
    return legal_moves


def generate_pawn_moves(square: str, color: str, pieces: dict[str, str]) -> list[str]:
    """Generate pawn moves"""
    moves = []
    file, rank = square[0], int(square[1])
    direction = 1 if color == 'w' else -1
    
    # Forward move
    new_rank = rank + direction
    if 1 <= new_rank <= 8:
        target_square = f"{file}{new_rank}"
        if target_square not in pieces:
            if new_rank == 8 or new_rank == 1:
                # Promotion
                for promo in ['n', 'b', 'r', 'q']:
                    moves.append(f"{square}{target_square}{promo}")
            else:
                moves.append(f"{square}{target_square}")
            
            # Double move from starting position
            if (color == 'w' and rank == 2) or (color == 'b' and rank == 7):
                new_rank2 = rank + 2 * direction
                target_square2 = f"{file}{new_rank2}"
                if target_square2 not in pieces:
                    moves.append(f"{square}{target_square2}")
    
    # Captures
    for file_offset in [-1, 1]:
        new_file = chr(ord(file) + file_offset)
        if 'a' <= new_file <= 'h':
            new_rank = rank + direction
            if 1 <= new_rank <= 8:
                target_square = f"{new_file}{new_rank}"
                if target_square in pieces and not pieces[target_square].startswith(color):
                    if new_rank == 8 or new_rank == 1:
                        for promo in ['n', 'b', 'r', 'q']:
                            moves.append(f"{square}{target_square}{promo}")
                    else:
                        moves.append(f"{square}{target_square}")
    
    return moves


def generate_knight_moves(square: str, color: str, pieces: dict[str, str]) -> list[str]:
    """Generate knight moves"""
    moves = []
    file, rank = square[0], int(square[1])
    
    knight_offsets = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    
    for file_offset, rank_offset in knight_offsets:
        new_file = chr(ord(file) + file_offset)
        new_rank = rank + rank_offset
        
        if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
            target_square = f"{new_file}{new_rank}"
            if target_square not in pieces or not pieces[target_square].startswith(color):
                moves.append(f"{square}{target_square}")
    
    return moves


def generate_bishop_moves(square: str, color: str, pieces: dict[str, str]) -> list[str]:
    """Generate bishop moves"""
    moves = []
    file, rank = square[0], int(square[1])
    
    # Four diagonal directions
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for file_dir, rank_dir in directions:
        for step in range(1, 8):
            new_file = chr(ord(file) + step * file_dir)
            new_rank = rank + step * rank_dir
            
            if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                target_square = f"{new_file}{new_rank}"
                if target_square in pieces:
                    if not pieces[target_square].startswith(color):
                        moves.append(f"{square}{target_square}")
                    break
                else:
                    moves.append(f"{square}{target_square}")
            else:
                break
    
    return moves


def generate_rook_moves(square: str, color: str, pieces: dict[str, str]) -> list[str]:
    """Generate rook moves"""
    moves = []
    file, rank = square[0], int(square[1])
    
    # Four orthogonal directions
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for file_dir, rank_dir in directions:
        for step in range(1, 8):
            new_file = chr(ord(file) + step * file_dir)
            new_rank = rank + step * rank_dir
            
            if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                target_square = f"{new_file}{new_rank}"
                if target_square in pieces:
                    if not pieces[target_square].startswith(color):
                        moves.append(f"{square}{target_square}")
                    break
                else:
                    moves.append(f"{square}{target_square}")
            else:
                break
    
    return moves


def generate_king_moves(square: str, color: str, pieces: dict[str, str]) -> list[str]:
    """Generate king moves"""
    moves = []
    file, rank = square[0], int(square[1])
    
    # Eight possible directions
    directions = [
        (-1, -1), (-1, 0), (-1, 1), (0, -1),
        (0, 1), (1, -1), (1, 0), (1, 1)
    ]
    
    for file_dir, rank_dir in directions:
        new_file = chr(ord(file) + file_dir)
        new_rank = rank + rank_dir
        
        if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
            target_square = f"{new_file}{new_rank}"
            if target_square not in pieces or not pieces[target_square].startswith(color):
                moves.append(f"{square}{target_square}")
    
    return moves


def evaluate_move(move: str, pieces: dict[str, str], color: str, opponent_color: str, piece_values: dict) -> float:
    """Evaluate a move based on various factors"""
    score = 0.0
    
    # Parse move
    if len(move) == 5:  # Promotion move
        from_sq = move[:2]
        to_sq = move[2:4]
        promotion = move[4]
    else:  # Regular move
        from_sq = move[:2]
        to_sq = move[2:4]
        promotion = None
    
    # Get piece being moved
    piece_being_moved = pieces.get(from_sq, None)
    if not piece_being_moved or not piece_being_moved.startswith(color):
        return float('-inf')  # Invalid move
    
    # Material gain
    captured_piece = pieces.get(to_sq, None)
    if captured_piece and captured_piece.startswith(opponent_color):
        captured_value = piece_values[captured_piece[1]]
        piece_value = piece_values[piece_being_moved[1]]
        score += captured_value - piece_value  # Simple exchange evaluation
    
    # Promotion bonus
    if promotion:
        score += piece_values[promotion.upper()] - piece_values['P']
    
    # Positional evaluation
    piece_type = piece_being_moved[1]
    from_file, from_rank = from_sq[0], int(from_sq[1])
    to_file, to_rank = to_sq[0], int(to_sq[1])
    
    # Simplified piece-square table evaluation
    if piece_type == 'N':
        # Knights prefer center
        center_bonus = 10 if 'd' <= to_file <= 'e' and 3 <= to_rank <= 6 else 0
        score += center_bonus
    elif piece_type == 'B':
        # Bishops like open diagonals (simplified)
        if to_file in 'cdef' and to_rank in [3, 4, 5, 6]:
            score += 5
    elif piece_type == 'P':
        # Pawns value advancement
        advance_bonus = (to_rank - from_rank) * 10 if color == 'w' else (from_rank - to_rank) * 10
        score += advance_bonus
        
        # Avoid doubled pawns (simplified)
        if from_file == to_file:
            file_ahead = f"{to_file}{to_rank + (1 if color == 'w' else -1)}"
            if file_ahead in pieces and pieces[file_ahead].startswith(color) and pieces[file_ahead][1] == 'P':
                score -= 10
    
    # King safety (avoid unnecessary king moves in opening)
    elif piece_type == 'K':
        if len(pieces) > 20:  # Rough opening/middlegame indicator
            score -= 20
    
    # Avoid hanging pieces (simplified)
    if captured_piece is None:  # Not a capture
        # Check if the piece could be captured next move
        # This is a very simplified version
        if piece_type in ['N', 'B', 'R', 'Q']:
            # Penalize moving to squares that could be attacked
            if to_file in 'abcdefgh' and to_rank in [1, 2, 7, 8]:
                score -= 5
    
    return score
