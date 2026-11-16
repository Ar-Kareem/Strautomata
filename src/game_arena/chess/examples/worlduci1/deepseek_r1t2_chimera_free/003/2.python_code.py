
import itertools

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def square_to_pos(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return (file, rank)

def pos_to_square(pos):
    file, rank = pos
    return chr(file + ord('a')) + str(rank + 1)

def is_inside_board(pos):
    return 0 <= pos[0] < 8 and 0 <= pos[1] < 8

def can_attack(pos1, pos2, board):
    fx, fy = pos1
    tx, ty = pos2
    dx = tx - fx
    dy = ty - fy
    piece = board[fy][fx]
    if not piece or abs(dx) + abs(dy) == 0:
        return False

    ptype = piece[1]
    attacker_color = piece[0]

    if ptype == 'P':
        attack_dir = 1 if attacker_color == 'w' else -1
        return dy == attack_dir and abs(dx) == 1
    elif ptype == 'N':
        return (abs(dx) == 2 and abs(dy) == 1) or (abs(dx) == 1 and abs(dy) == 2)
    elif ptype == 'B':
        if abs(dx) == abs(dy):
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            for i in range(1, abs(dx)):
                x = fx + step_x * i
                y = fy + step_y * i
                if board[y][x] is not None:
                    return False
            return True
    elif ptype == 'R':
        if dx == 0 or dy == 0:
            if dx == 0:
                step = 1 if dy > 0 else -1
                for r in range(fy + step, ty, step):
                    if board[r][fx] is not None:
                        return False
            else:
                step = 1 if dx > 0 else -1
                for c in range(fx + step, tx, step):
                    if board[fy][c] is not None:
                        return False
            return True
    elif ptype == 'Q':
        if abs(dx) == abs(dy) or dx == 0 or dy == 0:
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            steps = max(abs(dx), abs(dy))
            for i in range(1, steps):
                x = fx + step_x * i
                y = fy + step_y * i
                if board[y][x] is not None:
                    return False
            return True
    elif ptype == 'K':
        return abs(dx) <= 1 and abs(dy) <= 1
    return False

def king_after_move(move, king_pos, board, current_color):
    from_sq, to_sq = move[:2], move[2:4]
    new_king_pos = king_pos
    from_file, from_rank = square_to_pos(from_sq)
    if board[from_rank][from_file] == current_color + 'K':
        new_king_pos = square_to_pos(to_sq)
    return new_king_pos

def is_in_check(king_pos, current_color, board):
    opp_color = 'b' if current_color == 'w' else 'w'
    for rank in range(8):
        for file in range(8):
            pos = (file, rank)
            piece = board[rank][file]
            if piece and piece[0] == opp_color:
                if can_attack(pos, king_pos, board):
                    return True
    return False

def generate_pawn_moves(pos, current_color, board):
    moves = []
    file, rank = pos
    direction = 1 if current_color == 'w' else -1
    start_rank = 1 if current_color == 'w' else 6
    promotions = ['q', 'r', 'b', 'n'] if rank + direction in [0, 7] else [None]

    # Forward moves
    new_pos = (file, rank + direction)
    if is_inside_board(new_pos) and board[new_pos[1]][new_pos[0]] is None:
        for promo in promotions:
            move = pos_to_square(pos) + pos_to_square(new_pos) + (promo if promo else '')
            moves.append(move)

        if rank == start_rank:
            new_pos = (file, rank + 2 * direction)
            if is_inside_board(new_pos) and board[new_pos[1]][new_pos[0]] is None:
                moves.append(pos_to_square(pos) + pos_to_square(new_pos))

    # Captures
    for dx in [-1, 1]:
        new_pos = (file + dx, rank + direction)
        if is_inside_board(new_pos):
            target = board[new_pos[1]][new_pos[0]]
            if target and target[0] != current_color:
                for promo in promotions:
                    move = pos_to_square(pos) + pos_to_square(new_pos) + (promo if promo else '')
                    moves.append(move)
    return moves

def generate_knight_moves(pos, current_color, board):
    moves = []
    file, rank = pos
    targets = [(2, 1), (1, 2), (-1, 2), (-2, 1),
               (-2, -1), (-1, -2), (1, -2), (2, -1)]
    for dx, dy in targets:
        new_pos = (file + dx, rank + dy)
        if is_inside_board(new_pos):
            target = board[new_pos[1]][new_pos[0]]
            if target is None or target[0] != current_color:
                moves.append(pos_to_square(pos) + pos_to_square(new_pos))
    return moves

def generate_sliding_moves(pos, current_color, board, directions):
    moves = []
    file, rank = pos
    for dx, dy in directions:
        for dist in range(1, 8):
            new_pos = (file + dx * dist, rank + dy * dist)
            if not is_inside_board(new_pos):
                break
            target = board[new_pos[1]][new_pos[0]]
            if target:
                if target[0] != current_color:
                    moves.append(pos_to_square(pos) + pos_to_square(new_pos))
                break
            moves.append(pos_to_square(pos) + pos_to_square(new_pos))
    return moves

def generate_king_moves(pos, current_color, board):
    moves = []
    file, rank = pos
    for dx, dy in itertools.product([-1, 0, 1], repeat=2):
        if dx == 0 and dy == 0:
            continue
        new_pos = (file + dx, rank + dy)
        if is_inside_board(new_pos):
            target = board[new_pos[1]][new_pos[0]]
            if target is None or target[0] != current_color:
                moves.append(pos_to_square(pos) + pos_to_square(new_pos))
    return moves

def generate_legal_moves(board, current_color):
    moves = []
    king_pos = None
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if piece and piece[0] == current_color:
                pos = (file, rank)
                ptype = piece[1]
                if ptype == 'K':
                    king_pos = pos

                if ptype == 'P':
                    moves.extend(generate_pawn_moves(pos, current_color, board))
                elif ptype == 'N':
                    moves.extend(generate_knight_moves(pos, current_color, board))
                elif ptype == 'B':
                    moves.extend(generate_sliding_moves(pos, current_color, board, [(-1, -1), (-1, 1), (1, -1), (1, 1)]))
                elif ptype == 'R':
                    moves.extend(generate_sliding_moves(pos, current_color, board, [(-1, 0), (1, 0), (0, -1), (0, 1)]))
                elif ptype == 'Q':
                    directions = [(-1, -1), (-1, 0), (-1, 1),
                                (0, -1),           (0, 1),
                                (1, -1),  (1, 0), (1, 1)]
                    moves.extend(generate_sliding_moves(pos, current_color, board, directions))
                elif ptype == 'K':
                    moves.extend(generate_king_moves(pos, current_color, board))

    # Filter moves leaving king in check
    legal_moves = []
    for move in moves:
        # Create board copy
        new_board = [row.copy() for row in board]
        from_sq, to_sq = move[:2], move[2:4]
        promo = move[4] if len(move) == 5 else None
        from_f, from_r = square_to_pos(from_sq)
        to_f, to_r = square_to_pos(to_sq)
        piece = new_board[from_r][from_f]
        target_piece = new_board[to_r][to_f]

        # Apply move
        new_board[from_r][from_f] = None
        if promo:
            piece = current_color + promo.upper()
        new_board[to_r][to_f] = piece

        # Find king position after move
        current_king_pos = (to_f, to_r) if piece[1] == 'K' else king_pos
        if is_in_check(current_king_pos, current_color, new_board):
            continue

        legal_moves.append(move)

    return legal_moves

def evaluate_move(move, board, current_color):
    from_sq, to_sq = move[:2], move[2:4]
    promo = move[4] if len(move) == 5 else None

    # Get captured piece value
    to_f, to_r = square_to_pos(to_sq)
    captured_piece = board[to_r][to_f]
    captured_value = PIECE_VALUES[captured_piece[1]] if captured_piece else 0

    # Our moved piece
    from_f, from_r = square_to_pos(from_sq)
    moved_piece = board[from_r][from_f]
    moved_value = PIECE_VALUES[moved_piece[1]]

    # Promotion value
    promo_value = 0
    if promo:
        promo_value = PIECE_VALUES[promo.upper()] - PIECE_VALUES['P']

    # Immediate material gain
    score = captured_value + promo_value

    # Safety evaluation
    new_board = [row.copy() for row in board]
    new_board[from_r][from_f] = None
    if promo:
        moved_piece = current_color + promo.upper()
    new_board[to_r][to_f] = moved_piece

    opp_color = 'b' if current_color == 'w' else 'w'
    # Check if moved piece is attacked
    if is_in_check((to_f, to_r), opp_color, new_board):
        score -= moved_value * 0.5  # Penalize moving to attacked square

    return score

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Create board
    board = [[None for _ in range(8)] for _ in range(8)]
    for square, piece_code in pieces.items():
        file, rank = square_to_pos(square)
        board[rank][file] = piece_code

    current_color = 'w' if to_play == 'white' else 'b'
    legal_moves = generate_legal_moves(board, current_color)

    if not legal_moves:
        return ''  # Shouldn't happen in legal positions

    best_move = None
    best_score = -10000
    for move in legal_moves:
        score = evaluate_move(move, board, current_color)
        if score > best_score or (score == best_score and best_move is None):
            best_score = score
            best_move = move

    return best_move if best_move else legal_moves[0]
