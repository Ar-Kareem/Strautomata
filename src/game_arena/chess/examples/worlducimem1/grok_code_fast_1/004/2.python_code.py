
import copy
import numpy as np

# Piece values for evaluation
PIECE_VALUE = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

# Positional bonuses (central squares, pawn advancement)
POSITION_BONUS = {
    'white': {'P': {6: 3, 7: 2}, 'K': {}, 'Q': {}, 'R': {}, 'B': {}, 'N': {}},
    'black': {'P': {1: 3, 0: 2}, 'K': {}, 'Q': {}, 'R': {}, 'B': {}, 'N': {}}
}

def board_to_matrix(pieces):
    """Convert pieces dict to 8x8 matrix for easy access."""
    board = [['' for _ in range(8)] for _ in range(8)]
    for sq, piece in pieces.items():
        file, rank = ord(sq[0]) - ord('a'), int(sq[1]) - 1  # a1 -> 0,0; h8->7,7
        board[rank][file] = piece
    return board

def get_piece_at(board, row, col):
    if 0 <= row < 8 and 0 <= col < 8:
        return board[row][col]
    return ''

def square_to_coords(sq):
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1

def coords_to_square(col, row):
    return chr(col + ord('a')) + str(row + 1)

def generate_moves(board, to_play):
    """Generate pseudo-legal moves for to_play (need full legality in simulation, but approximate)."""
    moves = []
    for sq, piece in pieces.items():  # Assumes global pieces dict
        if piece[0] != to_play[0]:
            continue
        col, row = square_to_coords(sq)
        color = piece[0]
        ptype = piece[1]
        
        if ptype == 'P':
            direction = 1 if color == 'w' else -1
            start_row = 1 if color == 'w' else 6
            new_row = row + direction
            # Forward move
            if new_row >= 0 and new_row < 8 and board[new_row][col] == '':
                moves.append(sq + coords_to_square(col, new_row))
                # Double move from start
                if row == start_row and board[new_row + direction][col] == '':
                    moves.append(sq + coords_to_square(col, new_row + direction))
            # Captures
            for dc in [-1, 1]:
                if 0 <= col + dc < 8 and new_row >= 0 and new_row < 8:
                    target = board[new_row][col + dc]
                    if target and target[0] != color:
                        moves.append(sq + coords_to_square(col + dc, new_row))
            # Promotions handled in apply_move
        
        elif ptype == 'N':
            knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
            for dr, dc in knight_moves:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or target[0] != color:
                        moves.append(sq + coords_to_square(nc, nr))
        
        elif ptype == 'R':
            directions = [(-1,0), (1,0), (0,-1), (0,1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = board[r][c]
                    if target == '':
                        moves.append(sq + coords_to_square(c, r))
                    elif target[0] != color:
                        moves.append(sq + coords_to_square(c, r))
                        break
                    else:
                        break
                    r += dr
                    c += dc
        
        elif ptype == 'B':
            directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = board[r][c]
                    if target == '':
                        moves.append(sq + coords_to_square(c, r))
                    elif target[0] != color:
                        moves.append(sq + coords_to_square(c, r))
                        break
                    else:
                        break
                    r += dr
                    c += dc
        
        elif ptype == 'Q':
            # Combine R and B
            directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = board[r][c]
                    if target == '':
                        moves.append(sq + coords_to_square(c, r))
                    elif target[0] != color:
                        moves.append(sq + coords_to_square(c, r))
                        break
                    else:
                        break
                    r += dr
                    c += dc
        
        # King moves (no castling for simplicity)
        elif ptype == 'K':
            directions = [(-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if not target or target[0] != color:
                        moves.append(sq + coords_to_square(nc, nr))
    
    return moves

def apply_move(pieces, move):
    """Apply a move (UCI string) to create new piece positions."""
    new_pieces = copy.deepcopy(pieces)
    from_sq = move[:2]
    to_sq = move[2:4]
    prom = move[4:] if len(move) == 5 else ''
    
    if prom:
        new_pieces[to_sq] = new_pieces[from_sq][0] + prom.upper()
    else:
        new_pieces[to_sq] = new_pieces[from_sq]
    
    del new_pieces[from_sq]
    return new_pieces

def evaluate_board(pieces, my_color):
    """Static evaluation: material + positional bonuses."""
    score = 0
    opp_color = 'b' if my_color == 'w' else 'w'
    for sq, piece in pieces.items():
        color = piece[0]
        ptype = piece[1]
        val = PIECE_VALUE[ptype]
        if sq in POSITION_BONUS[color if color in POSITION_BONUS else 'white'].get(ptype, {}):
            val += POSITION_BONUS[color].get(ptype, {}).get(int(sq[1]) - 1, 0) if color in POSITION_BONUS else 0
        if color == my_color:
            score += val
        else:
            score -= val
    # Basic king safety: penalty if king near opponent pieces (simplified)
    king_sq = next(sq for sq, p in pieces.items() if p == my_color + 'K')
    k_col, k_row = square_to_coords(king_sq)
    opp_pieces_near = sum(1 for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)] 
                          if get_piece_at(board_to_matrix(pieces), k_row + dr, k_col + dc).startswith(opp_color))
    score -= opp_pieces_near * 0.1  # Small penalty
    return score

def minimax(pieces, depth, maximizing, alpha, beta, my_color):
    """Alpha-beta minimax to depth."""
    if depth == 0:
        return evaluate_board(pieces, my_color)
    
    current_to_play = my_color if maximizing else ('b' if my_color == 'w' else 'w')
    legal_moves = generate_moves(board_to_matrix(pieces), current_to_play)
    
    if maximizing:
        max_eval = -np.inf
        for move in legal_moves:
            new_pieces = apply_move(pieces, move)
            eval = minimax(new_pieces, depth - 1, False, alpha, beta, my_color)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        for move in legal_moves:
            new_pieces = apply_move(pieces, move)
            eval = minimax(new_pieces, depth - 1, True, alpha, beta, my_color)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces, to_play, legal_moves, memory):
    """Main policy: select best move via alpha-beta at depth 3."""
    if not legal_moves:
        return 'resign', memory  # Impossible, but fallback
    
    my_color = to_play[0] if to_play.startswith('w') else 'b'
    best_score = -np.inf
    best_move = legal_moves[0]
    
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        score = minimax(new_pieces, 3, False, -np.inf, np.inf, my_color)  # After move, opponent's turn
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
