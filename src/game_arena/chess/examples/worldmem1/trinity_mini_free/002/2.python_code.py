
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Material values for pieces
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
    
    # Helper function to apply a move to the pieces dictionary
    def apply_move(move: str, pieces: dict[str, str]) -> dict[str, str]:
        new_pieces = pieces.copy()
        move_parts = move.split()
        if len(move_parts) == 1:
            # Simple move (e.g., "c3")
            src, dest = move_parts[0][0], move_parts[0][1:]
        elif len(move_parts) == 2:
            # Capture move (e.g., "Bxf5")
            src, dest = move_parts[0][0], move_parts[1]
        else:
            # Castling (e.g., "O-O")
            return new_pieces  # Castling doesn't change piece positions
        
        # Remove moving piece from source
        moving_piece = new_pieces[src]
        del new_pieces[src]
        
        # Handle captures
        captured_piece = new_pieces.get(dest, None)
        if captured_piece:
            del new_pieces[dest]
        
        # Place piece on destination
        new_pieces[dest] = moving_piece
        return new_pieces
    
    # Helper function to check if a king is in check
    def is_king_in_check(pieces: dict[str, str], king_color: str) -> bool:
        king_square = next(sq for sq, pc in pieces.items() if pc == f'{king_color}K')
        for sq, pc in pieces.items():
            if pc[0] != king_color and is_square_attacked(sq, pc, king_square, pieces):
                return True
        return False
    
    # Helper function to check if a square is attacked
    def is_square_attacked(attacking_piece: str, attacking_color: str, target_square: str, pieces: dict[str, str]) -> bool:
        piece_type = attacking_piece[1]
        if piece_type == 'P':
            # Pawn attacks
            files = {'w': 'gh', 'b': 'ef'}
            return target_square in files[attacking_color] + f"{chr(ord(target_square[0])+1)}{target_square[1]}"
        elif piece_type == 'N':
            # Knight moves
            moves = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
            file_diff = abs(moves[target_square[0]] - moves[attacking_piece[0]])
            rank_diff = abs(int(target_square[1]) - int(attacking_piece[1]))
            return file_diff == 1 and rank_diff == 2 or file_diff == 2 and rank_diff == 1
        else:
            # Sliding pieces (B, R, Q)
            directions = {'B': [(1,1), (1,-1), (-1,1), (-1,-1)],
                          'R': [(1,0), (-1,0), (0,1), (0,-1)],
                          'Q': [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]}
            for dx, dy in directions[piece_type]:
                x, y = ord(attacking_piece[0]) - ord('a') + dx, int(attacking_piece[1]) - 1 + dy
                while 0 <= x < 8 and 0 <= y < 8:
                    sq = chr(x + ord('a')) + str(y + 1)
                    if sq == target_square:
                        return True
                    if pieces.get(sq):
                        break
                    x += dx
                    y += dy
            return False
    
    # Evaluate a move's score
    def evaluate_move(move: str, pieces: dict[str, str]) -> float:
        new_pieces = apply_move(move, pieces)
        score = 0.0
        
        # Check for check (high priority)
        if is_king_in_check(new_pieces, 'w' if to_play == 'white' else 'b'):
            score += 1000.0
        
        # Material balance
        white_material = sum(piece_values[pc[1]] for pc in new_pieces.values() if pc[0] == 'w')
        black_material = sum(piece_values[pc[1]] for pc in new_pieces.values() if pc[0] == 'b')
        score += (white_material - black_material) * 0.5
        
        # Promotion value
        if '=' in move:
            promotion = move.split('=')[1]
            score += piece_values[promotion] * 0.5
        
        return score
    
    # Evaluate all moves and select the best
    best_score = -float('inf')
    best_move = None
    for move in legal_moves:
        score = evaluate_move(move, pieces)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
