
import re

piece_values = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0
}

def get_target_square(move):
    """Extracts the target square from a move string."""
    if move in ['O-O', 'O-O-O']:
        return None
    move_part = move.split('=')[0] if '=' in move else move
    match = re.search(r'([a-h][1-8](?=\+|#|$))', move_part)
    return match.group(1) if match else None

def get_captured_piece_type(move, pieces, color_prefix):
    """Determines the captured piece type for a capturing move."""
    if 'x' in move:
        target_square = get_target_square(move)
        if target_square and target_square in pieces:
            target_piece = pieces[target_square]
            if target_piece[0] != color_prefix:
                return target_piece[1]
    return None

def get_moving_piece_type(move):
    """Infers the moving piece type from the move notation."""
    if move.startswith('O-O'):
        return 'K'
    piece_char = move.lstrip('abcdefghNBKRQ') if move[0].islower() else move[0]
    return piece_char if piece_char in 'KQRBN' else 'P'

def policy(pieces, to_play, legal_moves, memory):
    color_prefix = 'w' if to_play == 'white' else 'b'
    opponent_prefix = 'b' if color_prefix == 'w' else 'w'
    best_move = None
    best_score = -float('inf')
    
    # Initialize memory for move tracking
    if 'move_count' not in memory:
        memory['move_count'] = 0
    castling_done = memory.get(f'castling_done_{color_prefix}', False)
    
    center_squares = {'d4', 'e4', 'd5', 'e5'}
    
    for move in legal_moves:
        score = 0
        moving_piece = get_moving_piece_type(move)
        target_square = get_target_square(move)
        
        # 1. Checkmate detection
        if move.endswith('#'):
            return (move, memory)  # Immediately play forcing move
        
        # 2. Check bonus
        if '+' in move:
            score += 50
        
        # 3. Capture evaluation
        captured_type = get_captured_piece_type(move, pieces, color_prefix)
        if captured_type:
            score += piece_values[captured_type] * 10
        
        # 4. Promotion bonus
        if '=Q' in move:
            score += 900
        
        # 5. Castling priority
        if not castling_done:
            if move == 'O-O':
                score += 400
            elif move == 'O-O-O':
                score += 350
        
        # 6. Central square control
        if target_square and moving_piece != 'P' and target_square in center_squares:
            score += 50
        
        # 7. Early game development
        if memory['move_count'] < 12:
            if moving_piece in ('N', 'B'):
                score += 100
        
        # 8. King safety penalty
        if moving_piece == 'K' and memory['move_count'] < 20 and target_square not in {'g1', 'c1', 'g8', 'c8'}:
            score -= 200
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    # Update memory state
    memory['move_count'] += 1
    if best_move in ('O-O', 'O-O-O'):
        memory[f'castling_done_{color_prefix}'] = True
        
    return (best_move if best_move else legal_moves[0], memory)
