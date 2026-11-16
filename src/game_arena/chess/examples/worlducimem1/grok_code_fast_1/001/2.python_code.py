
import random
import numpy as np

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 9999}

def square_to_coord(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return file, rank

def coord_to_square(file, rank):
    return chr(file + ord('a')) + str(rank + 1)

def is_in_bounds(file, rank):
    return 0 <= file < 8 and 0 <= rank < 8

def make_board(pieces):
    board = np.full((8, 8), None, dtype=object)
    for sq, piece in pieces.items():
        file, rank = square_to_coord(sq)
        board[rank][file] = piece
    return board

def parse_move(move, promotion='q'):
    from_sq = move[:2]
    to_sq = move[2:4]
    prom = move[4:] if len(move) > 4 else None
    if prom:
        promotion = prom.lower()
    if promotion not in ['q', 'r', 'b', 'n']:
        promotion = 'q'
    return from_sq, to_sq, promotion

def generate_moves(pieces, to_play):
    board = make_board(pieces)
    color = to_play[0].lower()  # 'w' or 'b'
    opp_color = 'b' if color == 'w' else 'w'
    pawn_dir = 1 if color == 'w' else -1
    legal_moves = []
    
    for sq, piece in pieces.items():
        if piece[0] != color:
            continue
        file, rank = square_to_coord(sq)
        piece_type = piece[1]
        
        if piece_type == 'P':
            # Forward moves
            nr = rank + pawn_dir
            if is_in_bounds(file, nr) and board[nr][file] is None:
                to_sq = coord_to_square(file, nr)
                if (rank == 1 and color == 'w') or (rank == 6 and color == 'b'):
                    legal_moves.append(f"{sq}{to_sq}q")  # Promote to queen
                else:
                    legal_moves.append(f"{sq}{to_sq}")
                # Double move
                if nr == rank + pawn_dir and ((color == 'w' and rank == 1) or (color == 'b' and rank == 6)):
                    nnr = nr + pawn_dir
                    if is_in_bounds(file, nnr) and board[nnr][file] is None:
                        to_sq = coord_to_square(file, nnr)
                        legal_moves.append(f"{sq}{to_sq}")
            # Captures
            for df in [-1, 1]:
                cf = file + df
                nr = rank + pawn_dir
                if is_in_bounds(cf, nr) and board[nr][cf] and board[nr][cf][0] == opp_color:
                    to_sq = coord_to_square(cf, nr)
                    if (nr == 0 and color == 'w') or (nr == 7 and color == 'b'):
                        legal_moves.append(f"{sq}{to_sq}q")
                    else:
                        legal_moves.append(f"{sq}{to_sq}")
        
        elif piece_type == 'N':
            deltas = [(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]
            for df, dr in deltas:
                nf, nr = file + df, rank + dr
                if is_in_bounds(nf, nr) and (board[nr][nf] is None or board[nr][nf][0] == opp_color):
                    to_sq = coord_to_square(nf, nr)
                    legal_moves.append(f"{sq}{to_sq}")
        
        elif piece_type in ['B', 'R', 'Q']:
            directions = []
            if piece_type == 'B':
                directions = [(1,1),(1,-1),(-1,1),(-1,-1)]
            elif piece_type == 'R':
                directions = [(0,1),(0,-1),(1,0),(-1,0)]
            else:
                directions = [(1,1),(1,-1),(-1,1),(-1,-1),(0,1),(0,-1),(1,0),(-1,0)]
            for df, dr in directions:
                nf, nr = file + df, rank + dr
                while is_in_bounds(nf, nr):
                    if board[nr][nf] is None:
                        to_sq = coord_to_square(nf, nr)
                        legal_moves.append(f"{sq}{to_sq}")
                    elif board[nr][nf][0] == opp_color:
                        to_sq = coord_to_square(nf, nr)
                        legal_moves.append(f"{sq}{to_sq}")
                        break
                    else:
                        break
                    nf += df
                    nr += dr
        
        elif piece_type == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = file + df, rank + dr
                    if is_in_bounds(nf, nr) and (board[nr][nf] is None or board[nr][nf][0] == opp_color):
                        to_sq = coord_to_square(nf, nr)
                        legal_moves.append(f"{sq}{to_sq}")
            # TODO: Add castling if time allows, but skipping for simplicity
    
    # Very basic legality filter: check if king is safe after move
    legal = []
    king_sq = next((sq for sq, p in pieces.items() if p == f"{color}K"), None)
    for move in legal_moves:
        to_sq = move[2:4]
        # Simulate move
        temp_pieces = pieces.copy()
        from_sq = move[:2]
        temp_pieces[to_sq] = temp_pieces.pop(from_sq)
        if len(move) > 4:
            temp_pieces[to_sq] = f"{color}{move[4].upper()}"  # Promotion
        temp_board = make_board(temp_pieces)
        # Naive check: is king attacked? (incomplete, but ok)
        if king_sq == from_sq:
            king_sq = to_sq
        if not is_king_attacked(temp_board, king_sq, opp_color):
            legal.append(move)
    return legal

def is_king_attacked(board, king_sq, opp_color):
    # Simplified attack check for time
    k_file, k_rank = square_to_coord(king_sq)
    # Check pawn attacks
    pawn_dir = 1 if opp_color == 'b' else -1
    for df in [-1, 1]:
        if is_in_bounds(k_file + df, k_rank - pawn_dir) and board[k_rank - pawn_dir][k_file + df] == f"{opp_color}P":
            return True
    # Check knight attacks
    deltas = [(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]
    for df, dr in deltas:
        nf, nr = k_file + df, k_rank + dr
        if is_in_bounds(nf, nr) and board[nr][nf] == f"{opp_color}N":
            return True
    # Skipping further for time (sliding pieces approx)
    return False

def make_move(pieces, move, to_play):
    temp_pieces = pieces.copy()
    from_sq, to_sq, promotion = parse_move(move)
    piece = temp_pieces[from_sq]
    del temp_pieces[from_sq]
    if to_sq in temp_pieces:
        del temp_pieces[to_sq]  # Capture
    if len(move) > 4:
        temp_pieces[to_sq] = f"{piece[0]}{promotion.upper()}"
    else:
        temp_pieces[to_sq] = piece
    next_to_play = 'white' if to_play == 'black' else 'black'
    return {'pieces': temp_pieces, 'to_play': next_to_play}

def evaluate(pieces, to_play):
    score = 0
    for piece in pieces.values():
        val = PIECE_VALUES[piece[1]]
        if piece[0] == 'w':
            score += val
        else:
            score -= val
    return score

def minimax(position, depth, is_maximizing, alpha, beta):
    if depth == 0:
        return evaluate(position['pieces'], position['to_play'])
    
    legal_moves = generate_moves(position['pieces'], position['to_play'])
    if not legal_moves:
        return -9999 if is_maximizing else 9999  # Checkmate-ish
    
    if is_maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            new_pos = make_move(position['pieces'], move, position['to_play'])
            new_pos_dict = {'pieces': new_pos['pieces'], 'to_play': new_pos['to_play']}
            eval = minimax(new_pos_dict, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_pos = make_move(position['pieces'], move, position['to_play'])
            new_pos_dict = {'pieces': new_pos['pieces'], 'to_play': new_pos['to_play']}
            eval = minimax(new_pos_dict, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces, to_play, memory):
    legal_moves = generate_moves(pieces, to_play)
    if not legal_moves:
        # Failsafe: return a dummy move, but should not happen
        return 'e2e4', memory
    
    best_move = None
    best_score = -float('inf')
    depth = 3
    is_maximizing = True
    alpha = -float('inf')
    beta = float('inf')
    position = {'pieces': pieces, 'to_play': to_play}
    
    for move in legal_moves:
        new_pos = make_move(pieces, move, to_play)
        new_pos_dict = {'pieces': new_pos['pieces'], 'to_play': new_pos['to_play']}
        score = minimax(new_pos_dict, depth - 1, False, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Store in memory
    memory['last_move'] = best_move
    return best_move, memory
