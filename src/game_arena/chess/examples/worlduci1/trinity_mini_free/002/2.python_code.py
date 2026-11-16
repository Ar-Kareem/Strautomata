
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Convert pieces dictionary to a 2D board representation
    board = np.full((8, 8), '.', dtype=str)
    for square, piece in pieces.items():
        row = 8 - int(square[1])
        col = ord(square[0]) - ord('a')
        board[row, col] = piece
    
    # Generate all legal moves for the current player
    legal_moves = generate_legal_moves(board, to_play)
    
    # Evaluate each move and select the best
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    
    for move in legal_moves:
        # Simulate the move
        new_board = simulate_move(board, move, to_play)
        # Evaluate the resulting position
        score = evaluate_position(new_board, to_play)
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(board, color):
    moves = []
    for row in range(8):
        for col in range(8):
            piece = board[row, col]
            if piece == '.' or piece[0] != color:
                continue
            piece_type = piece[1]
            if piece_type == 'P':
                moves.extend(generate_pawn_moves(board, row, col, color))
            elif piece_type == 'N':
                moves.extend(generate_knight_moves(board, row, col, color))
            elif piece_type == 'B':
                moves.extend(generate_bishop_moves(board, row, col, color))
            elif piece_type == 'R':
                moves.extend(generate_rook_moves(board, row, col, color))
            elif piece_type == 'Q':
                moves.extend(generate_queen_moves(board, row, col, color))
            elif piece_type == 'K':
                moves.extend(generate_king_moves(board, row, col, color))
    return moves

def generate_pawn_moves(board, row, col, color):
    moves = []
    direction = 1 if color == 'w' else -1
    start_row = 6 if color == 'w' else 1
    # Single forward move
    new_row = row + direction
    if board[new_row, col] == '.':
        moves.append(f"{chr(col + ord('a'))}{8 - new_row}{chr(col + ord('a'))}{8 - row}")
        # Double move for starting position
        if row == start_row and board[new_row + direction, col] == '.':
            moves.append(f"{chr(col + ord('a'))}{8 - (new_row + direction)}{chr(col + ord('a'))}{8 - row}")
    # Captures
    for offset in [-1, 1]:
        new_row = row + direction
        new_col = col + offset
        if 0 <= new_col < 8 and board[new_row, new_col] != '.' and board[new_row, new_col][0] != color:
            moves.append(f"{chr(col + ord('a'))}{8 - new_row}{chr(new_col + ord('a'))}{8 - row}")
    return moves

def generate_knight_moves(board, row, col, color):
    moves = []
    knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in knight_moves:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row, new_col] == '.' or board[new_row, new_col][0] != color:
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
    return moves

def generate_bishop_moves(board, row, col, color):
    moves = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in directions:
        for step in range(1, 8):
            new_row = row + dr * step
            new_col = col + dc * step
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break
            if board[new_row, new_col] == '.':
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
            elif board[new_row, new_col][0] != color:
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                break
    return moves

def generate_rook_moves(board, row, col, color):
    moves = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        for step in range(1, 8):
            new_row = row + dr * step
            new_col = col + dc * step
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break
            if board[new_row, new_col] == '.':
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
            elif board[new_row, new_col][0] != color:
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                break
    return moves

def generate_queen_moves(board, row, col, color):
    moves = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        for step in range(1, 8):
            new_row = row + dr * step
            new_col = col + dc * step
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break
            if board[new_row, new_col] == '.':
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
            elif board[new_row, new_col][0] != color:
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                break
    return moves

def generate_king_moves(board, row, col, color):
    moves = []
    king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in king_moves:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row, new_col] == '.' or board[new_row, new_col][0] != color:
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
    return moves

def simulate_move(board, move, color):
    # Parse move string
    start_col = ord(move[0]) - ord('a')
    start_row = 8 - int(move[1])
    end_col = ord(move[2]) - ord('a')
    end_row = 8 - int(move[3])
    # Update board
    piece = board[start_row, start_col]
    board[end_row, end_col] = piece
    board[start_row, start_col] = '.'
    return board

def evaluate_position(board, color):
    # Material evaluation
    material = 0
    for row in range(8):
        for col in range(8):
            piece = board[row, col]
            if piece == '.':
                continue
            piece_val = 1 if piece[1] == 'P' else 3 if piece[1] == 'N' or piece[1] == 'B' else 5 if piece[1] == 'R' else 9
            if piece[0] != color:
                material -= piece_val
            else:
                material += piece_val
    
    # King safety evaluation
    king_row, king_col = find_king(board, color)
    king_safety = 0
    # Check for checks
    if is_in_check(board, king_row, king_col, color):
        king_safety -= 10
    
    # Pawn structure evaluation
    pawn_structure = evaluate_pawn_structure(board, color)
    
    return material + king_safety + pawn_structure

def find_king(board, color):
    for row in range(8):
        for col in range(8):
            if board[row, col] == f"{color}K":
                return row, col
    return -1, -1

def is_in_check(board, row, col, color):
    # Check horizontal/vertical threats
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        for step in range(1, 8):
            new_row = row + dr * step
            new_col = col + dc * step
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break
            if board[new_row, new_col] == '.':
                continue
            if board[new_row, new_col][0] != color and (board[new_row, new_col][1] == 'R' or board[new_row, new_col][1] == 'Q'):
                return True
            break
    
    # Check diagonal threats
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        for step in range(1, 8):
            new_row = row + dr * step
            new_col = col + dc * step
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                break
            if board[new_row, new_col] == '.':
                continue
            if board[new_row, new_col][0] != color and (board[new_row, new_col][1] == 'B' or board[new_row, new_col][1] == 'Q'):
                return True
            break
    
    # Check knight threats
    knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in knight_moves:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board[new_row, new_col] == f"{color}N":
                return True
    
    return False

def evaluate_pawn_structure(board, color):
    # Evaluate pawn structure for positional advantage
    structure_score = 0
    # Central pawn control
    for row in range(8):
        for col in range(8):
            if board[row, col] == f"{color}P":
                if 3 <= col <= 4:
                    structure_score += 1
    return structure_score
