
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if 'piece_values' not in memory:
        memory['piece_values'] = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
        memory['starting_positions'] = {
            'w': {'a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1', 'a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2'},
            'b': {'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8', 'a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7'}
        }
        memory['center_squares'] = {'d4', 'e4', 'd5', 'e5'}

    # Determine opponent color
    opponent = 'black' if to_play == 'white' else 'white'
    my_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    # Helper function to get piece value
    def get_piece_value(piece_code):
        if piece_code[0] == my_color:
            return memory['piece_values'].get(piece_code[1], 0)
        else:
            return -memory['piece_values'].get(piece_code[1], 0)

    # Evaluate each move
    move_scores = []
    for move in legal_moves:
        score = 0

        # Check for checkmate
        if '#' in move:
            score += 10000
            move_scores.append((move, score))
            continue

        # Check for check
        if '+' in move:
            score += 100

        # Check for promotion
        if '=' in move:
            score += 80  # High value for promotion

        # Check for capture
        if 'x' in move:
            # Extract the captured piece (assuming format like 'Bxf5' or 'hxg5')
            parts = move.split('x')
            if len(parts) > 1:
                target_square = parts[1]
                if target_square in pieces:
                    captured_piece = pieces[target_square]
                    if captured_piece[0] == opponent_color:
                        score += memory['piece_values'].get(captured_piece[1], 0) * 10

        # Check if move develops a piece (from starting position)
        if len(move) >= 2 and move[0].isalpha() and move[1].isdigit():
            from_square = move[:2] if move[2] != 'x' else move[:2]  # Handle moves like 'Nec3'
            if from_square in memory['starting_positions'][my_color]:
                score += 5

        # Check if move controls center
        if len(move) >= 2:
            to_square = move[-2:] if move[-1] not in '+#' else move[-3:-1]
            if to_square in memory['center_squares']:
                score += 3

        move_scores.append((move, score))

    # Sort moves by score (descending)
    move_scores.sort(key=lambda x: x[1], reverse=True)

    # Get the best move(s)
    best_score = move_scores[0][1]
    best_moves = [move for move, score in move_scores if score == best_score]

    # If multiple moves have the same best score, choose randomly
    chosen_move = random.choice(best_moves)

    return (chosen_move, memory)
