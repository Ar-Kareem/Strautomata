
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    def get_destination(move: str) -> str:
        if move in ['O-O', 'O-O-O']:
            return None
        squares = re.findall(r'[a-h][1-8]', move)
        return squares[-1] if squares else None

    best_score = -float('inf')
    best_move = None
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

    for move in legal_moves:
        score = 0

        # Checkmate detection
        if move.endswith('#'):
            score = 10000

        else:
            # Castling
            if move in ['O-O', 'O-O-O']:
                score += 50

            # Promotion
            elif '=' in move:
                promotion_type = move.split('=')[1].upper()
                if promotion_type in piece_values:
                    score += piece_values[promotion_type] * 100
                dest_square = get_destination(move)
                if dest_square and pieces.get(dest_square):
                    captured_type = pieces[dest_square][1]
                    score += piece_values.get(captured_type, 0) * 100

            # Regular capture or move
            else:
                dest_square = get_destination(move)
                if dest_square and pieces.get(dest_square):
                    # Material gain calculation
                    if move[0] in 'KQRBN':
                        moving_type = move[0]
                    else:
                        moving_type = 'P'
                    moving_value = piece_values.get(moving_type, 0)
                    captured_type = pieces[dest_square][1]
                    captured_value = piece_values.get(captured_type, 0)
                    material_gain = captured_value - moving_value
                    score += material_gain * 100

            # Check bonus
            if move.endswith('+'):
                score += 10

        # Update best move if score is higher
        if score > best_score:
            best_score = score
            best_move = move

    return (best_move, {})
