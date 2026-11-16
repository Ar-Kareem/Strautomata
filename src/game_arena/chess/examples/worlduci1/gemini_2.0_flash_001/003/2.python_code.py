
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Chooses the best move from the given legal moves based on a heuristic evaluation.
    """

    def get_legal_moves(board: dict[str, str], player: str) -> list[str]:
        """Placeholder for a proper legal move generator.  Returns random moves for now."""
        all_moves = []
        for start_square, piece in board.items():
            if (player == "white" and piece[0] == "w") or (player == "black" and piece[0] == "b"):
                for target_file in "abcdefgh":
                    for target_rank in "12345678":
                        target_square = target_file + target_rank
                        all_moves.append(start_square + target_square)  # Dummy Legal Move Generation, will always return valid format

        return all_moves
    
    def evaluate_board(board: dict[str, str], player: str) -> float:
        """
        Evaluates the board based on material, king safety, and piece activity.
        """
        material_value = 0
        king_safety_value = 0
        piece_activity_value = 0
        
        # Piece values
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000}
        
        # King safety is proxied by distance to center and number of pawns closeby.

        king_square = None
        for square, piece in board.items():
            if piece == 'wK' and player == 'white':
                king_square = square
            elif piece == 'bK' and player == 'black':
                king_square = square
            
        if king_square is not None:
            file = ord(king_square[0]) - ord('a')
            rank = int(king_square[1]) - 1
            distance_from_center = abs(3.5 - file) + abs(3.5 - rank) #closer to zero is safer

            king_safety_value = -distance_from_center

        
        for square, piece in board.items():
            color = piece[0]
            piece_type = piece[1]
            
            if color == 'w':
                if player == 'white':
                    material_value += piece_values.get(piece_type, 0)
                else:
                     material_value -= piece_values.get(piece_type, 0)
            else:
                if player == 'black':
                    material_value += piece_values.get(piece_type, 0)
                else:
                     material_value -= piece_values.get(piece_type, 0)

        # Piece activity is roughly related to how many moves a piece has.
        # Adding dummy values to incentivize move diversification.
        piece_activity_value = random.random() * 0.1 

        return material_value + king_safety_value + piece_activity_value


    def minimax(board: dict[str, str], depth: int, alpha: float, beta: float, maximizing_player: bool, original_player: str) -> tuple[str, float]:
        """
        Performs minimax search with alpha-beta pruning.
        """
        if depth == 0:
            return None, evaluate_board(board, original_player)

        legal_moves = get_legal_moves(board, "white" if maximizing_player else "black")
        if not legal_moves:
            # Checkmate or stalemate. Since a perfect move generator doesn't exist, add penalty to discourage "no moves."
            return None, -10000 if maximizing_player else 10000 #if its maximizing players turn and they have no moves, their score is -10k, and vice versa.

        best_move = None
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                new_board = make_move(board, move)
                _, eval = minimax(new_board, depth - 1, alpha, beta, False, original_player)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Beta cutoff
            return best_move, max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_board = make_move(board, move)
                _, eval = minimax(new_board, depth - 1, alpha, beta, True, original_player)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha cutoff
            return best_move, min_eval
    
    def make_move(board: dict[str, str], move: str) -> dict[str, str]:
        """
        Applies the given move to the board and returns the new board state.
        """
        start_square = move[:2]
        end_square = move[2:4]
        
        new_board = board.copy()
        piece = new_board[start_square]
        del new_board[start_square]
        new_board[end_square] = piece
        
        # Handle pawn promotion (very rudimentary)
        if len(move) == 5:
            promotion_piece = move[4].upper()
            if to_play == 'white':
                new_board[end_square] = 'w' + promotion_piece
            else:
                new_board[end_square] = 'b' + promotion_piece

        return new_board
        
    legal_moves = get_legal_moves(pieces, to_play)
    if not legal_moves:
        return "a1a2"  # Return a valid move if no legal moves are found.

    best_move, _ = minimax(pieces, 2, float('-inf'), float('inf'), to_play == "white", to_play) # Search depth of 2.

    if best_move is None:
        return random.choice(legal_moves)
    
    return best_move
