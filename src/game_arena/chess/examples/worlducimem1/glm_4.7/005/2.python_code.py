
import random
import numpy as np

# --- Constants and Configuration ---
# Piece encoding: Empty=0, Pawn=1, Knight=2, Bishop=3, Rook=4, Queen=5, King=6
# White pieces are positive, Black pieces are negative.
PIECE_INDICES = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
COLORS = {'w': 1, 'b': -1}

# Material Values
MAT_VALUES = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 20000}

# Piece-Square Tables (PST) - simplified centered on index 0..63
# Values are for White. Black is mirrored.
def get_pst():
    # Center control biases
    center_pawn = [0, 0, 0, 0, 0, 0, 0, 0,
                   50, 50, 50, 50, 50, 50, 50, 50,
                   10, 10, 20, 30, 30, 20, 10, 10,
                    5,  5, 10, 25, 25, 10,  5,  5,
                    0,  0,  0, 20, 20,  0,  0,  0,
                    5, -5,-10,  0,  0,-10, -5,  5,
                    5, 10, 10,-20,-20, 10, 10,  5,
                    0,  0,  0,  0,  0,  0,  0,  0]
    
    knight = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    bishop = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    # Midgame king preference
    king = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20
    ]

    return {1: center_pawn, 2: knight, 3: bishop, 4: np.zeros(64), 5: np.zeros(64), 6: king}

PST = get_pst()

# --- Helper Functions ---
def sq_to_idx(sq):
    """ 'a1' -> 0, 'h8' -> 63 """
    return (ord(sq[0]) - ord('a')) + 8 * (int(sq[1]) - 1)

