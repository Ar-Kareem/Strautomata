
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values for material evaluation
    PIECE_VALUES = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0  # King value is 0 (immovable)
    }
    
    # Helper function to evaluate board position
    def evaluate_position():
        score = 0
        for square, piece in pieces.items():
            if piece[0] == to_play[0]:  # Friendly pieces
                score += PIECE_VALUES[piece[1]]
            else:  # Opponent pieces
                score -= PIECE_VALUES[piece[1]]
        return score
    
    # Generate all legal moves (simplified for demonstration)
    legal_moves = []
    for square, piece in pieces.items():
        if piece[0] == to_play[0]:  # Only consider pieces of the current player
            # Simplified move generation (real implementation would be more complex)
            # This is a placeholder - actual implementation would require full move generation
            # For example: pawn moves, knight jumps, etc.
            if piece[1] == 'P':
                # Pawn moves (simplified)
                file, rank = square[0], int(square[1])
                if to_play == 'white':
                    if rank == 2:
                        legal_moves.append(f"{chr(ord(file)+1)}3")
                        legal_moves.append(f"{chr(ord(file)-1)}3")
                    legal_moves.append(f"{file}4")
                else:  # Black
                    if rank == 7:
                        legal_moves.append(f"{chr(ord(file)+1)}6")
                        legal_moves.append(f"{chr(ord(file)-1)}6")
                    legal_moves.append(f"{file}5")
    
    # Evaluate each move and select the best
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        # Simulate move (simplified - real implementation would require full simulation)
        # For example: pawn promotion to queen
        if move.endswith('1') or move.endswith('8'):
            candidate = move[:-1] + 'Q'  # Promote to queen
        else:
            candidate = move
        
        # Evaluate position after candidate move
        # (In real implementation, this would require full board simulation)
        move_score = evaluate_position()
        
        # Prefer moves that improve material balance
        if move_score > best_score:
            best_score = move_score
            best_move = candidate
    
    return best_move if best_move else random.choice(legal_moves)
