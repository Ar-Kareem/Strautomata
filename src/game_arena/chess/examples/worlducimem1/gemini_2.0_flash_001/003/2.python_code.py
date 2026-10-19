
import random

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    """
    Chooses a move based on a simple evaluation function.
    """

    def get_legal_moves(board: dict[str, str], player: str) -> list[str]:
        """
        This function is used to generate all possible and legal moves
        Args:
            board: a dictionary of the current board
            player: could be 'white' or 'black'

        Returns: list of legal moves
        """
        all_moves = []
        for start_square, piece in board.items():
                if piece[0] == player[0]:  # check if the piece belongs to the current player
                    piece_type = piece[1]
                    moves = get_moves_for_piece(board, start_square, piece_type, player)
                    all_moves.extend(moves)
        return all_moves

    def get_moves_for_piece(board, start_square, piece_type, player):
        """
        Given the piece and board, return all possible moves for that piece
        Args:
            board: a dictionary of the current board
            start_square: stating square
            piece_type: the type of the piece in the stating square
            player: could be 'white' or 'black'
        Returns: list of legal moves
        """
        moves = []
        if piece_type == 'P':
            moves = get_pawn_moves(board, start_square, player)
        elif piece_type == 'R':
            moves = get_rook_moves(board, start_square, player)
        elif piece_type == 'N':
            moves = get_knight_moves(board, start_square, player)
        elif piece_type == 'B':
            moves = get_bishop_moves(board, start_square, player)
        elif piece_type == 'Q':
            moves = get_queen_moves(board, start_square, player)
        elif piece_type == 'K':
            moves = get_king_moves(board, start_square, player)
        return moves

    def get_pawn_moves(board, start_square, player):
        """
        Given the pawn location and the board, return all possible moves for that pawn
        Pawns can be promoted
        """
        moves = []
        file = start_square[0]
        rank = int(start_square[1])
        direction = 1 if player == 'white' else -1
        
        # One square forward
        target_square = file + str(rank + direction)
        if target_square[1] in '12345678' and target_square not in board:
            if rank + direction == 8 or rank + direction == 1: # Promotion
                moves.append(start_square + target_square + 'q')
                moves.append(start_square + target_square + 'r')
                moves.append(start_square + target_square + 'b')
                moves.append(start_square + target_square + 'n')
            else:
                moves.append(start_square + target_square)

        # Two squares forward
        if rank == 2 and player == 'white' and file + '3' not in board and file + '4' not in board:
            target_square = file + '4'
            moves.append(start_square + target_square)
        if rank == 7 and player == 'black' and file + '6' not in board and file + '5' not in board:
            target_square = file + '5'
            moves.append(start_square + target_square)

        # Captures
        capture_files = [chr(ord(file) - 1), chr(ord(file) + 1)] # Adjacent files
        for capture_file in capture_files:
            target_square = capture_file + str(rank + direction)
            if target_square[0] in 'abcdefgh' and target_square in board and board[target_square][0] != player[0]:
                if rank + direction == 8 or rank + direction == 1: # Promotion
                    moves.append(start_square + target_square + 'q')
                    moves.append(start_square + target_square + 'r')
                    moves.append(start_square + target_square + 'b')
                    moves.append(start_square + target_square + 'n')
                else:
                    moves.append(start_square + target_square)
        return moves

    def get_rook_moves(board, start_square, player):
        """
        Given the rook location and the board, return all possible moves for that rook
        """
        moves = []
        file = start_square[0]
        rank = int(start_square[1])

        # Up
        for r in range(rank + 1, 9):
            target_square = file + str(r)
            if target_square in board:
                if board[target_square][0] != player[0]:
                    moves.append(start_square + target_square)
                break
            else:
                moves.append(start_square + target_square)

        # Down
        for r in range(rank - 1, 0, -1):
            target_square = file + str(r)
            if target_square in board:
                if board[target_square][0] != player[0]:
                    moves.append(start_square + target_square)
                break
            else:
                moves.append(start_square + target_square)

        # Right
        for f in range(ord(file) + 1, ord('h') + 1):
            target_square = chr(f) + str(rank)
            if target_square in board:
                if board[target_square][0] != player[0]:
                    moves.append(start_square + target_square)
                break
            else:
                moves.append(start_square + target_square)

        # Left
        for f in range(ord(file) - 1, ord('a') - 1, -1):
            target_square = chr(f) + str(rank)
            if target_square in board:
                if board[target_square][0] != player[0]:
                    moves.append(start_square + target_square)
                break
            else:
                moves.append(start_square + target_square)
        return moves

    def get_knight_moves(board, start_square, player):
        """
        Given the knight location and the board, return all possible moves for that knight
        """
        moves = []
        file = start_square[0]
        rank = int(start_square[1])
        possible_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        for file_offset, rank_offset in possible_moves:
            target_file = chr(ord(file) + file_offset)
            target_rank = rank + rank_offset
            target_square = target_file + str(target_rank)

            if target_file in 'abcdefgh' and target_rank in range(1, 9):
                if target_square not in board or board[target_square][0] != player[0]:
                    moves.append(start_square + target_square)
        return moves
    
    def get_bishop_moves(board, start_square, player):
        """
        Given the bishop location and the board, return all possible moves for that bishop
        """
        moves = []
        file = start_square[0]
        rank = int(start_square[1])

        # Up-Right
        for i in range(1, 8):
            target_file = chr(ord(file) + i)
            target_rank = rank + i
            target_square = target_file + str(target_rank)
            if target_file in 'abcdefgh' and target_rank in range(1, 9):
                if target_square in board:
                    if board[target_square][0] != player[0]:
                        moves.append(start_square + target_square)
                    break
                else:
                    moves.append(start_square + target_square)
            else:
                break

        # Up-Left
        for i in range(1, 8):
            target_file = chr(ord(file) - i)
            target_rank = rank + i
            target_square = target_file + str(target_rank)
            if target_file in 'abcdefgh' and target_rank in range(1, 9):
                if target_square in board:
                    if board[target_square][0] != player[0]:
                        moves.append(start_square + target_square)
                    break
                else:
                    moves.append(start_square + target_square)
            else:
                break

        # Down-Right
        for i in range(1, 8):
            target_file = chr(ord(file) + i)
            target_rank = rank - i
            target_square = target_file + str(target_rank)
            if target_file in 'abcdefgh' and target_rank in range(1, 9):
                if target_square in board:
                    if board[target_square][0] != player[0]:
                        moves.append(start_square + target_square)
                    break
                else:
                    moves.append(start_square + target_square)
            else:
                break

        # Down-Left
        for i in range(1, 8):
            target_file = chr(ord(file) - i)
            target_rank = rank - i
            target_square = target_file + str(target_rank)
            if target_file in 'abcdefgh' and target_rank in range(1, 9):
                if target_square in board:
                    if board[target_square][0] != player[0]:
                        moves.append(start_square + target_square)
                    break
                else:
                    moves.append(start_square + target_square)
            else:
                break
        return moves

    def get_queen_moves(board, start_square, player):
        """
        Given the queen location and the board, return all possible moves for that queen
        """
        moves = get_rook_moves(board, start_square, player) + get_bishop_moves(board, start_square, player)
        return moves

    def get_king_moves(board, start_square, player):
        """
        Given the king location and the board, return all possible moves for that king
        """
        moves = []
        file = start_square[0]
        rank = int(start_square[1])
        possible_moves = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        for file_offset, rank_offset in possible_moves:
            target_file = chr(ord(file) + file_offset)
            target_rank = rank + rank_offset
            target_square = target_file + str(target_rank)

            if target_file in 'abcdefgh' and target_rank in range(1, 9):
                if target_square not in board or board[target_square][0] != player[0]:
                    moves.append(start_square + target_square)
        
        # Castling (simplified - no check for being in check or passing through checks)
        if start_square == 'e1' and player == 'white':
            if 'h1' in board and board['h1'] == 'wR' and 'f1' not in board and 'g1' not in board:
                moves.append('e1g1')
            if 'a1' in board and board['a1'] == 'wR' and 'd1' not in board and 'c1' not in board and 'b1' not in board:
                moves.append('e1c1')
        if start_square == 'e8' and player == 'black':
            if 'h8' in board and board['h8'] == 'bR' and 'f8' not in board and 'g8' not in board:
                moves.append('e8g8')
            if 'a8' in board and board['a8'] == 'bR' and 'd8' not in board and 'c8' not in board and 'b8' not in board:
                moves.append('e8c8')
        return moves

    def evaluate_board(board: dict[str, str], player: str) -> float:
        """
        Simple evaluation function based on material balance and piece-square tables.
        """
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        score = 0
        for square, piece in board.items():
            color = piece[0]
            piece_type = piece[1]
            value = piece_values[piece_type]
            if color == player[0]:
                score += value
            else:
                score -= value
        return score

    def generate_candidate_moves(board, player):
      """
      Generate and filter candidate moves considering captures, checks and promotions.
      """
      legal_moves = get_legal_moves(board, player)
      candidate_moves = []
      
      for move in legal_moves:
        # Captures are always interesting.
        if len(move) == 4 and move[2:4] in board:
          candidate_moves.append(move)
        elif len(move) == 5: # Promotions
          candidate_moves.append(move)
              
      # Prefer captures
      if candidate_moves:
        return candidate_moves
      
      # No captures available, then proceed with all legal moves to be more aggressive
      return legal_moves

    legal_moves = generate_candidate_moves(pieces, to_play)

    if not legal_moves:
        return "", memory  # No legal moves, return an empty string as a safe default

    best_move = random.choice(legal_moves)
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move
        temp_board = pieces.copy()
        start_square = move[:2]
        end_square = move[2:4]

        # Handle promotion
        if len(move) == 5:
           promotion_piece = move[4].upper()
           temp_board[end_square] = to_play[0] + promotion_piece
           del temp_board[start_square]

        else:
          temp_board[end_square] = temp_board[start_square]
          del temp_board[start_square]

        # Evaluate the board after the move
        score = evaluate_board(temp_board, to_play)

        # Update the best move if the score is better
        if score > best_score:
            best_score = score
            best_move = move

    return best_move, memory
