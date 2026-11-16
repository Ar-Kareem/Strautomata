
import sys

# Piece values for evaluation
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-Square Tables (simplified) to encourage good positions
# Scores are from White's perspective (rank 0 is rank 1 on board)
PST = {
    'P': [0]*8 + [0, 0, 0, 0, 0, 0, 0, 0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10, 5, 5, 10, 25, 25, 10, 5, 5, 0, 0, 0, 20, 20, 0, 0, 0, 5, -5, -10, 0, 0, -10, -5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'N': [-50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 0, 0, 0, -20, -40, -30, 0, 10, 15, 15, 10, 0, -30, -30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30, -30, 5, 10, 15, 15, 10, 5, -30, -40, -20, 0, 5, 5, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40, -50],
    'B': [-20, -10, -10, -10, -10, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 10, 10, 5, 0, -10, -10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 10, 10, 10, 10, 0, -10, -10, 10, 10, 10, 10, 10, 10, -10, -10, 5, 0, 0, 0, 0, 5, -10, -20, -10, -10, -10, -10, -10, -10, -20],
    'R': [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, 10, 10, 10, 10, 5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 0, 0, 0, 5, 5, 0, 0, 0],
    'Q': [-20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 5, 5, 5, 0, -10, -5, 0, 5, 5, 5, 5, 0, -5, 0, 0, 5, 5, 5, 5, 0, -5, -10, 5, 5, 5, 5, 5, 0, -10, -10, 0, 5, 0, 0, 0, 0, -10, -20, -10, -10, -5, -5, -10, -10, -20],
    'K': [-30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -20, -30, -30, -40, -40, -30, -30, -20, -10, -20, -20, -20, -20, -20, -20, -10, 20, 20, 0, 0, 0, 0, 20, 20, 20, 30, 10, 0, 0, 10, 30, 20]
}

# Direction vectors
DIRECTIONS = {
    'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
    'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
    'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
    'K': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
}

def sq_to_idx(sq):
    c, r = ord(sq[0]) - ord('a'), int(sq[1]) - 1
    return r * 8 + c

def idx_to_sq(idx):
    return chr(idx % 8 + ord('a')) + str(idx // 8 + 1)

def is_white(piece):
    return piece[0] == 'w'

def get_piece_type(piece):
    return piece[1]

class Board:
    def __init__(self, pieces, to_play):
        self.board = [None] * 64
        self.to_play = to_play
        self.white_turn = to_play == 'white'
        for sq, p in pieces.items():
            self.board[sq_to_idx(sq)] = p
        self.king_sq = {'w': None, 'b': None}
        for i, p in enumerate(self.board):
            if p and p[1] == 'K':
                self.king_sq[p[0]] = i

    def get_moves(self):
        moves = []
        color = 'w' if self.white_turn else 'b'
        enemy = 'b' if self.white_turn else 'w'
        
        for i in range(64):
            p = self.board[i]
            if not p or p[0] != color: continue
            
            pt = p[1]
            r, c = i // 8, i % 8
            
            if pt == 'P':
                step = 1 if self.white_turn else -1
                start_r = 1 if self.white_turn else 6
                prom_r = 7 if self.white_turn else 0
                
                # Forward
                nr = r + step
                if 0 <= nr < 8:
                    ti = nr * 8 + c
                    if not self.board[ti]:
                        if nr == prom_r:
                            for pr in ['q', 'r', 'b', 'n']:
                                moves.append((i, ti, pr))
                        else:
                            moves.append((i, ti, None))
                            # Double step
                            if r == start_r:
                                ti2 = (r + 2*step) * 8 + c
                                if not self.board[ti2]:
                                    moves.append((i, ti2, None))
                
                # Captures
                for dc in [-1, 1]:
                    nc = c + dc
                    if 0 <= nc < 8:
                        ti = nr * 8 + nc
                        target = self.board[ti]
                        if target and target[0] == enemy:
                            if nr == prom_r:
                                for pr in ['q', 'r', 'b', 'n']:
                                    moves.append((i, ti, pr))
                            else:
                                moves.append((i, ti, None))
            
            elif pt == 'N':
                for dr, dc in DIRECTIONS['N']:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        ti = nr * 8 + nc
                        target = self.board[ti]
                        if not target or target[0] == enemy:
                            moves.append((i, ti, None))

            elif pt in ('B', 'R', 'Q'):
                for dr, dc in DIRECTIONS[pt]:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        ti = nr * 8 + nc
                        target = self.board[ti]
                        if not target:
                            moves.append((i, ti, None))
                        elif target[0] == enemy:
                            moves.append((i, ti, None))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc
            
            elif pt == 'K':
                for dr, dc in DIRECTIONS['K']:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        ti = nr * 8 + nc
                        target = self.board[ti]
                        if not target or target[0] == enemy:
                            moves.append((i, ti, None))
                
                # Castling
                # Check if King is on starting square and hasn't moved (implied by position)
                # We assume rights exist if pieces are on initial squares for simplicity
                if self.white_turn and r == 0 and c == 4:
                    # Kingside
                    if self.board[5] is None and self.board[6] is None and self.board[7] == 'wR':
                         if not self.is_attacked(4, enemy) and not self.is_attacked(5, enemy) and not self.is_attacked(6, enemy):
                             moves.append((4, 6, None)) # e1g1
                    # Queenside
                    if self.board[3] is None and self.board[2] is None and self.board[1] is None and self.board[0] == 'wR':
                         if not self.is_attacked(4, enemy) and not self.is_attacked(3, enemy) and not self.is_attacked(2, enemy):
                             moves.append((4, 2, None)) # e1c1
                elif not self.white_turn and r == 7 and c == 4:
                    # Kingside
                    if self.board[61] is None and self.board[62] is None and self.board[63] == 'bR':
                         if not self.is_attacked(60, 'w') and not self.is_attacked(61, 'w') and not self.is_attacked(62, 'w'):
                             moves.append((60, 62, None))
                    # Queenside
                    if self.board[59] is None and self.board[58] is None and self.board[57] is None and self.board[56] == 'bR':
                         if not self.is_attacked(60, 'w') and not self.is_attacked(59, 'w') and not self.is_attacked(58, 'w'):
                             moves.append((60, 58, None))
        
        # Filter illegal moves (leaving king in check)
        legal = []
        for m in moves:
            new_b = self.make_move(m)
            if not new_b.is_attacked(new_b.king_sq[color], enemy):
                legal.append(m)
        return legal

    def is_attacked(self, sq, by_color):
        r, c = sq // 8, sq % 8
        
        # Knight attacks
        for dr, dc in DIRECTIONS['N']:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr * 8 + nc]
                if p and p[0] == by_color and p[1] == 'N':
                    return True
        
        # Pawn attacks
        step = 1 if by_color == 'w' else -1
        for dc in [-1, 1]:
            nc = c + dc
            nr = r - step # Square the attacker would come from
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr * 8 + nc]
                if p and p[0] == by_color and p[1] == 'P':
                    return True
        
        # King attacks
        for dr, dc in DIRECTIONS['K']:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr * 8 + nc]
                if p and p[0] == by_color and p[1] == 'K':
                    return True

        # Sliding pieces
        for dr, dc in DIRECTIONS['Q']:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr * 8 + nc]
                if p:
                    if p[0] == by_color:
                        if p[1] == 'Q': return True
                        if p[1] == 'B' and abs(dr) == 1: return True
                        if p[1] == 'R' and dr == 0: return True
                    break
                nr += dr
                nc += dc
        return False

    def make_move(self, move):
        # Returns a new board state
        new_pieces = {}
        color = 'w' if self.white_turn else 'b'
        enemy = 'b' if self.white_turn else 'w'
        from_i, to_i, prom = move
        from_sq, to_sq = idx_to_sq(from_i), idx_to_sq(to_i)
        
        for i, p in enumerate(self.board):
            if p:
                sq = idx_to_sq(i)
                if i == from_i: continue # Moved piece
                if i == to_i: continue # Captured piece
                new_pieces[sq] = p
        
        moved_p = self.board[from_i]
        pt = moved_p[1]
        
        # Handle Castling Move logic (move the rook too)
        if pt == 'K':
            if abs(from_i - to_i) == 2:
                # Castling
                if to_i == 6: # g1
                    new_pieces['g1'] = moved_p
                    new_pieces['f1'] = self.board[7] # h1 rook
                    del new_pieces['h1']
                elif to_i == 2: # c1
                    new_pieces['c1'] = moved_p
                    new_pieces['d1'] = self.board[0] # a1 rook
                    del new_pieces['a1']
                elif to_i == 62: # g8
                    new_pieces['g8'] = moved_p
                    new_pieces['f8'] = self.board[63]
                    del new_pieces['h8']
                elif to_i == 58: # c8
                    new_pieces['c8'] = moved_p
                    new_pieces['d8'] = self.board[56]
                    del new_pieces['a8']
            else:
                new_pieces[to_sq] = moved_p
        else:
            new_pieces[to_sq] = moved_p
        
        # Handle Promotion
        if prom:
            new_pieces[to_sq] = color + prom.upper()
            
        return Board(new_pieces, 'black' if self.white_turn else 'white')

