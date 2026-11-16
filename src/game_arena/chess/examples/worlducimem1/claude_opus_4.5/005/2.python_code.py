
import copy

def policy(pieces, to_play, memory):
    board = Board(pieces, to_play, memory)
    legal_moves = board.get_legal_moves()
    
    if not legal_moves:
        return ('0000', memory)
    
    if len(legal_moves) == 1:
        return (legal_moves[0], memory)
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for depth in range(1, 4):
        move, score = board.search(depth)
        if move:
            best_move = move
            best_score = score
    
    new_memory = {'last_move': best_move}
    return (best_move, new_memory)

class Board:
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    def __init__(self, pieces, to_play, memory):
        self.pieces = pieces.copy()
        self.to_play = 'w' if to_play == 'white' else 'b'
        self.memory = memory
        self.castling = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant = None
    
    def get_legal_moves(self):
        moves = []
        my_color = self.to_play
        
        for sq, piece in self.pieces.items():
            if piece[0] == my_color:
                moves.extend(self.get_piece_moves(sq, piece))
        
        legal = []
        for move in moves:
            if self.is_legal(move):
                legal.append(move)
        return legal
    
    def sq_to_idx(self, sq):
        return ord(sq[0]) - ord('a'), int(sq[1]) - 1
    
    def idx_to_sq(self, f, r):
        if 0 <= f < 8 and 0 <= r < 8:
            return chr(ord('a') + f) + str(r + 1)
        return None
    
    def get_piece_moves(self, sq, piece):
        moves = []
        f, r = self.sq_to_idx(sq)
        color, ptype = piece[0], piece[1]
        
        if ptype == 'P':
            moves.extend(self.get_pawn_moves(sq, color))
        elif ptype == 'N':
            moves.extend(self.get_knight_moves(sq, color))
        elif ptype == 'B':
            moves.extend(self.get_bishop_moves(sq, color))
        elif ptype == 'R':
            moves.extend(self.get_rook_moves(sq, color))
        elif ptype == 'Q':
            moves.extend(self.get_queen_moves(sq, color))
        elif ptype == 'K':
            moves.extend(self.get_king_moves(sq, color))
        
        return moves
    
    def get_pawn_moves(self, sq, color):
        moves = []
        f, r = self.sq_to_idx(sq)
        direction = 1 if color == 'w' else -1
        start_rank = 1 if color == 'w' else 6
        promo_rank = 7 if color == 'w' else 0
        
        # Forward move
        new_sq = self.idx_to_sq(f, r + direction)
        if new_sq and new_sq not in self.pieces:
            if r + direction == promo_rank:
                for p in ['q', 'r', 'b', 'n']:
                    moves.append(sq + new_sq + p)
            else:
                moves.append(sq + new_sq)
                # Double move
                if r == start_rank:
                    new_sq2 = self.idx_to_sq(f, r + 2 * direction)
                    if new_sq2 and new_sq2 not in self.pieces:
                        moves.append(sq + new_sq2)
        
        # Captures
        for df in [-1, 1]:
            cap_sq = self.idx_to_sq(f + df, r + direction)
            if cap_sq:
                if cap_sq in self.pieces and self.pieces[cap_sq][0] != color:
                    if r + direction == promo_rank:
                        for p in ['q', 'r', 'b', 'n']:
                            moves.append(sq + cap_sq + p)
                    else:
                        moves.append(sq + cap_sq)
        
        return moves
    
    def get_knight_moves(self, sq, color):
        moves = []
        f, r = self.sq_to_idx(sq)
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for df, dr in offsets:
            new_sq = self.idx_to_sq(f + df, r + dr)
            if new_sq:
                if new_sq not in self.pieces or self.pieces[new_sq][0] != color:
                    moves.append(sq + new_sq)
        return moves
    
    def get_sliding_moves(self, sq, color, directions):
        moves = []
        f, r = self.sq_to_idx(sq)
        for df, dr in directions:
            nf, nr = f + df, r + dr
            while True:
                new_sq = self.idx_to_sq(nf, nr)
                if not new_sq:
                    break
                if new_sq in self.pieces:
                    if self.pieces[new_sq][0] != color:
                        moves.append(sq + new_sq)
                    break
                moves.append(sq + new_sq)
                nf, nr = nf + df, nr + dr
        return moves
    
    def get_bishop_moves(self, sq, color):
        return self.get_sliding_moves(sq, color, [(-1,-1),(-1,1),(1,-1),(1,1)])
    
    def get_rook_moves(self, sq, color):
        return self.get_sliding_moves(sq, color, [(-1,0),(1,0),(0,-1),(0,1)])
    
    def get_queen_moves(self, sq, color):
        return self.get_bishop_moves(sq, color) + self.get_rook_moves(sq, color)
    
    def get_king_moves(self, sq, color):
        moves = []
        f, r = self.sq_to_idx(sq)
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                new_sq = self.idx_to_sq(f + df, r + dr)
                if new_sq:
                    if new_sq not in self.pieces or self.pieces[new_sq][0] != color:
                        moves.append(sq + new_sq)
        
        # Castling
        if color == 'w' and sq == 'e1':
            if self.pieces.get('h1') == 'wR' and 'f1' not in self.pieces and 'g1' not in self.pieces:
                moves.append('e1g1')
            if self.pieces.get('a1') == 'wR' and 'b1' not in self.pieces and 'c1' not in self.pieces and 'd1' not in self.pieces:
                moves.append('e1c1')
        elif color == 'b' and sq == 'e8':
            if self.pieces.get('h8') == 'bR' and 'f8' not in self.pieces and 'g8' not in self.pieces:
                moves.append('e8g8')
            if self.pieces.get('a8') == 'bR' and 'b8' not in self.pieces and 'c8' not in self.pieces and 'd8' not in self.pieces:
                moves.append('e8c8')
        
        return moves
    
    def is_attacked(self, sq, by_color):
        for s, p in self.pieces.items():
            if p[0] == by_color:
                moves = self.get_piece_moves(s, p)
                for m in moves:
                    if m[2:4] == sq:
                        return True
        return False
    
    def find_king(self, color):
        for sq, p in self.pieces.items():
            if p == color + 'K':
                return sq
        return None
    
    def is_legal(self, move):
        new_board = self.make_move(move)
        king_sq = new_board.find_king(self.to_play)
        if not king_sq:
            return False
        opp = 'b' if self.to_play == 'w' else 'w'
        return not new_board.is_attacked(king_sq, opp)
    
    def make_move(self, move):
        new_pieces = self.pieces.copy()
        from_sq, to_sq = move[:2], move[2:4]
        piece = new_pieces.get(from_sq)
        
        if not piece:
            return Board(new_pieces, 'b' if self.to_play == 'w' else 'w', self.memory)
        
        del new_pieces[from_sq]
        
        # Promotion
        if len(move) == 5:
            new_pieces[to_sq] = piece[0] + move[4].upper()
        else:
            new_pieces[to_sq] = piece
        
        # Castling rook move
        if piece[1] == 'K':
            if move == 'e1g1':
                if 'h1' in new_pieces:
                    del new_pieces['h1']
                new_pieces['f1'] = 'wR'
            elif move == 'e1c1':
                if 'a1' in new_pieces:
                    del new_pieces['a1']
                new_pieces['d1'] = 'wR'
            elif move == 'e8g8':
                if 'h8' in new_pieces:
                    del new_pieces['h8']
                new_pieces['f8'] = 'bR'
            elif move == 'e8c8':
                if 'a8' in new_pieces:
                    del new_pieces['a8']
                new_pieces['d8'] = 'bR'
        
        new_to_play = 'b' if self.to_play == 'w' else 'w'
        return Board(new_pieces, 'white' if new_to_play == 'w' else 'black', self.memory)
    
    def evaluate(self):
        score = 0
        for sq, p in self.pieces.items():
            val = self.PIECE_VALUES.get(p[1], 0)
            if p[0] == 'w':
                score += val
            else:
                score -= val
        
        if self.to_play == 'b':
            score = -score
        return score
    
    def search(self, depth):
        return self.alphabeta(depth, float('-inf'), float('inf'), True)
    
    def alphabeta(self, depth, alpha, beta, maximizing):
        if depth == 0:
            return None, self.evaluate()
        
        moves = self.get_legal_moves()
        if not moves:
            king_sq = self.find_king(self.to_play)
            opp = 'b' if self.to_play == 'w' else 'w'
            if king_sq and self.is_attacked(king_sq, opp):
                return None, -100000 + (3 - depth)
            return None, 0
        
        # Move ordering
        def score_move(m):
            s = 0
            if m[2:4] in self.pieces:
                s += 10
            return -s
        moves.sort(key=score_move)
        
        best_move = moves[0]
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                new_board = self.make_move(move)
                _, eval_score = new_board.alphabeta(depth - 1, alpha, beta, False)
                eval_score = -eval_score
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return best_move, max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = self.make_move(move)
                _, eval_score = new_board.alphabeta(depth - 1, alpha, beta, True)
                eval_score = -eval_score
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_move, min_eval
