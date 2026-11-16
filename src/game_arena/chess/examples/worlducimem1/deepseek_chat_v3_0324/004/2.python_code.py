
import numpy as np

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Initialize or update memory
    if not memory:
        memory = {
            'previous_move': None,
            'seen_positions': set()
        }
    
    # Convert pieces to a board representation
    board = [[None for _ in range(8)] for _ in range(8)]
    for square, piece in pieces.items():
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        board[7 - rank][file] = piece  # Convert to 0-7 indices with rank 0 at bottom
    
    # Determine color prefix
    color_prefix = 'w' if to_play == 'white' else 'b'
    opponent_prefix = 'b' if color_prefix == 'w' else 'w'
    
    # Generate all possible moves
    legal_moves = generate_legal_moves(board, color_prefix)
    
    # If only one move, just return it
    if len(legal_moves) == 1:
        return (legal_moves[0], memory)
    
    # Evaluate all moves with a simple lookahead
    best_move = None
    best_score = -np.inf
    
    for move in legal_moves:
        # Make the move on a copy of the board
        new_board = [row.copy() for row in board]
        make_move(new_board, move, color_prefix)
        
        # Check for immediate checkmate
        if is_checkmate(new_board, opponent_prefix):
            return (move, memory)
        
        # Evaluate the position
        score = evaluate_position(new_board, color_prefix)
        
        # Look one move ahead for opponent's best response (minimax)
        opponent_moves = generate_legal_moves(new_board, opponent_prefix)
        if opponent_moves:
            opponent_best = None
            opponent_worst_score = np.inf
            
            for opponent_move in opponent_moves:
                opponent_board = [row.copy() for row in new_board]
                make_move(opponent_board, opponent_move, opponent_prefix)
                
                opp_score = evaluate_position(opponent_board, color_prefix)
                if opp_score < opponent_worst_score:
                    opponent_worst_score = opp_score
            
            score += opponent_worst_score * 0.5  # Discount opponent's best response
        
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Random tie-breaker to avoid being predictable
            if np.random.random() < 0.5:
                best_move = move
    
    # Store the move in memory
    memory['previous_move'] = best_move
    
    return (best_move, memory)

def generate_legal_moves(board, color_prefix):
    moves = []
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if piece and piece[0] == color_prefix:
                # Add moves for each piece type
                piece_type = piece[1]
                if piece_type == 'P':
                    moves.extend(generate_pawn_moves(board, rank, file, color_prefix))
                elif piece_type == 'N':
                    moves.extend(generate_knight_moves(board, rank, file, color_prefix))
                elif piece_type == 'B':
                    moves.extend(generate_bishop_moves(board, rank, file, color_prefix))
                elif piece_type == 'R':
                    moves.extend(generate_rook_moves(board, rank, file, color_prefix))
                elif piece_type == 'Q':
                    moves.extend(generate_queen_moves(board, rank, file, color_prefix))
                elif piece_type == 'K':
                    moves.extend(generate_king_moves(board, rank, file, color_prefix))
    return moves

def generate_pawn_moves(board, rank, file, color_prefix):
    moves = []
    direction = -1 if color_prefix == 'w' else 1  # White pawns move up (lower ranks)
    start_rank = 6 if color_prefix == 'w' else 1
    
    # Forward move
    if 0 <= rank + direction < 8 and not board[rank + direction][file]:
        # Check for promotion
        if (rank + direction == 0 and color_prefix == 'b') or (rank + direction == 7 and color_prefix == 'w'):
            for promo in 'qrbn':
                moves.append(format_move(rank, file, rank + direction, file, promo))
        else:
            moves.append(format_move(rank, file, rank + direction, file))
            # Double move from starting position
            if rank == start_rank and not board[rank + 2*direction][file]:
                moves.append(format_move(rank, file, rank + 2*direction, file))
    
    # Capture diagonally
    for dx in [-1, 1]:
        if 0 <= file + dx < 8 and 0 <= rank + direction < 8:
            target = board[rank + direction][file + dx]
            if target and target[0] != color_prefix:
                # Check for promotion
                if (rank + direction == 0 and color_prefix == 'b') or (rank + direction == 7 and color_prefix == 'w'):
                    for promo in 'qrbn':
                        moves.append(format_move(rank, file, rank + direction, file + dx, promo))
                else:
                    moves.append(format_move(rank, file, rank + direction, file + dx))
    
    # TODO: Add en passant
    
    return moves

def generate_knight_moves(board, rank, file, color_prefix):
    moves = []
    knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                    (1, -2), (1, 2), (2, -1), (2, 1)]
    
    for dr, df in knight_moves:
        new_rank, new_file = rank + dr, file + df
        if 0 <= new_rank < 8 and 0 <= new_file < 8:
            target = board[new_rank][new_file]
            if not target or target[0] != color_prefix:
                moves.append(format_move(rank, file, new_rank, new_file))
    
    return moves

def generate_bishop_moves(board, rank, file, color_prefix):
    return generate_sliding_moves(board, rank, file, color_prefix, [(-1, -1), (-1, 1), (1, -1), (1, 1)])

def generate_rook_moves(board, rank, file, color_prefix):
    return generate_sliding_moves(board, rank, file, color_prefix, [(-1, 0), (1, 0), (0, -1), (0, 1)])

def generate_queen_moves(board, rank, file, color_prefix):
    return generate_sliding_moves(board, rank, file, color_prefix, 
                                 [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)])

