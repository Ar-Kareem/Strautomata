
import math
from typing import Dict, List, Tuple, Optional
import copy

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables for positional evaluation
# Higher values = better squares
PAWN_PST = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_PST = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_PST = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

ROOK_PST = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

QUEEN_PST = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

KING_PST_MIDDLEGAME = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

KING_PST_ENDGAME = [
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
]

# Direction vectors for piece movement
KNIGHT_DIRS = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
BISHOP_DIRS = [(-1,-1), (-1,1), (1,-1), (1,1)]
ROOK_DIRS = [(-1,0), (1,0), (0,-1), (0,1)]
KING_DIRS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]


def parse_square(square: str) -> Tuple[int, int]:
    """Convert algebraic notation to (file, rank) 0-indexed."""
    file_idx = ord(square[0]) - ord('a')
    rank_idx = int(square[1]) - 1
    return (file_idx, rank_idx)


def square_to_str(file_idx: int, rank_idx: int) -> str:
    """Convert (file, rank) 0-indexed to algebraic notation."""
    return chr(ord('a') + file_idx) + str(rank_idx + 1)


def get_piece_info(piece_code: str) -> Tuple[str, str]:
    """Parse piece code into (color, type)."""
    return (piece_code[0], piece_code[1])


def evaluate_position(pieces: Dict[str, str], to_play: str) -> float:
    """Evaluate position from perspective of player to play."""
    eval_score = 0.0
    
    # Count material for both sides
    white_material = 0
    black_material = 0
    pawn_count = {'w': 0, 'b': 0}
    
    for square, piece_code in pieces.items():
        color, ptype = get_piece_info(piece_code)
        file_idx, rank_idx = parse_square(square)
        
        # Material value
        material = PIECE_VALUES[ptype]
        if color == 'w':
            white_material += material
            pawn_count['w'] += 1
        else:
            black_material += material
            pawn_count['b'] += 1
        
        # Positional value based on piece type
        if ptype == 'P':
            pst = PAWN_PST
            # Flip for black
            if color == 'b':
                pst = [[pst[7-rank][file] for file in range(8)] for rank in range(8)]
            eval_score += pst[rank_idx][file_idx] if color == 'w' else -pst[rank_idx][file_idx]
            
        elif ptype == 'N':
            pst = KNIGHT_PST
            if color == 'b':
                pst = [[pst[7-rank][file] for file in range(8)] for rank in range(8)]
            eval_score += pst[rank_idx][file_idx] if color == 'w' else -pst[rank_idx][file_idx]
            
        elif ptype == 'B':
            pst = BISHOP_PST
            if color == 'b':
                pst = [[pst[7-rank][file] for file in range(8)] for rank in range(8)]
            eval_score += pst[rank_idx][file_idx] if color == 'w' else -pst[rank_idx][file_idx]
            
        elif ptype == 'R':
            pst = ROOK_PST
            if color == 'b':
                pst = [[pst[7-rank][file] for file in range(8)] for rank in range(8)]
            eval_score += pst[rank_idx][file_idx] if color == 'w' else -pst[rank_idx][file_idx]
            
        elif ptype == 'Q':
            pst = QUEEN_PST
            if color == 'b':
                pst = [[pst[7-rank][file] for file in range(8)] for rank in range(8)]
            eval_score += pst[rank_idx][file_idx] if color == 'w' else -pst[rank_idx][file_idx]
            
        elif ptype == 'K':
            # Use endgame PST if few pieces remain
            total_material = white_material + black_material
            if total_material < 3000:
                pst = KING_PST_ENDGAME
            else:
                pst = KING_PST_MIDDLEGAME
            if color == 'b':
                pst = [[pst[7-rank][file] for file in range(8)] for rank in range(8)]
            eval_score += pst[rank_idx][file_idx] if color == 'w' else -pst[rank_idx][file_idx]
    
    # Final material difference
    material_diff = white_material - black_material
    eval_score += material_diff
    
    return eval_score if to_play == 'white' else -eval_score


