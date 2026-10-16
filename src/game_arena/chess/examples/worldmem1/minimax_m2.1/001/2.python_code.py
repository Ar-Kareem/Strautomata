
from collections import defaultdict
import math

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Chess move selection policy that evaluates moves based on:
    1. Checkmate availability
    2. Material balance
    3. Positional strength
    4. Tactical opportunities
    
    Args:
        pieces: Dictionary mapping squares to piece codes (e.g., 'e1': 'bK')
        to_play: 'white' or 'black'
        legal_moves: List of legal move strings
        memory: Dictionary for storing state between calls
    
    Returns:
        Tuple of (selected_move, updated_memory)
    """
    
    # Parse piece codes
    our_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    # Build piece location maps
    our_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] == our_color}
    opp_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] == opp_color}
    
    # Parse all legal moves into structured format
    parsed_moves = []
    for move in legal_moves:
        parsed = parse_move(move, pieces, our_color)
        if parsed:
            parsed_moves.append(parsed)
    
    # Priority 1: Find checkmates
    for move in parsed_moves:
        if move['is_checkmate']:
            return move['raw'], memory
    
    # Priority 2: Find material-gaining captures (sorted by value)
    captures = [m for m in parsed_moves if m['is_capture']]
    captures.sort(key=lambda x: (x['captured_value'], -x['defended']), reverse=True)
    
    # Check if captures are safe (not losing material to discovered attack)
    safe_captures = []
    for cap in captures:
        if is_safe_capture(cap, pieces, parsed_moves, our_pieces, opp_pieces, our_color):
            safe_captures.append(cap)
    
    if safe_captures:
        # Prefer undefended captures that gain material
        best_capture = safe_captures[0]
        if best_capture['captured_value'] > best_capture['piece_value'] or best_capture['defended'] == 0:
            return best_capture['raw'], memory
    
    # Priority 3: Block checks or escape threats
    in_check = is_in_check(pieces, our_color)
    if in_check:
        check_escape = find_check_escape(parsed_moves, pieces, our_color)
        if check_escape:
            return check_escape['raw'], memory
    
    # Priority 4: Defend threatened pieces
    threatened = find_threatened_pieces(pieces, our_pieces, opp_color)
    if threatened:
        defense_moves = [m for m in parsed_moves if m['dest'] in threatened and m['piece_type'] != 'P']
        if defense_moves:
            defense_moves.sort(key=lambda x: x['threatened_value'], reverse=True)
            return defense_moves[0]['raw'], memory
    
    # Priority 5: Evaluate all moves positionally
    move_scores = []
    for move in parsed_moves:
        score = evaluate_move(move, pieces, our_pieces, opp_pieces, our_color)
        move_scores.append((score, move))
    
    move_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Return best move
    if move_scores:
        return move_scores[0][1]['raw'], memory
    else:
        return legal_moves[0], memory


def parse_move(move_str: str, pieces: dict[str, str], our_color: str) -> dict:
    """Parse a move string into structured information."""
    try:
        raw = move_str
        
        # Handle castling
        if move_str in ['O-O', 'O-O-O']:
            return {
                'raw': raw,
                'piece_type': 'K',
                'origin': None,
                'dest': move_str,
                'is_capture': False,
                'captured_value': 0,
                'piece_value': 0,
                'is_check': False,
                'is_checkmate': False,
                'promotion': None,
                'disambig': None
            }
        
        # Check for check/mate suffix
        is_check = '+' in move_str
        is_checkmate = '#' in move_str
        clean_move = move_str.replace('+', '').replace('#', '')
        
        # Handle promotion
        promotion = None
        if '=' in clean_move:
            parts = clean_move.split('=')
            clean_move = parts[0]
            promotion = parts[1]
        
        # Parse the move
        piece_type = None
        origin = None
        dest = None
        is_capture = 'x' in clean_move
        disambig = None
        
        # Handle captures like Bxf5
        if 'x' in clean_move:
            parts = clean_move.split('x')
            notation = parts[0]
            dest = parts[1]
            
            # Check for disambiguation (e.g., Nec3)
            if len(notation) == 3 and notation[1] in 'abcdefgh':
                disambig = notation[1]
                piece_type = notation[0]
                origin = notation[2]
            elif len(notation) == 2:
                if notation[0] in 'KQRBN':
                    piece_type = notation[0]
                else:
                    # File disambiguation
                    disambig = notation[0]
                    piece_type = 'P'
                origin = notation[1]
        else:
            # Non-capture
            dest = clean_move[-2:]
            notation = clean_move[:-2]
            
            if len(notation) >= 1:
                if notation[0] in 'KQRBN':
                    piece_type = notation[0]
                    rest = notation[1:]
                    if len(rest) == 1 and rest[0] in 'abcdefgh':
                        disambig = rest[0]
                    elif len(rest) == 2:
                        disambig = rest
                else:
                    # Pawn move with file disambiguation
                    piece_type = 'P'
                    disambig = notation[0]
        
        # Determine piece value
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
        piece_value = piece_values.get(piece_type, 0)
        
        # Determine captured piece value
        captured_value = 0
        if is_capture and dest in pieces:
            cap_piece = pieces[dest]
            cap_type = cap_piece[1]
            captured_value = piece_values.get(cap_type, 0)
        
        return {
            'raw': raw,
            'piece_type': piece_type,
            'origin': origin,
            'dest': dest,
            'is_capture': is_capture,
            'captured_value': captured_value,
            'piece_value': piece_value,
            'is_check': is_check,
            'is_checkmate': is_checkmate,
            'promotion': promotion,
            'disambig': disambig
        }
    except:
        return None


def is_in_check(pieces: dict[str, str], color: str) -> bool:
    """Check if the given color's king is in check."""
    # Find the king
    king_square = None
    for sq, pc in pieces.items():
        if pc == f'{color}K':
            king_square = sq
            break
    
    if not king_square:
        return False
    
    opp_color = 'b' if color == 'w' else 'w'
    
    # Check if any opponent piece attacks the king
    for sq, pc in pieces.items():
        if pc[0] == opp_color:
            piece_type = pc[1]
            attacks = get_attacks(sq, piece_type, pieces)
            if king_square in attacks:
                return True
    
    return False


