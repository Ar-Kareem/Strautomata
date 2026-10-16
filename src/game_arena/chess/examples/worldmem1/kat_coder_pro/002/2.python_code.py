
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Define piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Determine which side we are playing
    if to_play == 'white':
        our_color = 'w'
        opponent_color = 'b'
    else:
        our_color = 'b'
        opponent_color = 'w'
    
    # Compute evaluation for each legal move
    scores = []
    for move in legal_moves:
        # Simulate applying this move to the pieces dictionary
        new_pieces = simulate_move(pieces, move, our_color, opponent_color)
        
        # Compute material score
        material_score = 0
        for sq, piece in new_pieces.items():
            color = piece[0]
            type_ = piece[1]
            if color == our_color:
                material_score += piece_values[type_]
            else:
                material_score -= piece_values[type_]
        
        # Compute positional score (basic center control)
        pos_score = 0
        for sq, piece in new_pieces.items():
            color = piece[0]
            type_ = piece[1]
            if color == our_color:
                # Simple center control: reward pieces on d/e files and 4/5 ranks
                file = sq[0]
                rank = int(sq[1])
                if file in 'de' and rank in [4, 5]:
                    pos_score += 0.1
                if file in 'de' and rank in [3, 6]:
                    pos_score += 0.05
                if type_ == 'P' and rank in [6, 7] and our_color == 'w':
                    pos_score += 0.5  # Pawn advancement
                if type_ == 'P' and rank in [2, 3] and our_color == 'b':
                    pos_score += 0.5
            else:
                if file in 'de' and rank in [4, 5]:
                    pos_score -= 0.1
                if file in 'de' and rank in [3, 6]:
                    pos_score -= 0.05
                if type_ == 'P' and rank in [2, 3] and our_color == 'w':
                    pos_score -= 0.5
                if type_ == 'P' and rank in [6, 7] and our_color == 'b':
                    pos_score -= 0.5
        
        # Compute safety score (king safety)
        safety_score = 0
        # Find our king
        our_king_sq = None
        for sq, piece in new_pieces.items():
            if piece == f'{our_color}K':
                our_king_sq = sq
                break
        # Simple king safety: penalize if center is controlled by opponent pieces
        if our_king_sq and our_king_sq in ['e1', 'e8']:
            # Check if opponent controls center
            center_sqs = ['d4', 'd5', 'e4', 'e5']
            for sq in center_sqs:
                if sq in new_pieces and new_pieces[sq][0] == opponent_color:
                    safety_score -= 0.1
        
        # Compute checkmate score
        checkmate_score = 0
        # If the move results in checkmate (simplified detection)
        # We can't easily detect checkmate without a full engine, so we skip this
        
        total_score = material_score + pos_score + safety_score
        scores.append(total_score)
    
    # Choose the move with highest score
    best_idx = np.argmax(scores)
    best_move = legal_moves[best_idx]
    
    return best_move, memory

