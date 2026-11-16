
import re

piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}

def get_to_square(move):
    # Remove check/mate and promotion suffixes
    move = re.sub(r'[#+]$', '', move)
    move = re.sub(r'=.*', '', move)
    # Find the last square in the move string
    squares = re.findall(r'[a-h][1-8]', move)
    if squares:
        return squares[-1]
    elif move == 'O-O':
        return 'g1' if to_play == 'white' else 'g8'
    elif move == 'O-O-O':
        return 'c1' if to_play == 'white' else 'c8'
    return None  # Shouldn't happen for legal moves

def policy(pieces, to_play, legal_moves):
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    scored_moves = []
    for move in legal_moves:
        score = 0
        if move.endswith('#'):
            score = 99999  # Checkmate priority
        elif 'x' in move:
            # Capture: score based on captured piece value (scale by 10 for weighting)
            to_sq = get_to_square(move)
            if to_sq and to_sq in pieces:
                captured_piece = pieces[to_sq]
                if captured_piece[0] == opp_color:
                    score += piece_values[captured_piece[1]] * 10
        elif move.endswith('+'):
            score += 10  # Check bonus
        elif '=' in move:
            # Promotion: net gain (pawn value -1, plus promoted piece value)
            promoted_to = move.split('=')[1]
            score += piece_values[promoted_to] - 1
        elif move in ['O-O', 'O-O-O']:
            score += 5  # Castling bonus for king safety
        
        scored_moves.append((score, move))
    
    # Choose the move with highest score, ties go to first in list (stable sort)
    scored_moves.sort(key=lambda x: -x[0])
    return scored_moves[0][1]
