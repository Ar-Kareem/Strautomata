
import numpy as np

piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
center_squares = {'d4', 'e4', 'd5', 'e5'}
knight_bonus = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]
])

def square_to_coords(square):
    file = square[0]
    rank = int(square[1]) - 1
    x = ord(file) - ord('a')
    y = rank
    return (x, y)

def coords_to_square(x, y):
    file = chr(ord('a') + x)
    rank = str(y + 1)
    return file + rank

def get_legal_moves(pieces, to_play, memory):
    color = 'w' if to_play == 'white' else 'b'
    moves = []
    for from_sq, piece_code in list(pieces.items()):
        if piece_code[0] != color:
            continue
        piece_type = piece_code[1]
        x, y = square_to_coords(from_sq)
        
        if piece_type == 'P':
            direction = 1 if color == 'w' else -1
            # Single push
            new_y = y + direction
            if 0 <= new_y < 8:
                to_sq = coords_to_square(x, new_y)
                if to_sq not in pieces:
                    moves.extend(generate_promotion(from_sq, to_sq, color))
                    # Double push
                    if (color == 'w' and y == 1) or (color == 'b' and y == 6):
                        to_sq2 = coords_to_square(x, y + 2 * direction)
                        if to_sq2 not in pieces:
                            moves.append(f"{from_sq}{to_sq2}")
            # Captures
            for dx in [-1, 1]:
                new_x, new_y = x + dx, y + direction
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    to_sq = coords_to_square(new_x, new_y)
                    if to_sq in pieces and pieces[to_sq][0] != color:
                        moves.extend(generate_promotion(from_sq, to_sq, color))
        elif piece_type == 'N':
            deltas = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
            for dx, dy in deltas:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    to_sq = coords_to_square(nx, ny)
                    if to_sq not in pieces or pieces[to_sq][0] != color:
                        moves.append(f"{from_sq}{to_sq}")
        elif piece_type in ['B', 'R', 'Q']:
            directions = []
            if piece_type in ['B', 'Q']:
                directions.extend([(1,1), (-1,1), (1,-1), (-1,-1)])
            if piece_type in ['R', 'Q']:
                directions.extend([(1,0), (-1,0), (0,1), (0,-1)])
            for dx, dy in directions:
                nx, ny = x, y
                while True:
                    nx += dx
                    ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8):
                        break
                    to_sq = coords_to_square(nx, ny)
                    if to_sq in pieces:
                        if pieces[to_sq][0] != color:
                            moves.append(f"{from_sq}{to_sq}")
                        break
                    moves.append(f"{from_sq}{to_sq}")
        elif piece_type == 'K':
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        to_sq = coords_to_square(nx, ny)
                        if to_sq not in pieces or pieces[to_sq][0] != color:
                            moves.append(f"{from_sq}{to_sq}")
            # Castling
            if from_sq == 'e1' and color == 'w':
                if 'h1' in pieces and pieces['h1'] == 'wR' and all(sq not in pieces for sq in ['f1', 'g1']):
                    moves.append('e1g1')
                if 'a1' in pieces and pieces['a1'] == 'wR' and all(sq not in pieces for sq in ['b1', 'c1', 'd1']):
                    moves.append('e1c1')
            elif from_sq == 'e8' and color == 'b':
                if 'h8' in pieces and pieces['h8'] == 'bR' and all(sq not in pieces for sq in ['f8', 'g8']):
                    moves.append('e8g8')
                if 'a8' in pieces and pieces['a8'] == 'bR' and all(sq not in pieces for sq in ['b8', 'c8', 'd8']):
                    moves.append('e8c8')
    
    legal_moves = []
    for move in moves:
        if is_move_legal(pieces, move, color):
            legal_moves.append(move)
    return legal_moves

def generate_promotion(from_sq, to_sq, color):
    promotions = []
    for promo in 'qnbr':
        promotions.append(f"{from_sq}{to_sq}{promo}")
    return promotions

