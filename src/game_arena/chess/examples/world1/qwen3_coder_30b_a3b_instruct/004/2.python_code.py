
import random
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Piece values for material evaluation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
        'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0
    }

    # Function to evaluate a move based on several criteria
    def evaluate_move(move):
        score = 0
        # Prioritize checkmate
        if '+' in move or '#' in move:
            score += 1000
        
        # Check for captures
        if 'x' in move:
            # Get the captured piece
            captured_square = move.split('x')[1]
            if captured_square in pieces:
                captured_piece = pieces[captured_square]
                score += piece_values[captured_piece[1].lower()] * 100
            # Add extra score for capturing queens or rooks
            if 'x' in move and move[-1] not in ['+', '#', '=']:
                if captured_piece[1].lower() in ['q', 'r']:
                    score += 500
        
        # King safety: prefer moves that defend the king
        if to_play == 'white' and 'K' in move:
            score += 50
        elif to_play == 'black' and 'k' in move:
            score += 50
            
        # Prefer pawn advancement
        if move[0] in 'abcdefgh' and len(move) >= 2:
            # If moving pawn up (white) or down (black)
            if to_play == 'white' and move[1] in '3456' and move[0] == move[0]:
                score += 10
            elif to_play == 'black' and move[1] in '3456' and move[0] == move[0]:
                score += 10
        
        # Prefer piece development
        if move[0].upper() in 'NBRQ':
            if len(move) == 3 and move[2] in '12345678':
                score += 5
        
        # Prefer castling if available
        if move == 'O-O' or move == 'O-O-O':
            score += 100
            
        # Prefer central control
        if move[1] in '45' and move[0] in 'def':
            score += 5
            
        # Prefer capturing pieces
        if 'x' in move and len(move) > 2:
            score += 20
        
        return score
    
    # If there are checkmate moves, return the first one
    checkmate_moves = [m for m in legal_moves if '+' in m or '#' in m]
    if checkmate_moves:
        return checkmate_moves[0]
    
    # If we have captures, prefer higher value captures
    capture_moves = [m for m in legal_moves if 'x' in m]
    if capture_moves:
        best_capture = capture_moves[0]
        best_score = evaluate_move(best_capture)
        for capture_move in capture_moves:
            move_score = evaluate_move(capture_move)
            if move_score > best_score:
                best_score = move_score
                best_capture = capture_move
        return best_capture
    
    # Evaluate all moves and choose the best one
    best_move = legal_moves[0]
    max_score = -float('inf')
    
    for move in legal_moves:
        score = evaluate_move(move)
        if score > max_score:
            max_score = score
            best_move = move
    
    # Add a small random factor to make the AI less predictable
    # Use a fixed seed to ensure deterministic behavior for the same inputs
    random.seed(len(legal_moves))  # seed based on number of legal moves for deterministic behavior
    if random.random() < 0.1 and len(legal_moves) > 1:  # 10% chance to choose a different move
        return random.choice(legal_moves)
    
    return best_move