def make_move(pieces: Dict[str, str], move: str, to_play: str) -> Dict[str, str]:
    """Apply a move to the position and return new pieces dict."""
    new_pieces = pieces.copy()
    
    # Parse the move
    move = move.strip()
    
    # Handle castling
    if move == 'O-O' or move == 'O-O-O':
        if to_play == 'white':
            if move == 'O-O':
                new_pieces['f1'] = 'wK'
                new_pieces['h1'] = 'wR'
                if 'e1' in new_pieces:
                    del new_pieces['e1']
                if 'h1' in new_pieces:
                    del new_pieces['h1']
            else:  # O-O-O
                new_pieces['d1'] = 'wK'
                new_pieces['a1'] = 'wR'
                if 'e1' in new_pieces:
                    del new_pieces['e1']
                if 'a1' in new_pieces:
                    del new_pieces['a1']
        else:
            if move == 'O-O':
                new_pieces['f8'] = 'bK'
                new_pieces['h8'] = 'bR'
                if 'e8' in new_pieces:
                    del new_pieces['e8']
                if 'h8' in new_pieces:
                    del new_pieces['h8']
            else:  # O-O-O
                new_pieces['d8'] = 'bK'
                new_pieces['a8'] = 'bR'
                if 'e8' in new_pieces:
                    del new_pieces['e8']
                if 'a8' in new_pieces:
                    del new_pieces['a8']
        return new_pieces
    
    # Handle promotion
    promotion_piece = None
    if '=' in move:
        parts = move.split('=')
        move = parts[0]
        promotion_piece = parts[1]
    
    # Handle capture
    capture = 'x' in move
    
    # Determine piece type and target square
    piece_type = 'P'
    if move[0] in 'KQRBN':
        piece_type = move[0]
        move = move[1:]
    
    # Remove check/mate symbols
    while move and move[-1] in '+#=':
        if move[-1] == '=':
            break
        move = move[:-1]
    
    # Find target square (last 2 characters)
    target_square = move[-2:]
    
    # Find source square
    if capture:
        move = move[:-3]  # Remove 'x' and target
    else:
        move = move[:-2]  # Remove target
    
    source_square = move
    
    # Apply the move
    if source_square:
        # Remove piece from source
        if source_square in new_pieces:
            piece_code = new_pieces[source_square]
            del new_pieces[source_square]
        else:
            # Disambiguation should have been resolved
            piece_code = to_play[0][0] + piece_type
    else:
        # Pawn move without disambiguation
        piece_code = to_play[0][0] + piece_type
    
    # Handle capture - remove captured piece
    if capture and target_square in new_pieces:
        del new_pieces[target_square]
    
    # Place piece at target
    if promotion_piece:
        piece_code = to_play[0][0] + promotion_piece
    new_pieces[target_square] = piece_code
    
    return new_pieces


