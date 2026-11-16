
import numpy as np

PIECE_VALUES = {
    'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0  # King has no direct material value
}

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if not memory:
        memory['move_count'] = 0
        memory['castled'] = {'white': False, 'black': False}
    
    # Extract player color (first letter)
    player = to_play[0].lower()
    
    best_move = legal_moves[0]  # Default to first move if none better
    best_score = -np.inf
    
    # Precompute current material balance
    current_material = sum(
        PIECE_VALUES[p[1]] if p[0] == player else -PIECE_VALUES[p[1]]
        for p in pieces.values()
    )
    
    for move in legal_moves:
        score = 0
        
        # 1. Checkmate detection (highest priority)
        if move.endswith('#'):
            return (move, memory)
        
        # 2. Check for captures
        if 'x' in move:
            # Determine captured piece and location
            move_parts = move.split('x')
            target_square = move_parts[-1][:2] if '=' not in move_parts[-1] else move_parts[-1][-3:-1]
            captured_piece = pieces.get(target_square, None)
            
            if captured_piece:
                capt_value = PIECE_VALUES.get(captured_piece[1], 0)
                mover_value = PIECE_VALUES.get(move[0], 1)  # Pawn if not specified
                
                # Prioritize higher value captures
                score += 5 * capt_value - mover_value  # Net material gain bonus
        
        # 3. Castling bonus
        if move in ['O-O', 'O-O-O'] and not memory['castled'][to_play]:
            score += 30
        
        # 4. Promotion (queen preferred)
        if '=Q' in move:
            score += 50  # Queen promotion bonus
        elif '=R' in move or '=B' in move or '=N' in move:
            score += 25  # Minor promotion bonus
        
        # 5. Check bonus
        if move.endswith('+'):
            score += 15
        
        # 6. Center control bonus (e4, d4, e5, d5) using piece type
        center_squares = {'d4', 'e4', 'd5', 'e5'}
        if len(move) >= 2 and move[-2:] in center_squares:
            piece_type = move[0] if move[0].isupper() else 'P'
            if piece_type in ('N', 'B'):
                score += 4
            elif piece_type == 'P':
                score += 2
        
        # 7. Opening development (first 10 moves)
        if memory['move_count'] < 20:  # Total moves < 20 (~10 per side)
            # Bonus for developing knights/bishops
            if move[0] in ['N', 'B'] and len(move) <= 3:  # Simple knight/bishop move
                score += 5
            
            # Penalize moving queen too early
            if move[0] == 'Q':
                score -= 3
        
        # 8. Avoid moving king unnecessarily
        if move.startswith('K') and not move.startswith('O'):
            score -= 2
        
        # Break ties by move string to ensure determinism
        if score > best_score or (score == best_score and move < best_move):
            best_score = score
            best_move = move
    
    # Update memory
    memory['move_count'] += 1
    if best_move in ['O-O', 'O-O-O']:
        memory['castled'][to_play] = True
    
    return (best_move, memory)
