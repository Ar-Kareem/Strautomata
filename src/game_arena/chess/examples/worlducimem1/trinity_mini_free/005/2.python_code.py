
import numpy as np

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Initialize evaluation constants
    MATERIAL = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 200}
    KING_SAFETY = {'w': 0, 'b': 0}
    POSITIONAL = {'w': 0, 'b': 0}
    
    # Initialize memory if not present
    if 'evaluation' not in memory:
        memory['evaluation'] = {'w': 0, 'b': 0}
    
    # Material evaluation
    for square, piece in pieces.items():
        color, type_ = piece[0], piece[1]
        if color == to_play:
            memory['evaluation'][color] += MATERIAL[type_]
        else:
            memory['evaluation'][color] -= MATERIAL[type_]
    
    # King safety evaluation
    king_square = None
    for square, piece in pieces.items():
        if piece[1] == 'k' and piece[0] == to_play:
            king_square = square
            break
    if king_square:
        for square, piece in pieces.items():
            if piece[0] != to_play and piece[1] in 'nqbr':
                # Check if piece attacks king_square
                if is_attacking(square, king_square, pieces, to_play):
                    memory['evaluation'][to_play] -= 10  # Penalty for king attacks
    
    # Positional evaluation (simplified)
    if to_play == 'w':
        memory['evaluation']['w'] += 5  # White's positional advantage
    else:
        memory['evaluation']['b'] += 5  # Black's positional advantage
    
    # Generate legal moves
    legal_moves = generate_legal_moves(pieces, to_play)
    
    # Evaluate each move
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        new_pieces = make_move(pieces, move)
        new_score = evaluate_position(new_pieces, to_play)
        if new_score > best_score:
            best_score = new_score
            best_move = move
    
    return best_move, memory

def is_attacking(attacker, target, pieces, color):
    # Simplified attack detection (only checks for queen, rook, bishop, knight)
    attacker_piece = pieces[attacker][1]
    if attacker_piece in 'nq':
        return True
    if attacker_piece == 'b':
        return is_diagonal_attacking(attacker, target, pieces, color)
    if attacker_piece == 'r':
        return is_horizontal_vertical_attacking(attacker, target, pieces, color)
    if attacker_piece == 'n':
        return is_knight_attacking(attacker, target, pieces, color)
    return False

def is_diagonal_attacking(attacker, target, pieces, color):
    # Check diagonal attacks
    delta = (ord(target[0]) - ord(attacker[0]), int(target[1]) - int(attacker[1]))
    if abs(delta[0]) != abs(delta[1]) or delta == (0,0):
        return False
    # Check path between attacker and target
    step_x = 1 if delta[0] > 0 else -1
    step_y = 1 if delta[1] > 0 else -1
    x, y = ord(attacker[0]) + step_x, int(attacker[1]) + step_y
    while x != ord(target[0]) and y != int(target[1]):
        if pieces.get(chr(x)+str(y), '') != '':
            return False
        x += step_x
        y += step_y
    return True

def is_horizontal_vertical_attacking(attacker, target, pieces, color):
    # Check horizontal/vertical attacks
    delta = (ord(target[0]) - ord(attacker[0]), int(target[1]) - int(attacker[1]))
    if delta[0] == 0 or delta[1] == 0:
        # Check path between attacker and target
        step_x = 1 if delta[0] > 0 else -1
        step_y = 1 if delta[1] > 0 else -1
        x, y = ord(attacker[0]) + step_x, int(attacker[1]) + step_y
        while x != ord(target[0]) and y != int(target[1]):
            if pieces.get(chr(x)+str(y), '') != '':
                return False
            x += step_x
            y += step_y
        return True
    return False

def is_knight_attacking(attacker, target, pieces, color):
    # Check knight attacks
    knight_moves = [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]
    for dx, dy in knight_moves:
        if chr(ord(attacker[0]) + dx) == target[0] and int(attacker[1]) + dy == int(target[1]):
            return True
    return False

