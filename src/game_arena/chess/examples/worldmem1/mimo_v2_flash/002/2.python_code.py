
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Selects a chess move based on heuristics.
    Priorities: Checkmate > Checks > Material Gain > Center Control > Random.
    """
    
    # Piece values for heuristic material calculation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }
    
    best_moves = []
    best_score = -float('inf')
    
    # Center targets for positional bonus
    center_squares = ['d4', 'e4', 'd5', 'e5']
    
    for move in legal_moves:
        score = 0
        
        # 1. Detect Checkmate (Highest Priority)
        # In SAN, checkmate is denoted by '#'
        if '#' in move:
            # Immediate return for checkmate
            return move, {}
        
        # 2. Detect Checks
        if '+' in move:
            score += 5  # Bonus for checking the opponent
        
        # 3. Material and Capture Analysis
        # Check if the move is a capture ('x' in standard algebraic notation)
        if 'x' in move:
            # Determine the piece being captured (this is a heuristic approximation)
            # We look at the opponent's pieces to find a piece on the target square.
            # Note: Parsing SAN strictly without a board state is hard, 
            # so we assume standard SAN where the target square is after 'x'.
            # e.g., "Bxf5", "exd5"
            
            # Extract target square (usually last 2 characters, or 3 if promotion)
            target_sq = move[-2:] 
            
            # Determine opponent color
            opponent = 'b' if to_play == 'white' else 'w'
            
            # Check if we know the piece being captured (from 'pieces' dict)
            # Note: 'pieces' dict maps squares to piece codes.
            # We must check if the target square is occupied by the opponent.
            captured_piece_code = pieces.get(target_sq)
            
            if captured_piece_code and captured_piece_code.startswith(opponent):
                captured_type = captured_piece_code[1]
                captured_val = piece_values.get(captured_type, 0)
                
                # Estimate capturing piece value based on the first letter of the move
                # (Standard SAN usually starts with piece letter or is a pawn move)
                move_char = move[0]
                if move_char.isupper():
                    capturing_val = piece_values.get(move_char, 1)
                else:
                    # Pawn move
                    capturing_val = 1
                
                # Add material difference if the capture is safe or winning
                # Simple heuristic: add value of captured piece
                score += captured_val
                
                # If we capture with a lower-value piece, apply a penalty (avoid traps)
                if capturing_val < captured_val:
                    score -= (captured_val - capturing_val) * 2
        
        # 4. Center Control Bonus
        # Check if the move moves to or through a center square
        # We check the target square (last 2 characters usually)
        target_sq = move[-2:]
        if target_sq in center_squares:
            score += 0.5
        
        # 5. King Safety / Development
        # Penalize moving King to center (not castling) unless necessary
        if move.startswith('K'):
            # If 'K' is followed by a move to d4, e4, etc., penalize
            if target_sq in ['d4', 'e4', 'd5', 'e5']:
                score -= 5
        
        # 6. Castling Bonus
        if 'O-O' in move:
            score += 3  # Encourage castling for king safety
            
        # Track best moves
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    # Select the best move (or random if tied)
    if best_moves:
        return random.choice(best_moves), {}
    
    # Fallback (should not happen if legal_moves is not empty)
    return random.choice(legal_moves), {}
