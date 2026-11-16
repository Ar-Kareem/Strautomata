
import numpy as np
from itertools import product

# Piece values
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3.2, 'R': 5, 'Q': 9, 'K': 100
}

# Square values for piece placement
CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}
EXTENDED_CENTER = {'c3', 'd3', 'e3', 'f3', 
                   'c4', 'd4', 'e4', 'f4',
                   'c5', 'd5', 'e5', 'f5',
                   'c6', 'd6', 'e6', 'f6'}

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Generate all legal moves
    legal_moves = generate_legal_moves(pieces, to_play)
    if not legal_moves:
        return ""
    
    # Get our color code
    our_color = 'w' if to_play == 'white' else 'b'
    
    # If we can checkmate in one move, do it
    for move in legal_moves:
        new_pieces = make_move(pieces, move, our_color)
        if is_checkmate(new_pieces, 'b' if our_color == 'w' else 'w'):
            return move
    
    # If we're in check, prioritize getting out of check
    if is_in_check(pieces, our_color):
        # Find moves that get us out of check
        safe_moves = []
        for move in legal_moves:
            new_pieces = make_move(pieces, move, our_color)
            if not is_in_check(new_pieces, our_color):
                safe_moves.append(move)
        if safe_moves:
            legal_moves = safe_moves
        else:
            # No legal moves that get out of check - return first move (will be stalemate or checkmate)
            return legal_moves[0]
    
    # Evaluate all legal moves with minimax
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        new_pieces = make_move(pieces, move, our_color)
        
        # Opponent's best response
        opponent_color = 'b' if our_color == 'w' else 'w'
        opponent_moves = generate_legal_moves(new_pieces, 'white' if opponent_color == 'w' else 'black')
        
        if opponent_moves:
            # Find opponent's best move (minimizing our score)
            worst_score = float('inf')
            for opp_move in opponent_moves:
                opp_pieces = make_move(new_pieces, opp_move, opponent_color)
                score = evaluate_position(opp_pieces, our_color)
                if score < worst_score:
                    worst_score = score
            current_score = worst_score
        else:
            # No opponent moves - checkmate or stalemate
            if is_in_check(new_pieces, opponent_color):
                current_score = 1000  # Checkmate
            else:
                current_score = 0  # Stalemate
        
        if current_score > best_score:
            best_score = current_score
            best_move = move
    
    return best_move if best_move else legal_moves[0]

