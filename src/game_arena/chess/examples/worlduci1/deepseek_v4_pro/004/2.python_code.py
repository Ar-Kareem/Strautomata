
import numpy as np
from typing import Dict, List, Tuple, Optional

def policy(pieces: dict, to_play: str) -> str:
    """
    Chess move selection policy using material and positional evaluation.
    """
    
    # Piece values for material evaluation
    PIECE_VALUES = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
    }
    
    # Positional bonuses for piece squares (simplified)
    # Center control bonus
    CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}
    CENTER_ADJACENT = {'c3', 'c4', 'c5', 'c6', 'd3', 'e3', 'f3', 'f4', 'f5', 'f6', 'd6', 'e6'}
    
    PAWN_BONUS = {
        'white': {'a7': 50, 'b7': 50, 'c7': 50, 'd7': 50, 'e7': 50, 'f7': 50, 'g7': 50, 'h7': 50,
                  'a6': 30, 'b6': 30, 'c6': 30, 'd6': 30, 'e6': 30, 'f6': 30, 'g6': 30, 'h6': 30},
        'black': {'a2': 50, 'b2': 50, 'c2': 50, 'd2': 50, 'e2': 50, 'f2': 50, 'g2': 50, 'h2': 50,
                  'a3': 30, 'b3': 30, 'c3': 30, 'd3': 30, 'e3': 30, 'f3': 30, 'g3': 30, 'h3': 30}
    }
    
    KNIGHT_BONUS = {
        'c3': 20, 'd3': 20, 'e3': 20, 'f3': 20, 'c4': 30, 'd4': 30, 'e4': 30, 'f4': 30,
        'c5': 30, 'd5': 30, 'e5': 30, 'f5': 30, 'c6': 20, 'd6': 20, 'e6': 20, 'f6': 20
    }
    
    BISHOP_BONUS = {
        'c4': 20, 'd4': 25, 'e4': 25, 'f4': 20, 'c3': 15, 'd3': 20, 'e3': 20, 'f3': 15,
        'd5': 25, 'e5': 25, 'c5': 20, 'f5': 20
    }
    
    ROOK_BONUS = {
        'd1': 15, 'e1': 15, 'd8': 15, 'e8': 15, 'c1': 10, 'f1': 10, 'c8': 10, 'f8': 10
    }
    
    def get_color(piece_code: str) -> str:
        return 'white' if piece_code[0] == 'w' else 'black'
    
    def get_type(piece_code: str) -> str:
        return piece_code[1]
    
    def algebraic_to_coords(square: str) -> Tuple[int, int]:
        file_idx = ord(square[0]) - ord('a')
        rank_idx = int(square[1]) - 1
        return (file_idx, rank_idx)
    
    def coords_to_algebraic(file_idx: int, rank_idx: int) -> str:
        return chr(ord('a') + file_idx) + str(rank_idx + 1)
    
    def get_legal_moves_from_position(pieces: Dict[str, str], to_play: str) -> List[str]:
        """Generate all legal moves from the current position."""
        legal_moves = []
        our_color = 'w' if to_play == 'white' else 'b'
        opponent_color = 'b' if to_play == 'white' else 'w'
        
        # Find our king position
        king_pos = None
        for square, piece in pieces.items():
            if piece == f'{our_color}K':
                king_pos = square
                break
        
        if king_pos is None:
            return legal_moves
        
        # Check if we are in check
        in_check = is_square_attacked(pieces, king_pos, opponent_color)
        
        for from_square, piece in pieces.items():
            if get_color(piece) != our_color:
                continue
            
            piece_type = get_type(piece)
            from_coords = algebraic_to_coords(from_square)
            
            possible_moves = []
            
            if piece_type == 'P':
                possible_moves = get_pawn_moves(pieces, from_square, our_color)
            elif piece_type == 'N':
                possible_moves = get_knight_moves(pieces, from_square, our_color)
            elif piece_type == 'B':
                possible_moves = get_sliding_moves(pieces, from_square, our_color, [(1, 1), (1, -1), (-1, 1), (-1, -1)])
            elif piece_type == 'R':
                possible_moves = get_sliding_moves(pieces, from_square, our_color, [(1, 0), (-1, 0), (0, 1), (0, -1)])
            elif piece_type == 'Q':
                possible_moves = get_sliding_moves(pieces, from_square, our_color, 
                                                   [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)])
            elif piece_type == 'K':
                possible_moves = get_king_moves(pieces, from_square, our_color)
            
            for to_square in possible_moves:
                # Make move on a copy
                new_pieces = pieces.copy()
                del new_pieces[from_square]
                new_pieces[to_square] = piece
                
                # Check if our king is safe after the move
                new_king_pos = to_square if piece_type == 'K' else king_pos
                if not is_square_attacked(new_pieces, new_king_pos, opponent_color):
                    # Handle promotions
                    if piece_type == 'P':
                        to_rank = int(to_square[1])
                        if (our_color == 'w' and to_rank == 8) or (our_color == 'b' and to_rank == 1):
                            for promo in ['q', 'r', 'b', 'n']:
                                legal_moves.append(from_square + to_square + promo)
                            continue
                    
                    legal_moves.append(from_square + to_square)
        
        return legal_moves
    
    def is_square_attacked(pieces: Dict[str, str], square: str, attacker_color: str) -> bool:
        """Check if a square is attacked by any piece of attacker_color."""
        sq_coords = algebraic_to_coords(square)
        
        for from_sq, piece in pieces.items():
            if get_color(piece) != attacker_color:
                continue
            
            piece_type = get_type(piece)
            from_coords = algebraic_to_coords(from_sq)
            
            # Quick check: different piece types
            if piece_type == 'P':
                direction = 1 if attacker_color == 'w' else -1
                # Pawns attack diagonally
                if (from_coords[0] + 1 == sq_coords[0] or from_coords[0] - 1 == sq_coords[0]) and \
                   from_coords[1] + direction == sq_coords[1]:
                    return True
            
            elif piece_type == 'N':
                dx = abs(from_coords[0] - sq_coords[0])
                dy = abs(from_coords[1] - sq_coords[1])
                if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
                    return True
            
            elif piece_type == 'B':
                if abs(from_coords[0] - sq_coords[0]) == abs(from_coords[1] - sq_coords[1]) and \
                   abs(from_coords[0] - sq_coords[0]) > 0:
                    dx = 1 if sq_coords[0] > from_coords[0] else -1
                    dy = 1 if sq_coords[1] > from_coords[1] else -1
                    x, y = from_coords[0] + dx, from_coords[1] + dy
                    blocked = False
                    while (x, y) != sq_coords:
                        if coords_to_algebraic(x, y) in pieces:
                            blocked = True
                            break
                        x += dx
                        y += dy
                    if not blocked:
                        return True
            
            elif piece_type == 'R':
                if from_coords[0] == sq_coords[0] or from_coords[1] == sq_coords[1]:
                    if from_coords[0] == sq_coords[0]:
                        dx, dy = 0, 1 if sq_coords[1] > from_coords[1] else -1
                    else:
                        dx, dy = 1 if sq_coords[0] > from_coords[0] else -1, 0
                    
                    x, y = from_coords[0] + dx, from_coords[1] + dy
                    blocked = False
                    while (x, y) != sq_coords:
                        if coords_to_algebraic(x, y) in pieces:
                            blocked = True
                            break
                        x += dx
                        y += dy
                    if not blocked:
                        return True
            
            elif piece_type == 'Q':
                if from_coords[0] == sq_coords[0] or from_coords[1] == sq_coords[1] or \
                   abs(from_coords[0] - sq_coords[0]) == abs(from_coords[1] - sq_coords[1]):
                    dx = 0 if from_coords[0] == sq_coords[0] else (1 if sq_coords[0] > from_coords[0] else -1)
                    dy = 0 if from_coords[1] == sq_coords[1] else (1 if sq_coords[1] > from_coords[1] else -1)
                    
                    if dx == 0 and dy == 0:
                        continue
                    
                    x, y = from_coords[0] + dx, from_coords[1] + dy
                    blocked = False
                    while (x, y) != sq_coords:
                        if coords_to_algebraic(x, y) in pieces:
                            blocked = True
                            break
                        x += dx
                        y += dy
                    if not blocked:
                        return True
            
            elif piece_type == 'K':
                dx = abs(from_coords[0] - sq_coords[0])
                dy = abs(from_coords[1] - sq_coords[1])
                if dx <= 1 and dy <= 1 and (dx > 0 or dy > 0):
                    return True
        
        return False
    
    def get_pawn_moves(pieces: Dict[str, str], square: str, color: str) -> List[str]:
        moves = []
        coords = algebraic_to_coords(square)
        direction = 1 if color == 'w' else -1
        start_rank = 1 if color == 'w' else 6
        
        # Forward move
        forward = coords_to_algebraic(coords[0], coords[1] + direction)
        if forward not in pieces:
            moves.append(forward)
            # Double move from starting position
            if coords[1] == start_rank:
                double_forward = coords_to_algebraic(coords[0], coords[1] + 2 * direction)
                if double_forward not in pieces:
                    moves.append(double_forward)
        
        # Captures
        for dx in [-1, 1]:
            new_file = coords[0] + dx
            if 0 <= new_file < 8:
                capture_square = coords_to_algebraic(new_file, coords[1] + direction)
                if capture_square in pieces and get_color(pieces[capture_square]) != color:
                    moves.append(capture_square)
        
        return moves
    
    def get_knight_moves(pieces: Dict[str, str], square: str, color: str) -> List[str]:
        moves = []
        coords = algebraic_to_coords(square)
        knight_offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        
        for dx, dy in knight_offsets:
            new_file = coords[0] + dx
            new_rank = coords[1] + dy
            if 0 <= new_file < 8 and 0 <= new_rank < 8:
                new_square = coords_to_algebraic(new_file, new_rank)
                if new_square not in pieces or get_color(pieces[new_square]) != color:
                    moves.append(new_square)
        
        return moves
    
    def get_sliding_moves(pieces: Dict[str, str], square: str, color: str, directions: List[Tuple[int, int]]) -> List[str]:
        moves = []
        coords = algebraic_to_coords(square)
        
        for dx, dy in directions:
            file_idx, rank_idx = coords[0] + dx, coords[1] + dy
            while 0 <= file_idx < 8 and 0 <= rank_idx < 8:
                new_square = coords_to_algebraic(file_idx, rank_idx)
                if new_square in pieces:
                    if get_color(pieces[new_square]) != color:
                        moves.append(new_square)
                    break
                moves.append(new_square)
                file_idx += dx
                rank_idx += dy
        
        return moves
    
    def get_king_moves(pieces: Dict[str, str], square: str, color: str) -> List[str]:
        moves = []
        coords = algebraic_to_coords(square)
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_file = coords[0] + dx
                new_rank = coords[1] + dy
                if 0 <= new_file < 8 and 0 <= new_rank < 8:
                    new_square = coords_to_algebraic(new_file, new_rank)
                    if new_square not in pieces or get_color(pieces[new_square]) != color:
                        moves.append(new_square)
        
        return moves
    
    def evaluate_position(pieces: Dict[str, str], to_play: str) -> float:
        """Evaluate the position from the perspective of 'to_play'."""
        score = 0.0
        our_color = 'w' if to_play == 'white' else 'b'
        opponent_color = 'b' if to_play == 'white' else 'w'
        
        for square, piece in pieces.items():
            piece_type = get_type(piece)
            piece_color = 'white' if get_color(piece) == 'w' else 'black'
            value = PIECE_VALUES[piece_type]
            
            if piece_color == to_play:
                score += value
                # Positional bonuses
                if piece_type == 'P':
                    if square in PAWN_BONUS.get(to_play, {}):
                        score += PAWN_BONUS[to_play][square]
                    if square in CENTER_SQUARES:
                        score += 10
                elif piece_type == 'N':
                    if square in KNIGHT_BONUS:
                        score += KNIGHT_BONUS[square]
                    if square in CENTER_SQUARES:
                        score += 15
                elif piece_type == 'B':
                    if square in BISHOP_BONUS:
                        score += BISHOP_BONUS[square]
                    if square in CENTER_SQUARES:
                        score += 10
                elif piece_type == 'R':
                    if square in ROOK_BONUS:
                        score += ROOK_BONUS[square]
                    # Bonus for rooks on open files
                    file_idx = algebraic_to_coords(square)[0]
                    has_pawn = False
                    for s, p in pieces.items():
                        if get_type(p) == 'P' and algebraic_to_coords(s)[0] == file_idx:
                            has_pawn = True
                            break
                    if not has_pawn:
                        score += 15
                elif piece_type == 'Q':
                    if square in CENTER_SQUARES:
                        score += 5
                elif piece_type == 'K':
                    # King safety: penalize exposed king, reward castled king
                    if to_play == 'white':
                        if square in {'g1', 'c1'}:
                            score += 30
                        if square in {'b1', 'f1', 'h1', 'a1', 'd1'} and len(pieces) > 10:
                            score -= 10
                    else:
                        if square in {'g8', 'c8'}:
                            score += 30
                        if square in {'b8', 'f8', 'h8', 'a8', 'd8'} and len(pieces) > 10:
                            score -= 10
            else:
                score -= value
                # Opponent positional penalties
                if piece_type == 'P':
                    if square in PAWN_BONUS.get(piece_color, {}):
                        score -= PAWN_BONUS[piece_color][square]
                elif piece_type == 'N':
                    if square in KNIGHT_BONUS:
                        score -= KNIGHT_BONUS[square]
                elif piece_type == 'B':
                    if square in BISHOP_BONUS:
                        score -= BISHOP_BONUS[square]
                elif piece_type == 'K':
                    # Weaker opponent king is good for us
                    if piece_color == 'white':
                        if square in {'e1', 'd1', 'f1'} and len(pieces) > 10:
                            score += 20
                    else:
                        if square in {'e8', 'd8', 'f8'} and len(pieces) > 10:
                            score += 20
        
        # Mobility bonus (our moves minus opponent moves)
        our_moves = len(get_legal_moves_from_position(pieces, to_play))
        
        # Create a temporary position to count opponent moves
        temp_pieces = pieces.copy()
        # Swap perspective for opponent move count
        opp_to_play = 'black' if to_play == 'white' else 'white'
        opp_moves = len(get_legal_moves_from_position(temp_pieces, opp_to_play))
        
        score += (our_moves - opp_moves) * 5
        
        return score
    
    # Generate legal moves
    legal_moves = get_legal_moves_from_position(pieces, to_play)
    
    if not legal_moves:
        return ""
    
    our_color = 'w' if to_play == 'white' else 'b'
    
    # Evaluate each move
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        # Simulate the move
        from_square = move[:2]
        to_square = move[2:4]
        promotion = move[4:] if len(move) > 4 else None
        
        new_pieces = pieces.copy()
        moving_piece = new_pieces[from_square]
        del new_pieces[from_square]
        
        if promotion:
            new_pieces[to_square] = f'{our_color}{promotion.upper()}'
        else:
            new_pieces[to_square] = moving_piece
        
        # Evaluate the resulting position (opponent's turn)
        opp_to_play = 'black' if to_play == 'white' else 'white'
        score = evaluate_position(new_pieces, to_play)
        
        # Bonus for captures
        if to_square in pieces and get_color(pieces[to_square]) != our_color:
            captured_value = PIECE_VALUES[get_type(pieces[to_square])]
            score += captured_value * 0.5
        
        # Bonus for promotions
        if promotion:
            promo_value = PIECE_VALUES[promotion.upper()]
            score += promo_value - PIECE_VALUES['P']
        
        # Bonus for checks
        opp_color = 'b' if to_play == 'white' else 'w'
        opp_king_pos = None
        for sq, p in new_pieces.items():
            if p == f'{opp_color}K':
                opp_king_pos = sq
                break
        
        if opp_king_pos and is_square_attacked(new_pieces, opp_king_pos, our_color):
            score += 50
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