def simulate_move(pieces: dict[str, str], move: str, our_color: str, opponent_color: str) -> dict[str, str]:
    # Create a copy of the pieces dictionary
    new_pieces = pieces.copy()
    
    # Handle castling
    if move == 'O-O':
        if our_color == 'w':
            new_pieces['e1'] = None
            new_pieces['f1'] = f'{our_color}K'
            new_pieces['g1'] = f'{our_color}R'
            new_pieces['h1'] = None
        else:
            new_pieces['e8'] = None
            new_pieces['f8'] = f'{our_color}K'
            new_pieces['g8'] = f'{our_color}R'
            new_pieces['h8'] = None
        # Remove None values
        new_pieces = {k: v for k, v in new_pieces.items() if v is not None}
        return new_pieces
    elif move == 'O-O-O':
        if our_color == 'w':
            new_pieces['e1'] = None
            new_pieces['d1'] = f'{our_color}K'
            new_pieces['c1'] = f'{our_color}R'
            new_pieces['a1'] = None
        else:
            new_pieces['e8'] = None
            new_pieces['d8'] = f'{our_color}K'
            new_pieces['c8'] = f'{our_color}R'
            new_pieces['a8'] = None
        new_pieces = {k: v for k, v in new_pieces.items() if v is not None}
        return new_pieces
    
    # Parse move
    # Remove check symbols
    move = move.replace('+', '').replace('#', '')
    
    # Handle promotion
    promotion = None
    if '=' in move:
        promotion = move.split('=')[1]
        move = move.split('=')[0]
    
    # Handle capture
    is_capture = 'x' in move
    if is_capture:
        move = move.replace('x', '')
    
    # Determine piece type and destination
    if move[0].isupper():
        # Piece move
        piece_type = move[0]
        dest = move[-2:]
        # For disambiguation, we need more info, but for basic simulation we ignore
        # Just move the piece of our color that is on a square that can move to dest
        # This is a simplification
        source = None
        for sq, piece in new_pieces.items():
            if piece[0] == our_color and piece[1] == piece_type:
                if can_move_to(pieces, sq, dest, piece_type):
                    source = sq
                    break
        if source is None:
            # Fallback to moving a piece
            source = move[1:-2] if len(move) > 3 else None
            if source is None:
                # Just pick first piece of type
                for sq, piece in new_pieces.items():
                    if piece[0] == our_color and piece[1] == piece_type:
                        source = sq
                        break
    else:
        # Pawn move
        piece_type = 'P'
        dest = move[-2:]
        source = move[:-2] if len(move) > 2 else None
        if source is None:
            # Find pawn
            for sq, piece in new_pieces.items():
                if piece[0] == our_color and piece[1] == 'P':
                    if can_move_to(pieces, sq, dest, 'P'):
                        source = sq
                        break
    
    if source is None:
        # Fallback to first piece
        for sq, piece in new_pieces.items():
            if piece[0] == our_color:
                source = sq
                break
    
    # Apply move
    if source and dest:
        # Remove captured piece
        if dest in new_pieces:
            del new_pieces[dest]
        # Move piece
        new_pieces[dest] = f'{our_color}{piece_type}'
        del new_pieces[source]
        # Handle promotion
        if promotion:
            new_pieces[dest] = f'{our_color}{promotion}'
    
    return new_pieces

def can_move_to(pieces: dict[str, str], source: str, dest: str, piece_type: str) -> bool:
    # Simplified move validation
    # This is not perfect but good enough for simulation
    if piece_type == 'P':
        # Pawn moves
        file_diff = abs(ord(source[0]) - ord(dest[0]))
        rank_diff = int(dest[1]) - int(source[1])
        if file_diff == 0:
            if rank_diff == 1 and pieces.get(source[0] + str(int(source[1])+1)) is None:
                return True
            if rank_diff == 2 and int(source[1]) == 2 and pieces.get(source[0] + '3') is None and pieces.get(source[0] + '4') is None:
                return True
        elif file_diff == 1 and rank_diff == 1:
            if dest in pieces and pieces[dest][0] != pieces[source][0]:
                return True
        return False
    elif piece_type == 'R':
        # Rook moves
        if source[0] == dest[0] or source[1] == dest[1]:
            return True
    elif piece_type == 'B':
        # Bishop moves
        if abs(ord(source[0]) - ord(dest[0])) == abs(int(source[1]) - int(dest[1])):
            return True
    elif piece_type == 'Q':
        # Queen moves
        if source[0] == dest[0] or source[1] == dest[1] or abs(ord(source[0]) - ord(dest[0])) == abs(int(source[1]) - int(dest[1])):
            return True
    elif piece_type == 'K':
        # King moves
        if abs(ord(source[0]) - ord(dest[0])) <= 1 and abs(int(source[1]) - int(dest[1])) <= 1:
            return True
    elif piece_type == 'N':
        # Knight moves
        file_diff = abs(ord(source[0]) - ord(dest[0]))
        rank_diff = abs(int(source[1]) - int(dest[1]))
        if (file_diff == 1 and rank_diff == 2) or (file_diff == 2 and rank_diff == 1):
            return True
    return False
