
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'

    best_score = -np.inf
    best_move = legal_moves[0]  # fallback

    for move in legal_moves:
        score = 0.0

        # Priority 1: Check for checkmate
        if '#' in move:
            return move  # Immediate mate

        # Priority 2: Capture
        if 'x' in move:
            # Find the target square: rightmost algebraic square in the move
            parts = move.replace('+', '').replace('#', '').split('x')
            if len(parts) > 1:
                target_square = parts[-1].strip()
                if target_square in pieces:
                    captured_piece_code = pieces[target_square]
                    if captured_piece_code[0] == opp_color:
                        piece_type = captured_piece_code[1]
                        score += piece_values[piece_type]

        # Priority 3: Promotion
        if '=' in move:
            promoted_piece = move.split('=')[-1].strip()[0]  # Q, R, B, or N
            score += piece_values[promoted_piece]
            if promoted_piece == 'Q':
                score += 0.5  # Prefer queens
            # Remove pawn being promoted (implicit)
            score -= piece_values['P']

        # Priority 4: Castling
        if move == 'O-O' or move == 'O-O-O':
            score += 0.4  # King safety and rook activation

        # Priority 5: Check
        if '+' in move:
            score += 0.2  # Encourage checks

        # Priority 6: Central pawn control (only for pawn moves to center)
        if move.startswith(('d3', 'd4', 'd5', 'd6', 'e3', 'e4', 'e5', 'e6')) and 'x' not in move and '=' not in move:
            score += 0.1  # Slight bonus for central pawn pushes

        # Break ties deterministically by move string (alphabetical)
        if score > best_score or (score == best_score and move < best_move):
            best_score = score
            best_move = move

    return best_move
