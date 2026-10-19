
import sys
import time

# Constants
INF = 100000
MATE_SCORE = 50000

# Piece values for evaluation
PIECE_VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
# Piece identifiers: P=1, N=2, B=3, R=4, Q=5, K=6. Color: White=1, Black=-1.
# Internal board is a list of 64 integers. 0 = empty.

# Piece Square Tables (PST) - Bonuses for positions
# Simple center control and advancement bonuses
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

def alg_to_idx(s):
    return (int(s[1]) - 1) * 8 + (ord(s[0]) - ord('a'))

def idx_to_alg(i):
    return chr(ord('a') + (i % 8)) + str(i // 8 + 1)

def piece_val_to_int(p_char):
    return {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}[p_char]

def int_to_piece_val(i):
    return {1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}[abs(i)]

class Board:
    def __init__(self, pieces, to_play):
        self.squares = [0] * 64
        for sq, p in pieces.items():
            idx = alg_to_idx(sq)
            color = 1 if p[0] == 'w' else -1
            val = piece_val_to_int(p[1])
            self.squares[idx] = color * val
        self.turn = 1 if to_play == 'white' else -1

    def find_king(self, color):
        target = color * 6
        for i, v in enumerate(self.squares):
            if v == target:
                return i
        return -1

    def is_attacked(self, sq, by_color):
        # Check Knights
        knight_diffs = [17, 15, 10, 6, -6, -10, -15, -17]
        sq_file = sq % 8
        for d in knight_diffs:
            target = sq + d
            if 0 <= target < 64:
                if abs((target % 8) - sq_file) <= 2: # valid knight jump
                    if self.squares[target] == by_color * 2:
                        return True

        # Check Pawns
        if by_color == 1: # White attacks upwards (lower ranks index smaller? No, rank 1 is idx 0. White moves +8)
            # White pawn on sq-7 or sq-9 attacks sq?
            # Wait, sq-7 means the pawn is on a "previous" rank relative to attack direction?
            # Board indices: 0(a1)..63(h8).
            # White pawn at idx 8 (a2). attacks 17(b3), 15(?). 
            # White moves +8. Attacks +7, +9.
            # So if I am at 'sq', a white pawn attacking me is at 'sq - 7' or 'sq - 9'.
            for d in [-7, -9]:
                target = sq + d
                if 0 <= target < 64:
                     if self.squares[target] == 1: # White Pawn
                         return True
        else: # Black attacks downwards (-8). Attacks -7, -9.
            for d in [7, 9]:
                target = sq + d
                if 0 <= target < 64:
                    if self.squares[target] == -1: # Black Pawn
                        return True

        # Check King
        king_diffs = [1, -1, 8, -8, 9, -9, 7, -7]
        for d in king_diffs:
            target = sq + d
            if 0 <= target < 64:
                if abs((target % 8) - sq_file) <= 1:
                    if self.squares[target] == by_color * 6:
                        return True

        # Check Sliders (Rook, Queen) - Ortho
        for d in [1, -1, 8, -8]:
            cur = sq
            while True:
                prev_file = cur % 8
                cur += d
                if not (0 <= cur < 64): break
                if abs((cur % 8) - prev_file) > 1: break # Wrap
                piece = self.squares[cur]
                if piece != 0:
                    if piece == by_color * 4 or piece == by_color * 5:
                        return True
                    break # Blocked
        
        # Check Sliders (Bishop, Queen) - Diag
        for d in [9, -9, 7, -7]:
            cur = sq
            while True:
                prev_file = cur % 8
                cur += d
                if not (0 <= cur < 64): break
                if abs((cur % 8) - prev_file) > 1: break # Wrap
                piece = self.squares[cur]
                if piece != 0:
                    if piece == by_color * 3 or piece == by_color * 5:
                        return True
                    break
        return False

def generate_moves(board):
    moves = [] # (from, to, promo)
    turn = board.turn
    for i in range(64):
        piece = board.squares[i]
        if piece == 0 or (piece > 0) != (turn > 0):
            continue
        
        p_type = abs(piece)
        file = i % 8
        rank = i // 8

        # Pawn
        if p_type == 1:
            direction = turn
            start_rank = 1 if turn == 1 else 6
            promo_rank = 7 if turn == 1 else 0
            
            # Forward
            to = i + 8 * direction
            if 0 <= to < 64 and board.squares[to] == 0:
                if to // 8 == promo_rank:
                    for pr in [5, 4, 3, 2]: moves.append((i, to, pr))
                else:
                    moves.append((i, to, 0))
                    # Double push
                    if rank == start_rank:
                        to2 = i + 16 * direction
                        if board.squares[to2] == 0:
                            moves.append((i, to2, 0))
            
            # Captures
            for d in [7, 9]:
                to = i + 8 * direction + d
                # Bounds check
                if 0 <= to < 64:
                    to_file = to % 8
                    if abs(to_file - file) == 1: # Diagonal is valid
                        target = board.squares[to]
                        if target != 0 and (target > 0) != (turn > 0):
                            if to // 8 == promo_rank:
                                for pr in [5, 4, 3, 2]: moves.append((i, to, pr))
                            else:
                                moves.append((i, to, 0))

        # Knight
        elif p_type == 2:
            for d in [17, 15, 10, 6, -6, -10, -15, -17]:
                to = i + d
                if 0 <= to < 64:
                    if abs((to % 8) - file) <= 2:
                        target = board.squares[to]
                        if target == 0 or (target > 0) != (turn > 0):
                            moves.append((i, to, 0))

        # Bishop
        elif p_type == 3:
            for d in [9, -9, 7, -7]:
                cur = i
                while True:
                    prev_file = cur % 8
                    cur += d
                    if not (0 <= cur < 64): break
                    if abs((cur % 8) - prev_file) > 1: break
                    target = board.squares[cur]
                    if target == 0:
                        moves.append((i, cur, 0))
                    else:
                        if (target > 0) != (turn > 0):
                            moves.append((i, cur, 0))
                        break

        # Rook
        elif p_type == 4:
            for d in [1, -1, 8, -8]:
                cur = i
                while True:
                    prev_file = cur % 8
                    cur += d
                    if not (0 <= cur < 64): break
                    if abs((cur % 8) - prev_file) > 1: break
                    target = board.squares[cur]
                    if target == 0:
                        moves.append((i, cur, 0))
                    else:
                        if (target > 0) != (turn > 0):
                            moves.append((i, cur, 0))
                        break
        
        # Queen
        elif p_type == 5:
            for d in [1, -1, 8, -8, 9, -9, 7, -7]:
                cur = i
                while True:
                    prev_file = cur % 8
                    cur += d
                    if not (0 <= cur < 64): break
                    if abs((cur % 8) - prev_file) > 1: break
                    target = board.squares[cur]
                    if target == 0:
                        moves.append((i, cur, 0))
                    else:
                        if (target > 0) != (turn > 0):
                            moves.append((i, cur, 0))
                        break

        # King
        elif p_type == 6:
            for d in [1, -1, 8, -8, 9, -9, 7, -7]:
                to = i + d
                if 0 <= to < 64:
                    if abs((to % 8) - file) <= 1:
                        target = board.squares[to]
                        if target == 0 or (target > 0) != (turn > 0):
                            moves.append((i, to, 0))
            
            # Castling
            # We assume rights if King and Rook on initial squares
            if turn == 1:
                if i == 4: # e1
                    # Kingside
                    if board.squares[7] == 4 and board.squares[5] == 0 and board.squares[6] == 0:
                        moves.append((4, 6, 0))
                    # Queenside
                    if board.squares[0] == 4 and board.squares[1] == 0 and board.squares[2] == 0 and board.squares[3] == 0:
                        moves.append((4, 2, 0))
            else:
                if i == 60: # e8
                    if board.squares[63] == -4 and board.squares[61] == 0 and board.squares[62] == 0:
                        moves.append((60, 62, 0))
                    if board.squares[56] == -4 and board.squares[57] == 0 and board.squares[58] == 0 and board.squares[59] == 0:
                        moves.append((60, 58, 0))
    return moves

def make_move(board, move):
    f, t, promo = move
    piece = board.squares[f]
    captured = board.squares[t]
    
    board.squares[f] = 0
    if promo:
        board.squares[t] = board.turn * promo
    else:
        board.squares[t] = piece

    # Castling rook move
    if abs(piece) == 6 and abs(f - t) == 2:
        if t == 6: # g1
            board.squares[7] = 0; board.squares[5] = 4
        elif t == 2: # c1
            board.squares[0] = 0; board.squares[3] = 4
        elif t == 62: # g8
            board.squares[63] = 0; board.squares[61] = -4
        elif t == 58: # c8
            board.squares[56] = 0; board.squares[59] = -4
            
    board.turn *= -1
    return captured

def unmake_move(board, move, captured):
    f, t, promo = move
    piece = board.squares[t] # The piece that moved (or promoted)
    
    # Undo promotion
    original_piece = piece
    if promo:
        original_piece = board.turn * 1 # turn is currently opposite, so -turn * 1 is wrong? 
        # Wait, board.turn is flipped AFTER make_move. So if White moved, board.turn is Black.
        # piece at t is White. board.turn is Black (-1).
        # original was White Pawn (1).
        # board.turn is -1. original should be 1.
        # so -board.turn * 1 works.
        original_piece = -board.turn * 1

    board.squares[f] = original_piece
    board.squares[t] = captured
    
    # Undo rook move
    # We check the destination square of the king to infer castling
    if abs(original_piece) == 6 and abs(f - t) == 2:
        if t == 6: # g1
            board.squares[5] = 0; board.squares[7] = 4
        elif t == 2: # c1
            board.squares[3] = 0; board.squares[0] = 4
        elif t == 62: # g8
            board.squares[61] = 0; board.squares[63] = -4
        elif t == 58: # c8
            board.squares[59] = 0; board.squares[56] = -4

    board.turn *= -1

def evaluate(board):
    score = 0
    for i, p in enumerate(board.squares):
        if p == 0: continue
        sign = 1 if p > 0 else -1
        p_type = abs(p)
        
        # Material
        val = PIECE_VAL[int_to_piece_val(p_type)]
        score += sign * val
        
        # Position
        # PST is from White perspective. For Black, we flip index.
        if sign == 1:
            idx = i
        else:
            # Flip rank: (7 - rank) * 8 + file
            idx = (7 - (i // 8)) * 8 + (i % 8)
            
        p_char = int_to_piece_val(p_type)
        pos_bonus = PST[p_char][idx]
        score += sign * pos_bonus
        
    return score

def is_legal(board, move):
    f, t, promo = move
    piece = board.squares[f]
    
    # Castling check: King passes through check
    if abs(piece) == 6 and abs(f - t) == 2:
        # Check if currently in check
        if board.is_attacked(f, -board.turn): return False
        # Check intermediate square
        inter = (f + t) // 2
        if board.is_attacked(inter, -board.turn): return False
        # Destination check handled later by generic king safety
    
    captured = make_move(board, move)
    king_sq = board.find_king(-board.turn) # turn has flipped, so we find the King of the side that just moved
    is_safe = not board.is_attacked(king_sq, board.turn) # attacked by opponent
    unmake_move(board, move, captured)
    return is_safe

def quiescence(board, alpha, beta):
    # Standing pat
    stand_pat = evaluate(board)
    if board.turn == -1: stand_pat = -stand_pat # Return relative to current player? No, evaluate is white relative.
    
    # We use Negamax, so we need score relative to side to move.
    # evaluate() is White relative.
    # If board.turn == White (1), score = eval.
    # If board.turn == Black (-1), score = -eval.
    stand_pat = evaluate(board) * board.turn
    
    if stand_pat >= beta: return beta
    if alpha < stand_pat: alpha = stand_pat

    # Generate captures only
    moves = generate_moves(board)
    captures = []
    for m in moves:
        # Filter captures
        if board.squares[m[1]] != 0: captures.append(m)
        # Also promotions?
        if m[2] != 0: captures.append(m)

    captures.sort(key=lambda m: PIECE_VAL.get(int_to_piece_val(abs(board.squares[m[1]])), 0) * -1)

    for m in captures:
        if not is_legal(board, m): continue
        captured = make_move(board, m)
        score = -quiescence(board, -beta, -alpha)
        unmake_move(board, m, captured)
        
        if score >= beta: return beta
        if score > alpha: alpha = score
    return alpha

def negamax(board, depth, alpha, beta):
    if depth == 0:
        return quiescence(board, alpha, beta)
    
    moves = generate_moves(board)
    
    # Move Ordering: Captures first
    def move_score(m):
        s = 0
        if board.squares[m[1]] != 0: # Capture
            s += 10 * PIECE_VAL.get(int_to_piece_val(abs(board.squares[m[1]])), 0) - PIECE_VAL.get(int_to_piece_val(abs(board.squares[m[0]])), 0)
        if m[2] != 0: s += 900 # Promotion
        return -s

    moves.sort(key=move_score)
    
    legal_found = False
    for m in moves:
        if not is_legal(board, m): continue
        legal_found = True
        captured = make_move(board, m)
        score = -negamax(board, depth - 1, -beta, -alpha)
        unmake_move(board, m, captured)
        
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
            
    if not legal_found:
        # Checkmate or Stalemate
        king_sq = board.find_king(board.turn)
        if board.is_attacked(king_sq, -board.turn):
            return -MATE_SCORE # Checkmated
        return 0 # Stalemate
        
    return alpha

def policy(pieces: dict[str, str], to_play: str) -> str:
    board = Board(pieces, to_play)
    
    depth = 3
    best_move = None
    best_score = -INF
    
    moves = generate_moves(board)
    # Random shuffle to avoid deterministic behavior in equal positions? 
    # Sorting by heuristic helps consistency.
    
    legal_moves = []
    for m in moves:
        if is_legal(board, m):
            legal_moves.append(m)
            
    if not legal_moves:
        return "" # Should not happen

    # Root move ordering
    legal_moves.sort(key=lambda m: (
        -1000 if board.squares[m[1]] != 0 else 0, # Captures first
        -1 if m[2] != 0 else 0 # Promotions
    ))

    alpha = -INF
    beta = INF
    
    for m in legal_moves:
        captured = make_move(board, m)
        score = -negamax(board, depth - 1, -beta, -alpha)
        unmake_move(board, m, captured)
        
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
            
    if best_move is None:
        best_move = legal_moves[0] # Fallback

    f, t, promo = best_move
    uci = idx_to_alg(f) + idx_to_alg(t)
    if promo:
        uci += int_to_piece_val(promo).lower()
    return uci
