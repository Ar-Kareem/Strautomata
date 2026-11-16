
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Piece values
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }
    
    # Piece-square tables (simplified)
    pawn_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10,-20,-20, 10, 10,  5,
        5, -5,-10,  0,  0,-10, -5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5,  5, 10, 25, 25, 10,  5,  5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    knight_table = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    # Determine color prefix
    color = 'w' if to_play == 'white' else 'b'
    
    def evaluate_position(pieces):
        score = 0
        
        # Material and piece-square evaluation
        for square, piece in pieces.items():
            if piece[0] == color:
                # Our pieces add to score
                score += piece_values.get(piece[1], 0)
                # Add piece-square value
                if piece[1] == 'P':
                    score += pawn_table[get_table_index(square, color)]
                elif piece[1] == 'N':
                    score += knight_table[get_table_index(square, color)]
            else:
                # Opponent pieces subtract from score
                score -= piece_values.get(piece[1], 0)
                # Subtract piece-square value
                if piece[1] == 'P':
                    score -= pawn_table[get_table_index(square, piece[0])]
                elif piece[1] == 'N':
                    score -= knight_table[get_table_index(square, piece[0])]
        
        return score
    
    def get_table_index(square, piece_color):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        if piece_color == 'b':
            rank = 7 - rank
        return rank * 8 + file
    
    def make_move(pieces, move):
        new_pieces = pieces.copy()
        # Handle castling
        if move == 'O-O':
            rank = '1' if color == 'w' else '8'
            new_pieces.pop('e' + rank)
            new_pieces.pop('h' + rank)
            new_pieces['g' + rank] = color + 'K'
            new_pieces['f' + rank] = color + 'R'
            return new_pieces
        elif move == 'O-O-O':
            rank = '1' if color == 'w' else '8'
            new_pieces.pop('e' + rank)
            new_pieces.pop('a' + rank)
            new_pieces['c' + rank] = color + 'K'
            new_pieces['d' + rank] = color + 'R'
            return new_pieces
        
        # Handle promotion
        if '=' in move:
            # Simplified promotion handling
            dest = move[-4:-2] if move[-2] in 'QRBN' else move[-3:-1]
            piece = move[-1] if move[-2] == '=' else move[-2:]
            new_pieces[dest] = color + piece[-1]
            # Find and remove the moving pawn
            for square, p in pieces.items():
                if p == color + 'P' and is_pawn_move(square, dest, move):
                    new_pieces.pop(square)
                    break
            return new_pieces
        
        # Handle captures
        if 'x' in move:
            # Simplified capture handling
            dest = move.split('x')[1][:2]
            if dest in new_pieces:
                new_pieces.pop(dest)
        
        # Find source square (simplified)
        src = None
        piece_type = move[0] if move[0].isupper() else 'P'
        if piece_type == 'P':
            # Pawn move - find the pawn that can move to destination
            dest = move[-2:]
            for square, p in pieces.items():
                if p == color + 'P' and is_pawn_move(square, dest, move):
                    src = square
                    break
        else:
            # Piece move - find the piece that can move to destination
            dest = move[-2:]
            for square, p in pieces.items():
                if p == color + piece_type and is_piece_move(square, dest, move):
                    src = square
                    break
        
        if src is not None:
            new_pieces.pop(src)
            new_pieces[dest] = color + piece_type
        
        return new_pieces
    
    def is_pawn_move(src, dest, move_str):
        src_file, src_rank = src[0], int(src[1])
        dest_file, dest_rank = dest[0], int(dest[1])
        
        if 'x' in move_str:
            # Capture move
            return (abs(ord(src_file) - ord(dest_file)) == 1 and 
                    ((color == 'w' and dest_rank - src_rank == 1) or 
                     (color == 'b' and src_rank - dest_rank == 1)))
        else:
            # Normal move
            if src_file != dest_file:
                return False
            if color == 'w':
                return (dest_rank - src_rank == 1) or (src_rank == 2 and dest_rank == 4 and '4' in move_str)
            else:
                return (src_rank - dest_rank == 1) or (src_rank == 7 and dest_rank == 5 and '5' in move_str)
    
    def is_piece_move(src, dest, move_str):
        # Simplified check - just verify the piece type matches
        return True
    
    best_move = None
    best_score = -float('inf')
    
    # Check for checkmate first
    for move in legal_moves:
        if move.endswith('#'):
            return move
    
    # Evaluate all legal moves
    for move in legal_moves:
        new_pieces = make_move(pieces, move)
        score = evaluate_position(new_pieces)
        
        # Bonus for castling
        if move == 'O-O' or move == 'O-O-O':
            score += 1
        
        # Bonus for checks
        if move.endswith('+'):
            score += 0.5
        
        # Bonus for captures
        if 'x' in move:
            captured_piece = None
            dest = move.split('x')[1][:2]
            if dest in pieces:
                captured_piece = pieces[dest][1]
            if captured_piece:
                score += piece_values.get(captured_piece, 0) * 0.9  # Slightly less than full value
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move is not None else legal_moves[0]
