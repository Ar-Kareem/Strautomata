
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    material_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0
    }

    # Immediate checkmate priority
    for move in legal_moves:
        if move.endswith('#'):
            return (move, memory)

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        current_score = 0

        # Castling bonus for king safety
        if move in ['O-O', 'O-O-O']:
            current_score += 50

        # Promotion evaluation
        elif '=' in move:
            parts = move.split('=')
            if len(parts) < 2 or len(parts[0]) < 2:
                continue
            dest_part = parts[0]
            dest_square = dest_part[-2:]  # Last two characters for destination
            captured = dest_square in pieces

            # Extract promoted piece type
            promoted_to = parts[1][0] if len(parts[1]) > 0 else 'Q'

            # Score promotion gain
            pm_value = material_values.get(promoted_to, 0)
            current_score += (pm_value - 1) * 10  # High weight for promotion

            # Add captured piece if promotion is a capture
            if captured:
                captured_piece = pieces[dest_square]
                ct = captured_piece[1]
                current_score += material_values[ct] * 10

        # Regular move evaluation (captures, checks)
        else:
            is_capture = 'x' in move
            clean_move = move.rstrip('+#')
            if len(clean_move) >= 2:
                dest_square = clean_move[-2:]
            else:
                dest_square = None

            # Score for captures
            if is_capture and dest_square and dest_square in pieces:
                ct = pieces[dest_square][1]
                current_score += material_values[ct] * 5  # Less weight than promotions

            # Small bonus for checks
            if move.endswith('+'):
                current_score += 2

        # Update best move if score improved
        if current_score > best_score:
            best_score = current_score
            best_move = move

    # Fallback to random/legal move if no scoring criteria triggered
    return (best_move if best_move else legal_moves[0], memory)
