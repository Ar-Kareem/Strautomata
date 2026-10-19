
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Generate all legal moves
    legal_moves = generate_legal_moves(pieces, to_play)
    
    # If no moves available, return None (should not happen per problem constraints)
    if not legal_moves:
        return None
    
    # Evaluate each move and select the best
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        # Generate new position after move
        new_pieces, new_to_play = make_move(pieces, move, to_play)
        
        # Evaluate position from opponent's perspective
        score = evaluate_position(new_pieces, new_to_play)
        
        # Select move with highest score
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(pieces: dict[str, str], to_play: str) -> list[str]:
    """Generate all legal moves for the current player"""
    moves = []
    for square, piece in pieces.items():
        if piece[0] != to_play:
            continue
        piece_type = piece[1]
        if piece_type == 'P':
            moves.extend(generate_pawn_moves(square, pieces, to_play))
        elif piece_type == 'N':
            moves.extend(generate_knight_moves(square, pieces, to_play))
        elif piece_type == 'B':
            moves.extend(generate_bishop_moves(square, pieces, to_play))
        elif piece_type == 'R':
            moves.extend(generate_rook_moves(square, pieces, to_play))
        elif piece_type == 'Q':
            moves.extend(generate_queen_moves(square, pieces, to_play))
        elif piece_type == 'K':
            moves.extend(generate_king_moves(square, pieces, to_play))
    return moves

def make_move(pieces: dict[str, str], move: str, to_play: str) -> tuple[dict[str, str], str]:
    """Apply move to pieces and return new position and next player"""
    src, dest = move[:2], move[2:]
    new_pieces = pieces.copy()
    
    # Handle captures
    if dest in new_pieces and new_pieces[dest][0] != to_play:
        del new_pieces[dest]
    
    # Update destination
    new_pieces[dest] = pieces[src]
    del new_pieces[src]
    
    # Handle pawn promotion
    if move[2:] == 'a1' or move[2:] == 'a8' or move[2:] == 'h1' or move[2:] == 'h8':
        promo = move[3:]
        new_pieces[dest] = to_play + promo
    
    return new_pieces, 'white' if to_play == 'black' else 'black'

def evaluate_position(pieces: dict[str, str], to_play: str) -> float:
    """Evaluate position strength from opponent's perspective"""
    # Material evaluation
    material = 0
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
    for square, piece in pieces.items():
        if piece[0] == to_play:
            material += piece_values.get(piece[1], 0)
        else:
            material -= piece_values.get(piece[1], 0)
    
    # King safety evaluation
    king_square = next(square for square, piece in pieces.items() if piece == to_play + 'K')
    king_safe = True
    for square, piece in pieces.items():
        if piece[0] != to_play and piece[1] != 'K':
            continue
        if is_attacked(square, king_square, pieces, to_play):
            king_safe = False
            break
    
    # Activity evaluation
    activity = 0
    for square, piece in pieces.items():
        if piece[0] == to_play:
            activity += activity_score(square, piece[1], pieces)
    
    # Final evaluation
    return material + (100 if king_safe else 0) + activity

def is_attacked(square: str, target: str, pieces: dict[str, str], attacker_color: str) -> bool:
    """Check if a square is attacked by any piece"""
    for sq, piece in pieces.items():
        if piece[0] == attacker_color and piece[1] != 'K':
            if is_attacked_by_piece(sq, piece[1], target, pieces):
                return True
    return False

def is_attacked_by_piece(source: str, piece_type: str, target: str, pieces: dict[str, str]) -> bool:
    """Check if a piece can attack a target square"""
    if piece_type == 'P':
        return pawn_can_attack(source, target, pieces)
    elif piece_type == 'N':
        return knight_can_attack(source, target)
    elif piece_type == 'B':
        return bishop_can_attack(source, target, pieces)
    elif piece_type == 'R':
        return rook_can_attack(source, target, pieces)
    elif piece_type == 'Q':
        return queen_can_attack(source, target, pieces)
    return False

# Helper functions for move generation and attack checks (omitted for brevity)
# (Full implementation would include all helper functions for complete move generation and attack checks)
