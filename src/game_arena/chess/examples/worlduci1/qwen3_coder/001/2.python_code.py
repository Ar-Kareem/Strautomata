
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Convert to_play to color code
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Get all legal moves (this would be provided by the game engine)
    # For this implementation, we assume legal_moves is available in scope
    # In a real implementation, this would be passed as a parameter
    
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Find my king position
    my_king_pos = None
    for square, piece in pieces.items():
        if piece == my_color + 'K':
            my_king_pos = square
            break
    
    # Find opponent's king position
    opp_king_pos = None
    for square, piece in pieces.items():
        if piece == opp_color + 'K':
            opp_king_pos = square
            break
    
    # Evaluate moves
    best_move = None
    best_score = -float('inf')
    
    # In a real implementation, legal_moves would be provided
    # For now, we'll generate a basic list of possible moves
    legal_moves = []
    
    # Generate all possible moves for my pieces
    for from_square, piece in pieces.items():
        if piece[0] == my_color:
            # Generate all possible moves for this piece
            # This is a simplified version - in reality, this would require
            # complex move generation logic
            for to_square in pieces.keys():
                if from_square != to_square:
                    # For pawns, we need to handle promotions
                    if piece[1] == 'P' and to_square[1] in ['1', '8']:
                        # Pawn promotion
                        legal_moves.append(from_square + to_square + 'q')  # Promote to queen
                    else:
                        legal_moves.append(from_square + to_square)
    
    # If no legal moves, return a random move (should not happen in real game)
    if not legal_moves:
        return 'e1e2'  # Dummy move
    
    # Evaluate each move
    for move in legal_moves:
        # Simulate the move
        new_pieces = pieces.copy()
        
        # Handle normal moves and captures
        if len(move) == 4:
            from_square, to_square = move[:2], move[2:]
            
            # Skip invalid moves (would not happen with real legal moves)
            if from_square not in pieces:
                continue
                
            moving_piece = pieces[from_square]
            
            # Skip if not my piece
            if moving_piece[0] != my_color:
                continue
                
            # Make the move
            new_pieces.pop(from_square, None)
            new_pieces[to_square] = moving_piece
            
            # Check if we captured a piece
            capture_value = 0
            if to_square in pieces and pieces[to_square][0] == opp_color:
                captured_piece = pieces[to_square]
                capture_value = piece_values[captured_piece[1]]
                
            # Evaluate move
            score = capture_value
            
            # Prefer moves that attack the opponent's king
            if to_square == opp_king_pos:
                score += 100  # High value for check
                
            # Prefer development moves for knights and bishops
            if moving_piece[1] in ['N', 'B'] and from_square[1] in ['1', '8']:
                score += 0.5
                
            # Prefer center control
            if to_square in ['d4', 'd5', 'e4', 'e5']:
                score += 0.5
                
            # Update best move
            if score > best_score:
                best_score = score
                best_move = move
                
        # Handle promotions
        elif len(move) == 5:
            from_square, to_square, promotion = move[:2], move[2:4], move[4]
            
            # Skip invalid moves
            if from_square not in pieces:
                continue
                
            moving_piece = pieces[from_square]
            
            # Skip if not my piece
            if moving_piece[0] != my_color:
                continue
                
            # Make the move
            new_pieces.pop(from_square, None)
            new_pieces[to_square] = my_color + promotion.upper()
            
            # Check capture
            capture_value = 0
            if to_square in pieces and pieces[to_square][0] == opp_color:
                captured_piece = pieces[to_square]
                capture_value = piece_values[captured_piece[1]]
                
            # Evaluate promotion
            promotion_value = piece_values[promotion.upper()]
            score = capture_value + promotion_value
            
            # Update best move
            if score > best_score:
                best_score = score
                best_move = move
    
    # Return best move or first legal move if no good moves found
    return best_move if best_move else legal_moves[0]
