
import time

# --- Constants & Configuration ---
# Board representation: 64 squares, 0=a1, 7=h1, ... 63=h8
EMPTY = 0
# Use 1=White, -1=Black for colors
COLOR_W = 1
COLOR_B = -1

# Piece types (values for encoding)
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6

# Piece Values for Evaluation
PIECE_VALS = {P: 100, N: 320, B: 330, R: 500, Q: 900, K: 20000}

# Piece-Square Tables (From White's perspective; mirrored for Black)
# Defined as 64-length arrays (0=a1 to 63=h8)
PST = {
    P: [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    N: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    B: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    R: [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         5, 10, 10, 10, 10, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    Q: [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    K: [
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

def parse_sq(s):
    # 'e4' -> index
    f, r = s[0], s[1:]
    return (ord(f) - ord('a')) + (int(r) - 1) * 8

def to_sq(idx):
    # index -> 'e4'
    return f"{chr((idx % 8) + ord('a'))}{str((idx // 8) + 1)}"

class Board:
    def __init__(self):
        self.squares = [0] * 64
        self.turn = COLOR_W

    def from_dict(self, pieces, to_play):
        self.squares = [0] * 64
        self.turn = COLOR_W if to_play == 'white' else COLOR_B
        mapper = {'P': P, 'N': N, 'B': B, 'R': R, 'Q': Q, 'K': K}
        for sq, code in pieces.items():
            color = COLOR_W if code[0] == 'w' else COLOR_B
            ptype = mapper[code[1]]
            idx = parse_sq(sq)
            self.squares[idx] = color * ptype

    def get_king_sq(self, color):
        val = color * K
        for i in range(64):
            if self.squares[i] == val:
                return i
        return -1

    def is_attacked(self, sq, by_color):
        r, c = sq // 8, sq % 8
        # Pawn attacks
        # If by_color matches board orientation:
        # White (1) attacks from r-1, Black (-1) attacks from r+1
        p_row_offset = 1 if by_color == COLOR_W else -1
        # The enemy pawn is at r - p_row_offset
        pr = r - p_row_offset
        if 0 <= pr < 8:
            for dc in [-1, 1]:
                if 0 <= c + dc < 8:
                    idx = pr * 8 + (c + dc)
                    if self.squares[idx] == by_color * P:
                        return True
        
        # Knight attacks
        knights = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knights:
            if 0 <= r + dr < 8 and 0 <= c + dc < 8:
                if self.squares[(r+dr)*8 + (c+dc)] == by_color * N:
                    return True
        
        # Slider attacks (B, R, Q)
        orth = [(1,0), (-1,0), (0,1), (0,-1)]
        diag = [(1,1), (1,-1), (-1,1), (-1,-1)]
        for dirs, types in [(orth, [R, Q]), (diag, [B, Q])]:
            for dr, dc in dirs:
                cr, cc = r + dr, c + dc
                while 0 <= cr < 8 and 0 <= cc < 8:
                    idx = cr*8 + cc
                    occ = self.squares[idx]
                    if occ != 0:
                        if (occ > 0) == (by_color > 0):
                            if abs(occ) in types:
                                return True
                        break
                    cr += dr
                    cc += dc
        
        # King attacks
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if not (dr == 0 and dc == 0):
                    if 0 <= r+dr < 8 and 0 <= c+dc < 8:
                        if self.squares[(r+dr)*8 + c+dc] == by_color * K:
                            return True
        return False

    def generate_moves(self):
        moves = []
        is_white = (self.turn == COLOR_W)
        
        for r in range(8):
            for c in range(8):
                idx = r*8 + c
                piece = self.squares[idx]
                if piece == 0 or ((piece > 0) != is_white):
                    continue
                
                pt = abs(piece)
                targets = [] # (tr, tc, promotion)

                if pt == P:
                    dr = 1 if is_white else -1
                    # Push
                    fr, fc = r + dr, c
                    if 0 <= fr < 8 and self.squares[fr*8 + fc] == 0:
                        if fr == 0 or fr == 7:
                            for prom in ['q', 'r', 'b', 'n']:
                                targets.append((fr, fc, prom))
                        else:
                            targets.append((fr, fc, None))
                            # Double push
                            start = 1 if is_white else 6
                            if r == start:
                                fr2 = r + 2*dr
                                if self.squares[fr2*8 + fc] == 0:
                                    targets.append((fr2, fc, None))
                    # Capture
                    for dc in [-1, 1]:
                        fr, fc = r + dr, c + dc
                        if 0 <= fr < 8 and 0 <= fc < 8:
                            occ = self.squares[fr*8 + fc]
                            if occ != 0 and ((occ > 0) != is_white):
                                if fr == 0 or fr == 7:
                                    for prom in ['q', 'r', 'b', 'n']:
                                        targets.append((fr, fc, prom))
                                else:
                                    targets.append((fr, fc, None))
                
                elif pt == N:
                    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                    for dr, dc in offsets:
                        tr, tc = r + dr, c + dc
                        if 0 <= tr < 8 and 0 <= tc < 8:
                            occ = self.squares[tr*8 + tc]
                            if occ == 0 or ((occ > 0) != is_white):
                                targets.append((tr, tc, None))
                
                elif pt == K:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            tr, tc = r + dr, c + dc
                            if 0 <= tr < 8 and 0 <= tc < 8:
                                occ = self.squares[tr*8 + tc]
                                if occ == 0 or ((occ > 0) != is_white):
                                    targets.append((tr, tc, None))
                
                else: # B, R, Q
                    dirs = []
                    if pt in [B, Q]: dirs.extend([(1,1),(1,-1),(-1,1),(-1,-1)])
                    if pt in [R, Q]: dirs.extend([(1,0),(-1,0),(0,1),(0,-1)])
                    
                    for dr, dc in dirs:
                        tr, tc = r + dr, c + dc
                        while 0 <= tr < 8 and 0 <= tc < 8:
                            occ = self.squares[tr*8 + tc]
                            if occ == 0:
                                targets.append((tr, tc, None))
                            else:
                                if (occ > 0) != is_white:
                                    targets.append((tr, tc, None))
                                break
                            tr += dr
                            tc += dc

                # Validate Moves
                src_pos = to_sq(idx)
                for tr, tc, prom in targets:
                    dst_idx = tr*8 + tc
                    orig_dst = self.squares[dst_idx]
                    
                    # Apply
                    if prom:
                        prom_map = {'q': Q, 'n': N, 'r': R, 'b': B}
                        val = (1 if is_white else -1) * prom_map[prom]
                    else:
                        val = piece
                    
                    self.squares[idx] = 0
                    self.squares[dst_idx] = val
                    
                    # Check King
                    k_sq = self.get_king_sq(COLOR_W if is_white else COLOR_B)
                    if not self.is_attacked(k_sq, COLOR_B if is_white else COLOR_W):
                        move_str = src_pos + to_sq(dst_idx) + (prom if prom else "")
                        moves.append(move_str)
                    
                    # Undo
                    self.squares[idx] = piece
                    self.squares[dst_idx] = orig_dst
        return moves

    def evaluate(self):
        score = 0
        for i in range(64):
            p = self.squares[i]
            if p == 0: continue
            pt = abs(p)
            val = PIECE_VALS[pt]
            if p > 0:
                score += val + PST[pt][i]
            else:
                score -= (val + PST[pt][i ^ 56]) # Mirror rank
        return score if self.turn == COLOR_W else -score

    def clone_and_move(self, move_str):
        nb = Board()
        nb.squares = self.squares[:]
        nb.turn = -self.turn
        
        src = parse_sq(move_str[:2])
        dst = parse_sq(move_str[2:4])
        prom = move_str[4] if len(move_str)>4 else None
        
        p = nb.squares[src]
        nb.squares[src] = 0
        if prom:
            prom_map = {'q': Q, 'n': N, 'r': R, 'b': B}
            nb.squares[dst] = (1 if p > 0 else -1) * prom_map[prom]
        else:
            nb.squares[dst] = p
        return nb

def policy(pieces: dict[str, str], to_play: str) -> str:
    start_time = time.time()
    b = Board()
    b.from_dict(pieces, to_play)
    
    legal_moves = b.generate_moves()
    if not legal_moves:
        return "0000" # Disqualified / Mate, but must return a string

    # Helper for sorting
    def move_prio(m):
        dst = parse_sq(m[2:4])
        cap = 10 if b.squares[dst] != 0 else 0
        prom = 5 if len(m) > 4 else 0
        return cap + prom
    
    legal_moves.sort(key=move_prio, reverse=True)
    best_move = legal_moves[0]
    
    nodes_visited = 0

    def alphabeta(board, depth, alpha, beta, maximizing):
        nonlocal nodes_visited
        nodes_visited += 1
        if nodes_visited % 500 == 0:
            if time.time() - start_time > 0.85:
                raise TimeoutError

        if depth == 0:
            return board.evaluate()

        moves = board.generate_moves()
        if not moves: # Mate or Stalemate logic
            king_sq = board.get_king_sq(board.turn)
            opp = COLOR_B if board.turn == COLOR_W else COLOR_W
            if board.is_attacked(king_sq, opp):
                return -100000 + (100 - depth) # Checkmate detection
            return 0 # Stalemate

        moves.sort(key=lambda m: 10 if board.squares[parse_sq(m[2:4])] != 0 else 0, reverse=True)

        if maximizing:
            value = -float('inf')
            for m in moves:
                nb = board.clone_and_move(m)
                value = max(value, alphabeta(nb, depth-1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta: break
            return value
        else:
            value = float('inf')
            for m in moves:
                nb = board.clone_and_move(m)
                value = min(value, alphabeta(nb, depth-1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha: break
            return value

    # Iterative Deepening
    try:
        if len(legal_moves) == 1:
            return best_move

        for depth in range(1, 5):
            alpha, beta = -float('inf'), float('inf')
            current_best_in_depth = best_move
            
            # Root search
            for m in legal_moves:
                nb = b.clone_and_move(m)
                val = alphabeta(nb, depth - 1, alpha, beta, False)
                if val > alpha:
                    alpha = val
                    current_best_in_depth = m
            
            best_move = current_best_in_depth
            if time.time() - start_time > 0.6:
                break
                
    except TimeoutError:
        pass

    return best_move
