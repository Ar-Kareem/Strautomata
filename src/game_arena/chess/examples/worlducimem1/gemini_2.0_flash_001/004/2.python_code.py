
import numpy as np

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    """
    Chooses the best legal move for the given player.
    """

    def square_to_index(square):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return rank * 8 + file

    def index_to_square(index):
        file = chr(ord('a') + (index % 8))
        rank = str((index // 8) + 1)
        return file + rank

    def get_legal_moves(board, player):
        legal_moves = []
        piece_values = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':0} #King has no value for eval

        # Determine piece colors based on the player to play.
        if player == 'white':
            friendly_color = 'w'
            opponent_color = 'b'
        else:
            friendly_color = 'b'
            opponent_color = 'w'

        # Function to check if a square is within the board boundaries
        def is_valid_square(square):
            return 0 <= square < 64

        # Function to simulate a move and check if the king is in check
        def is_in_check(board_state, king_square_index, color):
            # Check for attacks from each type of piece
            for i in range(64):
                piece = board_state.get(index_to_square(i)) #Iterate over populated pieces
                if piece is not None and piece[0] != color:
                    opponent_color = piece[0]
                    piece_type = piece[1]

                    # Pawn attacks
                    if piece_type == 'P':
                        direction = 1 if opponent_color == 'w' else -1
                        pawn_attacks = []
                        file = i % 8
                        #White pawns attack "up" the board, while black pawns attack "down"
                        if opponent_color == 'w': #White pawn attacks
                            if file > 0: pawn_attacks.append(i + 7)
                            if file < 7 : pawn_attacks.append(i + 9)
                        else: #Black pawn attacks
                            if file > 0: pawn_attacks.append(i - 9)
                            if file < 7: pawn_attacks.append(i - 7)

                        if king_square_index in pawn_attacks:
                            return True


                    # Knight attacks
                    if piece_type == 'N':
                        knight_moves = [-17, -15, -10, -6, 6, 10, 15, 17]
                        for move in knight_moves:
                            target_square = i + move
                            if is_valid_square(target_square):
                                if target_square == king_square_index:
                                    return True

                    # King attacks (adjacent squares)
                    if piece_type == 'K':
                        king_moves = [-9, -8, -7, -1, 1, 7, 8, 9]
                        for move in king_moves:
                            target_square = i + move
                            if is_valid_square(target_square):
                                if target_square == king_square_index:
                                    return True

                    #Rook and Queen attacks (horizontal and vertical)
                    if piece_type == 'R' or piece_type == 'Q':
                        directions = [-8, 8, -1, 1]  # Up, Down, Left, Right
                        for direction in directions:
                            for distance in range(1, 8): #max distance
                                target_square = i + direction * distance
                                if not is_valid_square(target_square): #Out of bounds, stop searching
                                    break

                                if target_square == king_square_index: #Check, return True
                                    return True
                                #Block by a piece
                                if index_to_square(target_square) in board_state.keys():
                                        break

                    #Bishop and Queen attacks (diagonal)
                    if piece_type == 'B' or piece_type == 'Q':
                        directions = [-9, -7, 7, 9] # Diagonals
                        for direction in directions:
                            for distance in range(1, 8): #max distance
                                target_square = i + direction * distance
                                if not is_valid_square(target_square): #Out of bounds
                                    break
                                if target_square == king_square_index:
                                    return True
                                #Block by a piece
                                if index_to_square(target_square) in board_state.keys():
                                        break
            return False

        #Find king position
        king_square = None
        for square, piece in board.items():
            if piece == friendly_color + 'K':
                king_square = square
                break
        king_square_index = square_to_index(king_square)

        # Iterate over the board to find the current player's pieces
        for start_square, piece in board.items():
            if piece[0] == friendly_color:
                start_index = square_to_index(start_square)
                piece_type = piece[1]

                # Pawn moves
                if piece_type == 'P':
                    direction = -1 if friendly_color == 'w' else 1
                    start_rank = int(start_square[1])
                    
                    # Single step forward
                    target_rank = start_rank + direction
                    target_square = start_square[0] + str(target_rank)
                    if 1 <= target_rank <= 8 and target_square not in board:
                        #Promotion
                        if target_rank == 1 or target_rank == 8:
                            promotions = ['q', 'r', 'b', 'n']
                            for promotion in promotions:
                                move = start_square + target_square + promotion
                                #Simulate move
                                temp_board = board.copy()
                                temp_board[target_square] = friendly_color + promotion.upper() #Promote piece
                                del temp_board[start_square]

                                #Check if move puts king in check.
                                if not is_in_check(temp_board, king_square_index, friendly_color):
                                    legal_moves.append(move)
                        else: #Regular move
                            move = start_square + target_square
                            #Simulate move
                            temp_board = board.copy()
                            temp_board[target_square] = piece
                            del temp_board[start_square]
                             #Check if move puts king in check.
                            if not is_in_check(temp_board, king_square_index, friendly_color):
                                legal_moves.append(move)
                   
                    # Double step forward
                    if start_rank == 2 and friendly_color == 'w' or start_rank == 7 and friendly_color == 'b':
                        target_rank = start_rank + 2 * direction
                        target_square = start_square[0] + str(target_rank)
                        intermediate_rank = start_rank + direction
                        intermediate_square = start_square[0] + str(intermediate_rank)

                        if (1 <= target_rank <= 8 and target_square not in board and intermediate_square not in board):
                            move = start_square + target_square
                             #Simulate move
                            temp_board = board.copy()
                            temp_board[target_square] = piece
                            del temp_board[start_square]
                             #Check if move puts king in check.
                            if not is_in_check(temp_board, king_square_index, friendly_color):
                                legal_moves.append(move)

                    # Captures
                    capture_files = []
                    current_file = ord(start_square[0]) - ord('a')
                    if current_file > 0:
                        capture_files.append(chr(ord(start_square[0]) - 1))
                    if current_file < 7:
                        capture_files.append(chr(ord(start_square[0]) + 1))

                    for file in capture_files:
                        target_rank = start_rank + direction
                        target_square = file + str(target_rank)

                        if 1 <= target_rank <= 8 and target_square in board and board[target_square][0] == opponent_color:
                            #Promotion
                            if target_rank == 1 or target_rank == 8:
                                promotions = ['q', 'r', 'b', 'n']
                                for promotion in promotions:
                                    move = start_square + target_square + promotion
                                     #Simulate move
                                    temp_board = board.copy()
                                    temp_board[target_square] = friendly_color + promotion.upper() #Promote piece
                                    del temp_board[start_square]

                                     #Check if move puts king in check.
                                    if not is_in_check(temp_board, king_square_index, friendly_color):
                                        legal_moves.append(move)

                            else: #Regular capture
                                move = start_square + target_square
                                #Simulate move
                                temp_board = board.copy()
                                temp_board[target_square] = piece
                                del temp_board[start_square]
                                 #Check if move puts king in check.
                                if not is_in_check(temp_board, king_square_index, friendly_color):
                                    legal_moves.append(move)

                # Knight moves
                if piece_type == 'N':
                    knight_moves = [-17, -15, -10, -6, 6, 10, 15, 17]
                    for move in knight_moves:
                        target_index = start_index + move
                        if is_valid_square(target_index):
                            target_square = index_to_square(target_index)
                            if target_square not in board or board[target_square][0] == opponent_color:
                                move = start_square + target_square
                                #Simulate move
                                temp_board = board.copy()
                                if target_square in board: #Capture the piece
                                    del temp_board[target_square]
                                temp_board[target_square] = piece
                                del temp_board[start_square]
                                 #Check if move puts king in check.
                                if not is_in_check(temp_board, king_square_index, friendly_color):
                                    legal_moves.append(move)

                # King moves
                if piece_type == 'K':
                    king_moves = [-9, -8, -7, -1, 1, 7, 8, 9]
                    for move in king_moves:
                        target_index = start_index + move
                        if is_valid_square(target_index):
                            target_square = index_to_square(target_index)
                            if target_square not in board or board[target_square][0] == opponent_color:
                                move = start_square + target_square
                                #Simulate move
                                temp_board = board.copy()

                                if target_square in board: #Capture the piece
                                    del temp_board[target_square]

                                temp_board[target_square] = piece
                                del temp_board[start_square]

                                 #Check if move puts king in check.
                                if not is_in_check(temp_board, king_square_index, friendly_color):
                                    legal_moves.append(move)

                # Rook, Bishop, Queen moves
                if piece_type in ['R', 'B', 'Q']:
                    directions = []
                    if piece_type in ['R', 'Q']:  #Rook & Queen
                        directions.extend([-8, 8, -1, 1])  # Up, Down, Left, Right
                    if piece_type in ['B', 'Q']:  #Bishop and Queen
                        directions.extend([-9, -7, 7, 9]) # Diagonals

                    for direction in directions:
                        for distance in range(1, 8):
                            target_index = start_index + direction * distance
                            if not is_valid_square(target_index):
                                break
                            target_square = index_to_square(target_index)
                            if target_square not in board:
                                move = start_square + target_square
                                 #Simulate move
                                temp_board = board.copy()
                                temp_board[target_square] = piece
                                del temp_board[start_square]
                                 #Check if move puts king in check.
                                if not is_in_check(temp_board, king_square_index, friendly_color):
                                    legal_moves.append(move)
                            else:
                                if board[target_square][0] == opponent_color:
                                    move = start_square + target_square
                                     #Simulate move
                                    temp_board = board.copy()
                                    del temp_board[target_square] #make capture
                                    temp_board[target_square] = piece
                                    del temp_board[start_square]
                                     #Check if move puts king in check.
                                    if not is_in_check(temp_board, king_square_index, friendly_color):
                                        legal_moves.append(move)
                                break
        return legal_moves

    def evaluate_board(board, player):
        """
        A simple evaluation function that considers material advantage.
        """
        score = 0
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}  # King has no value for eval

        # Determine piece colors based on the player to play.
        if player == 'white':
            friendly_color = 'w'
            opponent_color = 'b'
        else:
            friendly_color = 'b'
            opponent_color = 'w'

        for square, piece in board.items():
            if piece[0] == friendly_color:
                score += piece_values[piece[1]]
            elif piece[0] == opponent_color:
                score -= piece_values[piece[1]]
        return score

    legal_moves = get_legal_moves(pieces, to_play)

    if not legal_moves:
        return "", memory # No legal moves available - should not occur in arena, but added as a safe guard.

    best_move = legal_moves[0]
    best_score = -np.inf if to_play == 'white' else np.inf

    # Prioritize captures
    capture_moves = [move for move in legal_moves if len(move) == 4 and move[2:4] in pieces] #No promotions
    if capture_moves:
        for move in capture_moves:
            temp_pieces = pieces.copy()
            target_square = move[2:4]
            start_square = move[0:2]
            captured_piece = temp_pieces.get(target_square)
            start_piece = temp_pieces.get(start_square)
            if target_square in temp_pieces:
                del temp_pieces[target_square]
            del temp_pieces[start_square]
            temp_pieces[target_square] = start_piece
            score = evaluate_board(temp_pieces, to_play)
            if to_play == 'white' and score > best_score:
                best_score = score
                best_move = move
            elif to_play == 'black' and score < best_score:
                best_score = score
                best_move = move
    else:
        # Prioritize checks
        for move in legal_moves:
            temp_pieces = pieces.copy()
            target_square = move[2:4]
            start_square = move[0:2]
            start_piece = temp_pieces.get(start_square)

            #Handle Promotions
            if  len(move) > 4:
                promotion_type = move[4].upper() #Only concerned with type, color will be picked up from the promotion
                del temp_pieces[start_square]
                temp_pieces[target_square] = to_play[0] + promotion_type
            else: #No promotion
                if target_square in temp_pieces:
                    del temp_pieces[target_square] #take the target
                del temp_pieces[start_square] #remove moved piece
                temp_pieces[target_square] = start_piece

            if to_play == 'white':
                opponent_king_square = None
                for sq, pc in temp_pieces.items():
                    if pc == 'bK':
                        opponent_king_square = sq
                        break
                temp_legal_moves = get_legal_moves(temp_pieces, 'black')
                if opponent_king_square and any(opponent_king_square in m for m in temp_legal_moves):
                    best_move = move
                    break #take immediatley

            if to_play == 'black':
                opponent_king_square = None
                for sq, pc in temp_pieces.items():
                    if pc == 'wK':
                        opponent_king_square = sq
                        break
                temp_legal_moves = get_legal_moves(temp_pieces, 'white')
                if opponent_king_square and any(opponent_king_square in m for m in temp_legal_moves):
                    best_move = move
                    break #take immediatley

        #Otherwise, pick a random move
        else:
            best_move = np.random.choice(legal_moves)

    return best_move, memory
