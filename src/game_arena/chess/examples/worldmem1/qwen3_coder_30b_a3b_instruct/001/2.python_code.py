
import numpy as np
from typing import Dict, List, Tuple, Any

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str], memory: Dict[Any, Any]) -> Tuple[str, Dict[Any, Any]]:
    # Initialize the evaluation function coefficients
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    piece_positions = {
        'P': [[0, 0, 0, 0, 0, 0, 0, 0],
              [50, 50, 50, 50, 50, 50, 50, 50],
              [10, 10, 20, 30, 30, 20, 10, 10],
              [5, 5, 10, 25, 25, 10, 5, 5],
              [0, 0, 0, 20, 20, 0, 0, 0],
              [5, -5, -10, 0, 0, -10, -5, 5],
              [5, 10, 10, -20, -20, 10, 10, 5],
              [0, 0, 0, 0, 0, 0, 0, 0]],
        'N': [[-50, -40, -30, -30, -30, -30, -40, -50],
              [-40, -20, 0, 0, 0, 0, -20, -40],
              [-30, 0, 10, 15, 15, 10, 0, -30],
              [-30, 5, 15, 20, 20, 15, 5, -30],
              [-30, 0, 15, 20, 20, 15, 0, -30],
              [-30, 5, 10, 15, 15, 10, 5, -30],
              [-40, -20, 0, 5, 5, 0, -20, -40],
              [-50, -40, -30, -30, -30, -30, -40, -50]],
        'B': [[-20, -10, -10, -10, -10, -10, -10, -20],
              [-10, 0, 0, 0, 0, 0, 0, -10],
              [-10, 0, 5, 10, 10, 5, 0, -10],
              [-10, 5, 5, 10, 10, 5, 5, -10],
              [-10, 0, 10, 10, 10, 10, 0, -10],
              [-10, 10, 10, 10, 10, 10, 10, -10],
              [-10, 5, 0, 0, 0, 0, 5, -10],
              [-20, -10, -10, -10, -10, -10, -10, -20]],
        'R': [[0, 0, 0, 0, 0, 0, 0, 0],
              [5, 10, 10, 10, 10, 10, 10, 5],
              [-5, 0, 0, 0, 0, 0, 0, -5],
              [-5, 0, 0, 0, 0, 0, 0, -5],
              [-5, 0, 0, 0, 0, 0, 0, -5],
              [-5, 0, 0, 0, 0, 0, 0, -5],
              [-5, 0, 0, 0, 0, 0, 0, -5],
              [0, 0, 0, 5, 5, 0, 0, 0]],
        'Q': [[-20, -10, -10, -5, -5, -10, -10, -20],
              [-10, 0, 0, 0, 0, 0, 0, -10],
              [-10, 0, 5, 5, 5, 5, 0, -10],
              [-5, 0, 5, 5, 5, 5, 0, -5],
              [0, 0, 5, 5, 5, 5, 0, -5],
              [-10, 5, 5, 5, 5, 5, 0, -10],
              [-10, 0, 5, 0, 0, 0, 0, -10],
              [-20, -10, -10, -5, -5, -10, -10, -20]],
        'K': [[-30, -40, -40, -50, -50, -40, -40, -30],
              [-30, -40, -40, -50, -50, -40, -40, -30],
              [-30, -40, -40, -50, -50, -40, -40, -30],
              [-30, -40, -40, -50, -50, -40, -40, -30],
              [-20, -30, -30, -40, -40, -30, -30, -20],
              [-10, -20, -20, -20, -20, -20, -20, -10],
              [20, 20, 0, 0, 0, 0, 20, 20],
              [20, 30, 10, 0, 0, 10, 30, 20]]
    }
    
    # Function to evaluate a position
    def evaluate_position(pieces_dict):
        score = 0
        for square, piece in pieces_dict.items():
            piece_type = piece[1]
            color = piece[0]
            if piece_type == 'K':
                continue  # We'll handle kings specially
            if color == 'w':
                score += piece_values[piece_type]
                # Evaluate piece position
                file, rank = ord(square[0]) - ord('a'), int(square[1]) - 1
                score += piece_positions[piece_type][rank][file]
            else:  # black
                score -= piece_values[piece_type]
                # Evaluate piece position
                file, rank = ord(square[0]) - ord('a'), int(square[1]) - 1
                score -= piece_positions[piece_type][7-rank][file]
        return score

    # Simple function to check if a move is a check
    def is_check(move, pieces_dict, player):
        # We will simulate the move to check if the opponent king gets checked
        # For now, we avoid complex checking logic since it's computationally expensive
        # Just checking captures and such
        if 'x' in move or move.startswith('O'):
            return True
        return False
    
    # Function to evaluate the utility of a move for the given player
    def evaluate_move(move, pieces_dict, player):
        score = 0
        
        # Check if move captures a piece
        if 'x' in move:
            captured_piece = move.split('x')[1][0]
            if captured_piece.isupper():
                score += piece_values[captured_piece] * 100
            else:
                # Capturing a pawn with a pawn may give some advantage
                score += 100
        
        # Check for promotion
        if '=' in move:
            promo_piece = move.split('=')[1]
            score += piece_values[promo_piece] * 500
        
        # Preference for center control
        if 'e4' in move or 'd4' in move or 'e5' in move or 'd5' in move:
            score += 50
        if 'c3' in move or 'f3' in move or 'c6' in move or 'f6' in move:
            score += 30
            
        # Prefer moves that bring pieces to better squares (further from edge)
        if not (move[1] == '1' or move[1] == '8' or move[0] == 'a' or move[0] == 'h'):
            score += 50
            
        # Prefer development of knights and bishops
        if move[0] in 'bgh':
            score += 10
            
        return score
    
    # Simple minimax with heuristic
    def minimax(pieces_dict, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate_position(pieces_dict)
        
        legal = generate_legal_moves(pieces_dict, maximizing_player)
        if not legal:
            return evaluate_position(pieces_dict)
            
        if maximizing_player:
            max_eval = -float('inf')
            for move in legal:
                # Simulate the move
                new_pieces = simulate_move(pieces_dict, move)
                eval = minimax(new_pieces, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal:
                # Simulate the move
                new_pieces = simulate_move(pieces_dict, move)
                eval = minimax(new_pieces, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # Generate legal moves (simplified)
    def generate_legal_moves(pieces_dict, player):
        # We will just return the provided ones for efficiency
        return legal_moves
    
    # Simulate a move (simplified)
    def simulate_move(pieces_dict, move):
        new_dict = pieces_dict.copy()
        # Extremely simplified
        # In reality, we would parse the move string properly
        # But since we can't efficiently compute all moves in 1 second,
        # we'll use a simpler approach
        return new_dict
    
    # Prioritize moves with highest evaluation sums
    best_move = None
    best_score = -float('inf')
    
    # First, check for checkmate or captures of higher-value pieces
    # Filter moves to prioritize captures and special moves
    capture_moves = [move for move in legal_moves if 'x' in move or move.startswith('O') or '=' in move]
    
    if capture_moves:
        # Prefer captures that gain material
        for move in capture_moves:
            score = evaluate_move(move, pieces, to_play)
            if score > best_score:
                best_score = score
                best_move = move
        if best_move:
            return best_move, memory
    
    # If no captures, try to evaluate other moves
    for move in legal_moves:
        score = evaluate_move(move, pieces, to_play)
        if score > best_score:
            best_score = score
            best_move = move
            
    # If still no best move, return a random legal move
    if not best_move:
        best_move = legal_moves[0]
    
    return best_move, memory
