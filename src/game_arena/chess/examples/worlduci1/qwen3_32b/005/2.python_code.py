
import copy

def policy(pieces, to_play):
    legal_moves = generate_legal_moves(pieces, to_play)
    best_move = max(legal_moves, key=lambda move: evaluate_move(move, pieces, to_play[0]))
    return best_move

def generate_legal_moves(pieces, to_play):
    player_color = to_play[0]  # 'w' or 'b'
    legal_moves = []
    
    # Find the player's king square
    king_square = None
    for sq, piece in pieces.items():
        if piece[0] == player_color and piece[1] == 'K':
            king_square = sq
            break

    player_pieces = {sq: piece for sq, piece in pieces.items() if piece[0] == player_color}

    for sq, piece in player_pieces.items():
        piece_type = piece[1]
        if piece_type == 'P':
            pseudo_moves = generate_pawn_moves(sq, pieces, player_color)
        elif piece_type == 'N':
            pseudo_moves = generate_knight_moves(sq, pieces, player_color)
        elif piece_type == 'B':
            pseudo_moves = generate_bishop_moves(sq, pieces, player_color)
        elif piece_type == 'R':
            pseudo_moves = generate_rook_moves(sq, pieces, player_color)
        elif piece_type == 'Q':
            pseudo_moves = generate_queen_moves(sq, pieces, player_color)
        elif piece_type == 'K':
            pseudo_moves = generate_king_moves(sq, pieces, player_color)
        else:
            pseudo_moves = []

        for move in pseudo_moves:
            from_sq, to_sq = move[:2], move[2:4] if len(move) <= 4 else move[4:6]
            # Create a new_pieces dict after the move
            new_pieces = copy.deepcopy(pieces)
            # Remove the original square
            del new_pieces[from_sq]
            # Add to the new square
            if to_sq in new_pieces:
                del new_pieces[to_sq]  # Capture
            new_pieces[to_sq] = piece

            # Find the current player's king in new_pieces
            new_king_square = None
            for new_sq, new_piece in new_pieces.items():
                if new_piece[0] == player_color and new_piece[1] == 'K':
                    new_king_square = new_sq
                    break

            # Check if the king is in check after this move
            if not is_in_check(new_pieces, player_color, new_king_square):
                legal_moves.append(move)
    
    return legal_moves

def generate_pawn_moves(square, pieces, player_color):
    file = square[0]
    rank = int(square[1])
    direction = 1 if player_color == 'w' else -1
    start_rank = 2 if player_color == 'w' else 7
    moves = []

    # Forward one square
    forward_1 = file + str(rank + direction)
    if forward_1 not in pieces:
        if (rank + direction == 8 and player_color == 'w') or (rank + direction == 1 and player_color == 'b'):
            # Promotion
            for promo in ['q', 'r', 'b', 'n']:
                moves.append(square + forward_1 + promo)
        else:
            moves.append(square + forward_1)
        # Forward two squares from start
        if rank == start_rank:
            forward_2 = file + str(rank + 2 * direction)
            if forward_2 not in pieces:
                moves.append(square + forward_2)
    # Diagonal captures
    for delta in [-1, 1]:
        new_file = chr(ord(file) + delta)
        if new_file < 'a' or new_file > 'h':
            continue
        target = new_file + str(rank + direction)
        if target in pieces:
            if pieces[target][0] != player_color:
                if (rank + direction == 8 and player_color == 'w') or (rank + direction == 1 and player_color == 'b'):
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(square + target + promo)
                else:
                    moves.append(square + target)
    return moves

def generate_knight_moves(square, pieces, player_color):
    file = square[0]
    rank = int(square[1])
    moves = []
    deltas = [ (2,1), (2,-1), (-2,1), (-2,-1),
               (1,2), (1,-2), (-1,2), (-1,-2) ]
    file_num = ord(file) - ord('a')
    for dr, df in deltas:
        new_rank = rank + dr
        new_file = file_num + df
        if new_file < 0 or new_file > 7 or new_rank < 1 or new_rank > 8:
            continue
        new_sq = chr(new_file + ord('a')) + str(new_rank)
        if new_sq not in pieces:
            moves.append(square + new_sq)
        else:
            if pieces[new_sq][0] != player_color:
                moves.append(square + new_sq)
    return moves

def generate_bishop_moves(square, pieces, player_color):
    file = square[0]
    rank = int(square[1])
    moves = []
    directions = [ (1,1), (1,-1), (-1,1), (-1,-1) ]
    for dr, df in directions:
        r, f = rank, ord(file) - ord('a')
        while True:
            r += dr
            f += df
            if f < 0 or f >7 or r < 1 or r >8:
                break
            new_sq = chr(f + ord('a')) + str(r)
            if new_sq in pieces:
                if pieces[new_sq][0] != player_color:
                    moves.append(square + new_sq)
                break
            else:
                moves.append(square + new_sq)
    return moves

def generate_rook_moves(square, pieces, player_color):
    file = square[0]
    rank = int(square[1])
    moves = []
    directions = [ (1,0), (-1,0), (0,1), (0,-1) ]
    for dr, df in directions:
        r, f = rank, ord(file) - ord('a')
        while True:
            r += dr
            f += df
            if f < 0 or f >7 or r <1 or r>8:
                break
            new_sq = chr(f + ord('a')) + str(r)
            if new_sq in pieces:
                if pieces[new_sq][0] != player_color:
                    moves.append(square + new_sq)
                break
            else:
                moves.append(square + new_sq)
    return moves

def generate_queen_moves(square, pieces, player_color):
    # Queen is rook + bishop
    bishop_moves = generate_bishop_moves(square, pieces, player_color)
    rook_moves = generate_rook_moves(square, pieces, player_color)
    return bishop_moves + rook_moves