def generate_legal_moves(pieces, color):
    # Simplified legal moves generator (only pawn, knight, bishop, rook, queen)
    legal_moves = []
    for square, piece in pieces.items():
        if piece[0] != color:
            continue
        type_ = piece[1]
        if type_ == 'p':
            # Pawn moves
            pawn_moves = get_pawn_moves(square, color, pieces)
            legal_moves.extend(pawn_moves)
        elif type_ == 'n':
            # Knight moves
            knight_moves = get_knight_moves(square, color, pieces)
            legal_moves.extend(knight_moves)
        elif type_ in 'bq':
            # Bishop/Queen moves
            bishop_moves = get_diagonal_moves(square, color, pieces)
            queen_moves = get_horizontal_vertical_moves(square, color, pieces)
            legal_moves.extend(bishop_moves + queen_moves)
        elif type_ == 'r':
            # Rook moves
            rook_moves = get_horizontal_vertical_moves(square, color, pieces)
            legal_moves.extend(rook_moves)
    return legal_moves

def get_pawn_moves(square, color, pieces):
    # Returns valid pawn moves (including captures and promotions)
    moves = []
    direction = 1 if color == 'w' else -1
    start_rank = 2 if color == 'w' else 7
    end_rank = 7 if color == 'w' else 2
    
    # Single push
    new_square = chr(ord(square[0])) + str(int(square[1]) + direction)
    if new_square in pieces:
        return moves
    moves.append(new_square)
    
    # Double push
    if int(square[1]) == start_rank:
        double_square = chr(ord(square[0])) + str(int(square[1]) + 2*direction)
        if double_square not in pieces:
            moves.append(double_square)
    
    # Captures
    for dx in [-1, 1]:
        capture_square = chr(ord(square[0]) + dx) + str(int(square[1]) + direction)
        if capture_square in pieces and pieces[capture_square][0] != color:
            moves.append(capture_square)
    
    return moves

def get_knight_moves(square, color, pieces):
    # Returns valid knight moves
    knight_moves = [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]
    moves = []
    for dx, dy in knight_moves:
        new_square = chr(ord(square[0]) + dx) + str(int(square[1]) + dy)
        if 1 <= int(new_square[1]) <= 8 and new_square not in pieces:
            moves.append(new_square)
    return moves

def get_diagonal_moves(square, color, pieces):
    # Returns valid diagonal moves
    moves = []
    directions = [(1,1), (1,-1), (-1,1), (-1,-1)]
    for dx, dy in directions:
        x, y = ord(square[0]) + dx, int(square[1]) + dy
        while 1 <= y <= 8:
            new_square = chr(x) + str(y)
            if new_square in pieces:
                if pieces[new_square][0] != color:
                    moves.append(new_square)
                break
            moves.append(new_square)
            x += dx
            y += dy
    return moves

def get_horizontal_vertical_moves(square, color, pieces):
    # Returns valid horizontal/vertical moves
    moves = []
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    for dx, dy in directions:
        x, y = ord(square[0]) + dx, int(square[1]) + dy
        while 1 <= y <= 8:
            new_square = chr(x) + str(y)
            if new_square in pieces:
                if pieces[new_square][0] != color:
                    moves.append(new_square)
                break
            moves.append(new_square)
            x += dx
            y += dy
    return moves

def make_move(pieces, move):
    # Make a move and return new pieces dictionary
    new_pieces = pieces.copy()
    # Extract move components
    from_square = move[:2]
    to_square = move[2:]
    # Handle promotions
    if len(move) > 4:
        promotion = move[4]
        new_piece = to_play + promotion
    else:
        new_piece = to_play + pieces[from_square][1]
    
    # Remove captured piece if any
    if to_square in pieces:
        del new_pieces[to_square]
    
    # Update piece position
    new_pieces[to_square] = new_piece
    del new_pieces[from_square]
    return new_pieces

def evaluate_position(pieces, color):
    # Evaluate position score (higher is better for color)
    score = 0
    
    # Material evaluation
    for square, piece in pieces.items():
        if piece[0] == color:
            score += MATERIAL[piece[1]]
        else:
            score -= MATERIAL[piece[1]]
    
    # King safety evaluation
    king_square = None
    for square, piece in pieces.items():
        if piece[1] == 'k' and piece[0] == color:
            king_square = square
            break
    if king_square:
        for square, piece in pieces.items():
            if piece[0] != color and piece[1] in 'nqbr':
                if is_attacking(square, king_square, pieces, color):
                    score -= 10  # Penalty for king attacks
    
    # Positional evaluation
    if color == 'w':
        score += 5  # White's positional advantage
    else:
        score -= 5  # Black's positional disadvantage
    
    return score
