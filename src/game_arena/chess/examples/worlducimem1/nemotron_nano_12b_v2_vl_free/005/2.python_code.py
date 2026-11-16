
import itertools

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    def square_to_coord(sq):
        return (ord(sq[0]) - ord('a'), int(sq[1]) - 1)

    def coord_to_square(coord):
        return f"{chr(coord[0] + ord('a'))}{coord[1] + 1}"

    def is_valid(x, y):
        return 0 <= x < 8 and 0 <= y < 8

    current_color = to_play[0]
    board = [[None for _ in range(8)] for _ in range(8)]
    for sq, pcode in pieces.items():
        f, r = square_to_coord(sq)
        board[r][f] = pcode

    king_pos = None
    for sq, p in pieces.items():
        if p.startswith(current_color) and p[1] == 'K':
            king_pos = square_to_coord(sq)
            break
    if not king_pos:
        return (next(iter(pieces)), memory)

    legal_moves = []
    enemy_color = 'b' if current_color == 'w' else 'w'

    def check_piece_moves(piece_color, piece_type, f, r):
        moves = []
        if piece_type == 'P':
            if piece_color == 'w':
                target_rank = rank + 1
                if target_rank < 8 and not board[target_rank][file]:
                    moves.append((file, target_rank))
                if rank == 1 and target_rank < 8 and not board[target_rank][file] and not board[target_rank + 1][file]:
                    moves.append((file, target_rank + 1))
                for dx in (-1, 1):
                    target_f = file + dx
                    target_r = rank + 1
                    if 0 <= target_f < 8 and 0 <= target_r < 8 and board[target_r][target_f] and board[target_r][target_f][0] != piece_color:
                        moves.append((target_f, target_r))
            else:
                target_rank = rank - 1
                if target_rank >= 0 and not board[target_rank][file]:
                    moves.append((file, target_rank))
                if rank == 6:
                    if board[rank - 1][file] is None and board[rank - 2][file] is None:
                        moves.append((file, rank - 2))
                for dx in (-1, 1):
                    target_f = file + dx
                    target_r = rank - 1
                    if 0 <= target_f < 8 and 0 <= target_r < 8 and board[target_r][target_f] and board[target_r][target_f][0] != piece_color:
                        moves.append((target_f, target_r))
        elif piece_type == 'R':
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                x, y = file + dx, rank + dy
                while is_valid(x, y):
                    if board[y][x] is not None:
                        if board[y][x][0] != piece_color:
                            moves.append((x, y))
                        break
                    else:
                        moves.append((x, y))
                    x += dx
                    y += dy
        elif piece_type == 'B':
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                x, y = file + dx, rank + dy
                while is_valid(x, y):
                    if board[y][x] is not None:
                        if board[y][x][0] != piece_color:
                            moves.append((x, y))
                        break
                    else:
                        moves.append((x, y))
                    x += dx
                    y += dy
        elif piece_type == 'Q':
            moves += gen_rook(file, rank, current_color) + gen_bishop(file, rank, current_color)
        elif piece_type == 'N':
            for dx, dy in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                x, y = file + dx, rank + dy
                if is_valid(x, y) and (board[y][x] is None or board[y][x][0] != pcolor):
                    moves.append((x, y))
        elif piece_type == 'K':
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                x, y = file + dx, rank + dy
                if is_valid(x, y) and (board[y][x] is None or board[y][x][0] != pcolor):
                    moves.append((x, y))
            if current_color == 'w' and king_coords == (4, 0):
                rook_x, rook_y = 7, 0
                if board[rook_y][rook_x] == 'wR' and board[0][file + 1][rank] is None and board[0][file + 2][rank] is None:
                    if king_pos == (4, 0):
                        if not (attack_check((4, 0), (5, 0), enemy_color) or attack_check((4, 0), (6, 0), enemy_color)):
                            legal_moves.append(coord_to_square((6, 0)))
            elif current_color == 'b' and king_coords == (4, 7):
                rook_x, rook_y = 7, 7
                if board[rook_y][rook_x] == 'bR' and board[7][file + 1][rank] is None and board[7][file + 2][rank] is None:
                    if king_pos == (4, 7):
                        if not (attack_check((4, 7), (5, 7), enemy_color) or attack_check((4, 7), (6, 7), enemy_color)):
                            legal_moves.append(coord_to_square((6, 7)))
        elif piece_type == 'K':
            moves = []
            for dx, dy in [(-1, 0), (1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                x, y = file + dx, rank + dy
                if is_valid(x, y) and (board[y][x] is None or board[y][x][0] != pcolor):
                    moves.append((x, y))
            if current_color == 'w' and (file, rank) == (4, 0):
                if board[0][7][0] == 'w' and board[0][7][1] == 'R' and board[0][file + 1][rank] is None and board[0][file + 2][rank] is None:
                    if all(board[y][x] is None or board[y][x][0] != enemy_color for y, x in [(4, 0), (5, 0), (6, 0), (7, 0)]):
                        moves.append((6, 0))
            elif current_color == 'b' and (file, rank) == (4, 7):
                if board[7][7][0] == 'b' and board[7][7][1] == 'R' and board[7][file + 1][rank] is None and board[7][file + 2][rank] is None:
                    if all(board[y][x] is None or board[y][x][0] != enemy_color for y, x in [(4, 7), (5, 7), (6, 7), (7, 7)]):
                        moves.append((6, 7))
        return [coord_to_square((x, y)) for x, y in moves]

    def attack_check(square, move_square, enemy_color):
        x, y = square_to_coord(square)
        mx, my = square_to_coord(move_square)
        for fx in range(8):
            for fy in range(8):
                p = board[fy][fx]
                if not p or p[0] == current_color:
                    continue
                ptype = p[1]
                if ptype == 'N':
                    moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                    for dx, dy in moves:
                        tx, ty = fx + dx, fy + dy
                        if (tx, ty) == (mx, my):
                            return True
                elif ptype == 'B':
                    if (fx - mx) * (fy - my) == 0:
                        continue
                    dx = (mx - fx) // abs(mx - fx) if mx != fx else 0
                    dy = (my - fy) // abs(my - fy) if my != fy else 0
                    x_step, y_step = fx, fy
                    while is_valid(x_step + dx, y_step + dy):
                        x_step += dx
                        y_step += dy
                        if (x_step, y_step) == (mx, my):
                            return True
                        if board[y_step][x_step] is not None:
                            break
                elif ptype == 'R':
                    if fx == mx or fy == my:
                        dx = (mx - fx) // abs(mx - fx) if mx != fx else 0
                        dy = (my - fy) // abs(my - fy) if my != fy else 0
                        x_step, y_step = fx, fy
                        while is_valid(x_step + dx, y_step + dy):
                            x_step += dx
                            y_step += dy
                            if (x_step, y_step) == (mx, my):
                                return True
                            if board[y_step][x_step] is not None:
                                break
                elif ptype == 'Q':
                    if fx == mx or fy == my or (fx - mx) * (fy - my) == 0:
                        dx = (mx - fx) // abs(mx - fx) if mx != fx else 0
                        dy = (my - fy) // abs(my - fy) if my != fy else 0
                        x_step, y_step = fx, fy
                        while is_valid(x_step + dx, y_step + dy):
                            x_step += dx
                            y_step += dy
                            if (x_step, y_step) == (mx, my):
                                return True
                            if board[y_step][x_step] is not None:
                                break
                elif ptype == 'P':
                    px, py = square_to_coord(p)
                    if ((current_color == 'w' and ptype is ('w') and my == py + 1 and x == fx + (mx - px)) or
                        (current_color == 'b' and ptype is ('b') and my == py - 1 and x == fx + (mx - px))):
                        return True
                elif ptype == 'K':
                    if abs(fx - mx) <= 1 and abs(fy - my) <= 1:
                        return True
        return False

    for f in range(8):
        for r in range(8):
            piece = board[r][f]
            if not piece:
                continue
            pcolor, ptype = piece
            if pcolor != current_color:
                continue
            if ptype == 'P':
                if current_color == 'w':
                    target_r = r + 1
                    if target_r < 8 and not board[target_r][f]:
                        from_sq = coord_to_square((f, r))
                        to_sq = coord_to_square((f, target_r))
                        if not attack_check(coord_to_square(king_pos), (f, target_r), enemy_color):
                            legal_moves.append(to_sq + from_sq)
                    if r == 1:
                        target_r = r + 2
                        if target_r < 8 and not board[target_r][f] and not board[target_r - 1][f]:
                            from_sq = coord_to_square((f, r))
                            to_sq = coord_to_square((f, target_r))
                            if not attack_check(coord_to_square(king_pos), (f, target_r), enemy_color):
                                legal_moves.append(to_sq + from_sq)
                    for dx in (-1, 1):
                        target_f = f + dx
                        target_r = r + 1
                        if 0 <= target_f < 8 and target_r < 8:
                            if board[target_r][target_f] and board[target_r][target_f][0] == enemy_color:
                                from_sq = coord_to_square((f, r))
                                to_sq = coord_to_square((target_f, target_r))
                                if not attack_check(coord_to_square(king_pos), (target_f, target_r), enemy_color):
                                    legal_moves.append(to_sq + from_sq)
                else:
                    target_r = r - 1
                    if target_r >= 0 and not board[target_r][f]:
                        from_sq = coord_to_square((f, r))
                        to_sq = coord_to_square((f, target_r))
                        if not attack_check(coord_to_square(king_pos), (f, target_r), enemy_color):
                            legal_moves.append(to_sq + from_sq)
                    if r == 6:
                        target_r = r - 2
                        if board[target_r][f] is None and board[target_r + 1][f] is None:
                            from_sq = coord_to_square((f, r))
                            to_sq = coord_to_square((f, target_r))
                            if not attack_check(coord_to_square(king_pos), (f, target_r), enemy_color):
                                legal_moves.append(to_sq + from_sq)
                    for dx in (-1, 1):
                        target_f = f + dx
                        target_r = r - 1
                        if 0 <= target_f < 8 and target_r >= 0:
                            if board[target_r][target_f] and board[target_r][target_f][0] == enemy_color:
                                from_sq = coord_to_square((f, r))
                                to_sq = coord_to_square((target_f, target_r))
                                if not attack_check(coord_to_square(king_pos), (target_f, target_r), enemy_color):
                                    legal_moves.append(to_sq + from_sq)
            elif ptype == 'R':
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    x, y = f + dx, r + dy
                    while is_valid(x, y):
                        if board[y][x] is None or board[y][x][0] != pcolor:
                            from_sq = coord_to_square((f, r))
                            to_sq = coord_to_square((x, y))
                            if not attack_check(coord_to_square(king_pos), (x, y), enemy_color):
                                legal_moves.append(to_sq + from_sq)
                        if board[y][x] is not None:
                            break
                        x += dx
                        y += dy
            elif ptype == 'B':
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    x, y = f + dx, r + dy
                    while is_valid(x, y):
                        if board[y][x] is None or board[y][x][0] != pcolor:
                            from_sq = coord_to_square((f, r))
                            to_sq = coord_to_square((x, y))
                            if not attack_check(coord_to_square(king_pos), (x, y), enemy_color):
                                legal_moves.append(to_sq + from_sq)
                        if board[y][x] is not None:
                            break
                        x += dx
                        y += dy
            elif ptype == 'Q':
                moves = []
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    x, y = f + dx, r + dy
                    while is_valid(x, y):
                        if board[y][x] is None or board[y][x][0] != pcolor:
                            moves.append((x, y))
                        if board[y][x] is not None:
                            break
                        x += dx
                        y += dy
                for x, y in moves:
                    if not attack_check(coord_to_square(king_pos), (x, y), enemy_color):
                        legal_moves.append(coord_to_square((x, y)) + coord_to_square((f, r)))
            elif ptype == 'N':
                for dx, dy in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                    x, y = f + dx, r + dy
                    if is_valid(x, y) and (board[y][x] is None or board[y][x][0] != pcolor):
                        from_sq = coord_to_square((f, r))
                        to_sq = coord_to_square((x, y))
                        if not attack_check(coord_to_square(king_pos), (x, y), enemy_color):
                            legal_moves.append(to_sq + from_sq)
            elif ptype == 'K':
                for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    x, y = f + dx, r + dy
                    if is_valid(x, y) and (board[y][x] is None or board[y][x][0] != pcolor):
                        from_sq = coord_to_square((f, r))
                        to_sq = coord_to_square((x, y))
                        if not attack_check(coord_to_square(king_pos), (x, y), enemy_color):
                            legal_moves.append(to_sq + from_sq)
                if current_color == 'w' and (f, r) == (4, 0):
                    rook_sq = (7, 0)
                    if board[rook_y][rook_x] == 'wR':
                        if all(board[0][i] is None for i in range(5, 7)):
                            king_check = False
                            for move in legal_moves:
                                if move.startswith('e1g1'):
                                    king_check = False
                                    for fx in range(8):
                                        for fy in range(8):
                                            p = board[fy][fx]
                                            if p and p[0] == enemy_color:
                                                if (fx + 1, fy) == (6, 0) or (fx + 2, fy) == (6, 0):
                                                    king_check = True
                                                    break
                        if not king_check:
                            legal_moves.append('e1g1')
                elif current_color == 'b' and (f, r) == (4, 7):
                    rook_sq = (7, 7)
                    if board[rook_y][rook_x] == 'bR':
                        if all(board[7][i] is None for i in range(5, 7)):
                            k_check = False
                            for move in legal_moves:
                                if move.startswith('e7c7'):
                                    k_check = False
                                    for fx in range(8):
                                        for fy in range(8):
                                            p = board[fy][fx]
                                            if p and p[0] == enemy_color:
                                                if (fx - 1, fy) == (5, 7) or (fx - 2, fy) == (5, 7):
                                                    k_check = True
                                                    break
                        if not k_check:
                            legal_moves.append('e7c7')
            elif ptype == 'K':
                pass

    moves_with_promotion = []
    for move in legal_moves:
        if len(move) == 6:
            from_sq, to_sq = move[:2], move[4:]
            promotion = 'q'
            captured_sq = to_sq
            to_file = ord(captured_sq[0]) - ord('a')
            to_rank = int(captured_sq[1]) - 1
            if board[to_rank][to_file]:
                captured_piece = board[to_rank][to_file][1]
                if captured_piece in ['Q', 'R', 'B', 'N', 'P']:
                    move_value = max(1, current_value.get(captured_piece, 0) - current_value.get('P', 1))
                    moves_with_promotion.append((move_value, move))
                    continue
            if current_color == 'b' and to_rank == 0:
                moves_with_promotion.append((10000, move))
            elif current_color == 'w' and to_rank == 7:
                moves_with_promotion.append((10000, move))
        else:
            moves_with_promotion.append((-1, move))

    moves_with_promotion.sort(reverse=True)
    if moves_with_promotion:
        return (moves_with_promotion[0][1], {})

    attack_rank = None
    attack_file = None
    max_material = -1
    for f in range(8):
        for r in range(8):
            piece = board[r][f]
            if piece and piece[0] == enemy_color:
                value = current_value.get(piece[1], 0)
                if value > max_material:
                    max_material = value
                    attack_rank = f
                    attack_file = r

    best_move = None
    max_eval = -float('inf')
    for move in legal_moves:
        from_sq = move[:2]
        to_sq = move[2:]
        from_f, from_r = square_to_coord(from_sq)
        to_f = ord(to_sq[0]) - ord('a')
        to_r = int(to_sq[1]) - 1
        if board[to_r][to_f] and board[to_r][to_f][0] == enemy_color:
            value = {'Q': 900, 'R': 500, 'B': 330, 'N': 320, 'P': 100, 'K': 9999}.get(board[to_r][to_f][1], 0)
        else:
            value = 0
        if current_color == 'w':
            rank = 7 - from_r
        else:
            rank = from_r
        eval = value + ((from_f - attack_file) ** 2 + (from_r - attack_rank) ** 2) * -1
        if eval > max_eval:
            max_eval = eval
            best_move = move

    return (best_move, memory) if best_move else (next(iter(legal_moves)), memory)
