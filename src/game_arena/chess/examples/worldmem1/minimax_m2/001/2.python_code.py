
piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}

def policy(pieces, to_play, legal_moves, memory):
    # Step 1: Check for checkmate
    for move in legal_moves:
        if move.endswith('#'):
            return move, {}
    
    # Step 2: Check for captures
    capture_moves = []
    for move in legal_moves:
        if 'x' not in move:
            continue
        
        move_clean = move.rstrip('+#')
        if move_clean.startswith('O-'):
            continue
        
        if '=' in move_clean:
            parts = move_clean.split('=')
            dest_part = parts[0]
            promotion = parts[1]
            dest = dest_part[-2:]
            if 'x' not in dest_part:
                continue
            captured_piece = pieces.get(dest)
            if captured_piece is None:
                continue
            moving_piece_type = 'P'
            net_gain = piece_values[promotion] - piece_values['P'] - piece_values[captured_piece[1]]
        else:
            dest = move_clean[-2:]
            if 'x' not in move_clean:
                continue
            captured_piece = pieces.get(dest)
            if captured_piece is None:
                continue
            first_char = move_clean[0]
            if first_char in 'NBRQK':
                moving_piece_type = first_char
            else:
                moving_piece_type = 'P'
            net_gain = piece_values[captured_piece[1]] - piece_values[moving_piece_type]
        
        capture_moves.append((move, net_gain))
    
    if capture_moves:
        best_move = max(capture_moves, key=lambda x: x[1])
        return best_move[0], {}
    
    # Step 3: Check for check moves (non-capture)
    for move in legal_moves:
        if '+' in move and not '#' and 'x' not in move:
            return move, {}
    
    # Step 4: Return first move if no other moves found
    return legal_moves[0], {}