def generate_king_moves(board, rank, file, color_prefix):
    moves = []
    king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), 
                  (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for dr, df in king_moves:
        new_rank, new_file = rank + dr, file + df
        if 0 <= new_rank < 8 and 0 <= new_file < 8:
            target = board[new_rank][new_file]
            if not target or target[0] != color_prefix:
                moves.append(format_move(rank, file, new_rank, new_file))
    
    # TODO: Add castling
    return moves

def generate_sliding_moves(board, rank, file, color_prefix, directions):
    moves = []
    for dr, df in directions:
        r, f = rank + dr, file + df
        while 0 <= r < 8 and 0 <= f < 8:
            target = board[r][f]
            if not target:
                moves.append(format_move(rank, file, r, f))
                r += dr
                f += df
            else:
                if target[0] != color_prefix:
                    moves.append(format_move(rank, file, r, f))
                break
    return moves

def format_move(rank, file, new_rank, new_file, promo=None):
    # Convert back to algebraic notation
    move = chr(file + ord('a')) + str(8 - rank) + chr(new_file + ord('a')) + str(8 - new_rank)
    if promo is not None:
        move += promo
    return move

def make_move(board, move, color_prefix):
    # Parse UCI move
    start_file = ord(move[0]) - ord('a')
    start_rank = 8 - int(move[1])
    end_file = ord(move[2]) - ord('a')
    end_rank = 8 - int(move[3])
    promo = move[4] if len(move) == 5 else None
    
    piece = board[start_rank][start_file]
    board[start_rank][start_file] = None
    
    if promo:
        piece = color_prefix + promo.upper()
    
    board[end_rank][end_file] = piece

def is_checkmate(board, color_prefix):
    # Check if the opponent has no legal moves and is in check
    opponent_moves = generate_legal_moves(board, color_prefix)
    if not opponent_moves:
        return is_king_in_check(board, color_prefix)
    return False

def is_king_in_check(board, color_prefix):
    # Find the king
    king_pos = None
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if piece == color_prefix + 'K':
                king_pos = (rank, file)
                break
        if king_pos:
            break
    
    if not king_pos:
        return False
    
    # Check if any opponent piece can attack the king
    opponent_prefix = 'b' if color_prefix == 'w' else 'w'
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if piece and piece[0] == opponent_prefix:
                if is_square_attacked_by(board, rank, file, king_pos[0], king_pos[1]):
                    return True
    return False

def is_square_attacked_by(board, piece_rank, piece_file, target_rank, target_file):
    piece = board[piece_rank][piece_file]
    piece_type = piece[1]
    
    dr = target_rank - piece_rank
    df = target_file - piece_file
    
    if piece_type == 'P':
        direction = -1 if piece[0] == 'w' else 1
        return abs(df) == 1 and (target_rank - piece_rank) == direction
    
    elif piece_type == 'N':
        return (abs(dr) == 2 and abs(df) == 1) or (abs(dr) == 1 and abs(df) == 2)
    
    elif piece_type == 'B':
        if abs(dr) != abs(df):
            return False
        step_r = 1 if dr > 0 else -1
        step_f = 1 if df > 0 else -1
        r, f = piece_rank + step_r, piece_file + step_f
        while r != target_rank and f != target_file:
            if board[r][f]:
                return False
            r += step_r
            f += step_f
        return True
    
    elif piece_type == 'R':
        if dr != 0 and df != 0:
            return False
        step_r = 1 if dr > 0 else (-1 if dr < 0 else 0)
        step_f = 1 if df > 0 else (-1 if df < 0 else 0)
        r, f = piece_rank + step_r, piece_file + step_f
        while r != target_rank or f != target_file:
            if board[r][f]:
                return False
            r += step_r
            f += step_f
        return True
    
    elif piece_type == 'Q':
        if abs(dr) == abs(df) or dr == 0 or df == 0:
            step_r = 1 if dr > 0 else (-1 if dr < 0 else 0)
            step_f = 1 if df > 0 else (-1 if df < 0 else 0)
            r, f = piece_rank + step_r, piece_file + step_f
            while r != target_rank or f != target_file:
                if board[r][f]:
                    return False
                r += step_r
                f += step_f
            return True
        return False
    
    elif piece_type == 'K':
        return abs(dr) <= 1 and abs(df) <= 1
    
    return False

def evaluate_position(board, color_prefix):
    opponent_prefix = 'b' if color_prefix == 'w' else 'w'
    
    material = 0
    position = 0
    
    # Piece values
    piece_values = {
        'P': 100, 'N': 320, 'B': 330, 
        'R': 500, 'Q': 900, 'K': 20000
    }
    
    # Piece-square tables for positional evaluation
    pawn_table = [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    knight_table = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    # Evaluate material and positional scores
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if piece:
                pos_index = rank * 8 + file
                if piece[0] == color_prefix:
                    material += piece_values[piece[1]]
                    if piece[1] == 'P':
                        position += pawn_table[pos_index] if color_prefix == 'w' else pawn_table[63 - pos_index]
                    elif piece[1] == 'N':
                        position += knight_table[pos_index] if color_prefix == 'w' else knight_table[63 - pos_index]
                    # TODO: Add more piece tables
                else:
                    material -= piece_values[piece[1]]
                    if piece[1] == 'P':
                        position -= pawn_table[pos_index] if opponent_prefix == 'w' else pawn_table[63 - pos_index]
                    elif piece[1] == 'N':
                        position -= knight_table[pos_index] if opponent_prefix == 'w' else knight_table[63 - pos_index]
                    # TODO: Add more piece tables
    
    # King safety
    king_pos = find_king(board, color_prefix)
    if king_pos:
        king_safety = 0
        # Encourage castling by checking if king is on starting position
        if color_prefix == 'w' and king_pos == (7, 4):
            king_safety -= 20
        elif color_prefix == 'b' and king_pos == (0, 4):
            king_safety -= 20
        position += king_safety
    
    return material + position * 0.1

def find_king(board, color_prefix):
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if piece == color_prefix + 'K':
                return (rank, file)
    return None
