
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values for material evaluation
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0  # King's value is not considered in material evaluation
    }

    # Determine the color of the current player
    current_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    # Generate all legal moves (this is a placeholder; in practice, legal_moves would be provided)
    # For the purpose of this example, we assume legal_moves is provided as a global variable or similar
    # Here, we simulate the process of selecting the best move from legal_moves

    # Placeholder for legal_moves (in a real scenario, this would be provided)
    legal_moves = []  # This should be populated with actual legal moves

    # If no legal moves are provided, return a default move (this is a fallback)
    if not legal_moves:
        return 'e2e4'  # Default move if no legal moves are provided (should not happen in practice)

    # Evaluate each move based on material gain and other factors
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move to evaluate its outcome
        # This is a simplified evaluation; in practice, you would use a more sophisticated method
        # For example, you could use a minimax algorithm with alpha-beta pruning

        # Check if the move captures a piece
        if len(move) == 4:
            from_square = move[:2]
            to_square = move[2:]

            # Check if the destination square has an opponent's piece
            if to_square in pieces and pieces[to_square][0] == opponent_color:
                captured_piece = pieces[to_square][1]
                score = piece_values.get(captured_piece, 0)

                # Prioritize capturing higher-value pieces
                if score > best_score:
                    best_score = score
                    best_move = move

        # Check for pawn promotion (move length is 5)
        elif len(move) == 5:
            # Pawn promotion is always a good move, so prioritize it
            best_move = move
            break

    # If no capturing move is found, choose a random legal move
    if best_move is None:
        best_move = legal_moves[0]  # Default to the first legal move

    return best_move
