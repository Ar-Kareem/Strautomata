
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Selects a chess move based on a simple policy.

    Args:
        pieces (dict[str, str]): A dictionary mapping squares to piece codes.
        to_play (str): Either 'white' or 'black', indicating the player's turn.
        legal_moves (list[str]): A list of legal moves.

    Returns:
        str: A legal move string.
    """

    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}  # Assign numerical values to pieces

    def evaluate_capture(move: str) -> float:
        """
        Evaluates the material gain from a capture.
        Returns a positive float if the capture is favorable, 0 if no capture occurs,
        or a negative float if the piece being captured is more valuable than the capturing piece.
        """
        if 'x' in move:
            captured_piece = move.split('x')[-1][0].upper()
            if captured_piece.isdigit():
              captured_piece = move.split('x')[-1][1].upper()
              #If pawn promotion is occuring.

            for piece_type, value in piece_values.items():
                if captured_piece == piece_type:
                    captured_value = value
                    break
            else:
                captured_value = 1  #If no letter found assume pawn capture.

            capturing_piece = move[0].upper()
            if capturing_piece in piece_values:
              capturing_piece_value = piece_values[capturing_piece]
            else:
               capturing_piece_value = 1 #pawn?

            return captured_value - capturing_piece_value
        else:
            return 0.0  # No capture, therefore no material change

    # 1. Checkmate
    for move in legal_moves:
        if '#' in move:
            return move

    # 2. Prioritize Captures (Material Gain) - Improved capture evaluation
    best_capture_move = None
    best_capture_value = -1000  # Initialize with a very low value

    for move in legal_moves:
        capture_value = evaluate_capture(move)
        if capture_value > best_capture_value:
             best_capture_value = capture_value
             best_capture_move = move

    if best_capture_move:
        return best_capture_move


    # 3. Check moves - Evaluate enemy's mobility, checks or captures
    for move in legal_moves:
        if '+' in move:
            return move

    # 4. Basic Move (Pawn/Piece advancement) - Default to center if nothing else applies
    for move in legal_moves:
        if 'e4' in move or 'd4' in move or 'e5' in move or 'd5' in move:
            return move
        if 'Nf3' in move or 'Nc3' in move:
            return move

    # 5. Return the first legal move - Avoid illegal move errors in all cases
    return legal_moves[0]
