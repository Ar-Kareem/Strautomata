
import random
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str], memory: Dict) -> Tuple[str, Dict]:
    # Heuristic evaluation function for moves
    def evaluate_move(move_str: str) -> int:
        score = 0
        # If the move results in checkmate, it's top priority
        if move_str.endswith('+') or move_str.endswith('#'):
            score += 10000
        # Captures get high scores
        if 'x' in move_str:
            # For simplicity, we'll weigh captures higher
            score += 1000
        # Check if move is a promotion (very strong)
        if '=' in move_str:
            # Promoting to queen is strongest, knight next
            if '=Q' in move_str or '=q' in move_str:
                score += 800
            elif '=R' in move_str or '=r' in move_str:
                score += 500
            elif '=B' in move_str or '=b' in move_str:
                score += 300
            elif '=N' in move_str or '=n' in move_str:
                score += 300
        # Castling moves
        if move_str in ['O-O', 'O-O-O']:
            score += 500
        # Control central squares (e4, e5, d4, d5)
        if any(sq in move_str for sq in ['e4', 'e5', 'd4', 'd5']):
            score += 100
        # Development moves (knights and bishops)
        if move_str.startswith('N') or move_str.startswith('B'):
            score += 50
        # King safety improvements
        if move_str.startswith('K'):
            score += 20
        # Avoid moves that leave own pieces undefended or vulnerable
        # We don't implement full vulnerability analysis in this basic version
        return score

    # If there's only one move, pick it
    if len(legal_moves) == 1:
        return (legal_moves[0], memory)
    
    # Evaluate all legal moves
    move_scores = [(move, evaluate_move(move)) for move in legal_moves]
    
    # Sort moves by score descending
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick the move with the highest score
    best_move = move_scores[0][0]
    
    return (best_move, memory)
