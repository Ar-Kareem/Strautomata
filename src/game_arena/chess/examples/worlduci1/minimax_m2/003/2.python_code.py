
import copy

# Piece values for material evaluation
piece_values = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0
}

# Central and next-to-central squares for development bonuses
central_squares = ['d4', 'e4', 'd5', 'e5']
next_central = ['c3', 'd3', 'e3', 'f3', 'c5', 'd5', 'e5', 'f5', 'c6', 'd6', 'e6', 'f6']

def attacks(board, from_sq, to_sq, color):
    """Check if a piece at from_sq attacks to_sq on the given board."""
    piece = board.get(from_sq)
    if not piece or piece[0] != color:
        return False
    ptype = piece[1]
    
    # Convert squares to coordinates
    f1, r1 = from_sq[0], int(from_sq[1])
    f2, r2 = to_sq[0], int(to_sq[1])
    dr = r2 - r1
    dc = ord(f2) - ord(f1)
    
    if ptype == 'N':
        return (abs(dr), abs(dc)) in [(1, 2), (2, 1)]
    if ptype == 'K':
        return max(abs(dr), abs(dc)) == 1
    if ptype == 'P':
        if color == 'w':
            return dr == 1 and abs(dc) == 1
        else:  # Black pawn
            return dr == -1 and abs(dc) == 1
    
    # Sliding pieces (rook, bishop, queen)
    if ptype in ['R', 'B', 'Q']:
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        
        if ptype == 'R':
            if step_r != 0 and step_c != 0:
                return False
        if ptype == 'B':
            if step_r == 0 or step_c == 0 or abs(dr) != abs(dc):
                return False
        
        # Traverse squares in between
        current_r = r1 + step_r
        current_c = chr(ord(f1) + step_c)
        while (current_r, current_c) != (r2, f2):
            inter_sq = current_c + str(current_r)
            if inter_sq in board:
                return False
            current_r += step_r
            current_c = chr(ord(current_c) + step_c)
        return True
    
    return False

def is_attacked(board, target_sq, attacker_color):
    """Check if target_sq is attacked by any piece of attacker_color."""
    for sq, piece in board.items():
        if piece[0] == attacker_color:
            if attacks(board, sq, target_sq, attacker_color):
                return True
    return False

def simulate_move(pieces, move):
    """Simulate a move and return the new board state and captured piece."""
    new_board = copy.deepcopy(pieces)
    from_sq, to_sq = move[:2], move[2:4]
    promo = move[4:] if len(move) > 4 else None
    
    moving_piece = new_board.pop(from_sq)
    captured_piece = new_board.pop(to_sq, None)
    
    # Handle castling
    if from_sq == 'e1' and to_sq == 'g1':
        new_board.pop('h1', None)
        new_board['f1'] = 'wR'
    elif from_sq == 'e1' and to_sq == 'c1':
        new_board.pop('a1', None)
        new_board['d1'] = 'wR'
    elif from_sq == 'e8' and to_sq == 'g8':
        new_board.pop('h8', None)
        new_board['f8'] = 'bR'
    elif from_sq == 'e8' and to_sq == 'c8':
        new_board.pop('a8', None)
        new_board['d8'] = 'bR'
    
    # Handle promotion
    if promo:
        moving_piece = moving_piece[0] + promo
    
    new_board[to_sq] = moving_piece
    return new_board, captured_piece