def generate_legal_moves(pieces, to_play):
    color = 'w' if to_play == 'white' else 'b'
    legal_moves = []
    
    for square, piece in pieces.items():
        if piece[0] != color:
            continue
            
        piece_type = piece[1]
        x, y = ord(square[0]) - ord('a'), int(square[1]) - 1
        
        if piece_type == 'P':
            # Pawn moves
            direction = 1 if color == 'w' else -1
            # Single push
            new_y = y + direction
            if 0 <= new_y < 8:
                new_square = f"{chr(x + ord('a'))}{new_y + 1}"
                if new_square not in pieces:
                    legal_moves.append(f"{square}{new_square}")
                    # Double push from starting position
                    if (color == 'w' and y == 1) or (color == 'b' and y == 6):
                        new_y2 = y + 2 * direction
                        new_square2 = f"{chr(x + ord('a'))}{new_y2 + 1}"
                        if new_square2 not in pieces and new_square not in pieces:
                            legal_moves.append(f"{square}{new_square2}")
            # Captures
            for dx in [-1, 1]:
                new_x = x + dx
                if 0 <= new_x < 8:
                    new_y = y + direction
                    if 0 <= new_y < 8:
                        new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                        if new_square in pieces and pieces[new_square][0] != color:
                            legal_moves.append(f"{square}{new_square}")
                        # En passant would need additional state
        
        elif piece_type == 'N':
            # Knight moves
            for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                    if new_square not in pieces or pieces[new_square][0] != color:
                        legal_moves.append(f"{square}{new_square}")
        
        elif piece_type == 'B':
            # Bishop moves
            for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                for i in range(1, 8):
                    new_x, new_y = x + i*dx, y + i*dy
                    if 0 <= new_x < 8 and 0 <= new_y < 8:
                        new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                        if new_square in pieces:
                            if pieces[new_square][0] != color:
                                legal_moves.append(f"{square}{new_square}")
                            break
                        legal_moves.append(f"{square}{new_square}")
                    else:
                        break
        
        elif piece_type == 'R':
            # Rook moves
            for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                for i in range(1, 8):
                    new_x, new_y = x + i*dx, y + i*dy
                    if 0 <= new_x < 8 and 0 <= new_y < 8:
                        new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                        if new_square in pieces:
                            if pieces[new_square][0] != color:
                                legal_moves.append(f"{square}{new_square}")
                            break
                        legal_moves.append(f"{square}{new_square}")
                    else:
                        break
        
        elif piece_type == 'Q':
            # Queen moves (rook + bishop)
            for dx, dy in [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                for i in range(1, 8):
                    new_x, new_y = x + i*dx, y + i*dy
                    if 0 <= new_x < 8 and 0 <= new_y < 8:
                        new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                        if new_square in pieces:
                            if pieces[new_square][0] != color:
                                legal_moves.append(f"{square}{new_square}")
                            break
                        legal_moves.append(f"{square}{new_square}")
                    else:
                        break
        
        elif piece_type == 'K':
            # King moves
            for dx, dy in [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                    if new_square not in pieces or pieces[new_square][0] != color:
                        legal_moves.append(f"{square}{new_square}")
            # Castling would need additional state
    
    # Filter out moves that leave our king in check
    valid_moves = []
    for move in legal_moves:
        new_pieces = make_move(pieces, move, color)
        if not is_in_check(new_pieces, color):
            valid_moves.append(move)
    
    return valid_moves

def make_move(pieces, move, color):
    new_pieces = pieces.copy()
    start, end = move[:2], move[2:4]
    piece = new_pieces.pop(start)
    
    # Handle promotion
    if len(move) == 5:
        promo_piece = move[4]
        new_pieces[end] = color + promo_piece.upper()
    else:
        new_pieces[end] = piece
    
    return new_pieces

def is_in_check(pieces, color):
    # Find the king
    king_square = None
    for square, piece in pieces.items():
        if piece == color + 'K':
            king_square = square
            break
    if not king_square:
        return False
    
    x, y = ord(king_square[0]) - ord('a'), int(king_square[1]) - 1
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Check for attacking knights
    for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < 8 and 0 <= new_y < 8:
            square = f"{chr(new_x + ord('a'))}{new_y + 1}"
            if square in pieces and pieces[square] == opponent_color + 'N':
                return True
    
    # Check for attacking pawns
    pawn_dir = 1 if opponent_color == 'w' else -1
    for dx in [-1, 1]:
        new_x, new_y = x + dx, y + pawn_dir
        if 0 <= new_x < 8 and 0 <= new_y < 8:
            square = f"{chr(new_x + ord('a'))}{new_y + 1}"
            if square in pieces and pieces[square] == opponent_color + 'P':
                return True
    
    # Check for sliding pieces (rook, bishop, queen)
    for dx, dy in [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
        for i in range(1, 8):
            new_x, new_y = x + i*dx, y + i*dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                if square in pieces:
                    piece = pieces[square]
                    if piece[0] == opponent_color:
                        # Check if piece attacks in this direction
                        if (dx == 0 or dy == 0):  # Rook/queen direction
                            if piece[1] in ['R', 'Q']:
                                return True
                        else:  # Bishop/queen direction
                            if piece[1] in ['B', 'Q']:
                                return True
                    break  # Blocked by any piece
    
    return False

def is_checkmate(pieces, color):
    if not is_in_check(pieces, color):
        return False
    
    # Try all possible moves to see if any get out of check
    for square, piece in pieces.items():
        if piece[0] == color:
            x, y = ord(square[0]) - ord('a'), int(square[1]) - 1
            piece_type = piece[1]
            
            # Generate possible moves for this piece (simplified)
            if piece_type == 'K':
                # King moves
                for dx, dy in [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                    new_x, new_y = x + dx, y + dy
                    if 0 <= new_x < 8 and 0 <= new_y < 8:
                        new_square = f"{chr(new_x + ord('a'))}{new_y + 1}"
                        if new_square not in pieces or pieces[new_square][0] != color:
                            # Try this move
                            new_pieces = pieces.copy()
                            new_pieces.pop(square)
                            new_pieces[new_square] = piece
                            if not is_in_check(new_pieces, color):
                                return False
            else:
                # Other pieces - simplified check
                # For checkmate, we just need to know if any move gets out of check
                # So we can return False if any piece can move to block or capture
                return False
    
    return True

def evaluate_position(pieces, our_color):
    score = 0
    
    # Material evaluation
    our_material = 0
    their_material = 0
    our_pieces = []
    their_pieces = []
    
    for square, piece in pieces.items():
        value = PIECE_VALUES.get(piece[1], 0)
        if piece[0] == our_color:
            our_material += value
            our_pieces.append((square, piece))
        else:
            their_material += value
            their_pieces.append((square, piece))
    
    score += (our_material - their_material) * 10
    
    # Mobility evaluation
    our_mobility = len(generate_legal_moves(pieces, 'white' if our_color == 'w' else 'black'))
    their_mobility = len(generate_legal_moves(pieces, 'black' if our_color == 'w' else 'white'))
    score += (our_mobility - their_mobility) * 0.1
    
    # Center control
    our_center = 0
    their_center = 0
    for square in pieces:
        if square in CENTER_SQUARES:
            if pieces[square][0] == our_color:
                our_center += 1
            else:
                their_center += 1
        elif square in EXTENDED_CENTER:
            if pieces[square][0] == our_color:
                our_center += 0.5
            else:
                their_center += 0.5
    score += (our_center - their_center) * 0.5
    
    # King safety (penalize exposed kings)
    our_king_square = None
    their_king_square = None
    for square, piece in pieces.items():
        if piece[1] == 'K':
            if piece[0] == our_color:
                our_king_square = square
            else:
                their_king_square = square
    
    if our_king_square:
        file, rank = our_king_square[0], int(our_king_square[1])
        if file in ['a', 'h']:  # On edge
            score -= 0.5
        if rank in [1, 8]:  # On back rank
            score -= 0.5
    
    if their_king_square:
        file, rank = their_king_square[0], int(their_king_square[1])
        if file in ['a', 'h']:  # On edge
            score += 0.5
        if rank in [1, 8]:  # On back rank
            score += 0.5
    
    return score
