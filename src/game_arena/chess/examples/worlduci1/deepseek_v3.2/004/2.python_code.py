
import math
from typing import List, Tuple, Dict

piece_value = {
    'P': 1.0,
    'N': 3.0,
    'B': 3.25,
    'R': 5.0,
    'Q': 9.0,
    'K': 0.0
}

def policy(pieces: Dict[str, str], to_play: str) -> str:
    # Determine my color code
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Convert pieces dict to board representation (8x8, None for empty)
    board = [[None for _ in range(8)] for _ in range(8)]
    for sq, code in pieces.items():
        file_idx = ord(sq[0]) - ord('a')
        rank_idx = int(sq[1]) - 1
        board[rank_idx][file_idx] = code
    
    # Generate legal moves for current player
    legal_moves = generate_legal_moves(board, my_color, opp_color)
    
    # If only one move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Check for immediate checkmate
    for move in legal_moves:
        new_board = make_move(board, move, my_color)
        # Generate opponent's legal moves after this move
        opp_moves = generate_legal_moves(new_board, opp_color, my_color)
        # If opponent has no legal moves, check if king is in check
        if len(opp_moves) == 0:
            # See if opponent king is in check
            if is_king_in_check(new_board, opp_color, my_color):
                return move  # Checkmate!
    
    # Use minimax with alpha-beta, depth 3
    best_move = None
    best_eval = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    # Sort moves: captures first, then checks, then others
    legal_moves = sorted(legal_moves, key=lambda m: move_sort_key(m, board, my_color, opp_color), reverse=True)
    
    for move in legal_moves:
        new_board = make_move(board, move, my_color)
        eval = minimax(new_board, 3, False, alpha, beta, my_color, opp_color)
        if eval > best_eval:
            best_eval = eval
            best_move = move
        alpha = max(alpha, eval)
    
    return best_move

def move_sort_key(move: str, board, my_color, opp_color) -> float:
    # Higher score = better move to explore first
    score = 0.0
    from_sq = move[:2]
    to_sq = move[2:4]
    from_rank, from_file = square_to_idx(from_sq)
    to_rank, to_file = square_to_idx(to_sq)
    target_piece = board[to_rank][to_file]
    if target_piece and target_piece[0] == opp_color:
        # Capture
        captured_type = target_piece[1]
        score += piece_value[captured_type]
    
    # Check?
    new_board = make_move(board, move, my_color)
    if is_king_in_check(new_board, opp_color, my_color):
        score += 0.5
    return score

def generate_legal_moves(board, color, opp_color) -> List[str]:
    moves = []
    for r in range(8):
        for f in range(8):
            piece = board[r][f]
            if piece and piece[0] == color:
                moves.extend(get_piece_moves(board, r, f, color, opp_color))
    # Filter moves that leave own king in check
    legal = []
    for move in moves:
        new_board = make_move(board, move, color)
        if not is_king_in_check(new_board, color, opp_color):
            legal.append(move)
    return legal

def get_piece_moves(board, r, f, color, opp_color) -> List[str]:
    piece = board[r][f]
    ptype = piece[1]
    moves = []
    if ptype == 'P':
        # Pawn moves
        dir = 1 if color == 'w' else -1
        start_rank = 1 if color == 'w' else 6
        # Forward one
        if 0 <= r + dir < 8 and board[r + dir][f] is None:
            moves.append(idx_to_square(r, f) + idx_to_square(r + dir, f))
            # Forward two from start
            if r == start_rank and board[r + 2*dir][f] is None:
                moves.append(idx_to_square(r, f) + idx_to_square(r + 2*dir, f))
        # Captures
        for df in [-1, 1]:
            nr, nf = r + dir, f + df
            if 0 <= nr < 8 and 0 <= nf < 8:
                target = board[nr][nf]
                if target and target[0] == opp_color:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
        # Promotions (simplified: always promote to queen for move generation)
        promotion_rank = 7 if color == 'w' else 0
        if (r + dir) == promotion_rank:
            # Need to generate promotion moves separately
            base_moves = []
            # Forward non-capture
            if 0 <= r + dir < 8 and board[r + dir][f] is None:
                base = idx_to_square(r, f) + idx_to_square(r + dir, f)
                for promo in ['q', 'r', 'b', 'n']:
                    base_moves.append(base + promo)
            # Capture promotions
            for df in [-1, 1]:
                nr, nf = r + dir, f + df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    target = board[nr][nf]
                    if target and target[0] == opp_color:
                        base = idx_to_square(r, f) + idx_to_square(nr, nf)
                        for promo in ['q', 'r', 'b', 'n']:
                            base_moves.append(base + promo)
            return base_moves
    elif ptype == 'N':
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, df in knight_moves:
            nr, nf = r + dr, f + df
            if 0 <= nr < 8 and 0 <= nf < 8:
                target = board[nr][nf]
                if target is None or target[0] == opp_color:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
    elif ptype == 'B':
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, df in directions:
            nr, nf = r + dr, f + df
            while 0 <= nr < 8 and 0 <= nf < 8:
                target = board[nr][nf]
                if target is None:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
                elif target[0] == opp_color:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
                    break
                else:
                    break
                nr += dr
                nf += df
    elif ptype == 'R':
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, df in directions:
            nr, nf = r + dr, f + df
            while 0 <= nr < 8 and 0 <= nf < 8:
                target = board[nr][nf]
                if target is None:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
                elif target[0] == opp_color:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
                    break
                else:
                    break
                nr += dr
                nf += df
    elif ptype == 'Q':
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, df in directions:
            nr, nf = r + dr, f + df
            while 0 <= nr < 8 and 0 <= nf < 8:
                target = board[nr][nf]
                if target is None:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
                elif target[0] == opp_color:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
                    break
                else:
                    break
                nr += dr
                nf += df
    elif ptype == 'K':
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, df in king_moves:
            nr, nf = r + dr, f + df
            if 0 <= nr < 8 and 0 <= nf < 8:
                target = board[nr][nf]
                if target is None or target[0] == opp_color:
                    moves.append(idx_to_square(r, f) + idx_to_square(nr, nf))
        # Castling (simplified: only if squares empty and not in check)
        # We'll ignore for brevity to keep code short, but can be added.
    return moves