def generate_moves_for_piece(board, from_sq, color):
    """Generate all possible moves for a piece at from_sq."""
    moves = []
    piece = board.get(from_sq)
    if not piece or piece[0] != color:
        return moves
    ptype = piece[1]
    
    if ptype == 'P':
        r = int(from_sq[1])
        f = from_sq[0]
        step = 1 if color == 'w' else -1
        
        # Forward move
        to_sq = f + str(r + step)
        if to_sq not in board:
            if (r + step == 8 and color == 'w') or (r + step == 1 and color == 'b'):
                # Promotion
                for promo in ['q', 'r', 'b', 'n']:
                    moves.append(from_sq + to_sq + promo)
            else:
                moves.append(from_sq + to_sq)
        
        # Double move
        if (color == 'w' and r == 2) or (color == 'b' and r == 7):
            to_sq2 = f + str(r + 2 * step)
            if to_sq2 not in board and to_sq not in board:
                moves.append(from_sq + to_sq2)
        
        # Captures
        for df in [-1, 1]:
            to_sq_cap = chr(ord(f) + df) + str(r + step)
            if to_sq_cap in board and board[to_sq_cap][0] != color:
                moves.append(from_sq + to_sq_cap)
    
    elif ptype == 'N':
        r = int(from_sq[1])
        f = from_sq[0]
        steps = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
        for dr, dc in steps:
            try:
                to_sq = chr(ord(f) + dc) + str(r + dr)
                if not (0 < r + dr < 9) or not (96 < ord(chr(ord(f) + dc)) < 105):
                    continue
            except:
                continue
            if to_sq not in board or board[to_sq][0] != color:
                moves.append(from_sq + to_sq)
    
    elif ptype in ['B', 'R', 'Q']:
        r = int(from_sq[1])
        f = from_sq[0]
        if ptype in ['B', 'Q']:
            dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        if ptype in ['R', 'Q']:
            dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        for step_r, step_c in dirs:
            for i in range(1, 8):
                to_sq = chr(ord(f) + i * step_c) + str(r + i * step_r)
                try:
                    if not (0 < r + i * step_r < 9) or not (96 < ord(chr(ord(f) + i * step_c)) < 105):
                        break
                except:
                    break
                if to_sq in board:
                    if board[to_sq][0] != color:
                        moves.append(from_sq + to_sq)
                    break
                else:
                    moves.append(from_sq + to_sq)
    
    elif ptype == 'K':
        r = int(from_sq[1])
        f = from_sq[0]
        for step_r, step_c in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            to_sq = chr(ord(f) + step_c) + str(r + step_r)
            if not (0 < r + step_r < 9) or not (96 < ord(chr(ord(f) + step_c)) < 105):
                continue
            if to_sq not in board or board[to_sq][0] != color:
                moves.append(from_sq + to_sq)
        
        # Castling
        if color == 'w' and from_sq == 'e1':
            # King side
            if 'f1' not in board and 'g1' not in board:
                if board.get('h1') == 'wR':
                    if not is_attacked(board, 'e1', 'b') and not is_attacked(board, 'f1', 'b') and not is_attacked(board, 'g1', 'b'):
                        moves.append('e1g1')
            # Queen side
            if 'd1' not in board and 'c1' not in board and 'b1' not in board:
                if board.get('a1') == 'wR':
                    if not is_attacked(board, 'e1', 'b') and not is_attacked(board, 'd1', 'b') and not is_attacked(board, 'c1', 'b'):
                        moves.append('e1c1')
        elif color == 'b' and from_sq == 'e8':
            if 'f8' not in board and 'g8' not in board:
                if board.get('h8') == 'bR':
                    if not is_attacked(board, 'e8', 'w') and not is_attacked(board, 'f8', 'w') and not is_attacked(board, 'g8', 'w'):
                        moves.append('e8g8')
            if 'd8' not in board and 'c8' not in board and 'b8' not in board:
                if board.get('a8') == 'bR':
                    if not is_attacked(board, 'e8', 'w') and not is_attacked(board, 'd8', 'w') and not is_attacked(board, 'c8', 'w'):
                        moves.append('e8c8')
    
    return moves

def generate_legal_moves(pieces, to_play):
    """Generate all legal moves for the current player."""
    color = to_play[0]
    legal_moves = []
    
    for from_sq in list(pieces.keys()):
        candidate_moves = generate_moves_for_piece(pieces, from_sq, color)
        for move in candidate_moves:
            # Simulate move and check if king is safe
            new_board = simulate_move(pieces, move)[0]
            king_piece = color + 'K'
            king_sq = None
            for sq, p in new_board.items():
                if p == king_piece:
                    king_sq = sq
                    break
            if king_sq is None:
                continue
            opponent_color = 'b' if color == 'w' else 'w'
            if not is_attacked(new_board, king_sq, opponent_color):
                legal_moves.append(move)
    
    return legal_moves

def score_move(pieces, move, to_play):
    """Score a move based on material, king safety, and development."""
    score = 0
    new_board, captured_piece = simulate_move(pieces, move)
    
    # Material value
    if captured_piece is not None:
        score += piece_values[captured_piece[1]]
    
    # Promotion
    promo = move[4:] if len(move) > 4 else None
    if promo:
        score += piece_values[promo]
    
    # Castling bonus
    from_sq, to_sq = move[:2], move[2:4]
    if (from_sq == 'e1' and to_sq in ['g1', 'c1']) or (from_sq == 'e8' and to_sq in ['g8', 'c8']):
        score += 2.0
    
    # Check bonus: if opponent's king is under attack
    opponent_color = 'b' if to_play == 'white' else 'w'
    opponent_king_piece = opponent_color + 'K'
    opponent_king_sq = None
    for sq, p in new_board.items():
        if p == opponent_king_piece:
            opponent_king_sq = sq
            break
    if opponent_king_sq and is_attacked(new_board, opponent_king_sq, to_play[0]):
        score += 1.0
    
    # Penalty for moving the king
    from_sq = move[:2]
    moving_piece = pieces[from_sq]
    if moving_piece[1] == 'K':
        score -= 0.5
    
    # Development bonus for central squares
    if to_sq in central_squares:
        score += 0.3
    elif to_sq in next_central:
        score += 0.2
    
    # Penalty for leaving our king in check
    our_color = to_play[0]
    our_king_piece = our_color + 'K'
    our_king_sq = None
    for sq, p in new_board.items():
        if p == our_king_piece:
            our_king_sq = sq
            break
    if our_king_sq:
        opponent_color = 'b' if our_color == 'w' else 'w'
        if is_attacked(new_board, our_king_sq, opponent_color):
            score -= 5.0  # Large penalty for leaving king in check
    
    return score

def policy(pieces: dict[str, str], to_play: str) -> str:
    """Select the best legal move based on scoring."""
    legal_moves = generate_legal_moves(pieces, to_play)
    if not legal_moves:
        # No legal moves (shouldn't happen in a legal game)
        return ""
    
    best_move = ""
    best_score = float('-inf')
    
    for move in legal_moves:
        score = score_move(pieces, move, to_play)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
