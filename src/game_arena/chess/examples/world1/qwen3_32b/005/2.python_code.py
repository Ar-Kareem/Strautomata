
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    best_move = legal_moves[0]
    max_score = -float('inf')
    
    for move in legal_moves:
        score = 0
        
        if move.endswith('#'):
            score = 10000
        elif move == 'O-O' or move == 'O-O-O':
            score = 100
        elif '=' in move:
            promoted_part = move.split('=')[1]
            promoted_to = promoted_part[0]
            promotion_value = 9 if promoted_to == 'Q' else 5 if promoted_to == 'R' else 3 if promoted_to == 'B' else 2 if promoted_to == 'N' else 0
            score = 1000 + promotion_value
        elif 'x' in move:
            move_stripped = move.rstrip('+#')
            if '=' in move_stripped:
                move_stripped = move_stripped.split('=')[0]
            if len(move_stripped) >= 2:
                destination = move_stripped[-2:]
            else:
                destination = ''
            captured_piece = pieces.get(destination)
            if captured_piece is not None:
                captured_type = captured_piece[1]
                captured_value = piece_values.get(captured_type, 0)
                first_char = move[0]
                moving_type = first_char if first_char in 'NBQRK' else 'P'
                moving_value = piece_values.get(moving_type, 0)
                gain = captured_value - moving_value
                score = gain
                if move.endswith('+'):
                    score += 50
        elif move.endswith('+'):
            score = 50
        else:
            first_char = move[0] if len(move) >= 1 else 'P'
            moving_type = first_char if first_char in 'NBQRK' else 'P'
            if moving_type == 'P':
                score = 1
            else:
                score = 0
        
        if score > max_score:
            max_score = score
            best_move = move
    
    return best_move
