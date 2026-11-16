
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Chooses the best move based on material advantage and tactical considerations.
    """

    def get_piece_value(piece):
        if piece == 'Q':
            return 9
        elif piece == 'R':
            return 5
        elif piece == 'B':
            return 3
        elif piece == 'N':
            return 3
        elif piece == 'P':
            return 1
        elif piece == 'K': #arbitrary value
            return 100
        else:
            return 0

    def evaluate_board(pieces, to_play):
        """
        Evaluates the chess board based on material advantage.
        """
        white_value = 0
        black_value = 0

        for square, piece in pieces.items():
            if piece[0] == 'w':
                white_value += get_piece_value(piece[1])
            else:
                black_value += get_piece_value(piece[1])

        if to_play == 'white':
            return white_value - black_value
        else:
            return black_value - white_value

    def generate_legal_moves(pieces, to_play):
        """
        Generates a list of legal moves from the current board state.

        Note: This is a simplified move generator and doesn't cover all chess rules.
              It focuses on the most common move types to ensure speed.
        """

        legal_moves = []

        def get_rank_file(square):
            return ord(square[0]) - ord('a'), int(square[1]) - 1

        def get_square(rank, file):
            return chr(file + ord('a')) + str(rank + 1)

        color = 'w' if to_play == 'white' else 'b'
        opponent_color = 'b' if to_play == 'white' else 'w'

        for start_square, piece in pieces.items():
            if piece[0] == color:
                piece_type = piece[1]
                start_rank, start_file = get_rank_file(start_square)

                # Pawn moves
                if piece_type == 'P':
                    # Forward moves
                    if to_play == 'white':
                        if start_rank < 7 and get_square(start_rank + 1, start_file) not in pieces:
                            legal_moves.append(start_square + get_square(start_rank + 1, start_file))
                            if start_rank == 1 and get_square(start_rank + 2, start_file) not in pieces and get_square(start_rank + 1, start_file) not in pieces:
                                legal_moves.append(start_square + get_square(start_rank + 2, start_file))

                        # Captures
                        if start_rank < 7 and start_file > 0 and get_square(start_rank + 1, start_file - 1) in pieces and pieces[get_square(start_rank + 1, start_file - 1)][0] == opponent_color :
                            legal_moves.append(start_square + get_square(start_rank + 1, start_file - 1))
                        if start_rank < 7 and start_file < 7 and get_square(start_rank + 1, start_file + 1) in pieces and pieces[get_square(start_rank + 1, start_file + 1)][0] == opponent_color:
                            legal_moves.append(start_square + get_square(start_rank + 1, start_file + 1))

                        # Promotion
                        if start_rank == 6:
                            if start_rank < 7 and get_square(start_rank + 1, start_file) not in pieces:
                                legal_moves.append(start_square + get_square(start_rank + 1, start_file) + 'q')
                            if start_rank < 7 and start_file > 0 and get_square(start_rank + 1, start_file - 1) in pieces and pieces[get_square(start_rank + 1, start_file - 1)][0] == opponent_color:
                                legal_moves.append(start_square + get_square(start_rank + 1, start_file - 1) + 'q')
                            if start_rank < 7 and start_file < 7 and get_square(start_rank + 1, start_file + 1) in pieces and pieces[get_square(start_rank + 1, start_file + 1)][0] == opponent_color:
                                legal_moves.append(start_square + get_square(start_rank + 1, start_file + 1) + 'q')
                    else: # black
                        if start_rank > 0 and get_square(start_rank - 1, start_file) not in pieces:
                            legal_moves.append(start_square + get_square(start_rank - 1, start_file))
                            if start_rank == 6 and get_square(start_rank - 2, start_file) not in pieces and get_square(start_rank - 1, start_file) not in pieces:
                                legal_moves.append(start_square + get_square(start_rank - 2, start_file))

                        # Captures
                        if start_rank > 0 and start_file > 0 and get_square(start_rank - 1, start_file - 1) in pieces and pieces[get_square(start_rank - 1, start_file - 1)][0] == opponent_color:
                            legal_moves.append(start_square + get_square(start_rank - 1, start_file - 1))
                        if start_rank > 0 and start_file < 7 and get_square(start_rank - 1, start_file + 1) in pieces and pieces[get_square(start_rank - 1, start_file + 1)][0] == opponent_color:
                            legal_moves.append(start_square + get_square(start_rank - 1, start_file + 1))
                        # Promotion
                        if start_rank == 1:
                            if start_rank > 0 and get_square(start_rank - 1, start_file) not in pieces:
                                legal_moves.append(start_square + get_square(start_rank - 1, start_file) + 'q')
                            if start_rank > 0 and start_file > 0 and get_square(start_rank - 1, start_file - 1) in pieces and pieces[get_square(start_rank - 1, start_file - 1)][0] == opponent_color:
                                legal_moves.append(start_square + get_square(start_rank - 1, start_file - 1) + 'q')
                            if start_rank > 0 and start_file < 7 and get_square(start_rank - 1, start_file + 1) in pieces and pieces[get_square(start_rank - 1, start_file + 1)][0] == opponent_color:
                                legal_moves.append(start_square + get_square(start_rank - 1, start_file + 1) + 'q')
                # Knight moves
                if piece_type == 'N':
                    possible_moves = [(start_rank + 2, start_file + 1), (start_rank + 2, start_file - 1),
                                        (start_rank - 2, start_file + 1), (start_rank - 2, start_file - 1),
                                        (start_rank + 1, start_file + 2), (start_rank + 1, start_file - 2),
                                        (start_rank - 1, start_file + 2), (start_rank - 1, start_file - 2)]

                    for rank, file in possible_moves:
                        if 0 <= rank < 8 and 0 <= file < 8:
                            target_square = get_square(rank, file)
                            if target_square not in pieces or pieces[target_square][0] == opponent_color:
                                legal_moves.append(start_square + target_square)

                # King moves
                if piece_type == 'K':
                    possible_moves = [(start_rank + 1, start_file), (start_rank - 1, start_file),
                                        (start_rank, start_file + 1), (start_rank, start_file - 1),
                                        (start_rank + 1, start_file + 1), (start_rank + 1, start_file - 1),
                                        (start_rank - 1, start_file + 1), (start_rank - 1, start_file - 1)]

                    for rank, file in possible_moves:
                        if 0 <= rank < 8 and 0 <= file < 8:
                            target_square = get_square(rank, file)
                            if target_square not in pieces or pieces[target_square][0] == opponent_color:
                                legal_moves.append(start_square + target_square)
                
                # Rook, Bishop and Queen moves
                if piece_type in ['R', 'B', 'Q']:
                    directions = []
                    if piece_type in ['R', 'Q']:
                        directions.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])  # Rook directions
                    if piece_type in ['B', 'Q']:
                        directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])  # Bishop directions

                    for dr, df in directions:
                        for i in range(1, 8):
                            rank = start_rank + i * dr
                            file = start_file + i * df

                            if 0 <= rank < 8 and 0 <= file < 8:
                                target_square = get_square(rank, file)
                                if target_square not in pieces:
                                    legal_moves.append(start_square + target_square)
                                else:
                                    if pieces[target_square][0] == opponent_color:
                                        legal_moves.append(start_square + target_square)
                                    break  # blocked by own or opponent's piece
                            else:
                                break # Out of bounds

        return legal_moves

    legal_moves = generate_legal_moves(pieces, to_play)

    if not legal_moves:
        return None  # No legal moves available

    best_move = None
    best_value = -np.inf if to_play == 'white' else np.inf

    for move in legal_moves:
        temp_pieces = pieces.copy()
        start_square = move[:2]
        end_square = move[2:4]
        promotion = len(move) > 4

        # Perform the move on the temporary board
        piece_to_move = temp_pieces[start_square]
        del temp_pieces[start_square]
        temp_pieces[end_square] = piece_to_move

        if promotion:
            temp_pieces[end_square] = piece_to_move[0] + move[4].upper()

        # Evaluate the board after the move
        value = evaluate_board(temp_pieces, to_play)

        # Update the best move if needed
        if to_play == 'white':
            if value > best_value:
                best_value = value
                best_move = move
        else:
            if value < best_value:
                best_value = value
                best_move = move

    # If no best_move, return any legal move
    if best_move is None:
        return legal_moves[0]
    return best_move
