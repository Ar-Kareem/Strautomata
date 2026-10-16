
import copy

def policy(pieces, to_play, memory):
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Convert square to indices
    def sq_to_idx(sq):
        return ord(sq[0]) - ord('a'), int(sq[1]) - 1
    
    def idx_to_sq(f, r):
        return chr(ord('a') + f) + str(r + 1)
    
    # Build board
    def build_board(pieces):
        board = [[None]*8 for _ in range(8)]
        for sq, pc in pieces.items():
            f, r = sq_to_idx(sq)
            board[f][r] = pc
        return board
    
    def get_piece(board, f, r):
        if 0 <= f < 8 and 0 <= r < 8:
            return board[f][r]
        return None
    
    def is_enemy(board, f, r, color):
        pc = get_piece(board, f, r)
        return pc is not None and pc[0] != color
    
    def is_empty(board, f, r):
        return 0 <= f < 8 and 0 <= r < 8 and board[f][r] is None
    
    def is_empty_or_enemy(board, f, r, color):
        if not (0 <= f < 8 and 0 <= r < 8):
            return False
        pc = board[f][r]
        return pc is None or pc[0] != color
    
    def generate_moves(board, color, ep_sq=None, castling_rights=None):
        moves = []
        opp = 'b' if color == 'w' else 'w'
        pawn_dir = 1 if color == 'w' else -1
        start_rank = 1 if color == 'w' else 6
        promo_rank = 7 if color == 'w' else 0
        
        for f in range(8):
            for r in range(8):
                pc = board[f][r]
                if pc is None or pc[0] != color:
                    continue
                pt = pc[1]
                
                if pt == 'P':
                    # Forward
                    nr = r + pawn_dir
                    if 0 <= nr < 8 and board[f][nr] is None:
                        if nr == promo_rank:
                            for p in 'qrbn':
                                moves.append((f, r, f, nr, p))
                        else:
                            moves.append((f, r, f, nr, None))
                        # Double push
                        if r == start_rank:
                            nr2 = r + 2*pawn_dir
                            if board[f][nr2] is None:
                                moves.append((f, r, f, nr2, None))
                    # Captures
                    for df in [-1, 1]:
                        nf = f + df
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            if is_enemy(board, nf, nr, color):
                                if nr == promo_rank:
                                    for p in 'qrbn':
                                        moves.append((f, r, nf, nr, p))
                                else:
                                    moves.append((f, r, nf, nr, None))
                            # En passant
                            if ep_sq and idx_to_sq(nf, nr) == ep_sq:
                                moves.append((f, r, nf, nr, None))
                
                elif pt == 'N':
                    for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                        nf, nr = f+df, r+dr
                        if is_empty_or_enemy(board, nf, nr, color):
                            moves.append((f, r, nf, nr, None))
                
                elif pt == 'B':
                    for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                        nf, nr = f+df, r+dr
                        while 0 <= nf < 8 and 0 <= nr < 8:
                            if board[nf][nr] is None:
                                moves.append((f, r, nf, nr, None))
                            elif board[nf][nr][0] != color:
                                moves.append((f, r, nf, nr, None))
                                break
                            else:
                                break
                            nf, nr = nf+df, nr+dr
                
                elif pt == 'R':
                    for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nf, nr = f+df, r+dr
                        while 0 <= nf < 8 and 0 <= nr < 8:
                            if board[nf][nr] is None:
                                moves.append((f, r, nf, nr, None))
                            elif board[nf][nr][0] != color:
                                moves.append((f, r, nf, nr, None))
                                break
                            else:
                                break
                            nf, nr = nf+df, nr+dr
                
                elif pt == 'Q':
                    for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]:
                        nf, nr = f+df, r+dr
                        while 0 <= nf < 8 and 0 <= nr < 8:
                            if board[nf][nr] is None:
                                moves.append((f, r, nf, nr, None))
                            elif board[nf][nr][0] != color:
                                moves.append((f, r, nf, nr, None))
                                break
                            else:
                                break
                            nf, nr = nf+df, nr+dr
                
                elif pt == 'K':
                    for df, dr in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                        nf, nr = f+df, r+dr
                        if is_empty_or_enemy(board, nf, nr, color):
                            moves.append((f, r, nf, nr, None))
                    # Castling
                    if castling_rights:
                        base_rank = 0 if color == 'w' else 7
                        if f == 4 and r == base_rank:
                            # Kingside
                            if castling_rights.get(color + 'K'):
                                if board[5][base_rank] is None and board[6][base_rank] is None:
                                    if not is_attacked(board, 4, base_rank, opp) and not is_attacked(board, 5, base_rank, opp) and not is_attacked(board, 6, base_rank, opp):
                                        moves.append((4, base_rank, 6, base_rank, None))
                            # Queenside
                            if castling_rights.get(color + 'Q'):
                                if board[3][base_rank] is None and board[2][base_rank] is None and board[1][base_rank] is None:
                                    if not is_attacked(board, 4, base_rank, opp) and not is_attacked(board, 3, base_rank, opp) and not is_attacked(board, 2, base_rank, opp):
                                        moves.append((4, base_rank, 2, base_rank, None))
        return moves
    
    def is_attacked(board, f, r, by_color):
        # Check if square (f,r) is attacked by by_color
        # Knights
        for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nf, nr = f+df, r+dr
            pc = get_piece(board, nf, nr)
            if pc and pc[0] == by_color and pc[1] == 'N':
                return True
        # King
        for df, dr in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nf, nr = f+df, r+dr
            pc = get_piece(board, nf, nr)
            if pc and pc[0] == by_color and pc[1] == 'K':
                return True
        # Pawns
        pawn_dir = 1 if by_color == 'w' else -1
        for df in [-1, 1]:
            nf, nr = f+df, r-pawn_dir
            pc = get_piece(board, nf, nr)
            if pc and pc[0] == by_color and pc[1] == 'P':
                return True
        # Rooks/Queens (straight)
        for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
            nf, nr = f+df, r+dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                pc = board[nf][nr]
                if pc:
                    if pc[0] == by_color and pc[1] in 'RQ':
                        return True
                    break
                nf, nr = nf+df, nr+dr
        # Bishops/Queens (diagonal)
        for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nf, nr = f+df, r+dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                pc = board[nf][nr]
                if pc:
                    if pc[0] == by_color and pc[1] in 'BQ':
                        return True
                    break
                nf, nr = nf+df, nr+dr
        return False
    
    def make_move(board, move, ep_sq=None):
        f1, r1, f2, r2, promo = move
        new_board = [row[:] for row in board]
        pc = new_board[f1][r1]
        new_board[f1][r1] = None
        
        # En passant capture
        if pc[1] == 'P' and ep_sq and idx_to_sq(f2, r2) == ep_sq:
            cap_r = r2 - (1 if pc[0] == 'w' else -1)
            new_board[f2][cap_r] = None
        
        # Castling - move rook
        if pc[1] == 'K' and abs(f2 - f1) == 2:
            if f2 == 6:  # Kingside
                new_board[5][r2] = new_board[7][r2]
                new_board[7][r2] = None
            else:  # Queenside
                new_board[3][r2] = new_board[0][r2]
                new_board[0][r2] = None
        
        if promo:
            new_board[f2][r2] = pc[0] + promo.upper()
        else:
            new_board[f2][r2] = pc
        
        # New en passant square
        new_ep = None
        if pc[1] == 'P' and abs(r2 - r1) == 2:
            new_ep = idx_to_sq(f1, (r1 + r2) // 2)
        
        return new_board, new_ep
    
    def in_check(board, color):
        opp = 'b' if color == 'w' else 'w'
        for f in range(8):
            for r in range(8):
                pc = board[f][r]
                if pc and pc[0] == color and pc[1] == 'K':
                    return is_attacked(board, f, r, opp)
        return False
    
    def legal_moves(board, color, ep_sq=None, castling_rights=None):
        opp = 'b' if color == 'w' else 'w'
        moves = generate_moves(board, color, ep_sq, castling_rights)
        legal = []
        for m in moves:
            new_board, _ = make_move(board, m, ep_sq)
            if not in_check(new_board, color):
                legal.append(m)
        return legal
    
    def evaluate(board, color):
        score = 0
        for f in range(8):
            for r in range(8):
                pc = board[f][r]
                if pc:
                    val = PIECE_VALUES.get(pc[1], 0)
                    if pc[0] == color:
                        score += val
                    else:
                        score -= val
        return score
    
    def minimax(board, depth, alpha, beta, maximizing, color, ep_sq, castling_rights):
        opp = 'b' if color == 'w' else 'w'
        
        moves = legal_moves(board, color if maximizing else opp, ep_sq, castling_rights)
        
        if depth == 0 or not moves:
            if not moves:
                c = color if maximizing else opp
                if in_check(board, c):
                    return -100000 if maximizing else 100000
                return 0
            return evaluate(board, color)
        
        if maximizing:
            max_eval = -float('inf')
            for m in moves:
                new_board, new_ep = make_move(board, m, ep_sq)
                ev = minimax(new_board, depth-1, alpha, beta, False, color, new_ep, castling_rights)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for m in moves:
                new_board, new_ep = make_move(board, m, ep_sq)
                ev = minimax(new_board, depth-1, alpha, beta, True, color, new_ep, castling_rights)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval
    
    board = build_board(pieces)
    ep_sq = memory.get('ep_sq')
    castling_rights = memory.get('castling', {'wK': True, 'wQ': True, 'bK': True, 'bQ': True})
    
    moves = legal_moves(board, my_color, ep_sq, castling_rights)
    
    if not moves:
        return "0000", memory
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for m in moves:
        new_board, new_ep = make_move(board, m, ep_sq)
        score = minimax(new_board, 2, -float('inf'), float('inf'), False, my_color, new_ep, castling_rights)
        if score > best_score:
            best_score = score
            best_move = m
    
    f1, r1, f2, r2, promo = best_move
    move_str = idx_to_sq(f1, r1) + idx_to_sq(f2, r2)
    if promo:
        move_str += promo
    
    # Update memory
    new_ep = None
    pc = board[f1][r1]
    if pc and pc[1] == 'P' and abs(r2 - r1) == 2:
        new_ep = idx_to_sq(f1, (r1 + r2) // 2)
    
    memory['ep_sq'] = new_ep
    memory['castling'] = castling_rights
    
    return move_str, memory