def idx_to_sq(idx):
    """ 0 -> 'a1', 63 -> 'h8' """
    return chr(idx % 8 + ord('a')) + str(idx // 8 + 1)

# --- Move Generation Engine ---
class Engine:
    def __init__(self):
        self.board = np.zeros(64, dtype=int)
        self.turn = 1 # 1 for white, -1 for black
        self.castling = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.ep = None # En passant target square index
        self.history = []
        
    def set_state(self, pieces, to_play, memory):
        self.turn = 1 if to_play == 'white' else -1
        self.board.fill(0)
        
        # Parse pieces
        for sq, code in pieces.items():
            color_char = code[0]
            type_char = code[1]
            val = PIECE_INDICES[type_char] * COLORS[color_char]
            self.board[sq_to_idx(sq)] = val
            
        # Restore state from memory
        if 'castling' in memory:
            self.castling = memory['castling']
        if 'ep' in memory:
            self.ep = memory['ep']
            
        # Validate castling rights based on current board positions
        # (If king or rook moved, rights are lost. If pieces are missing, rights lost)
        white_king = 4 if self.turn == 1 else -4 # e1 index is 4? No. a1=0. e1=4. e8=60.
        # Wait, a1=0, e1=4. h1=7.
        # White King e1 (4), Rooks a1 (0), h1 (7)
        # Black King e8 (60), Rooks a8 (56), h8 (63)
        
        if self.castling['K'] and (self.board[4] != 6 or self.board[7] != 4): self.castling['K'] = False
        if self.castling['Q'] and (self.board[4] != 6 or self.board[0] != 4): self.castling['Q'] = False
        if self.castling['k'] and (self.board[60] != -6 or self.board[63] != -4): self.castling['k'] = False
        if self.castling['q'] and (self.board[60] != -6 or self.board[56] != -4): self.castling['q'] = False

    def is_attacked(self, sq_idx, attacker_color):
        # Check pawn attacks
        pawn_dir = -1 if attacker_color == 1 else 1
        start_file = sq_idx % 8
        # Pawn left capture
        if start_file > 0:
            p_idx = sq_idx + pawn_dir * 8 - 1
            if 0 <= p_idx < 64:
                if self.board[p_idx] == 1 * attacker_color: return True
        # Pawn right capture
        if start_file < 7:
            p_idx = sq_idx + pawn_dir * 8 + 1
            if 0 <= p_idx < 64:
                if self.board[p_idx] == 1 * attacker_color: return True
                
        # Knight attacks
        knight_moves = [6, 10, 15, 17, -6, -10, -15, -17] # Approx offsets
        for off in knight_moves:
            target = sq_idx + off
            if 0 <= target < 64:
                if abs(target % 8 - start_file) <= 2: # simple wrap check
                    if self.board[target] == 2 * attacker_color: return True
        
        # King attacks (for detecting king contact)
        for off in [-9, -8, -7, -1, 1, 7, 8, 9]:
            target = sq_idx + off
            if 0 <= target < 64:
                 if abs(target % 8 - start_file) <= 1:
                    if self.board[target] == 6 * attacker_color: return True

        # Sliding attacks (Rook/Queen)
        directions = [-8, 8, -1, 1]
        for d in directions:
            curr = sq_idx + d
            while 0 <= curr < 64 and abs((curr-d)%8 - curr%8) <= 1: # check file wrap
                piece = self.board[curr]
                if piece != 0:
                    if piece == 4 * attacker_color or piece == 5 * attacker_color: return True
                    break
                curr += d
                
        # Sliding attacks (Bishop/Queen)
        directions = [-9, -7, 7, 9]
        for d in directions:
            curr = sq_idx + d
            while 0 <= curr < 64 and abs((curr-d)%8 - curr%8) <= 1: # check file wrap
                piece = self.board[curr]
                if piece != 0:
                    if piece == 3 * attacker_color or piece == 5 * attacker_color: return True
                    break
                curr += d
                
        return False

    def get_legal_moves(self):
        moves = []
        # Find pieces
        for i in range(64):
            piece = self.board[i]
            if piece == 0: continue
            if (piece > 0 and self.turn == 1) or (piece < 0 and self.turn == -1):
                p_type = abs(piece)
                file = i % 8
                rank = i // 8
                
                # Pawn
                if p_type == 1:
                    direction = 1 if self.turn == 1 else -1
                    start_rank = 1 if self.turn == 1 else 6
                    
                    # Push
                    forward = i + direction * 8
                    if 0 <= forward < 64 and self.board[forward] == 0:
                        # Promotion check
                        if (rank == 6 and self.turn == 1) or (rank == 1 and self.turn == -1):
                            for prom in ['q', 'r', 'b', 'n']: # Always Q is best, but need variety?
                                moves.append((i, forward, prom))
                        else:
                            moves.append((i, forward, ''))
                            
                            # Double Push
                            if rank == start_rank:
                                double = i + direction * 16
                                if self.board[double] == 0:
                                    moves.append((i, double, ''))
                    
                    # Captures
                    for cap_off in [-1, 1]:
                        target = i + direction * 8 + cap_off
                        if 0 <= target < 64 and abs(target % 8 - file) == 1:
                            target_piece = self.board[target]
                            # Normal capture
                            if target_piece != 0 and (target_piece > 0) != (piece > 0):
                                if (rank == 6 and self.turn == 1) or (rank == 1 and self.turn == -1):
                                    for prom in ['q', 'r', 'b', 'n']:
                                        moves.append((i, target, prom))
                                else:
                                    moves.append((i, target, ''))
                            # En Passant
                            if self.ep is not None and target == self.ep:
                                moves.append((i, target, ''))

                # Knight
                elif p_type == 2:
                    offsets = [6, 10, 15, 17, -6, -10, -15, -17]
                    for off in offsets:
                        target = i + off
                        if 0 <= target < 64:
                            if abs(target % 8 - file) <= 2:
                                t_piece = self.board[target]
                                if t_piece == 0 or (t_piece > 0) != (piece > 0):
                                    moves.append((i, target, ''))

                # Bishop
                elif p_type == 3:
                    offsets = [-9, -7, 7, 9]
                    for off in offsets:
                        curr = i + off
                        while 0 <= curr < 64 and abs(curr % 8 - (curr-off)%8) <= 1:
                            t_piece = self.board[curr]
                            if t_piece == 0:
                                moves.append((i, curr, ''))
                            else:
                                if (t_piece > 0) != (piece > 0):
                                    moves.append((i, curr, ''))
                                break
                            curr += off
                            
                # Rook
                elif p_type == 4:
                    offsets = [-8, 8, -1, 1]
                    for off in offsets:
                        curr = i + off
                        while 0 <= curr < 64 and abs(curr % 8 - (curr-off)%8) <= 1:
                            t_piece = self.board[curr]
                            if t_piece == 0:
                                moves.append((i, curr, ''))
                            else:
                                if (t_piece > 0) != (piece > 0):
                                    moves.append((i, curr, ''))
                                break
                            curr += off

                # Queen
                elif p_type == 5:
                    offsets = [-9, -7, 7, 9, -8, 8, -1, 1]
                    for off in offsets:
                        curr = i + off
                        while 0 <= curr < 64 and abs(curr % 8 - (curr-off)%8) <= 1:
                            t_piece = self.board[curr]
                            if t_piece == 0:
                                moves.append((i, curr, ''))
                            else:
                                if (t_piece > 0) != (piece > 0):
                                    moves.append((i, curr, ''))
                                break
                            curr += off

                # King
                elif p_type == 6:
                    offsets = [-9, -8, -7, -1, 1, 7, 8, 9]
                    for off in offsets:
                        target = i + off
                        if 0 <= target < 64 and abs(target % 8 - file) <= 1:
                            t_piece = self.board[target]
                            if t_piece == 0 or (t_piece > 0) != (piece > 0):
                                moves.append((i, target, ''))
                    
                    # Castling
                    # White
                    if self.turn == 1:
                        if i == 4 and self.castling['K']:
                            if self.board[5] == 0 and self.board[6] == 0:
                                if not self.is_attacked(4, -1) and not self.is_attacked(5, -1) and not self.is_attacked(6, -1):
                                    moves.append((4, 6, ''))
                        if i == 4 and self.castling['Q']:
                            if self.board[3] == 0 and self.board[2] == 0 and self.board[1] == 0:
                                if not self.is_attacked(4, -1) and not self.is_attacked(3, -1) and not self.is_attacked(2, -1):
                                    moves.append((4, 2, ''))
                    # Black
                    else:
                        if i == 60 and self.castling['k']:
                            if self.board[61] == 0 and self.board[62] == 0:
                                if not self.is_attacked(60, 1) and not self.is_attacked(61, 1) and not self.is_attacked(62, 1):
                                    moves.append((60, 62, ''))
                        if i == 60 and self.castling['q']:
                            if self.board[59] == 0 and self.board[58] == 0 and self.board[57] == 0:
                                if not self.is_attacked(60, 1) and not self.is_attacked(59, 1) and not self.is_attacked(58, 1):
                                    moves.append((60, 58, ''))

        # Filter illegal moves (king in check)
        legal_moves = []
        for f, t, prom in moves:
            # Apply move
            captured = self.board[t]
            moved_piece = self.board[f]
            
            # Handle En Passant capture
            ep_cap_idx = -1
            if abs(moved_piece) == 1 and t == self.ep:
                # Remove the pawn behind
                ep_dir = -1 if self.turn == 1 else 1
                ep_cap_idx = t + ep_dir * 8
                captured = self.board[ep_cap_idx]
                self.board[ep_cap_idx] = 0
            
            self.board[f] = 0
            self.board[t] = moved_piece
            
            # Promotion
            if prom:
                prom_piece = PIECE_INDICES[prom.upper()] * self.turn
                self.board[t] = prom_piece
                
            # Find King
            king_idx = np.where(self.board == 6 * self.turn)[0]
            if len(king_idx) == 0:
                # Should not happen
                is_legal = False
            else:
                if not self.is_attacked(king_idx[0], -self.turn):
                    legal_moves.append((f, t, prom))
            
            # Undo move
            if prom:
                self.board[t] = moved_piece
            else:
                self.board[t] = captured # if ep, this puts 0 there, handled below?
                
            self.board[f] = moved_piece
            
            if ep_cap_idx != -1:
                self.board[ep_cap_idx] = captured # restore captured pawn
                self.board[t] = 0 # ep destination was 0
        
        return legal_moves

    def evaluate(self):
        # Material + PST
        score = 0
        for i in range(64):
            p = self.board[i]
            if p == 0: continue
            ptype = abs(p)
            val = MAT_VALUES[ptype]
            
            # Positional value
            pst_idx = i if p > 0 else 63 - i
            pos_val = PST[ptype][pst_idx]
            
            if p > 0:
                score += (val + pos_val)
            else:
                score -= (val + pos_val)
        return score

    def minimax(self, depth, alpha, beta, is_maximizing):
        if depth == 0:
            return self.evaluate()
        
        moves = self.get_legal_moves()
        if not moves:
            if self.is_attacked(np.where(self.board == 6 * self.turn)[0][0], -self.turn):
                return -100000 if is_maximizing else 100000
            else:
                return 0 # Stalemate
        
        # Sort moves for pruning (captures first)
        moves.sort(key=lambda m: abs(self.board[m[1]]), reverse=True)
        
        if is_maximizing:
            max_eval = -float('inf')
            for f, t, prom in moves:
                # Do move
                moved = self.board[f]
                captured = self.board[t]
                
                # EP
                ep_cap = -1
                if abs(moved)==1 and t == self.ep:
                     ep_dir = -1 if self.turn == 1 else 1
                     ep_cap = t + ep_dir * 8
                     self.board[ep_cap] = 0
                
                self.board[f] = 0
                self.board[t] = moved if not prom else (PIECE_INDICES[prom.upper()] * 1)
                
                self.turn = -1
                eval = self.minimax(depth - 1, alpha, beta, False)
                
                # Undo
                self.board[f] = moved
                self.board[t] = captured
                if ep_cap != -1: self.board[ep_cap] = -1 # simplistic restore, color doesnt matter for empty check
                if ep_cap != -1: self.board[ep_cap] = 1 * -1 # Wait, captured was -1 for black pawn
                # Actually, captured logic for EP is messy without 'captured' var for the ep piece
                # Correct Undo:
                if ep_cap != -1:
                     # We know the piece captured was a pawn of opposite color
                     self.board[ep_cap] = -1 * self.turn # Since turn flipped, this is original color
                
                self.turn = 1
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for f, t, prom in moves:
                moved = self.board[f]
                captured = self.board[t]
                
                ep_cap = -1
                if abs(moved)==1 and t == self.ep:
                     ep_dir = -1 if self.turn == 1 else 1
                     ep_cap = t + ep_dir * 8
                     self.board[ep_cap] = 0
                
                self.board[f] = 0
                self.board[t] = moved if not prom else (PIECE_INDICES[prom.upper()] * -1)
                
                self.turn = 1
                eval = self.minimax(depth - 1, alpha, beta, True)
                
                self.board[f] = moved
                self.board[t] = captured
                if ep_cap != -1: self.board[ep_cap] = 1 * self.turn 

                self.turn = -1
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self):
        moves = self.get_legal_moves()
        if not moves:
            return None
        
        # Shuffle to add variety if evals equal
        random.shuffle(moves)
        
        best_move = None
        best_val = -float('inf')
        
        # Depth 3 search
        for f, t, prom in moves:
            moved = self.board[f]
            captured = self.board[t]
            
            ep_cap = -1
            if abs(moved)==1 and t == self.ep:
                 ep_dir = -1 if self.turn == 1 else 1
                 ep_cap = t + ep_dir * 8
                 # Store actual captured for ep (it's 0 on t, but pawn behind)
                 ep_captured_piece = self.board[ep_cap]
                 self.board[ep_cap] = 0
            
            self.board[f] = 0
            self.board[t] = moved if not prom else (PIECE_INDICES[prom.upper()] * self.turn)
            
            self.turn = -self.turn
            val = self.minimax(2, -float('inf'), float('inf'), self.turn == 1)
            self.turn = -self.turn
            
            self.board[f] = moved
            self.board[t] = captured
            if ep_cap != -1:
                self.board[ep_cap] = ep_captured_piece
            
            if val > best_val:
                best_val = val
                best_move = (f, t, prom)
        
        return best_move

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    eng = Engine()
    eng.set_state(pieces, to_play, memory)
    
    best = eng.get_best_move()
    
    if not best:
        # Should not happen in valid game, but fallback
        return "", memory
    
    f, t, prom = best
    move_str = idx_to_sq(f) + idx_to_sq(t) + prom
    
    # Update memory for next turn (castling/EP)
    # Note: This is a simplified state update. 
    # A full engine would apply the move to the state struct.
    # Here we just update what we can infer.
    memory['castling'] = eng.castling
    
    # Update En Passant
    new_ep = None
    piece = eng.board[f]
    if abs(piece) == 1: # Pawn
        if abs(t - f) == 16:
            new_ep = (f + t) // 2
    memory['ep'] = new_ep
    
    return move_str, memory
