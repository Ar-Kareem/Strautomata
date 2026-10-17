
import copy
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    if not legal_moves:
        # Fallback to empty move, though legal_moves should always have options
        return '', memory
    
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    def evaluate(pieces_dict, side):
        white_mat = sum(values.get(p[1], 0) for p in pieces_dict.values() if p[0] == 'w')
        black_mat = sum(values.get(p[1], 0) for p in pieces_dict.values() if p[0] == 'b')
        if side == 'white':
            return white_mat - black_mat
        else:
            return black_mat - white_mat
    
    def apply_move(pieces_dict, move, side):
        new_pieces = copy.deepcopy(pieces_dict)
        side_color = 'w' if side == 'white' else 'b'
        
        if move.startswith('O-O'):
            # Kingside castling
            if side == 'white':
                del new_pieces['e1']
                del new_pieces['h1']
                new_pieces['g1'] = 'wK'
                new_pieces['f1'] = 'wR'
            else:
                del new_pieces['e8']
                del new_pieces['h8']
                new_pieces['g8'] = 'bK'
                new_pieces['f8'] = 'bR'
            return new_pieces
        elif move.startswith('O-O-O'):
            # Queenside castling
            if side == 'white':
                del new_pieces['e1']
                del new_pieces['a1']
                new_pieces['c1'] = 'wK'
                new_pieces['d1'] = 'wR'
            else:
                del new_pieces['e8']
                del new_pieces['a8']
                new_pieces['c8'] = 'bK'
                new_pieces['d8'] = 'bR'
            return new_pieces
        
        # Parse to_square and promotion
        if '=' in move:
            parts = move.split('=')
            to_square = parts[0][-2:]
            promo = parts[1][0]
        else:
            to_square = move[-2:]
            promo = None
            if not to_square[0].isalpha() or not to_square[1].isdigit():
                # Malformed, skip
                raise ValueError("Cannot parse move")
        
        capture = 'x' in move
        
        # Determine moved piece
        if move[0].isupper():
            piece_type = move[0]
        else:
            piece_type = 'P'
        
        # Find candidate from_squares for the piece
        candidates = [sq for sq, p in new_pieces.items() if p[1] == piece_type and p[0] == side_color]
        
        if not candidates:
            raise ValueError("No candidate pieces")
        
        from_square = None
        if len(candidates) == 1:
            from_square = candidates[0]
        else:
            # Handle disambiguation
            disamb = move[1] if len(move) > 1 and move[1].isalnum() else None
            if disamb:
                if disamb.isdigit():  # Rank
                    for sq in candidates:
                        if sq[1] == disamb:
                            from_square = sq
                            break
                else:  # File
                    for sq in candidates:
                        if sq[0] == disamb:
                            from_square = sq
                            break
            if not from_square:
                from_square = candidates[0]  # Fallback, arbitrary
        
        if not from_square:
            raise ValueError("Cannot determine from_square")
        
        # Apply capture
        if capture:
            captured_piece = new_pieces.get(to_square)
            new_pieces.pop(to_square, None)
        
        # Move piece
        moved_piece = new_pieces[from_square]
        new_pieces.pop(from_square)
        if promo:
            new_pieces[to_square] = side_color + promo
        else:
            new_pieces[to_square] = moved_piece
        
        return new_pieces
    
    # Evaluate each move
    best_move = None
    best_eval = float('-inf')
    for move in legal_moves:
        try:
            new_pieces = apply_move(pieces, move, to_play)
            eval_score = evaluate(new_pieces, to_play)
            if eval_score > best_eval:
                best_eval = eval_score
                best_move = move
        except:
            # Skip unparseable moves
            continue
    
    # If no best move found, pick random
    if best_move is None:
        best_move = random.choice(legal_moves)
    
    # Memory unused but can be extended
    return best_move, memory
