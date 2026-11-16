
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Material values for pieces
    material_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Helper function to parse move string
    def parse_move(move: str) -> tuple[str, str, str]:
        if move in ['O-O', 'O-O-O']:
            return move, '', ''
        if '=' in move:
            target, promo = move.split('=')
            return target, promo, ''
        if 'x' in move:
            target, capture = move.split('x')
            return target, capture, ''
        return move, '', ''
    
    # Helper function to simulate move and check for checkmate
    def simulate_move(move: str, pieces: dict) -> tuple[bool, dict]:
        target, promo, capture = parse_move(move)
        if move in ['O-O', 'O-O-O']:
            # Handle castling
            king = 'K' if to_play == 'white' else 'k'
            rook = 'R' if to_play == 'white' else 'r'
            king_pos = next(pos for pos, p in pieces.items() if p == king)
            rook_pos = next(pos for pos, p in pieces.items() if p == rook)
            if move == 'O-O':
                new_king = 'g1' if to_play == 'white' else 'g8'
                new_rook = 'f1' if to_play == 'white' else 'f8'
            else:
                new_king = 'c1' if to_play == 'white' else 'c8'
                new_rook = 'd1' if to_play == 'white' else 'd8'
            pieces[new_king] = king
            pieces[new_rook] = rook
            pieces.pop(king_pos)
            pieces.pop(rook_pos)
            return False, pieces
        else:
            # Parse source square (if needed)
            if len(move) == 2:
                source = ''
            elif len(move) == 3:
                source = move[0]
            else:
                source = move[:2]
            target = move[-2:]
            # Move piece
            piece = pieces[source]
            pieces[target] = piece
            pieces.pop(source)
            # Handle promotion
            if promo:
                pieces[target] = promo + ('w' if to_play == 'white' else 'b')
            return False, pieces
    
    # Check for checkmate in legal moves
    for move in legal_moves:
        _, _, _ = parse_move(move)
        if move in ['O-O', 'O-O-O']:
            continue
        if len(move) == 2:
            source = ''
        elif len(move) == 3:
            source = move[0]
        else:
            source = move[:2]
        target = move[-2:]
        if source == '' and target in pieces:
            continue
        if source != '' and target not in pieces:
            continue
        # Simulate move
        _, new_pieces = simulate_move(move, pieces.copy())
        # Check if opponent's king is in check
        king = 'K' if to_play == 'white' else 'k'
        king_pos = next(pos for pos, p in new_pieces.items() if p == king)
        # Check if king has legal moves
        # (Simplified: assume no legal moves if king is in check)
        return move, {}
    
    # Evaluate moves if no checkmate found
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        target, promo, capture = parse_move(move)
        if move in ['O-O', 'O-O-O']:
            # Castling evaluation
            score = 1000  # High priority for castling
        else:
            # Parse source and target
            if len(move) == 2:
                source = ''
            elif len(move) == 3:
                source = move[0]
            else:
                source = move[:2]
            target = move[-2:]
            # Material change
            captured_piece = pieces[target] if target in pieces else ''
            captured_value = material_values.get(captured_piece[1], 0)
            piece_value = material_values.get(pieces[source][1], 0)
            material_change = captured_value - piece_value
            # King safety check
            king = 'K' if to_play == 'white' else 'k'
            king_pos = next(pos for pos, p in pieces.items() if p == king)
            # Check if move exposes king to check
            # (Simplified: assume move is safe if not moving king)
            if source == king_pos:
                king_exposed = True
            else:
                king_exposed = False
            # Piece activity (simplified)
            activity = 0
            if source == 'e4' or source == 'd4':
                activity += 1
            if target == 'e4' or target == 'd4':
                activity += 1
            # Score calculation
            score = material_change * 2
            if king_exposed:
                score -= 10
            score += activity * 0.5
        # Select best move
        if score > best_score:
            best_score = score
            best_move = move
    return best_move, {}