def is_move_legal(pieces, move, color):
    from_sq = move[:2]
    to_sq = move[2:4] if len(move) <= 5 else move[2:4]
    promo = move[4] if len(move) == 5 else None
    
    new_pieces = pieces.copy()
    piece = new_pieces.pop(from_sq)
    if len(move) == 4:
        if to_sq in new_pieces:
            del new_pieces[to_sq]
        new_pieces[to_sq] = piece
    else:
        new_pieces[to_sq] = color + promo.upper()
    
    king_sq = next(sq for sq, pc in new_pieces.items() if pc == color + 'K')
    x, y = square_to_coords(king_sq)
    opponent = 'b' if color == 'w' else 'w'
    
    for sq, pc in new_pieces.items():
        if pc[0] != opponent:
            continue
        px, py = square_to_coords(sq)
        pt = pc[1]
        if pt == 'N':
            if (abs(px - x) == 2 and abs(py - y) == 1) or (abs(px - x) == 1 and abs(py - y) == 2):
                return False
        elif pt == 'P':
            if py == y + (1 if opponent == 'b' else -1) and abs(px - x) == 1:
                return False
        elif pt in ['B', 'Q']:
            dx = px - x
            dy = py - y
            if abs(dx) == abs(dy):
                step_x = 1 if dx > 0 else -1
                step_y = 1 if dy > 0 else -1
                tx, ty = x + step_x, y + step_y
                while tx != px and ty != py:
                    if coords_to_square(tx, ty) in new_pieces:
                        break
                    tx += step_x
                    ty += step_y
                if tx == px and ty == py:
                    return False
        elif pt in ['R', 'Q']:
            if px == x or py == y:
                step_x = 0 if px == x else (1 if px > x else -1)
                step_y = 0 if py == y else (1 if py > y else -1)
                tx, ty = x + step_x, y + step_y
                while tx != px or ty != py:
                    if coords_to_square(tx, ty) in new_pieces:
                        break
                    tx += step_x
                    ty += step_y
                if tx == px and ty == py:
                    return False
    return True

def evaluate_move(move, to_play, pieces, memory):
    score = 0
    color = 'w' if to_play == 'white' else 'b'
    from_sq = move[:2]
    to_sq = move[2:4] if len(move) <= 5 else move[2:4]
    piece_type = pieces[from_sq][1]
    
    # Capture bonus
    capture_val = 0
    if to_sq in pieces:
        capture_val = piece_values.get(pieces[to_sq][1], 0)
    score += capture_val * 10
    
    # Promotion bonus
    if len(move) == 5:
        promo = move[4]
        if promo == 'q':
            score += 90
        else:
            score += 50
    
    # Center control
    if piece_type == 'P' and to_sq in center_squares:
        score += 5
    
    # Knight position bonus
    if piece_type == 'N':
        x, y = square_to_coords(to_sq)
        score += knight_bonus[y][x] * 2
    
    # King safety (castling)
    if piece_type == 'K' and (abs(ord(from_sq[0]) - ord(to_sq[0])) == 2):
        score += 50
    
    # Penalty for moving king
    if piece_type == 'K' and 'king_moved' not in memory:
        score -= 30
    
    # Development bonus (moving minor pieces out)
    if piece_type in ['N', 'B'] and from_sq[1] in ['1', '2'] and to_sq[1] in ['3','4','5','6']:
        score += 2
    
    # Check for immediate checkmate
    temp_pieces = {}
    # Applying move to temp_pieces
    # Skipped for performance; approximated by high capture/check score
    
    return score

def policy(pieces, to_play, memory):
    legal_moves = get_legal_moves(pieces, to_play, memory)
    if not legal_moves:
        return ('', memory)
    
    best_move = None
    best_score = -99999
    
    for move in legal_moves:
        score = evaluate_move(move, to_play, pieces, memory)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Update memory for king moves
    if best_move.startswith('e1') or best_move.startswith('e8'):
        memory['king_moved'] = True
    return (best_move, memory)
