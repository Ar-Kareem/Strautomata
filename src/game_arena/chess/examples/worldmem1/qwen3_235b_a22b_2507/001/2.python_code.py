
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Piece values
    VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Map color to prefix
    color_prefix = 'w' if to_play == 'white' else 'b'
    opp_prefix = 'b' if to_play == 'white' else 'w'
    
    # Track move count and piece move history
    if 'move_count' not in memory:
        memory['move_count'] = 0
        memory['piece_moves'] = {}
    memory['move_count'] += 1
    
    # Central squares
    center_squares = {'d4', 'd5', 'e4', 'e5'}
    
    # Score each legal move
    best_score = -np.inf
    best_move = legal_moves[0]  # fallback
    
    for move in legal_moves:
        score = 0.0
        
        # 1. Immediate mate
        if move.endswith('#'):
            return move, memory
        
        # 2. Capture bonus
        if 'x' in move:
            target_square = move.split('x')[1].split('+')[0].split('=')[0]
            if target_square in pieces:
                captured_piece = pieces[target_square]
                if captured_piece.startswith(opp_prefix):
                    piece_type = captured_piece[1]
                    value = VALUES[piece_type]
                    # Try to capture high-value pieces with low-value pieces
                    attacker_value = VALUES[move[0]] if move[0] in VALUES else 0
                    score += value * 10 - attacker_value  # Strongly prefer winning exchanges
        
        # 3. Promotion bonus
        if '=Q' in move:
            score += 90
        elif '=R' in move:
            score += 50
        elif '=B' in move or '=N' in move:
            score += 30
        
        # 4. Check bonus
        if move.endswith('+'):
            score += 5
        
        # 5. Castling bonus
        if move == 'O-O' or move == 'O-O-O':
            score += 15
        
        # 6. Center control / development
        # Simple heuristic: reward moving non-pawn pieces to center in early game
        if memory['move_count'] < 20:  # Opening phase
            if move[0] in 'NBRQ' and len(move) >= 2:
                dest = move[-2:]
                if dest in center_squares:
                    score += 3
        
        # 7. Penalize moving same piece many times early
        # Extract piece type and starting square heuristic
        piece_char = move[0]
        if piece_char in 'KQRBN':
            key = f"{piece_char}_{move}"
            if key in memory['piece_moves']:
                move_freq = memory['piece_moves'][key]
                if move_freq > 1 and memory['move_count'] < 20:
                    score -= 5 * move_freq
            memory['piece_moves'][key] = memory['piece_moves'].get(key, 0) + 1
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