def is_check(pieces: Dict[str, str], king_color: str) -> bool:
    """Check if king of given color is in check."""
    # Find the king
    king_square = None
    target_piece = king_color + 'K'
    for square, piece in pieces.items():
        if piece == target_piece:
            king_square = square
            break
    
    if not king_square:
        return False
    
    kf, kr = parse_square(king_square)
    opponent = 'b' if king_color == 'w' else 'w'
    
    # Check for pawn attacks
    if king_color == 'w':
        # White king attacked by black pawns from below
        if kf > 0 and kr > 0:
            left_pawn = square_to_str(kf-1, kr-1)
            if left_pawn in pieces and pieces[left_pawn] == 'bP':
                return True
        if kf < 7 and kr > 0:
            right_pawn = square_to_str(kf+1, kr-1)
            if right_pawn in pieces and pieces[right_pawn] == 'bP':
                return True
    else:
        # Black king attacked by white pawns from above
        if kf > 0 and kr < 7:
            left_pawn = square_to_str(kf-1, kr+1)
            if left_pawn in pieces and pieces[left_pawn] == 'wP':
                return True
        if kf < 7 and kr < 7:
            right_pawn = square_to_str(kf+1, kr+1)
            if right_pawn in pieces and pieces[right_pawn] == 'wP':
                return True
    
    # Check for knight attacks
    for df, dr in KNIGHT_DIRS:
        nf, nr = kf + df, kr + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            square = square_to_str(nf, nr)
            if square in pieces:
                piece = pieces[square]
                if piece[0] == opponent and piece[1] == 'N':
                    return True
    
    # Check for sliding attacks (bishop, rook, queen)
    all_dirs = BISHOP_DIRS + ROOK_DIRS
    for df, dr in all_dirs:
        nf, nr = kf + df, kr + dr
        steps = 1
        while 0 <= nf < 8 and 0 <= nr < 8:
            square = square_to_str(nf, nr)
            if square in pieces:
                piece = pieces[square]
                if piece[0] == opponent:
                    ptype = piece[1]
                    # Determine if this piece can attack the king
                    can_attack = False
                    if (df, dr) in BISHOP_DIRS and ptype in ['B', 'Q']:
                        can_attack = True
                    elif (df, dr) in ROOK_DIRS and ptype in ['R', 'Q']:
                        can_attack = True
                    if can_attack:
                        return True
                break
            nf += df
            nr += dr
            steps += 1
    
    # Check for king attacks
    for df, dr in KING_DIRS:
        nf, nr = kf + df, kr + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            square = square_to_str(nf, nr)
            if square in pieces and pieces[square] == opponent + 'K':
                return True
    
    return False


def is_checkmate(pieces: Dict[str, str], to_play: str) -> bool:
    """Check if position is checkmate for the player to play."""
    if not is_check(pieces, to_play[0]):
        return False
    
    # If in check and no legal moves, it's checkmate
    # This is a simplified check - we'll rely on the legal_moves list
    return True


def get_capture_value(move: str, pieces: Dict[str, str]) -> int:
    """Get the material value gained from a capture move."""
    if 'x' not in move:
        return 0
    
    # Find target square
    parts = move.split('x')
    target_square = parts[1].split('+')[0].split('#')[0]
    
    if target_square in pieces:
        captured_piece = pieces[target_square]
        return PIECE_VALUES[captured_piece[1]]
    return 0


def get_piece_type_from_move(move: str) -> str:
    """Extract piece type from move string."""
    move = move.strip()
    if move[0] in 'KQRBN':
        return move[0]
    return 'P'


def order_moves(moves: List[str], pieces: Dict[str, str], to_play: str) -> List[str]:
    """Order moves for better alpha-beta pruning."""
    scored_moves = []
    
    for move in moves:
        score = 0
        
        # Prioritize checks and checkmates
        if '+' in move or '#' in move:
            score += 10000
            if '#' in move:
                score += 50000
        
        # Prioritize captures by value
        capture_value = get_capture_value(move, pieces)
        score += capture_value
        
        # Prioritize promotions
        if '=' in move:
            score += 900
        
        # Prioritize castling
        if move in ['O-O', 'O-O-O']:
            score += 500
        
        # Prioritize queen moves slightly
        if move.startswith('Q') and 'x' not in move and '+' not in move:
            score += 10
        
        scored_moves.append((score, move))
    
    # Sort by score descending
    scored_moves.sort(key=lambda x: -x[1])
    return [m[0] for m in scored_moves]


