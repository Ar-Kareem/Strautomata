
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    """
    Chooses the best move based on a simplified chess engine policy.
    """

    def get_legal_moves(board: dict[str, str], player: str) -> list[str]:
        """Placeholder function, replace with actual move generation."""
        # In a real implementation, this function would use the board state
        # to generate a list of all legal moves for the given player.
        # For now, return an empty list as we cannot use chess library.
        return [] # Should be replaced by a call to a move generation function

    def evaluate_board(board: dict[str, str], player: str) -> float:
        """
        A simple evaluation function based on material balance.
        """
        material_score = 0
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}  # King has no material value
        for square, piece in board.items():
            color = piece[0]
            piece_type = piece[1]
            value = piece_values.get(piece_type, 0)
            if color == 'w':
                material_score += value
            else:
                material_score -= value
        return material_score if player == 'white' else -material_score

    def generate_legal_moves(board: dict[str, str], to_play: str) -> list[str]:
        """Generates legal moves without using `chess` library."""
        moves = []
        for start_square in board:
            piece = board[start_square]
            if piece[0] == ('w' if to_play == 'white' else 'b'):
                piece_type = piece[1]
                # Implement move generation logic for each piece type...
                # This is a simplified example and needs to be expanded for full chess rules
                for end_square in generate_candidate_squares(start_square):
                    # Basic collision check
                    if end_square in board:
                        if board[end_square][0] == piece[0]:  # Same color
                            continue  # blocked
                        else:
                            # Capture, determine valid capture moves by Piece type
                            if is_valid_capture_move(start_square, end_square, board, to_play):
                                moves.append(start_square + end_square)
                    else:
                        # Non-capture, determine valid non-capture moves by Piece type
                        if is_valid_non_capture_move(start_square, end_square, board, to_play):
                                moves.append(start_square + end_square)

                # Pawn promotion (simplified to queen for now):
                if piece_type == 'P' and ((to_play == 'white' and start_square[1] == '7') or (to_play == 'black' and start_square[1] == '2')):
                    for end_square in generate_candidate_squares(start_square):
                        if end_square in generate__pawn_promotion_squares(start_square, to_play):
                            moves.append(start_square + end_square + "q") # promote to queen

        return moves

    def generate_candidate_squares(start_square: str) -> list[str]:
        """Dummy candidate square generation for all square on board"""
        candidate_squares = []
        for file in "abcdefgh":
            for rank in "12345678":
                candidate_squares.append(file + rank)
        return candidate_squares

    def is_valid_capture_move(start_square: str, end_square: str, board: dict[str, str], to_play: str) -> bool:
        """Dummy valid capture move checker , always returns False"""
        return False

    def is_valid_non_capture_move(start_square: str, end_square: str, board: dict[str, str], to_play: str) -> bool:
        """Dummy valid non capture move checker , always returns False"""
        return False

    def generate__pawn_promotion_squares(start_square: str, to_play: str) -> list[str]:
         """dummy square generation for pawn promotion"""
         candidate_squares = []
         for file in "abcdefgh":
             if to_play == "white":
                 candidate_squares.append( file + "8")
             else:
                 candidate_squares.append(file + "1")
         return candidate_squares

    legal_moves = generate_legal_moves(pieces, to_play)

    if not legal_moves:
        return "", memory

    best_move = legal_moves[0]  # Initialize with the first legal move
    best_score = float('-inf') if to_play == 'white' else float('inf')

    for move in legal_moves:
        # Create a copy of the board to simulate the move
        new_board = pieces.copy()
        start_square = move[:2]
        end_square = move[2:4]

        # Handle pawn promotion
        if len(move) == 5:  # Pawn promotion case
            new_board[end_square] = ('w' if to_play == 'white' else 'b') + 'Q' # promote to queen
        else:
            new_board[end_square] = new_board[start_square]

        del new_board[start_square]


        score = evaluate_board(new_board, to_play)

        if to_play == 'white':
            if score > best_score:
                best_score = score
                best_move = move
        else:
            if score < best_score:
                best_score = score
                best_move = move


    return best_move, memory