def evaluate(board):
    score = 0
    for i, p in enumerate(board.board):
        if not p: continue
        val = PIECE_VALUES[p[1]]
        # Positional bonus
        r = i // 8
        if p[0] == 'w':
            # White wants higher ranks (indices)
            val += PST[p[1]][i]
            score += val
        else:
            # Black wants lower ranks (mirrored)
            # Mirror index: (7-r)*8 + c
            mir_i = (7 - r) * 8 + (i % 8)
            val += PST[p[1]][mir_i]
            score -= val
    return score if board.white_turn else -score

def alphabeta(board, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(board), None
    
    moves = board.get_moves()
    
    if not moves:
        # No legal moves: Checkmate or Stalemate
        color = 'w' if board.white_turn else 'b'
        enemy = 'b' if board.white_turn else 'w'
        if board.is_attacked(board.king_sq[color], enemy):
            return -99999 - depth, None # Checkmate (bad for current player)
        return 0, None # Stalemate
    
    best_move = None
    
    # Move ordering: prioritize captures and checks
    def score_move(m):
        val = 0
        to_p = board.board[m[1]]
        if to_p: val += PIECE_VALUES[to_p[1]] * 10 # Capture
        if m[2]: val += 800 # Promotion
        return val
    
    moves.sort(key=score_move, reverse=True)
    
    if maximizing:
        max_eval = -float('inf')
        for m in moves:
            new_board = board.make_move(m)
            eval_s, _ = alphabeta(new_board, depth-1, alpha, beta, False)
            if eval_s > max_eval:
                max_eval = eval_s
                best_move = m
            alpha = max(alpha, eval_s)
            if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for m in moves:
            new_board = board.make_move(m)
            eval_s, _ = alphabeta(new_board, depth-1, alpha, beta, True)
            if eval_s < min_eval:
                min_eval = eval_s
                best_move = m
            beta = min(beta, eval_s)
            if beta <= alpha: break
        return min_eval, best_move

def policy(pieces: dict[str, str], to_play: str, legal_moves=None) -> str:
    # Use optional legal_moves if provided to verify our generator or use if faster
    # But we rely on our internal generator for the search tree
    
    board = Board(pieces, to_play)
    
    # Start search
    # Depth 3 is a good balance for 1s constraint
    _, best_move = alphabeta(board, 3, -float('inf'), float('inf'), True)
    
    if best_move:
        from_sq = idx_to_sq(best_move[0])
        to_sq = idx_to_sq(best_move[1])
        promo = best_move[2] if best_move[2] else ''
        return from_sq + to_sq + promo
    else:
        # Fallback: if search failed or no moves found (shouldn't happen if game not over)
        # If we have legal_moves provided, return first one as safety
        if legal_moves:
            return legal_moves[0]
        # If we calculated moves ourselves but somehow search failed:
        moves = board.get_moves()
        if moves:
            m = moves[0]
            return idx_to_sq(m[0]) + idx_to_sq(m[1]) + (m[2] if m[2] else '')
        return ""