def minimax(pieces: Dict[str, str], depth: int, alpha: float, beta: float, 
            maximizing: bool, to_play: str, legal_moves: List[str]) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_position(pieces, to_play)
    
    if not legal_moves:
        # No moves available - check if checkmate or stalemate
        if is_check(pieces, to_play[0]):
            return -100000 if maximizing else 100000
        else:
            return 0
    
    if maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            new_pieces = make_move(pieces, move, to_play)
            next_to_play = 'black' if to_play == 'white' else 'white'
            # Generate legal moves for opponent (simplified - use all possible moves)
            opponent_moves = get_all_legal_moves(new_pieces, next_to_play)
            eval_score = minimax(new_pieces, depth - 1, alpha, beta, False, 
                               next_to_play, opponent_moves)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_pieces = make_move(pieces, move, to_play)
            next_to_play = 'black' if to_play == 'white' else 'white'
            opponent_moves = get_all_legal_moves(new_pieces, next_to_play)
            eval_score = minimax(new_pieces, depth - 1, alpha, beta, True, 
                               next_to_play, opponent_moves)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def get_all_legal_moves(pieces: Dict[str, str], to_play: str) -> List[str]:
    """Generate all pseudo-legal moves. In a full engine, this would use a proper move generator."""
    # This is a simplified move generator for the search
    # It generates some plausible moves for each piece type
    moves = []
    color_prefix = to_play[0]
    
    # Find all pieces of the current player
    player_pieces = {}
    for square, piece in pieces.items():
        if piece[0] == color_prefix:
            player_pieces[square] = piece
    
    # Generate moves for each piece (simplified - not exhaustive)
    for square, piece in player_pieces.items():
        ptype = piece[1]
        sf, sr = parse_square(square)
        
        if ptype == 'P':
            # Pawn moves
            direction = 1 if color_prefix == 'w' else -1
            
            # Forward move
            nf, nr = sf, sr + direction
            if 0 <= nr < 8:
                target = square_to_str(nf, nr)
                if target not in pieces:
                    # Check for promotion
                    if nr == 7 or nr == 0:
                        for promo in ['Q', 'R', 'B', 'N']:
                            moves.append(f'{square}{target}={promo}')
                    else:
                        moves.append(square + target)
                    
                    # Double move from starting position
                    if (sr == 1 and color_prefix == 'w') or (sr == 6 and color_prefix == 'b'):
                        nr2 = sr + 2 * direction
                        target2 = square_to_str(nf, nr2)
                        if target2 not in pieces:
                            moves.append(square + target2)
            
            # Captures
            for df in [-1, 1]:
                nf, nr = sf + df, sr + direction
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = square_to_str(nf, nr)
                    if target in pieces and pieces[target][0] != color_prefix:
                        if nr == 7 or nr == 0:
                            for promo in ['Q', 'R', 'B', 'N']:
                                moves.append(f'{square}x{target}={promo}')
                        else:
                            moves.append(square + 'x' + target)
        
        elif ptype == 'N':
            for df, dr in KNIGHT_DIRS:
                nf, nr = sf + df, sr + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = square_to_str(nf, nr)
                    if target not in pieces or pieces[target][0] != color_prefix:
                        move_str = f'N{square}{target}' if target not in pieces else f'N{square}x{target}'
                        moves.append(move_str)
        
        elif ptype == 'B':
            for df, dr in BISHOP_DIRS:
                nf, nr = sf + df, sr + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = square_to_str(nf, nr)
                    if target not in pieces:
                        moves.append(f'B{target}')
                    else:
                        if pieces[target][0] != color_prefix:
                            moves.append(f'B{square}x{target}')
                        break
                    nf += df
                    nr += dr
        
        elif ptype == 'R':
            for df, dr in ROOK_DIRS:
                nf, nr = sf + df, sr + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = square_to_str(nf, nr)
                    if target not in pieces:
                        moves.append(f'R{target}')
                    else:
                        if pieces[target][0] != color_prefix:
                            moves.append(f'R{square}x{target}')
                        break
                    nf += df
                    nr += dr
        
        elif ptype == 'Q':
            for df, dr in BISHOP_DIRS + ROOK_DIRS:
                nf, nr = sf + df, sr + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = square_to_str(nf, nr)
                    if target not in pieces:
                        moves.append(f'Q{target}')
                    else:
                        if pieces[target][0] != color_prefix:
                            moves.append(f'Q{square}x{target}')
                        break
                    nf += df
                    nr += dr
        
        elif ptype == 'K':
            for df, dr in KING_DIRS:
                nf, nr = sf + df, sr + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = square_to_str(nf, nr)
                    if target not in pieces or pieces[target][0] != color_prefix:
                        move_str = f'K{target}' if target not in pieces else f'K{square}x{target}'
                        moves.append(move_str)
            
            # Simple castling check (not comprehensive)
            if to_play == 'white' and sf == 4 and sr == 0:
                if 'e1' in pieces and pieces['e1'] == 'wK':
                    if 'h1' in pieces and pieces['h1'] == 'wR':
                        if 'f1' not in pieces and 'g1' not in pieces:
                            if not is_check(pieces, 'w'):
                                moves.append('O-O')
                    if 'a1' in pieces and pieces['a1'] == 'wR':
                        if 'b1' not in pieces and 'c1' not in pieces and 'd1' not in pieces:
                            if not is_check(pieces, 'w'):
                                moves.append('O-O-O')
            elif to_play == 'black' and sf == 4 and sr == 7:
                if 'e8' in pieces and pieces['e8'] == 'bK':
                    if 'h8' in pieces and pieces['h8'] == 'bR':
                        if 'f8' not in pieces and 'g8' not in pieces:
                            if not is_check(pieces, 'b'):
                                moves.append('O-O')
                    if 'a8' in pieces and pieces['a8'] == 'bR':
                        if 'b8' not in pieces and 'c8' not in pieces and 'd8' not in pieces:
                            if not is_check(pieces, 'b'):
                                moves.append('O-O-O')
    
    return moves