def is_king_in_check(board, color, opp_color) -> bool:
    # Find king
    king_pos = None
    for r in range(8):
        for f in range(8):
            piece = board[r][f]
            if piece and piece[0] == color and piece[1] == 'K':
                king_pos = (r, f)
                break
        if king_pos:
            break
    if not king_pos:
        return False  # shouldn't happen
    
    # Check opponent's pieces attacking king
    # Simulate opponent's moves to see if any can capture king
    for r in range(8):
        for f in range(8):
            piece = board[r][f]
            if piece and piece[0] == opp_color:
                # Generate pseudo-legal moves for this piece
                moves = get_piece_moves(board, r, f, opp_color, color)
                for move in moves:
                    to_sq = move[2:4]
                    to_rank, to_file = square_to_idx(to_sq)
                    if (to_rank, to_file) == king_pos:
                        return True
    return False

def make_move(board, move: str, color) -> List[List]:
    # Create a deep copy of board and apply move
    new_board = [row[:] for row in board]
    from_sq = move[:2]
    to_sq = move[2:4]
    fr, ff = square_to_idx(from_sq)
    tr, tf = square_to_idx(to_sq)
    piece = new_board[fr][ff]
    new_board[fr][ff] = None
    # Promotion
    if len(move) == 5:
        promo = move[4]
        piece = color + promo.upper()
    new_board[tr][tf] = piece
    return new_board

def square_to_idx(sq: str) -> Tuple[int, int]:
    file_idx = ord(sq[0]) - ord('a')
    rank_idx = int(sq[1]) - 1
    return rank_idx, file_idx

def idx_to_square(r: int, f: int) -> str:
    return chr(ord('a') + f) + str(r + 1)

def evaluate_board(board, my_color, opp_color) -> float:
    # Material balance
    score = 0.0
    total_pieces = 0
    for r in range(8):
        for f in range(8):
            piece = board[r][f]
            if piece:
                total_pieces += 1
                value = piece_value[piece[1]]
                if piece[0] == my_color:
                    score += value
                else:
                    score -= value
    
    # Pawn advancement in endgame
    if total_pieces <= 10:
        for r in range(8):
            for f in range(8):
                piece = board[r][f]
                if piece and piece[0] == my_color and piece[1] == 'P':
                    advance = r if my_color == 'w' else 7 - r
                    score += 0.01 * advance
                elif piece and piece[0] == opp_color and piece[1] == 'P':
                    advance = r if opp_color == 'w' else 7 - r
                    score -= 0.01 * advance
    
    # King safety in middlegame
    if total_pieces > 10:
        # Penalize king near center
        for r in range(8):
            for f in range(8):
                piece = board[r][f]
                if piece and piece[1] == 'K':
                    if piece[0] == my_color:
                        center_dist = abs(r - 3.5) + abs(f - 3.5)
                        score -= 0.05 * center_dist
                    else:
                        center_dist = abs(r - 3.5) + abs(f - 3.5)
                        score += 0.05 * center_dist
    return score

def minimax(board, depth: int, maximizing: bool, alpha: float, beta: float, my_color, opp_color) -> float:
    if depth == 0:
        return evaluate_board(board, my_color, opp_color)
    
    if maximizing:
        max_eval = -math.inf
        moves = generate_legal_moves(board, my_color, opp_color)
        moves = sorted(moves, key=lambda m: move_sort_key(m, board, my_color, opp_color), reverse=True)
        for move in moves:
            new_board = make_move(board, move, my_color)
            eval = minimax(new_board, depth - 1, False, alpha, beta, my_color, opp_color)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        moves = generate_legal_moves(board, opp_color, my_color)
        moves = sorted(moves, key=lambda m: move_sort_key(m, board, opp_color, my_color), reverse=True)
        for move in moves:
            new_board = make_move(board, move, opp_color)
            eval = minimax(new_board, depth - 1, True, alpha, beta, my_color, opp_color)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
