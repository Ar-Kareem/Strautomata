
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    import copy
    
    # Piece values for evaluation
    piece_values = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
    }
    
    # Piece-square tables for positional evaluation
    pawn_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    knight_table = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    bishop_table = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    rook_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    queen_table = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    
    king_middle_table = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    king_end_table = [
        -50,-40,-30,-20,-20,-30,-40,-50,
        -30,-20,-10,  0,  0,-10,-20,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-30,  0,  0,  0,  0,-30,-30,
        -50,-30,-30,-30,-30,-30,-30,-50
    ]
    
    def parse_square(square):
        """Convert algebraic notation to coordinates."""
        file_idx = ord(square[0]) - ord('a')
        rank_idx = int(square[1]) - 1
        return file_idx + rank_idx * 8
    
    def make_move(pieces_dict, move_str):
        """Apply a move to a pieces dictionary and return new dictionary."""
        new_pieces = copy.deepcopy(pieces_dict)
        
        # Handle castling
        if move_str in ['O-O', 'O-O-O']:
            color = 'w' if to_play == 'white' else 'b'
            if move_str == 'O-O':
                if color == 'w':
                    new_pieces['g1'] = 'wK'
                    new_pieces['f1'] = 'wR'
                    del new_pieces['e1']
                    del new_pieces['h1']
                else:
                    new_pieces['g8'] = 'bK'
                    new_pieces['f8'] = 'bR'
                    del new_pieces['e8']
                    del new_pieces['h8']
            else:
                if color == 'w':
                    new_pieces['c1'] = 'wK'
                    new_pieces['d1'] = 'wR'
                    del new_pieces['e1']
                    del new_pieces['a1']
                else:
                    new_pieces['c8'] = 'bK'
                    new_pieces['d8'] = 'bR'
                    del new_pieces['e8']
                    del new_pieces['a8']
            return new_pieces
        
        # Parse the move
        # Handle disambiguation (e.g., 'Nec3' -> piece='N', from_file='e', to_square='c3')
        i = 0
        piece_type = ''
        from_file = None
        from_rank = None
        
        if move_str[0] in 'RNBQK':
            piece_type = move_str[0]
            i = 1
            # Check for disambiguation
            if move_str[i] in 'abcdefgh':
                from_file = ord(move_str[i]) - ord('a')
                i += 1
                if move_str[i] in '12345678':
                    from_rank = int(move_str[i]) - 1
                    i += 1
        else:
            piece_type = 'P'
        
        # Capture indicator
        is_capture = move_str[i] == 'x'
        if is_capture:
            i += 1
        
        # Destination square
        dest_square = move_str[i:i+2]
        i += 2
        
        # Promotion
        promotion = None
        if i < len(move_str) and move_str[i] == '=':
            promotion = move_str[i+1]
        
        # Determine source square
        if not from_file and not from_rank:
            # Need to find the piece
            color = 'w' if to_play == 'white' else 'b'
            for square, piece in new_pieces.items():
                if piece[0] == color and piece[1] == piece_type:
                    sq_idx = parse_square(square)
                    dest_idx = parse_square(dest_square)
                    
                    # Check if this piece can move to destination
                    # Simplified check - in real chess this would be more complex
                    file_match = from_file is None or (ord(square[0]) - ord('a')) == from_file
                    rank_match = from_rank is None or (int(square[1]) - 1) == from_rank
                    
                    if file_match and rank_match:
                        # Basic movement validation
                        if piece_type == 'P':
                            direction = 1 if color == 'w' else -1
                            start_rank = 1 if color == 'w' else 6
                            curr_rank = int(square[1]) - 1
                            dest_rank = int(dest_square[1]) - 1
                            file_diff = abs(ord(square[0]) - ord(dest_square[0]))
                            
                            if is_capture:
                                if file_diff == 1 and dest_rank - curr_rank == direction:
                                    from_sq = square
                                    break
                            else:
                                if square[0] == dest_square[0]:
                                    if dest_rank - curr_rank == direction:
                                        from_sq = square
                                        break
                                    if curr_rank == start_rank and dest_rank - curr_rank == 2 * direction:
                                        from_sq = square
                                        break
                        else:
                            from_sq = square
                            break
        else:
            # We have disambiguation info
            from_sq = chr(ord('a') + from_file) + str(from_rank + 1) if from_rank else chr(ord('a') + from_file) + '?'
        
        # Make the move
        if from_sq in new_pieces:
            piece = new_pieces[from_sq]
            if promotion:
                piece = piece[0] + promotion
            new_pieces[dest_square] = piece
            del new_pieces[from_sq]
        
        return new_pieces
    
    def count_material(pieces_dict, color):
        """Count total material for a color."""
        total = 0
        for piece in pieces_dict.values():
            if piece[0] == ('w' if color == 'white' else 'b'):
                total += piece_values[piece[1]]
        return total
    
    def evaluate_position(pieces_dict):
        """Evaluate a position from the perspective of the player to move."""
        score = 0
        
        # Count material difference
        white_material = count_material(pieces_dict, 'white')
        black_material = count_material(pieces_dict, 'black')
        score += white_material - black_material
        
        # Determine if we're in endgame (both sides have queens or no queens)
        has_queen_white = any(p[1] == 'Q' for p in pieces_dict.values() if p[0] == 'w')
        has_queen_black = any(p[1] == 'Q' for p in pieces_dict.values() if p[0] == 'b')
        is_endgame = not has_queen_white or not has_queen_black
        
        # Evaluate piece positions
        for square, piece in pieces_dict.items():
            idx = parse_square(square)
            piece_type = piece[1]
            
            # Flip index for black pieces (they're evaluated from black's perspective)
            if piece[0] == 'b':
                idx = 63 - idx
            
            if piece_type == 'P':
                score += pawn_table[idx]
            elif piece_type == 'N':
                score += knight_table[idx]
            elif piece_type == 'B':
                score += bishop_table[idx]
            elif piece_type == 'R':
                score += rook_table[idx]
            elif piece_type == 'Q':
                score += queen_table[idx]
            elif piece_type == 'K':
                if is_endgame:
                    score += king_end_table[idx]
                else:
                    score += king_middle_table[idx]
        
        # Bonus for development in opening
        minor_pieces_deployed = sum(1 for p in pieces_dict.values() 
                                    if p[0] == 'w' and p[1] in 'NBR' and p[1] != 'K')
        if minor_pieces_deployed < 4:  # Still in opening
            score += minor_pieces_deployed * 10
        
        return score
    
    def is_checkmate(pieces_dict, color):
        """Check if the side to move is in checkmate."""
        # This is a simplified check - in a real engine we'd need full move generation
        # For now, we'll assume if only king moves are available and king is in check, it's mate
        return False  # Placeholder - too complex for simple implementation
    
    def minimax(pieces_dict, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate_position(pieces_dict)
        
        # Generate legal moves for current position (simplified)
        # In a full implementation, we'd use a proper move generator
        # Here we just return the static evaluation
        return evaluate_position(pieces_dict)
    
    # Main evaluation logic
    def evaluate_move(pieces_dict, move):
        """Evaluate a single move and return a score."""
        score = 0
        
        # 1. Check for checkmate
        if move.endswith('#'):
            return 1000000
        
        # 2. Check for check
        if move.endswith('+'):
            score += 500
        
        # 3. Evaluate captures
        if 'x' in move:
            # Simple capture detection
            parts = move.split('x')
            dest = parts[-1][:2] if len(parts[-1]) >= 2 else parts[-1]
            if dest in pieces_dict:
                captured_piece = pieces_dict[dest]
                score += piece_values[captured_piece[1]] * 1.1  # 10% bonus for captures
        
        # 4. Check for promotion
        if '=' in move:
            promo_piece = move.split('=')[1][0]
            if promo_piece == 'Q':
                score += 800
            elif promo_piece == 'R':
                score += 500
            elif promo_piece == 'B':
                score += 330
            elif promo_piece == 'N':
                score += 320
        
        # 5. Castling is good
        if move in ['O-O', 'O-O-O']:
            score += 150
        
        # 6. Penalize moving king early (opening principle)
        if move.startswith('K') and not move.startswith('Kx'):
            score -= 50
        
        # 7. Reward developing pieces (knights and bishops from back rank)
        if move[0] in 'NBR' and move[-2] in '12345678':
            score += 20
        
        # 8. Reward central control (moves to center squares)
        center_squares = ['d4', 'e4', 'd5', 'e5']
        dest = move[-2:] if len(move) >= 2 else ''
        if dest in center_squares:
            score += 30
        
        # 9. Penalize moving same piece twice in opening
        if move in memory.get('repeated_moves', []):
            score -= 30
        
        # 10. Basic positional evaluation after move
        new_pieces = make_move(pieces_dict, move)
        pos_score = evaluate_position(new_pieces)
        
        # Adjust based on whose perspective
        if to_play == 'black':
            pos_score = -pos_score
        
        score += pos_score * 0.1
        
        return score
    
    # Evaluate all moves and select the best one
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        move_score = evaluate_move(pieces, move)
        if move_score > best_score:
            best_score = move_score
            best_move = move
    
    # Update memory for next turn
    repeated_moves = memory.get('repeated_moves', [])
    repeated_moves.append(best_move)
    if len(repeated_moves) > 10:
        repeated_moves = repeated_moves[-10:]
    
    new_memory = {'repeated_moves': repeated_moves}
    
    return best_move, new_memory