def get_attacks(square: str, piece_type: str, pieces: dict[str, str]) -> set:
    """Get all squares attacked by a piece on the given square."""
    file_idx = ord(square[0]) - ord('a')
    rank_idx = int(square[1]) - 1
    attacks = set()
    
    piece_directions = {
        'R': [(1,0), (-1,0), (0,1), (0,-1)],
        'B': [(1,1), (1,-1), (-1,1), (-1,-1)],
        'Q': [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)],
        'N': [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)],
        'K': [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
    }
    
    if piece_type == 'P':
        direction = -1 if pieces.get(square, '')[0] == 'w' else 1
        attacks.add(chr(ord('a') + file_idx + 1) + str(rank_idx + direction + 1))
        attacks.add(chr(ord('a') + file_idx - 1) + str(rank_idx + direction + 1))
    elif piece_type in piece_directions:
        for dx, dy in piece_directions[piece_type]:
            x, y = file_idx, rank_idx
            step = 1 if piece_type in ['R', 'B', 'Q'] else 1
            for _ in range(1 if piece_type in ['K', 'N'] else 7):
                x += dx
                y += dy
                if 0 <= x < 8 and 0 <= y < 8:
                    sq = chr(ord('a') + x) + str(y + 1)
                    attacks.add(sq)
                    if sq in pieces:
                        break
                else:
                    break
    
    return attacks


def find_check_escape(moves: list, pieces: dict[str, str], color: str) -> dict:
    """Find a move that escapes check."""
    for move in moves:
        if move['dest'] in ['O-O', 'O-O-O']:
            continue
            
        # Simulate the move
        new_pieces = simulate_move(pieces, move)
        if not is_in_check(new_pieces, color):
            return move
    
    return None


