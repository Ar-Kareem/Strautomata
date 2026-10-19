
import random

def piece_value(piece):
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000}
    return values.get(piece.upper(), 0)

def parse_move(move):
    if 'O-O' in move:
        return None, None, 'castle_k'
    if 'O-O-O' in move:
        return None, None, 'castle_q'
    if '=' in move:
        # Promotion: e.g., 'e7=Q'
        parts = move.split('=')
        first_part = parts[0]
        dest = first_part[-2:]
        prom_piece = parts[1]
        is_capture = 'x' in move
        return dest, is_capture, 'promotion_' + prom_piece
    else:
        # Regular move, find destination
        if move[-1] in ['+', '#']:
            dest = move[-3:-1]
        elif move[-1].isalpha():
            dest = move[-2:]
        else:
            dest = move[-2:]
        is_capture = 'x' in move
        return dest, is_capture, None

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    our_color = 'w' if to_play == 'white' else 'b'
    scored_moves = []
    for move in legal_moves:
        score = 0
        dest, is_capture, info = parse_move(move)
        if dest and dest in pieces:
            captured_piece = pieces[dest]
            captured_color = captured_piece[0]
            captured_type = captured_piece[1]
            if is_capture and captured_color != our_color:
                score += piece_value(captured_type)
        if info:
            if 'castle' in info:
                score += 100  # Encourage castling for safety
            elif 'promotion' in info:
                prom_type = info.split('_')[1]
                score += piece_value(prom_type) - 1  # Promotion gain
        if move.endswith('#'):
            score += 10000  # Checkmate priority
        elif move.endswith('+'):
            score += 500  # Check priority
        scored_moves.append((score, move))
    
    # Get the max score, pick the first move with that score
    if scored_moves:
        max_score = max(event[0] for event in scored_moves)
        best_moves = [move for score, move in scored_moves if score == max_score]
        chosen_move = best_moves[0]  # Pick first in case of ties
    else:
        # Fallback, though should never happen
        chosen_move = legal_moves[0]
    
    return chosen_move, {}  # Return empty memory
