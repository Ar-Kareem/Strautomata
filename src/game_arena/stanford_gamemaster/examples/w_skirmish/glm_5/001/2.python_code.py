
import random

PIECE_VALUES = {'king': 11, 'queen': 9, 'rook': 5, 'bishop': 3, 'knight': 3, 'pawn': 1}

def col_to_idx(col):
    return ord(col) - ord('a')

def idx_to_col(idx):
    return chr(ord('a') + idx)

def is_valid_cell(col, row):
    return 'a' <= col <= 'h' and 1 <= row <= 8

def format_move(piece, target_col, target_row):
    return f"move(piece({piece[1]},{piece[2]},{piece[3]}),cell({target_col},{target_row}))"

def generate_pawn_moves(board, col, row, role):
    moves = []
    direction = 1 if role == 'white' else -1
    start_row = 2 if role == 'white' else 7
    piece = board[(col, row)]
    col_idx = col_to_idx(col)
    
    new_row = row + direction
    if is_valid_cell(col, new_row) and (col, new_row) not in board:
        moves.append((piece, col, new_row))
        if row == start_row:
            new_row2 = row + 2 * direction
            if is_valid_cell(col, new_row2) and (col, new_row2) not in board:
                moves.append((piece, col, new_row2))
    
    for dc in [-1, 1]:
        new_col = idx_to_col(col_idx + dc)
        new_row = row + direction
        if is_valid_cell(new_col, new_row):
            target = board.get((new_col, new_row))
            if target and target[1] != role:
                moves.append((piece, new_col, new_row))
    return moves

def generate_knight_moves(board, col, row, role):
    moves = []
    piece = board[(col, row)]
    col_idx = col_to_idx(col)
    for dc, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        new_col, new_row = idx_to_col(col_idx + dc), row + dr
        if is_valid_cell(new_col, new_row):
            target = board.get((new_col, new_row))
            if not target or target[1] != role:
                moves.append((piece, new_col, new_row))
    return moves

def generate_sliding_moves(board, col, row, role, directions):
    moves = []
    piece = board[(col, row)]
    col_idx = col_to_idx(col)
    for dc, dr in directions:
        c, r = col_idx, row
        while True:
            c, r = c + dc, r + dr
            new_col = idx_to_col(c)
            if not is_valid_cell(new_col, r): break
            target = board.get((new_col, r))
            if not target:
                moves.append((piece, new_col, r))
            else:
                if target[1] != role:
                    moves.append((piece, new_col, r))
                break
    return moves

def generate_legal_moves(board, role):
    moves = []
    for (col, row), piece in board.items():
        if piece[1] != role: continue
        pt = piece[2]
        if pt == 'pawn': moves.extend(generate_pawn_moves(board, col, row, role))
        elif pt == 'knight': moves.extend(generate_knight_moves(board, col, row, role))
        elif pt == 'bishop': moves.extend(generate_sliding_moves(board, col, row, role, [(-1,-1),(-1,1),(1,-1),(1,1)]))
        elif pt == 'rook': moves.extend(generate_sliding_moves(board, col, row, role, [(-1,0),(1,0),(0,-1),(0,1)]))
        elif pt == 'queen': moves.extend(generate_sliding_moves(board, col, row, role, [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]))
        elif pt == 'king': moves.extend(generate_sliding_moves(board, col, row, role, [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]))
    return moves

def is_square_attacked(board, col, row, attacker_role):
    col_idx = col_to_idx(col)
    pawn_row = -1 if attacker_role == 'white' else 1
    for dc in [-1, 1]:
        if is_valid_cell(idx := idx_to_col(col_idx + dc), row + pawn_row):
            p = board.get((idx, row + pawn_row))
            if p and p[1] == attacker_role and p[2] == 'pawn': return True
    for dc, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        if is_valid_cell(idx := idx_to_col(col_idx + dc), row + dr):
            p = board.get((idx, row + dr))
            if p and p[1] == attacker_role and p[2] == 'knight': return True
    for dc, dr in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
        if is_valid_cell(idx := idx_to_col(col_idx + dc), row + dr):
            p = board.get((idx, row + dr))
            if p and p[1] == attacker_role and p[2] == 'king': return True
    for dc, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        c, r = col_idx, row
        while True:
            c, r = c + dc, r + dr
            if not is_valid_cell(nc := idx_to_col(c), r): break
            p = board.get((nc, r))
            if p:
                if p[1] == attacker_role and p[2] in ['bishop','queen']: return True
                break
    for dc, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
        c, r = col_idx, row
        while True:
            c, r = c + dc, r + dr
            if not is_valid_cell(nc := idx_to_col(c), r): break
            p = board.get((nc, r))
            if p:
                if p[1] == attacker_role and p[2] in ['rook','queen']: return True
                break
    return False

def find_piece_pos(board, piece):
    for pos, p in board.items():
        if p == piece: return pos
    return None

def policy(state, role):
    board, step, scores = {}, 1, {}
    for fact in state:
        if fact[0] == "location":
            board[(fact[1][1], int(fact[1][2]))] = fact[2]
        elif fact[0] == "step": step = int(fact[1])
        elif len(fact) == 2 and fact[0] in ["white","black"]: scores[fact[0]] = int(fact[1])
    
    moves = generate_legal_moves(board, role)
    if not moves: return ""
    
    opp = 'black' if role == 'white' else 'white'
    my_score, opp_score = scores.get(role, 50), scores.get(opp, 50)
    best_move, best_eval = None, -float('inf')
    
    for move in moves:
        piece, tc, tr = move
        pv = PIECE_VALUES[piece[2]]
        cur_pos = find_piece_pos(board, piece)
        score = 0
        
        target = board.get((tc, tr))
        cap_val = PIECE_VALUES[target[2]] if target else 0
        if cap_val > 0:
            score += cap_val * 100
            if pv < cap_val: score += (cap_val - pv) * 30
        
        new_board = dict(board)
        if cur_pos: del new_board[cur_pos]
        new_board[(tc, tr)] = piece
        
        if is_square_attacked(new_board, tc, tr, opp):
            if not is_square_attacked(new_board, tc, tr, role):
                score -= pv * 80
            elif cap_val > 0 and pv > cap_val:
                score -= (pv - cap_val) * 40
        
        if piece[2] in ['knight','bishop'] and cur_pos:
            back = 1 if role == 'white' else 8
            if cur_pos[1] == back: score += 10
        
        if tc in ['c','d','e','f'] and tr in [3,4,5,6]: score += 5
        if piece[2] == 'king' and step < 30: score -= 30
        if my_score - opp_score > 5 and cap_val > 0: score += 20
        
        score += random.random() * 0.5
        if score > best_eval: best_eval, best_move = score, move
    
    return format_move(best_move[0], best_move[1], best_move[2])
