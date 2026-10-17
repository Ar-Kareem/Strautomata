
import copy

piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    memory = copy.deepcopy(memory) if memory else {}
    memory.setdefault('castled', False)
    memory.setdefault('move_count', 0)
    
    our_color = 'w' if to_play == 'white' else 'b'
    best_move = legal_moves[0]
    best_score = -999999
    
    for move in legal_moves:
        score = 0
        target_sq = get_target_square(move)
        
        # Checkmate (highest priority)
        if move.endswith('#'):
            return move, {**memory, 'castled': memory['castled'], 'move_count': memory['move_count'] + 1}
        
        # Castling
        if move in ['O-O', 'O-O-O']:
            score += 1000 if not memory['castled'] else 200
        else:
            # Promotion
            if '=' in move:
                promo_piece = move.split('=')[1][0]
                score += piece_values.get(promo_piece, 9) - 1  # Pawn upgrade bonus
                if is_capture(move, target_sq, pieces, our_color) and target_sq in pieces:
                    score += piece_values.get(pieces[target_sq][1], 0)
            
            # Captures
            elif is_capture(move, target_sq, pieces, our_color) and target_sq in pieces:
                captured_val = piece_values.get(pieces[target_sq][1], 0)
                attacker_val = piece_values.get(get_moving_piece_type(move), 3)
                score += captured_val - attacker_val
            
            # Pawn center control
            if move[0].islower() and target_sq:
                if target_sq in ['d4', 'e4', 'd5', 'e5']:
                    score += 1
            
            # Knight development
            if move.startswith('N') and target_sq in ['c3', 'f3', 'c6', 'f6']:
                score += 2 if memory['move_count'] < 10 else 0
            
            # Check bonus
            if move.endswith('+'):
                score += 1
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Update memory for castling
    new_memory = {
        'castled': memory['castled'] or best_move in ['O-O', 'O-O-O'],
        'move_count': memory['move_count'] + 1
    }
    return best_move, new_memory

def get_target_square(move: str) -> str:
    if move in ['O-O', 'O-O-O']:
        return None
    clean_move = move.rstrip('+#').split('=')[0]
    for i in range(len(clean_move)-1, 0, -1):
        if clean_move[i-1] in 'abcdefgh' and clean_move[i] in '12345678':
            return clean_move[i-1:i+1]
    return None

def is_capture(move: str, target_sq: str, pieces: dict, our_color: str) -> bool:
    return 'x' in move or (target_sq and target_sq in pieces and pieces[target_sq][0] != our_color)

def get_moving_piece_type(move: str) -> str:
    return move[0] if move[0] in piece_values else 'P'