def generate_king_moves(square, pieces, player_color):
    file = square[0]
    rank = int(square[1])
    moves = []
    deltas = [ (1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1) ]
    for dr, df in deltas:
        new_rank = rank + dr
        new_file = ord(file) + df
        if new_file < ord('a') or new_file > ord('h') or new_rank < 1 or new_rank >8:
            continue
        new_sq = chr(new_file) + str(new_rank)
        if new_sq in pieces:
            if pieces[new_sq][0] != player_color:
                moves.append(square + new_sq)
        else:
            moves.append(square + new_sq)
    return moves

def is_in_check(new_pieces, player_color, king_square):
    enemy_color = 'b' if player_color == 'w' else 'w'
    for sq, piece in new_pieces.items():
        if piece[0] == enemy_color:
            if can_attack(sq, piece[1], enemy_color, king_square, new_pieces):
                return True
    return False

def can_attack(attacker_sq, attacker_type, attacker_color, target_sq, pieces):
    af = ord(attacker_sq[0]) - ord('a')
    ar = 8 - int(attacker_sq[1])
    tf = ord(target_sq[0]) - ord('a')
    tr = 8 - int(target_sq[1])

    if attacker_type == 'P':
        if attacker_color == 'w':
            if (abs(tf - af) == 1) and (tr == ar - 1):
                return True
        else: # black
            if (abs(tf - af) == 1) and (tr == ar + 1):
                return True
        return False
    elif attacker_type == 'N':
        if (abs(tf - af) == 2 and abs(tr - ar) == 1) or (abs(tf - af) == 1 and abs(tr - ar) == 2):
            return True
        return False
    elif attacker_type == 'B':
        if abs(tf - af) != abs(tr - ar):
            return False
        step_f = 1 if tf > af else -1
        step_r = 1 if tr > ar else -1
        current_f, current_r = af + step_f, ar + step_r
        while current_f != tf or current_r != tr:
            if chr(current_f + ord('a')) + str(8 - current_r) in pieces:
                return False
            current_f += step_f
            current_r += step_r
        return True
    elif attacker_type == 'R':
        if not (af == tf or ar == tr):
            return False
        if af == tf:
            step = 1 if tr > ar else -1
            current_r = ar + step
            while current_r != tr:
                if chr(af + ord('a')) + str(8 - current_r) in pieces:
                    return False
                current_r += step
        else:
            step = 1 if tf > af else -1
            current_f = af + step
            while current_f != tf:
                if chr(current_f + ord('a')) + str(8 - current_r) in pieces:
                    return False
                current_f += step
        return True
    elif attacker_type == 'Q':
        if (abs(tf - af) == abs(tr - ar) or af == tf or ar == tr):
            if abs(tf - af) == abs(tr - ar):
                step_f = 1 if tf > af else -1
                step_r = 1 if tr > ar else -1
                current_f, current_r = af + step_f, ar + step_r
                while current_f != tf or current_r != tr:
                    if chr(current_f + ord('a')) + str(8 - current_r) in pieces:
                        return False
                    current_f += step_f
                    current_r += step_r
            else:
                if af == tf:
                    step = 1 if tr > ar else -1
                    current_r = ar + step
                    while current_r != tr:
                        if chr(af + ord('a')) + str(8 - current_r) in pieces:
                            return False
                        current_r += step
                else:
                    step = 1 if tf > af else -1
                    current_f = af + step
                    while current_f != tf:
                        if chr(current_f + ord('a')) + str(8 - current_r) in pieces:
                            return False
                        current_f += step
            return True
        return False
    elif attacker_type == 'K':
        if abs(tf - af) <= 1 and abs(tr - ar) <= 1 and not (tf == af and tr == ar):
            return True
        return False
    return False

piece_values = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

def evaluate_move(move, pieces, to_play_color):
    from_sq = move[:2]
    to_sq = move[2:4] if len(move) == 4 else move[4:6]
    is_promotion = len(move) > 4
    moving_piece = pieces[from_sq]
    moving_value = piece_values[moving_piece[1]]
    
    captured = to_sq in pieces and pieces[to_sq][0] != to_play_color
    if captured:
        captured_piece = pieces[to_sq]
        captured_value = piece_values[captured_piece[1]]
        capture_score = captured_value - moving_value
    else:
        capture_score = 0

    # Check if gives check
    gives_check = is_check_after_move(from_sq, to_sq, pieces, to_play_color)
    check_score = 10 if gives_check else 0

    promotion_score = 100 if is_promotion else 0

    total_score = capture_score + check_score + promotion_score
    return total_score

def is_check_after_move(from_sq, to_sq, pieces, to_play_color):
    new_pieces = copy.deepcopy(pieces)
    moving_piece = new_pieces[from_sq]
    del new_pieces[from_sq]
    if to_sq in new_pieces:
        del new_pieces[to_sq]
    new_pieces[to_sq] = moving_piece

    enemy_color = 'b' if to_play_color == 'w' else 'w'
    enemy_king = None
    for sq, piece in new_pieces.items():
        if piece[0] == enemy_color and piece[1] == 'K':
            enemy_king = sq
            break
    if enemy_king is None:
        return True  # opponent's king is gone (checkmate)
    return is_enemy_check(new_pieces, enemy_king, enemy_color, to_play_color)

def is_enemy_check(new_pieces, enemy_king, enemy_color, current_color):
    for sq, piece in new_pieces.items():
        if piece[0] == current_color:
            if can_attack(sq, piece[1], current_color, enemy_king, new_pieces):
                return True
    return False
