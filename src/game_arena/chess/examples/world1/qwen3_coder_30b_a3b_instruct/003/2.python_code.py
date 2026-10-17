
import random
from typing import Dict, List, Tuple

def evaluate_board(pieces: Dict[str, str], to_play: str) -> int:
    """Simple piece value evaluation"""
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }
    
    score = 0
    for piece in pieces.values():
        piece_type = piece[1]
        if piece[0] == to_play[0]:  # Same color as player
            score += piece_values[piece_type]
        else:  # Opponent piece
            score -= piece_values[piece_type]
    
    return score

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    """
    Select the best move using a combination of tactical awareness and
    positional evaluation.
    """
    if not legal_moves:
        return random.choice(legal_moves)
    
    # Check for checkmate moves first (if we can deliver checkmate)
    for move in legal_moves:
        # This is a simplified approach - we'll use basic heuristics
        if move.endswith('+') or move.endswith('#'):  # Check/checkmate
            return move
    
    # Prioritize captures
    capture_moves = []
    for move in legal_moves:
        if 'x' in move:
            capture_moves.append(move)
    
    if capture_moves:
        # Prefer captures of high-value pieces
        def capture_priority(move):
            if 'x' in move:
                captured_piece = move[move.index('x') + 1]
                if captured_piece == 'Q':
                    return 4
                elif captured_piece == 'R':
                    return 3
                elif captured_piece == 'B' or captured_piece == 'N':
                    return 2
                elif captured_piece == 'P':
                    return 1
                else:
                    return 0
            return 0
        
        capture_moves.sort(key=capture_priority, reverse=True)
        return capture_moves[0]
    
    # Prefer castling moves if available
    castling_moves = [m for m in legal_moves if m in ['O-O', 'O-O-O']]
    if castling_moves:
        return castling_moves[0]
    
    # Prefer moves that develop pieces (not moving the king early)
    development_moves = [m for m in legal_moves if m[0] in 'NBRQ' or (m[0] == 'K' and len(m) > 1)]
    if development_moves:
        # Prefer knights and bishops over rooks and queens for development
        def develop_score(move):
            if move[0] == 'N':
                return 3
            elif move[0] == 'B':
                return 2
            elif move[0] == 'R':
                return 1
            elif move[0] == 'Q':
                return 0
            else:
                return -1
        development_moves.sort(key=develop_score, reverse=True)
        return development_moves[0]
    
    # If nothing special, just return a random legal move
    return random.choice(legal_moves)
