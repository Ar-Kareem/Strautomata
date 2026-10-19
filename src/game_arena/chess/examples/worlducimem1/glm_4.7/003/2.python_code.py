
import random
import math

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # --- Constants & Tables ---
    # Piece Values
    PV = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Simplified Piece-Square Tables (PST) for positional evaluation
    # Encourages center control, development, and king safety in middle-game
    PST = {
        'P': [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ],
        'N': [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ],
        'B': [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ],
        'R': [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10,  5,  0],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ],
        'Q': [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ],
        'K': [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ]
    }

    # --- Helper Functions ---
    def on_board(r, f): return 0 <= r < 8 and 0 <= f < 8
    
    # Convert algebraic notation (e.g., 'e4') to board indices
    def sq_to_idx(sq):
        f = ord(sq[0]) - 97
        r = int(sq[1]) - 1
        return r, f
    
    # Convert board indices to UCI move string
    def idx_to_uci(fr, ff, tr, tf, prom=''):
        return chr(ff+97) + str(fr+1) + chr(tf+97) + str(tr+1) + prom

    # Initialize board
    board = [[None]*8 for _ in range(8)]
    for sq, pc in pieces.items():
        r, f = sq_to_idx(sq)
        board[r][f] = pc

    turn = to_play[0] # 'w' or 'b'
    opponent = 'b' if turn == 'w' else 'w'

    # --- Core Logic ---

    def is_attacked(tr, tf, by_color):
        # Check Pawn attacks
        if by_color == 'w':
            if on_board(tr+1, tf-1) and board[tr+1][tf-1] == 'wP': return True
            if on_board(tr+1, tf+1) and board[tr+1][tf+1] == 'wP': return True
        else:
            if on_board(tr-1, tf-1) and board[tr-1][tf-1] == 'bP': return True
            if on_board(tr-1, tf+1) and board[tr-1][tf+1] == 'bP': return True

        # Check Knight attacks
        for dr, df in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            r, f = tr+dr, tf+df
            if on_board(r, f) and board[r][f] == by_color+'N': return True
        
        # Check King attacks (for adjacent kings)
        for dr in [-1,0,1]:
            for df in [-1,0,1]:
                if dr==0 and df==0: continue
                r, f = tr+dr, tf+df
                if on_board(r, f) and board[r][f] == by_color+'K': return True
        
        # Check Sliding attacks (Rook/Queen -> Linear, Bishop/Queen -> Diagonal)
        # Linear
        for dr, df in [(-1,0), (1,0), (0,-1), (0,1)]:
            r, f = tr+dr, tf+df
            while on_board(r, f):
                p = board[r][f]
                if p:
                    if p[0] == by_color and p[1] in ['R', 'Q']: return True
                    break
                r += dr; f += df
        
        # Diagonal
        for dr, df in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            r, f = tr+dr, tf+df
            while on_board(r, f):
                p = board[r][f]
                if p:
                    if p[0] == by_color and p[1] in ['B', 'Q']: return True
                    break
                r += dr; f += df
        
        return False

    def get_legal_moves(color):
        moves = []
        opp = 'b' if color == 'w' else 'w'
        
        for r in range(8):
            for f in range(8):
                p = board[r][f]
                if not p or p[0] != color: continue
                
                type = p[1]
                
                # Pawn
                if type == 'P':
                    d = -1 if color == 'w' else 1
                    # Move 1
                    if on_board(r+d, f) and board[r+d][f] is None:
                        # Promotion check
                        prom = 'q' if (r+d == 0 or r+d == 7) else ''
                        moves.append((r,f,r+d,f,prom))
                        
                        # Move 2
                        start_r = 6 if color == 'w' else 1
                        if r == start_r and on_board(r+2*d, f) and board[r+2*d][f] is None:
                            moves.append((r,f,r+2*d,f,''))
                    
                    # Captures
                    for df in [-1, 1]:
                        if on_board(r+d, f+df):
                            target = board[r+d][f+df]
                            if target and target[0] == opp:
                                prom = 'q' if (r+d == 0 or r+d == 7) else ''
                                moves.append((r,f,r+d,f+df,prom))
                
                # Knight
                elif type == 'N':
                    for dr, df in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                        nr, nf = r+dr, f+df
                        if on_board(nr, nf):
                            target = board[nr][nf]
                            if target is None or target[0] == opp:
                                moves.append((r,f,nr,nf,''))
                
                # King
                elif type == 'K':
                    for dr in [-1,0,1]:
                        for df in [-1,0,1]:
                            if dr==0 and df==0: continue
                            nr, nf = r+dr, f+df
                            if on_board(nr, nf):
                                target = board[nr][nf]
                                if target is None or target[0] == opp:
                                    moves.append((r,f,nr,nf,''))
                
                # Sliding (B, R, Q)
                else:
                    directions = []
                    if type in ['B', 'Q']: directions += [(-1,-1), (-1,1), (1,-1), (1,1)]
                    if type in ['R', 'Q']: directions += [(-1,0), (1,0), (0,-1), (0,1)]
                    
                    for dr, df in directions:
                        nr, nf = r+dr, f+df
                        while on_board(nr, nf):
                            target = board[nr][nf]
                            if target is None:
                                moves.append((r,f,nr,nf,''))
                            else:
                                if target[0] == opp:
                                    moves.append((r,f,nr,nf,''))
                                break
                            nr += dr; nf += df

        # Filter illegal moves (leaves king in check)
        legal_moves = []
        for move in moves:
            fr, ff, tr, tf, prom = move
            
            # Make move
            captured = board[tr][tf]
            moved_piece = board[fr][ff]
            
            # Promotion update
            new_piece = moved_piece
            if prom:
                new_piece = color + 'Q'
                
            board[tr][tf] = new_piece
            board[fr][ff] = None
            
            # Find King
            kr, kf = None, None
            for i in range(8):
                for j in range(8):
                    if board[i][j] == color+'K':
                        kr, kf = i, j
                        break
            
            in_check = is_attacked(kr, kf, opp)
            
            # Undo move
            board[fr][ff] = moved_piece
            board[tr][tf] = captured
            
            if not in_check:
                legal_moves.append(idx_to_uci(fr, ff, tr, tf, prom))
        
        # Add Castling (if legal)
        # Castling is tricky without history, so we infer based on current piece positions
        # and check path safety.
        if type == 'K' and not is_attacked(r, f, opp): # Must check from King's perspective
             pass # Logic moved below to avoid scope issues
             
        # Separate Castling Logic applied after standard moves
        if color == 'w':
            # Kingside
            if board[7][4] == 'wK' and board[7][7] == 'wR' and board[7][5] is None and board[7][6] is None:
                if not is_attacked(7, 4, 'b') and not is_attacked(7, 5, 'b') and not is_attacked(7, 6, 'b'):
                    legal_moves.append('e1g1')
            # Queenside
            if board[7][4] == 'wK' and board[7][0] == 'wR' and board[7][1] is None and board[7][2] is None and board[7][3] is None:
                if not is_attacked(7, 4, 'b') and not is_attacked(7, 3, 'b') and not is_attacked(7, 2, 'b'):
                    legal_moves.append('e1c1')
        else:
            # Kingside
            if board[0][4] == 'bK' and board[0][7] == 'bR' and board[0][5] is None and board[0][6] is None:
                if not is_attacked(0, 4, 'w') and not is_attacked(0, 5, 'w') and not is_attacked(0, 6, 'w'):
                    legal_moves.append('e8g8')
            # Queenside
            if board[0][4] == 'bK' and board[0][0] == 'bR' and board[0][1] is None and board[0][2] is None and board[0][3] is None:
                if not is_attacked(0, 4, 'w') and not is_attacked(0, 3, 'w') and not is_attacked(0, 2, 'w'):
                    legal_moves.append('e8c8')
                    
        return legal_moves

    def evaluate():
        score = 0
        for r in range(8):
            for f in range(8):
                p = board[r][f]
                if p:
                    val = PV[p[1]]
                    # Positional value
                    pst_idx = r if p[0] == 'w' else 7 - r
                    pos_val = PST[p[1]][pst_idx][f]
                    
                    if p[0] == 'w':
                        score += val + pos_val
                    else:
                        score -= (val + pos_val)
        return score

    def minimax(depth, alpha, beta, is_maximizing, color):
        # Terminal check or depth limit
        if depth == 0:
            return evaluate()
        
        moves = get_legal_moves(color)
        if not moves:
            # No legal moves -> Checkmate or Stalemate
            king_pos = None
            for r in range(8):
                for f in range(8):
                    if board[r][f] == color+'K':
                        king_pos = (r, f)
                        break
            if is_attacked(king_pos[0], king_pos[1], 'b' if color=='w' else 'w'):
                return -20000 if is_maximizing else 20000 # Checkmate
            return 0 # Stalemate
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                # Make move
                ff, fr = ord(move[0])-97, int(move[1])-1
                tf, tr = ord(move[2])-97, int(move[3])-1
                prom = move[4] if len(move) > 4 else ''
                
                captured = board[tr][tf]
                piece = board[fr][ff]
                new_piece = piece
                if prom: new_piece = color + 'Q'
                
                board[tr][tf] = new_piece
                board[fr][ff] = None
                
                eval_score = minimax(depth-1, alpha, beta, False, 'b' if color=='w' else 'w')
                
                # Undo
                board[fr][ff] = piece
                board[tr][tf] = captured
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                ff, fr = ord(move[0])-97, int(move[1])-1
                tf, tr = ord(move[2])-97, int(move[3])-1
                prom = move[4] if len(move) > 4 else ''
                
                captured = board[tr][tf]
                piece = board[fr][ff]
                new_piece = piece
                if prom: new_piece = color + 'Q'
                
                board[tr][tf] = new_piece
                board[fr][ff] = None
                
                eval_score = minimax(depth-1, alpha, beta, True, 'b' if color=='w' else 'w')
                
                # Undo
                board[fr][ff] = piece
                board[tr][tf] = captured
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Search ---
    legal_moves = get_legal_moves(turn)
    if not legal_moves:
        return "a0a0", memory # No moves, return dummy (game should be over)

    # Move ordering: prioritize captures
    def score_move(m):
        target_sq = m[2:4]
        tr, tf = ord(target_sq[0])-97, int(target_sq[1])-1
        target = board[tr][tf]
        if target: return PV[target[1]] * 10
        return 0
        
    legal_moves.sort(key=score_move, reverse=True)

    best_move = None
    best_val = -float('inf')
    
    # Adaptive depth: depth 3 for smaller node counts, 2 for larger to stay within time
    search_depth = 3 if len(legal_moves) < 25 else 2

    for move in legal_moves:
        ff, fr = ord(move[0])-97, int(move[1])-1
        tf, tr = ord(move[2])-97, int(move[3])-1
        prom = move[4] if len(move) > 4 else ''
        
        captured = board[tr][tf]
        piece = board[fr][ff]
        new_piece = piece
        if prom: new_piece = turn + 'Q'
        
        board[tr][tf] = new_piece
        board[fr][ff] = None
        
        val = minimax(search_depth-1, -float('inf'), float('inf'), False, opponent)
        
        # Undo
        board[fr][ff] = piece
        board[tr][tf] = captured
        
        if val > best_val:
            best_val = val
            best_move = move

    # Fallback to random if search fails or equal
    if best_move is None:
        best_move = random.choice(legal_moves)

    return best_move, memory
