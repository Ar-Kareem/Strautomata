
import random

def piece_value(piece: str) -> int:
    """Assign a numerical value to each piece."""
    if piece == 'Q':
        return 9
    elif piece == 'R':
        return 5
    elif piece == 'B':
        return 3
    elif piece == 'N':
        return 3
    elif piece == 'P':
        return 1
    elif piece == 'K':
        return 0 # King has no material value
    else:
        return 0

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Select the best move based on a combination of heuristics.
    """

    my_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    def evaluate_move(move: str) -> float:
      """Evaluates a given move."""
      score = 0.0

      # Checkmate
      if '#' in move:
        return float('inf')

      # Captures
      if 'x' in move:
        captured_piece = move[move.find('x') + 1]
        if captured_piece.isupper():
          score += piece_value(captured_piece)
        else:
          #Captures of pawns are less valuable, but should still be captures if safe
          score +=0.5
      # Check
      if '+' in move:
        score += 0.1  # Slightly prioritize checks

      return score
    
    best_move = random.choice(legal_moves)
    best_score = float('-inf')

    for move in legal_moves:
      score = evaluate_move(move)
      
      if score > best_score:
        best_score = score
        best_move = move
    

    return best_move