def simulate_move(pieces: dict[str, str], move: dict) -> dict:
    """Simulate a move and return the new position."""
    new_pieces = pieces.copy()
    
    if move['dest'] in ['O-O', 'O-O-O']:
        return new_pieces  # Castling handling is complex, skip for simplicity
    
    origin = None
    if move['origin']:
        if move['disambig'] and len(move['disambig']) == 2:
            origin = move['disambig']
        elif move['disambig'] and move['disambig'] in 'abcdefgh':
            origin = move['disambig'] + move['origin']
        else:
            origin = move['origin']
    
    # Find the actual origin square
    if origin:
        for sq, pc in pieces.items():
            if pc[0] == ('w' if move['piece_type'].isupper() else 'b'):
                if pc[1] == move['piece_type']:
                    if sq[0] == origin[0] and (len(origin) == 1 or sq[1] == origin[1]):
                        origin = sq
                        break
    else:
        # Find the piece that can move to dest
        for sq, pc in pieces.items():
            if pc[0] == ('w' if move['piece_type'].isupper() else 'b'):
                if pc[1] == move['piece_type']:
                    attacks = get_attacks(sq, move['piece_type'], pieces)
                    if move['dest'] in attacks:
                        origin = sq
                        break
    
    if not origin:
        return new_pieces
    
    # Remove captured piece
    if move['is_capture'] and move['dest'] in new_pieces:
        del new_pieces[move['dest']]
    
    # Move the piece
    del new_pieces[origin]
    color = 'w' if move['piece_type'].isupper() else 'b'
    piece_code = color + move['piece_type']
    if move['promotion']:
        piece_code = color + move['promotion']
    new_pieces[move['dest']] = piece_code
    
    return new_pieces


def is_safe_capture(move: dict, pieces: dict, all_moves: list, our_pieces: dict, opp_pieces: dict, color: str) -> bool:
    """Check if a capture is safe (not losing to discovered attack)."""
    if not move['is_capture']:
        return False
    
    # If capturing an undefended piece, it's likely safe
    dest = move['dest']
    opp_color = 'b' if color == 'w' else 'w'
    
    # Check if the destination square is defended
    is_defended = False
    for sq, pc in opp_pieces.items():
        attacks = get_attacks(sq, pc[1], pieces)
        if dest in attacks:
            is_defended = True
            break
    
    if not is_defended:
        return True
    
    # If defended, check if we're capturing a higher value piece
    if move['captured_value'] > move['piece_value']:
        return True
    
    # Otherwise, be cautious
    return False


def find_threatened_pieces(pieces: dict[str, str], our_pieces: dict[str, str], opp_color: str) -> set:
    """Find our pieces that are under attack."""
    threatened = set()
    
    for sq, pc in our_pieces.items():
        piece_type = pc[1]
        if piece_type == 'K':
            continue
            
        # Check if any opponent piece attacks this square
        for opp_sq, opp_pc in pieces.items():
            if opp_pc[0] == opp_color:
                attacks = get_attacks(opp_sq, opp_pc[1], pieces)
                if sq in attacks:
                    threatened.add(sq)
                    break
    
    return threatened


def evaluate_move(move: dict, pieces: dict, our_pieces: dict, opp_pieces: dict, color: str) -> float:
    """Evaluate a move and return a score."""
    score = 0.0
    
    # Base piece value
    score += move['piece_value'] * 10
    
    # Capture bonus
    if move['is_capture']:
        score += move['captured_value'] * 15
        # Extra bonus for capturing defended piece
        score += 5
    
    # Piece-square tables for positional evaluation
    center_control = {'d4': 3, 'e4': 3, 'd5': 3, 'e5': 3,
                      'c4': 2, 'e4': 2, 'd4': 2, 'c5': 2, 'd5': 2, 'e5': 2}
    
    if move['dest'] in center_control:
        score += center_control[move['dest']]
    
    # Development bonus (moving pieces from starting squares)
    if move['piece_type'] in ['N', 'B']:
        development_squares = {'b1': 'N', 'c1': 'B', 'g1': 'N', 'f1': 'B',
                               'b8': 'N', 'c8': 'B', 'g8': 'N', 'f8': 'B'}
        if move['origin'] in development_squares:
            score += 2
    
    # King safety
    if move['piece_type'] == 'K':
        # Prefer castling for king safety
        if move['dest'] in ['O-O', 'O-O-O']:
            score += 5
        else:
            score -= 2  # King shouldn't move unnecessarily
    
    # Pawn advancement (with diminishing returns)
    if move['piece_type'] == 'P':
        dest_rank = int(move['dest'][1])
        if color == 'w':
            score += dest_rank - 1
        else:
            score += 8 - dest_rank
    
    # Connectivity bonus (pieces protecting each other)
    if move['dest']:
        for sq, pc in our_pieces.items():
            if sq != move.get('origin'):
                attacks = get_attacks(sq, pc[1], pieces)
                if move['dest'] in attacks:
                    score += 0.5
    
    # Add small random factor for variety
    score += hash(move['raw']) % 100 / 1000.0
    
    return score
