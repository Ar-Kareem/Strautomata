
import time

# Piece values for evaluation
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-Square Tables (simplified) - Encourages central control and advancement
# Scores are from White's perspective. We will flip them for Black.
PST = {
    'P': [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'R': [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ],
    'Q': [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    'K': [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
}

def sq_to_idx(sq):
    f = ord(sq[0]) - ord('a')
    r = int(sq[1]) - 1
    return r, f

def idx_to_sq(r, f):
    return chr(f + ord('a')) + str(r + 1)

def is_white(piece):
    return piece[0] == 'w'

def get_piece_type(piece):
    return piece[1]

def flip_score_table(table):
    # Flip for black (rank 0 becomes rank 7, etc.)
    return table[::-1]

# Precompute flipped tables for black
PST_BLACK = {k: flip_score_table(v) for k, v in PST.items()}

def evaluate(pieces, to_play):
    score = 0
    for sq, piece in pieces.items():
        r, f = sq_to_idx(sq)
        p_type = get_piece_type(piece)
        val = PIECE_VALUES[p_type]
        
        if is_white(piece):
            score += val
            # Add PST bonus
            score += PST[p_type][r * 8 + f]
        else:
            score -= val
            # Add PST bonus (from Black's perspective)
            # r=0 is rank 1. For black, rank 1 is the top of their PST (index 0 in standard representation, but here we flip)
            # Actually, standard PST is for White. For Black, we need to mirror the rank.
            # If r is 0 (rank 1), it corresponds to row 7 in standard PST if we view from White.
            # Let's use the PST_BLACK we generated.
            score -= PST_BLACK[p_type][r * 8 + f]

    return score if to_play == 'white' else -score

def get_raw_moves(pieces, color):
    # Generate pseudo-legal moves
    moves = []
    
    for sq, piece in pieces.items():
        if (color == 'white' and not is_white(piece)) or (color == 'black' and is_white(piece)):
            continue
            
        r, f = sq_to_idx(sq)
        p_type = get_piece_type(piece)
        
        directions = []
        
        if p_type == 'N':
            directions = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
            for dr, df in directions:
                nr, nf = r + dr, f + df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    target_sq = idx_to_sq(nr, nf)
                    target_piece = pieces.get(target_sq)
                    if target_piece:
                        if (is_white(target_piece) != (color == 'white')):
                            moves.append((sq, target_sq, None))
                    else:
                        moves.append((sq, target_sq, None))
                        
        elif p_type == 'K':
            directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for dr, df in directions:
                nr, nf = r + dr, f + df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    target_sq = idx_to_sq(nr, nf)
                    target_piece = pieces.get(target_sq)
                    if target_piece:
                        if (is_white(target_piece) != (color == 'white')):
                            moves.append((sq, target_sq, None))
                    else:
                        moves.append((sq, target_sq, None))
            # Castling generation is skipped for simplicity in internal nodes
            # to avoid tracking rights, but usually not critical for depth 3-4.
            
        elif p_type == 'R':
            directions = [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, df in directions:
                for i in range(1, 8):
                    nr, nf = r + dr*i, f + df*i
                    if 0 <= nr < 8 and 0 <= nf < 8:
                        target_sq = idx_to_sq(nr, nf)
                        target_piece = pieces.get(target_sq)
                        if target_piece:
                            if (is_white(target_piece) != (color == 'white')):
                                moves.append((sq, target_sq, None))
                            break
                        else:
                            moves.append((sq, target_sq, None))
                    else:
                        break
                        
        elif p_type == 'B':
            directions = [(-1,-1),(-1,1),(1,-1),(1,1)]
            for dr, df in directions:
                for i in range(1, 8):
                    nr, nf = r + dr*i, f + df*i
                    if 0 <= nr < 8 and 0 <= nf < 8:
                        target_sq = idx_to_sq(nr, nf)
                        target_piece = pieces.get(target_sq)
                        if target_piece:
                            if (is_white(target_piece) != (color == 'white')):
                                moves.append((sq, target_sq, None))
                            break
                        else:
                            moves.append((sq, target_sq, None))
                    else:
                        break
                        
        elif p_type == 'Q':
            directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
            for dr, df in directions:
                for i in range(1, 8):
                    nr, nf = r + dr*i, f + df*i
                    if 0 <= nr < 8 and 0 <= nf < 8:
                        target_sq = idx_to_sq(nr, nf)
                        target_piece = pieces.get(target_sq)
                        if target_piece:
                            if (is_white(target_piece) != (color == 'white')):
                                moves.append((sq, target_sq, None))
                            break
                        else:
                            moves.append((sq, target_sq, None))
                    else:
                        break
                        
        elif p_type == 'P':
            # Direction
            step = 1 if color == 'white' else -1
            start_rank = 1 if color == 'white' else 6
            promo_rank = 7 if color == 'white' else 0
            
            # Forward
            nr = r + step
            if 0 <= nr < 8:
                target_sq = idx_to_sq(nr, f)
                if not pieces.get(target_sq):
                    if nr == promo_rank:
                        for pr in ['q', 'r', 'b', 'n']:
                            moves.append((sq, target_sq, pr))
                    else:
                        moves.append((sq, target_sq, None))
                        
                    # Double push
                    if r == start_rank:
                        nr2 = r + 2*step
                        target_sq2 = idx_to_sq(nr2, f)
                        if not pieces.get(target_sq2):
                            moves.append((sq, target_sq2, None))

            # Captures
            for df in [-1, 1]:
                nf = f + df
                if 0 <= nf < 8:
                    nr = r + step
                    if 0 <= nr < 8:
                        target_sq = idx_to_sq(nr, nf)
                        target_piece = pieces.get(target_sq)
                        if target_piece and (is_white(target_piece) != (color == 'white')):
                            if nr == promo_rank:
                                for pr in ['q', 'r', 'b', 'n']:
                                    moves.append((sq, target_sq, pr))
                            else:
                                moves.append((sq, target_sq, None))
            # En passant not implemented in generator to avoid state history tracking complexity.
                                
    return moves

def find_king(pieces, color):
    king_code = 'wK' if color == 'white' else 'bK'
    for sq, p in pieces.items():
        if p == king_code:
            return sq
    return None

def is_attacked(pieces, target_sq, by_color):
    # Check if target_sq is attacked by by_color
    # We can reuse the raw move generation logic but simplified (check if any piece can move to target)
    # Or just scan from target square.
    tr, tf = sq_to_idx(target_sq)
    
    # Knight attacks
    knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
    for dr, df in knight_moves:
        nr, nf = tr + dr, tf + df
        if 0 <= nr < 8 and 0 <= nf < 8:
            sq = idx_to_sq(nr, nf)
            p = pieces.get(sq)
            if p:
                p_type = get_piece_type(p)
                is_white_p = is_white(p)
                if p_type == 'N' and ((by_color == 'white' and is_white_p) or (by_color == 'black' and not is_white_p)):
                    return True
                    
    # King attacks
    king_moves = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for dr, df in king_moves:
        nr, nf = tr + dr, tf + df
        if 0 <= nr < 8 and 0 <= nf < 8:
            sq = idx_to_sq(nr, nf)
            p = pieces.get(sq)
            if p:
                p_type = get_piece_type(p)
                is_white_p = is_white(p)
                if p_type == 'K' and ((by_color == 'white' and is_white_p) or (by_color == 'black' and not is_white_p)):
                    return True
                    
    # Pawn attacks
    # If target is attacked by White, White pawn is at (tr-1, tf-1) or (tr-1, tf+1)
    # If target is attacked by Black, Black pawn is at (tr+1, tf-1) or (tr+1, tf+1)
    if by_color == 'white':
        pr = tr - 1
        if pr >= 0:
            for df in [-1, 1]:
                pf = tf + df
                if 0 <= pf < 8:
                    sq = idx_to_sq(pr, pf)
                    p = pieces.get(sq)
                    if p == 'wP': return True
    else:
        pr = tr + 1
        if pr < 8:
            for df in [-1, 1]:
                pf = tf + df
                if 0 <= pf < 8:
                    sq = idx_to_sq(pr, pf)
                    p = pieces.get(sq)
                    if p == 'bP': return True
                     
    # Sliding pieces (R, Q for ortho, B, Q for diag)
    # Orthogonal
    for dr, df in [(-1,0),(1,0),(0,-1),(0,1)]:
        for i in range(1, 8):
            nr, nf = tr + dr*i, tf + df*i
            if 0 <= nr < 8 and 0 <= nf < 8:
                sq = idx_to_sq(nr, nf)
                p = pieces.get(sq)
                if p:
                    p_type = get_piece_type(p)
                    is_white_p = is_white(p)
                    if (by_color == 'white' and is_white_p) or (by_color == 'black' and not is_white_p):
                        if p_type in ['R', 'Q']:
                            return True
                    break # Blocked
            else:
                break
                
    # Diagonal
    for dr, df in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        for i in range(1, 8):
            nr, nf = tr + dr*i, tf + df*i
            if 0 <= nr < 8 and 0 <= nf < 8:
                sq = idx_to_sq(nr, nf)
                p = pieces.get(sq)
                if p:
                    p_type = get_piece_type(p)
                    is_white_p = is_white(p)
                    if (by_color == 'white' and is_white_p) or (by_color == 'black' and not is_white_p):
                        if p_type in ['B', 'Q']:
                            return True
                    break
            else:
                break
                
    return False

def make_move(pieces, move):
    # move is (start, end, promo)
    new_pieces = pieces.copy()
    s, e, pr = move
    piece = new_pieces.pop(s)
    
    if pr:
        # Promotion
        color = 'w' if is_white(piece) else 'b'
        piece = color + pr.upper()
        
    new_pieces[e] = piece
    return new_pieces

def get_legal_moves(pieces, color):
    raw = get_raw_moves(pieces, color)
    legal = []
    opp_color = 'black' if color == 'white' else 'white'
    
    for m in raw:
        new_board = make_move(pieces, m)
        king_sq = find_king(new_board, color)
        if king_sq and not is_attacked(new_board, king_sq, opp_color):
            legal.append(m)
            
    return legal

def negamax(pieces, depth, alpha, beta, color):
    if depth == 0:
        return evaluate(pieces, color), None
        
    moves = get_legal_moves(pieces, color)
    
    if not moves:
        # Check for checkmate or stalemate
        opp_color = 'black' if color == 'white' else 'white'
        my_king = find_king(pieces, color)
        if my_king and is_attacked(pieces, my_king, opp_color):
            return -100000 - depth, None # Checkmate (worse if sooner)
        return 0, None # Stalemate
        
    # Move ordering: captures first
    def move_score(m):
        s, e, pr = m
        score = 0
        target = pieces.get(e)
        if target:
            # MVV-LVA
            score += PIECE_VALUES[get_piece_type(target)] * 10 - PIECE_VALUES[get_piece_type(pieces[s])]
        if pr == 'q': score += 800
        return -score
        
    moves.sort(key=move_score)
    
    best_score = -float('inf')
    best_move = moves[0] if moves else None
    
    for m in moves:
        new_board = make_move(pieces, m)
        opp_color = 'black' if color == 'white' else 'white'
        score, _ = negamax(new_board, depth - 1, -beta, -alpha, opp_color)
        score = -score
        
        if score > best_score:
            best_score = score
            best_move = m
            
        alpha = max(alpha, score)
        if alpha >= beta:
            break
            
    return best_score, best_move

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str] = None) -> str:
    start_time = time.time()
    
    color = to_play
    
    # If legal_moves are provided, we can use them for the root node to save time/ensure legality
    # We map UCI strings to our internal move tuples to interface with the search
    
    internal_legal_moves = []
    
    # Helper to convert UCI to internal if needed
    # Internal format: (start_sq, end_sq, promotion_char_lower)
    # UCI: e2e4, e7e8q
    
    if legal_moves:
        for uci in legal_moves:
            s, e = uci[0:2], uci[2:4]
            pr = uci[4] if len(uci) > 4 else None
            internal_legal_moves.append((s, e, pr))
    else:
        # Generate them if not provided
        internal_legal_moves = get_legal_moves(pieces, color)

    if not internal_legal_moves:
        return "" # Should not happen if game is valid

    # Iterative Deepening
    best_move = internal_legal_moves[0]
    
    # Time management: aim for < 1s
    for depth in range(1, 5):
        try:
            # We filter the search to only the legal moves provided/generated
            # We implement a specific root search loop
            
            current_best_score = -float('inf')
            current_best_move = best_move
            
            alpha = -float('inf')
            beta = float('inf')
            
            # Order moves
            def move_score_root(m):
                s, e, pr = m
                score = 0
                target = pieces.get(e)
                if target:
                    score += PIECE_VALUES[get_piece_type(target)] * 10 - PIECE_VALUES[get_piece_type(pieces[s])]
                if pr == 'q': score += 800
                return -score
            
            internal_legal_moves.sort(key=move_score_root)
            
            for m in internal_legal_moves:
                new_board = make_move(pieces, m)
                opp_color = 'black' if color == 'white' else 'white'
                score, _ = negamax(new_board, depth - 1, -beta, -alpha, opp_color)
                score = -score
                
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = m
                    
                alpha = max(alpha, score)
                
            best_move = current_best_move
            
            # Check time
            if time.time() - start_time > 0.5: # Safety margin
                 break
        except:
            break
            
    # Convert back to UCI
    s, e, pr = best_move
    uci_str = s + e + (pr if pr else '')
    return uci_str
