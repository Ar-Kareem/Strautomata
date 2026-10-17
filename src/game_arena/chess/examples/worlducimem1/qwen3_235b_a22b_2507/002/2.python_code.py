
import numpy as np
from copy import deepcopy

def parse_square(sq):
    """Convert algebraic notation to (row, col): a1 -> (7,0), h8 -> (0,7)"""
    file = ord(sq[0]) - ord('a')
    rank = 8 - int(sq[1])
    return rank, file

def square_to_str(pos):
    """Convert (row, col) to algebraic: (7,0) -> 'a1'"""
    file = chr(ord('a') + pos[1])
    rank = str(8 - pos[0])
    return file + rank

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def is_opponent(piece, color):
    if not piece:
        return False
    pc_color = 'w' if piece[0] == 'w' else 'b'
    return pc_color != color

def is_friendly(piece, color):
    if not piece:
        return False
    pc_color = 'w' if piece[0] == 'w' else 'b'
    return pc_color == color

def get_piece_value(piece):
    if not piece:
        return 0
    pt = piece[1]
    values = {'P': 100, 'N': 300, 'B': 300, 'R': 500, 'Q': 900, 'K': 10000}
    return values.get(pt, 0)

def board_from_pieces(pieces):
    """Create 8x8 board from pieces dict. None for empty squares."""
    board = np.full((8,8), None, dtype=object)
    for sq, pc in pieces.items():
        r, f = parse_square(sq)
        board[r, f] = pc
    return board

def pieces_from_board(board):
    """Convert board back to pieces dict"""
    pieces = {}
    for r in range(8):
        for f in range(8):
            if board[r,f] is not None:
                sq = square_to_str((r,f))
                pieces[sq] = board[r,f]
    return pieces

def get_king_square(board, color):
    king_code = color + 'K'
    for r in range(8):
        for c in range(8):
            if board[r,c] == king_code:
                return (r,c)
    return None

def is_in_check(board, color):
    """Check if the given color's king is under attack"""
    king_sq = get_king_square(board, color)
    if not king_sq:
        return False
    opp_color = 'b' if color == 'w' else 'w'
    # Check if any opponent piece attacks the king
    for r in range(8):
        for c in range(8):
            piece = board[r,c]
            if piece and piece[0] == opp_color:
                attacks = get_attacked_squares(board, r, c)
                if king_sq in attacks:
                    return True
    return False

def get_pawn_moves(board, r, c, color):
    moves = []
    direction = -1 if color == 'w' else 1
    start_row = 6 if color == 'w' else 1

    # Forward move
    if in_bounds(r+direction, c) and board[r+direction, c] is None:
        moves.append((r+direction, c))
        # Double move from start
        if r == start_row and board[r+2*direction, c] is None:
            moves.append((r+2*direction, c))

    # Captures
    for dc in [-1,1]:
        nr, nc = r+direction, c+dc
        if in_bounds(nr, nc):
            if board[nr, nc] is not None and is_opponent(board[nr, nc], color):
                moves.append((nr, nc))
    return moves

def get_knight_moves(board, r, c):
    moves = []
    offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
    for dr, dc in offsets:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc):
            if board[nr, nc] is None or is_opponent(board[nr, nc], board[r,c][0]):
                moves.append((nr, nc))
    return moves

def get_bishop_moves(board, r, c, color):
    moves = []
    directions = [(-1,-1),(-1,1),(1,-1),(1,1)]
    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            if board[nr, nc] is None:
                moves.append((nr, nc))
            else:
                if is_opponent(board[nr, nc], color):
                    moves.append((nr, nc))
                break
            nr, nc = nr+dr, nc+dc
    return moves

def get_rook_moves(board, r, c, color):
    moves = []
    directions = [(-1,0),(1,0),(0,-1),(0,1)]
    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            if board[nr, nc] is None:
                moves.append((nr, nc))
            else:
                if is_opponent(board[nr, nc], color):
                    moves.append((nr, nc))
                break
            nr, nc = nr+dr, nc+dc
    return moves

def get_queen_moves(board, r, c, color):
    return get_bishop_moves(board, r, c, color) + get_rook_moves(board, r, c, color)

def get_king_moves(board, r, c, color):
    moves = []
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc):
                if board[nr, nc] is None or is_opponent(board[nr, nc], color):
                    moves.append((nr, nc))
    # Castling not considered here for simplicity in attack calc
    return moves

def get_attacked_squares(board, r, c):
    """Get all squares attacked by piece at (r,c) regardless of color"""
    piece = board[r,c]
    if not piece:
        return []
    color = piece[0]
    pt = piece[1]
    if pt == 'P':
        direction = -1 if color == 'w' else 1
        attacks = [(r+direction, c-1), (r+direction, c+1)]
        return [(nr, nc) for nr, nc in attacks if in_bounds(nr, nc)]
    elif pt == 'N':
        return get_knight_moves(board, r, c)
    elif pt == 'B':
        return get_bishop_moves(board, r, c, color)
    elif pt == 'R':
        return get_rook_moves(board, r, c, color)
    elif pt == 'Q':
        return get_queen_moves(board, r, c, color)
    elif pt == 'K':
        return get_king_moves(board, r, c, color)
    return []

def is_square_attacked(board, r, c, by_color):
    """Check if square (r,c) is attacked by any piece of by_color"""
    for i in range(8):
        for j in range(8):
            piece = board[i,j]
            if piece and piece[0] == by_color:
                attacks = get_attacked_squares(board, i, j)
                if (r,c) in attacks:
                    return True
    return False

