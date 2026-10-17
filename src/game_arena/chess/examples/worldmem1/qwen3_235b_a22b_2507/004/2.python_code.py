
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Standard piece values (for material calculation)
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

    # Determine player color
    our_color = 'w' if to_play == 'white' else 'b'
    enemy_color = 'b' if to_play == 'white' else 'w'

    def get_piece_at(square: str) -> str:
        return pieces.get(square, None)

    def is_capture(move: str) -> bool:
        return 'x' in move and '=' not in move  # exclude promotions with capture notation

    def is_promotion(move: str) -> bool:
        return '=Q' in move or '=R' in move or '=B' in move or '=N' in move

    def is_castle(move: str) -> bool:
        return move == 'O-O' or move == 'O-O-O'

    def is_checkmate(move: str) -> bool:
        return move.endswith('#')

    def is_check(move: str) -> bool:
        return move.endswith('+') and not move.endswith('#')

    def evaluate_move(move: str) -> float:
        score = 0.0

        # 1. Checkmate is absolutely prioritized
        if is_checkmate(move):
            return 10000

        # 2. Promotions: highly valuable, especially to Queen
        if is_promotion(move):
            promoted_piece = move[-1]
            score += piece_values[promoted_piece] * 2  # extra incentive
            if promoted_piece == 'Q':
                score += 5  # bonus for queening
            return score

        # 3. Castling: big safety bonus
        if is_castle(move):
            score += 4
            return score

        # 4. Capture evaluation
        if is_capture(move):
            # Extract captured square — tricky due to disambiguation and checks
            # Format like: Rxe5, Nfxe5, Qd2xc3+, bxc3
            # We look for 'x' and the following square
            x_index = move.index('x')
            # The square after 'x' up to '+' or '=' or end
            potential_square = ''
            for c in move[x_index+1:]:
                if c in 'abcdefgh' and len(potential_square) == 0:
                    potential_square += c
                elif c in '12345678' and len(potential_square) == 1:
                    potential_square += c
                    break
                else:
                    break

            if len(potential_square) == 2:
                captured_piece_code = get_piece_at(potential_square)
                if captured_piece_code is not None:
                    captured_color = captured_piece_code[0]
                    captured_piece_type = captured_piece_code[1]
                    if captured_color != our_color:  # valid capture
                        material_gain = piece_values[captured_piece_type]
                        score += material_gain
                    else:
                        # Risky capture (maybe a trap)
                        score -= piece_values[captured_piece_type]  # penalize
            else:
                # Could not parse square — fallback
                score += 1  # still something

        # 5. Check moves: tactical alert
        if is_check(move):
            score += 1.5

        # 6. Encourage central pawn advances
        # Simple heuristic: e-pawn and d-pawn up to e4/d4 (for white), e5/d5 (for black)
        if move in ['e4', 'd4', 'e5', 'd5'] and move.islower():
            score += 0.5

        # 7. Penalize non-castling king moves unless necessary
        if move.startswith('K') and len(move) == 3 and not is_capture(move) and not is_castle(move):
            score -= 0.2  # discourage random king walks

        return score

    # Evaluate all legal moves
    scored_moves = [(move, evaluate_move(move)) for move in legal_moves]

    # Choose the move with the highest score
    best_move = max(scored_moves, key=lambda x: x[1])[0]

    return best_move, memory
