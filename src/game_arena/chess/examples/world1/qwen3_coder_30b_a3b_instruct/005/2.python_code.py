
import random
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Piece values: King (ignored), Pawn=1, Knight/Bishop=3, Rook=5, Queen=9
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
    
    # King is ignored
    piece_values['K'] = 0

    def evaluate_move(move: str) -> float:
        # Prioritize checkmate moves (this is a heuristic; real implementation would check for checkmate)
        if '+' in move:
            return 10000.0  # High priority for check moves

        # For captures, check if there's a piece being captured
        capture_value = 0.0
        if 'x' in move:
            # Extract the captured piece type from the move (after the 'x')
            # Handle disambiguation characters by getting the actual piece part of the move
            # Simplified: look for piece characters (KQRBPN) after 'x'
            try:
                x_index = move.index('x')
                if x_index + 1 < len(move):
                    captured_piece_char = move[x_index + 1]
                    if captured_piece_char in piece_values:
                        capture_value = piece_values[captured_piece_char]
            except:
                pass

        # Base move scoring:
        move_score = 0.0
        
        # Prefer captures
        if 'x' in move:
            move_score += capture_value * 100
        else:
            # For non-captures, prioritize moves that are likely central (e.g., move to center ranks/files)
            if len(move) >= 2:
                if move[1] in '45' and move[0] in 'de':  # center squares
                    move_score += 10
                elif move[1] in '3456' and move[0] in 'cdf':  # more central
                    move_score += 5
                
        # Prefer queen promotions and rook moves for material gain
        if '=' in move:
            if 'Q' in move:
                move_score += 1000
            elif 'R' in move:
                move_score += 500
            elif 'B' in move or 'N' in move:
                move_score += 200
                
        return move_score

    # Prioritize checkmate
    for move in legal_moves:
        if move in ['O-O', 'O-O-O']:
            return move  # Prioritize castling
        if '+' in move:
            return move

    # Evaluate all legal moves
    move_scores = [(move, evaluate_move(move)) for move in legal_moves]
    
    # Find the maximum score among legal moves
    max_score = max(score for _, score in move_scores)
    
    # Collect moves that match max score
    best_moves = [move for move, score in move_scores if score == max_score]
    
    # If multiple moves have same score, make a random selection to avoid cycles
    return random.choice(best_moves)