def generate_moves(board, color):
    """Generate all pseudo-legal moves for color as UCI strings"""
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r,c]
            if piece and piece[0] == color:
                pt = piece[1]
                if pt == 'P':
                    piece_moves = get_pawn_moves(board, r, c, color)
                    start_sq = square_to_str((r,c))
                    for nr, nc in piece_moves:
                        end_sq = square_to_str((nr,nc))
                        move = start_sq + end_sq
                        # Promotion
                        if (color == 'w' and nr == 0) or (color == 'b' and nr == 7):
                            for promo in ['q','r','b','n']:
                                moves.append(move + promo)
                        else:
                            moves.append(move)
                elif pt == 'N':
                    piece_moves = get_knight_moves(board, r, c)
                    start_sq = square_to_str((r,c))
                    for nr, nc in piece_moves:
                        if board[nr,nc] is None or is_opponent(board[nr,nc], color):
                            end_sq = square_to_str((nr,nc))
                            moves.append(start_sq + end_sq)
                elif pt == 'B':
                    piece_moves = get_bishop_moves(board, r, c, color)
                    start_sq = square_to_str((r,c))
                    for nr, nc in piece_moves:
                        if board[nr,nc] is None or is_opponent(board[nr,nc], color):
                            end_sq = square_to_str((nr,nc))
                            moves.append(start_sq + end_sq)
                elif pt == 'R':
                    piece_moves = get_rook_moves(board, r, c, color)
                    start_sq = square_to_str((r,c))
                    for nr, nc in piece_moves:
                        if board[nr,nc] is None or is_opponent(board[nr,nc], color):
                            end_sq = square_to_str((nr,nc))
                            moves.append(start_sq + end_sq)
                elif pt == 'Q':
                    piece_moves = get_queen_moves(board, r, c, color)
                    start_sq = square_to_str((r,c))
                    for nr, nc in piece_moves:
                        if board[nr,nc] is None or is_opponent(board[nr,nc], color):
                            end_sq = square_to_str((nr,nc))
                            moves.append(start_sq + end_sq)
                elif pt == 'K':
                    piece_moves = get_king_moves(board, r, c, color)
                    start_sq = square_to_str((r,c))
                    for nr, nc in piece_moves:
                        if board[nr,nc] is None or is_opponent(board[nr,nc], color):
                            end_sq = square_to_str((nr,nc))
                            moves.append(start_sq + end_sq)
    return moves

def apply_move(board, move):
    """Apply a UCI move to board and return new board. Does not handle castling/enpassant fully."""
    fr = parse_square(move[0:2])
    to = parse_square(move[2:4])
    new_board = deepcopy(board)
    piece = new_board[fr[0], fr[1]]
    promo = None
    if len(move) == 5:
        promo = move[4]
    # Simple: just move piece
    new_board[to[0], to[1]] = piece
    new_board[fr[0], fr[1]] = None
    # Promotion
    if promo and piece[1] == 'P':
        color = piece[0]
        new_board[to[0], to[1]] = color + promo.upper()
    return new_board

def is_checkmate(board, color, legal_moves):
    """Check if current player is in checkmate"""
    if not is_in_check(board, color):
        return False
    # If there are legal moves, not checkmate
    if len(legal_moves) > 0:
        # But verify these moves actually escape check
        for move in legal_moves:
            new_board = apply_move(board, move)
            if not is_in_check(new_board, color):
                return False
        return True
    return True  # no moves and in check

def evaluate_move(board, move, color, legal_moves):
    """Heuristic evaluation of a move"""
    score = 0
    fr = parse_square(move[0:2])
    to = parse_square(move[2:4])
    piece = board[fr[0], fr[1]]
    target = board[to[0], to[1]]

    # 1. Promotion: very strong
    if len(move) == 5:
        promo = move[4]
        if promo == 'q':
            score += 900
        elif promo == 'r':
            score += 500
        elif promo == 'b' or promo == 'n':
            score += 300

    # 2. Capture
    if target is not None:
        score += get_piece_value(target) * 2  # Bonus for capturing

    # 3. Checkmate detection
    new_board = apply_move(board, move)
    opp_color = 'b' if color == 'w' else 'w'
    # Simulate if this move leads to checkmate
    if is_in_check(new_board, opp_color):
        # Generate opponent moves to see if they have any legal escape
        opp_moves = generate_moves(new_board, opp_color)
        if is_checkmate(new_board, opp_color, opp_moves):
            score += 100000  # Highest priority

    # 4. Prevent hanging high-value pieces from being captured next
    # (simplified: avoid moves that leave queen hanging)
    new_opp_moves = generate_moves(new_board, opp_color)  # Opponent's response
    king_after = get_king_square(new_board, color)
    if king_after and is_square_attacked(new_board, king_after[0], king_after[1], opp_color):
        score -= 200  # Penalty for leaving king exposed

    # 5. Penalty for moving king early without reason (simplified)
    if piece[1] == 'K' and (color == 'w' and move == 'e1g1' or move == 'e1c1') or \
                     (color == 'b' and move == 'e8g8' or move == 'e8c8'):
        # Castling is good
        score += 100
    elif piece[1] == 'K':
        score -= 50  # Just moving king without castling is risky early

    # 6. Pawn advance in center gets slight bonus
    if piece[1] == 'P':
        f = to[1]
        if f in [3,4]:
            score += 10

    return score

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Convert color
    color = 'w' if to_play == 'white' else 'b'
    board = board_from_pieces(pieces)

    # Get legal moves
    legal_moves = memory.get('legal_moves', [])
    if not legal_moves:
        # Fallback: generate all moves
        legal_moves = generate_moves(board, color)

    if not legal_moves:
        # No moves — return first from input? Shouldn't happen.
        return 'e2e4', memory  # Fallback

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(board, move, color, legal_moves)
        if score > best_score:
            best_score = score
            best_move = move

    # Ensure we return a legal move
    if best_move not in legal_moves:
        best_move = legal_moves[0]

    return best_move, memory
