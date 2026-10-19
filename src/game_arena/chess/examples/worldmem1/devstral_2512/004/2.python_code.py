
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if 'move_count' not in memory:
        memory['move_count'] = 0
        memory['game_phase'] = 'opening'  # opening, middlegame, endgame

    memory['move_count'] += 1

    # Determine game phase (simplified)
    if memory['move_count'] < 10:
        memory['game_phase'] = 'opening'
    elif memory['move_count'] < 30:
        memory['game_phase'] = 'middlegame'
    else:
        memory['game_phase'] = 'endgame'

    # Piece values for material evaluation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0  # King value is 0 for material calculation
    }

    # Evaluate each move
    best_move = None
    best_score = float('-inf')

    for move in legal_moves:
        score = 0

        # 1. Check for checkmate (highest priority)
        if '#' in move:
            return (move, memory)

        # 2. Material gain
        if 'x' in move:
            # Extract captured piece (if any)
            captured_piece = None
            if len(move) > 2 and move[1] == 'x':
                # Format like Bxf5
                captured_piece = move[2]
            elif len(move) > 3 and move[2] == 'x':
                # Format like Nxf5 or R1xf5
                captured_piece = move[3]

            if captured_piece:
                # Get the full piece code (color + type)
                # Find the piece at the destination square
                dest_square = move[-2:] if move[-1] in ['+', '#'] else move[-1]
                if dest_square in pieces:
                    captured_piece_full = pieces[dest_square]
                    if captured_piece_full[0] != to_play[0]:  # Opponent's piece
                        score += piece_values[captured_piece_full[1]] * 10

        # 3. Check
        if '+' in move:
            score += 5

        # 4. Promotion
        if '=' in move:
            promotion_piece = move.split('=')[1]
            score += piece_values[promotion_piece] * 2

        # 5. Castling
        if move in ['O-O', 'O-O-O']:
            score += 3

        # 6. Central control (simplified)
        central_squares = ['d4', 'e4', 'd5', 'e5']
        if memory['game_phase'] == 'opening':
            # Extract destination square
            dest_square = move[-2:] if move[-1] in ['+', '#'] else move[-1]
            if dest_square in central_squares:
                score += 1

        # 7. Piece development (opening only)
        if memory['game_phase'] == 'opening':
            if move[0] in ['N', 'B'] and not move.startswith('Nx') and not move.startswith('Bx'):
                # Developing knight or bishop
                score += 1

        # 8. King safety (avoid moving king in opening)
        if memory['game_phase'] == 'opening' and move[0] == 'K':
            score -= 2

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_move = move

    # If no move was selected (shouldn't happen as legal_moves is non-empty)
    if best_move is None:
        best_move = random.choice(legal_moves)

    return (best_move, memory)
