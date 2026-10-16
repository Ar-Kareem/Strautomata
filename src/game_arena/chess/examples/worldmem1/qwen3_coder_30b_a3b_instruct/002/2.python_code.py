
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Simple heuristic scoring for move selection
    def evaluate_move(move: str, pieces: dict[str, str], to_play: str) -> float:
        score = 0.0
        
        # Check for captures
        if 'x' in move:
            captured_piece = None
            if move[0].isupper() and move[0] != 'O':  # Piece move
                # Find the captured piece
                for square, piece in pieces.items():
                    if square == move[-2:] and piece[0] != to_play[0]:  # Opponent piece
                        captured_piece = piece[1]
                        break
            else:  # Pawn capture
                for square, piece in pieces.items():
                    if square == move[-2:] and piece[0] != to_play[0]:
                        captured_piece = piece[1]
                        break

            # Score based on captured piece type
            if captured_piece == 'P':
                score += 1.0
            elif captured_piece == 'N':
                score += 3.0
            elif captured_piece == 'B':
                score += 3.0
            elif captured_piece == 'R':
                score += 5.0
            elif captured_piece == 'Q':
                score += 9.0
        
        # Check for checkmate or check
        if move.endswith('+'):
            score += 0.5  # Slight preference for checks
        
        # Prefer moves that develop pieces to central squares
        if len(move) >= 2 and move[-2] in 'ef' and move[-1] in '45':
            score += 0.2
        
        # Prefer moves that bring pieces to center
        if len(move) >= 2 and move[-2] in 'def' and move[-1] in '456':
            score += 0.1
        
        # Prefer moves that don't expose king to checks
        # Simple rule: if it's a king move, it's likely safe or beneficial
        if move.startswith('K'):
            score += 0.1
        
        # Prefer pawn advancement
        if move.startswith('P') or (len(move) >= 2 and move[0].lower() == 'p' and len(move) > 2):
            score += 0.05
        
        # Prefer captures that don't result in losing pieces
        # This is a simplified version
        if 'x' in move:
            if len(move) > 2 and move[0].isupper():
                piece_moved = move[0]
                if piece_moved in "NBRQ":
                    score += 0.2  # Piece capture
                else:
                    score += 0.1  # Pawn capture
        
        # Add randomness to avoid predictable patterns
        score += random.uniform(0, 0.01)
        
        return score
    
    # Prefer captures, then checkmate, then other heuristics
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Look for immediate checkmate
        if 'checkmate' in move.lower() and to_play == 'white':
            return (move, memory)
        
        score = evaluate_move(move, pieces, to_play)
        
        if score > best_score:
            best_score = score
            best_move = move
            
    if best_move is not None:
        return (best_move, memory)
    else:
        return (random.choice(legal_moves), memory)