def policy(pieces: dict, to_play: str, legal_moves: list, memory: dict) -> Tuple[str, dict]:
    """
    Main policy function - selects the best move from legal moves.
    
    Args:
        pieces: Dictionary mapping squares to piece codes
        to_play: 'white' or 'black'
        legal_moves: List of legal move strings
        memory: Dictionary for storing state between calls
    
    Returns:
        Tuple of (selected_move, updated_memory)
    """
    # Always return a legal move
    if not legal_moves:
        # No legal moves - should be checkmate or stalemate
        return ('', memory)
    
    # Check for immediate checkmate first
    for move in legal_moves:
        if '#' in move:
            return (move, memory)
    
    # Check for check moves (might lead to mate)
    check_moves = [m for m in legal_moves if '+' in m]
    
    # Use search for better moves
    best_move = None
    best_value = -float('inf') if to_play == 'white' else float('inf')
    
    # Order moves for better search
    ordered_moves = order_moves(legal_moves, pieces, to_play)
    
    # Depth 2 search with alpha-beta
    depth = 2
    
    for i, move in enumerate(ordered_moves):
        # Apply the move
        new_pieces = make_move(pieces, move, to_play)
        next_to_play = 'black' if to_play == 'white' else 'white'
        
        # Generate opponent's legal moves (simplified)
        opponent_moves = get_all_legal_moves(new_pieces, next_to_play)
        
        # Filter to only moves that are actually legal
        # In practice, we'd use a proper move validator
        opponent_moves = [m for m in opponent_moves if m in legal_moves or True]
        
        if to_play == 'white':
            # Opponent tries to minimize our score
            opponent_value = minimax(new_pieces, depth - 1, -float('inf'), float('inf'), 
                                   False, next_to_play, opponent_moves)
            if opponent_value > best_value:
                best_value = opponent_value
                best_move = move
        else:
            # Opponent tries to maximize (which hurts us since we're black)
            opponent_value = minimax(new_pieces, depth - 1, -float('inf'), float('inf'), 
                                   True, next_to_play, opponent_moves)
            if opponent_value < best_value:
                best_value = opponent_value
                best_move = move
    
    # If search didn't find a good move, use the best capture or first move
    if best_move is None:
        # Prioritize captures
        capture_moves = [m for m in legal_moves if 'x' in m]
        if capture_moves:
            # Sort captures by value
            capture_moves.sort(key=lambda m: -get_capture_value(m, pieces))
            best_move = capture_moves[0]
        else:
            # Prioritize checks
            if check_moves:
                best_move = check_moves[0]
            else:
                # Use first move or random
                best_move = legal_moves[0] if legal_moves else ''
    
    return (best_move, memory)
