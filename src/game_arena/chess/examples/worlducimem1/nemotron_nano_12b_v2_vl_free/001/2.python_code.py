
piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def generate_moves(pieces, to_play):
    current_color = 'w' if to_play == 'white' else 'b'
    color_char = current_color[0]
    moves = []

    for square in pieces:
        piece = pieces[square]
        if piece[0] != color_char:
            continue

        color, ptype = piece
        rank = int(square[1])
        file = ord(square[0])

        # King
        if ptype == 'K':
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    new_file = file + dx
                    new_rank = rank + dy
                    if 'a' <= chr(new_file) <= 'h' and 1 <= new_rank <= 8:
                        new_sq = chr(new_file) + str(new_rank)
                        target = pieces.get(new_sq, "")
                        if target == "" or target[0] != color_char:
                            moves.append((square, new_sq))

        # Knight
        elif ptype == 'N':
            for dx in [-2, 2]:
                for dy in [-1, 1]:
                    new_file = chr(ord(file) + dx)
                    new_rank = rank + dy
                    if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                        new_sq = new_file + str(new_rank)
                        target = pieces.get(new_sq, "")
                        if target == "" or target[0] != color_char:
                            moves.append((square, new_sq))
            for dx in [-1, 1]:
                for dy in [-2, 2]:
                    new_file = chr(ord(file) + dx)
                    new_rank = rank + dy
                    if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                        new_sq = new_file + str(new_rank)
                        target = pieces.get(new_sq, "")
                        if target == "" or target[0] != color_char:
                            moves.append((square, new_sq))

        # Rook
        elif ptype == 'R':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in directions:
                nx, ny = file, rank
                while True:
                    nx += dx
                    ny += dy
                    if nx < ord('a') or nx > ord('h') or ny < 1 or ny > 8:
                        break
                    move_sq = chr(nx) + str(ny)
                    target = pieces.get(move_sq, "")
                    if target == "":
                        moves.append((square, move_sq))
                    elif target[0] != color_char:
                        moves.append((square, move_sq))
                        break
                    else:
                        break

        # Bishop
        elif ptype == 'B':
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dx, dy in directions:
                nx, ny = file, rank
                while True:
                    nx += dx
                    ny += dy
                    if nx < ord('a') or nx > ord('h') or ny < 1 or ny > 8:
                        break
                    move_sq = chr(nx) + str(ny)
                    target = pieces.get(move_sq, "")
                    if target == "":
                        moves.append((square, move_sq))
                    elif target[0] != color_char:
                        moves.append((square, move_sq))
                        break
                    else:
                        break

        # Queen
        elif ptype == 'Q':
            rook_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            bishop_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            moves.extend(get_sliding_moves(pieces, square, rook_dirs, color_char))
            moves.extend(get_sliding_moves(pieces, square, bishop_dirs, color_char))

        # Pawn
        elif ptype == 'P':
            if current_color == 'w':
                # Move forward
                new_rank = rank + 1
                if new_rank <= 8:
                    new_sq = square[0] + str(new_rank)
                    if pieces.get(new_sq, "")[0] != color_char:
                        moves.append((square, new_sq))
                # Double move from starting rank
                if rank == 2:
                    new_rank = rank + 2
                    if pieces.get(square[0] + str(rank + 1), "")[0] != color_char and \
                       pieces.get(new_sq, "")[0] != color_char:
                        moves.append((square, new_sq))

                # Capture
                for dx in (-1, 1):
                    new_file = chr(ord(square[0]) + dx)
                    new_rank = rank + 1
                    if new_file >= 'a' and new_file <= 'h' and new_rank <= 8:
                        new_sq = new_file + str(new_rank)
                        target = pieces.get(new_sq, "")
                        if target != "" and target[0] != color_char:
                            moves.append((square, new_sq))

            else:
                # Move forward
                new_rank = rank - 1
                if new_rank >= 1:
                    new_sq = square[0] + str(new_rank)
                    if pieces.get(new_sq, "")[0] != color_char:
                        moves.append((square, new_sq))

                # Double move from starting rank
                if rank == 7:
                    new_rank = rank - 2
                    if pieces.get(square[0] + str(rank - 1), "")[0] != color_char and \
                       pieces.get(new_sq, "")[0] != color_char:
                        moves.append((square, new_sq))

                # Capture
                for dx in (-1, 1):
                    new_file = chr(ord(square[0]) + dx)
                    new_rank = rank - 1
                    if new_file >= 'a' and new_file <= 'h' and new_rank >= 1:
                        new_sq = new_file + str(new_rank)
                        target = pieces.get(new_sq, "")
                        if target != "" and target[0] != color_char:
                            moves.append((square, new_sq))

    return moves

def get_sliding_moves(pieces, start_sq, directions, color_char):
    moves = []
    rank = int(start_sq[1])
    file = ord(start_sq[0])
    for dx, dy in directions:
        nx, ny = file, rank
        while True:
            nx += dx
            ny += dy
            if nx < ord('a') or nx > ord('h') or ny < 1 or ny > 8:
                break
            move_sq = f"{chr(nx)}{ny}"
            target = pieces.get(move_sq, "")
            if target == "":
                moves.append((start_sq, move_sq))
            elif target[0] != color_char:
                moves.append((start_sq, move_sq))
                break
            else:
                break
    return moves

def is_move_legal(board, move, current_color, king_sq):
    from_sq, to_sq = move[0], move[1]
    new_board = dict(board)
    # Remove the piece from the original square
    new_board[from_sq] = "" if to_sq in new_board else ""
    # Place the piece at the new square
    new_board[to_sq] = new_board.get(to_sq, "") + current_color

    # Check if the king is in check
    king_value = 'K' if current_color == 'w' else 'k'
    king_sq_new = king_sq
    for sq, pc in new_board.items():
        if pc == king_value:
            king_sq_new = sq
            break

    for sq, pc in new_board.items():
        if pc[0] == current_color:
            continue
        moves = get_attack_squares(sq, new_board, pc[1])
        if king_sq_new in moves:
            return False
    return True

def get_attack_squares(sq, board, ptype):
    # Knight
    if ptype == 'N':
        moves = []
        x, y = ord(sq[0]), int(sq[1])
        for dx in [-2, 2]:
            for dy in [-1, 1]:
                nx = x + dx
                ny = y + dy
                if 'a' <= chr(nx) <= 'h' and 1 <= ny <= 8:
                    moves.append(chr(nx) + str(ny))
        for dx in [-1, 1]:
            for dy in [-2, 2]:
                nx = x + dx
                ny = y + dy
                if 'a' <= chr(nx) <= 'h' and 1 <= ny <= 8:
                    moves.append(chr(nx) + str(ny))
        return moves

    # Bishop
    elif ptype == 'B':
        moves = []
        x, y = ord(sq[0]), int(sq[1])
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in directions:
            nx, ny = x, y
            while True:
                nx += dx
                ny = ny + dy
                if nx < ord('a') or nx > ord('h') or ny < 1 or ny > 8:
                    break
                moves.append(chr(nx) + str(ny))
        return moves

    # Rook
    elif ptype == 'R':
        moves = []
        x, y = ord(sq[0]), int(sq[1])
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            nx, ny = x, y
            while True:
                nx += dx
                ny += dy
                if nx < ord('a') or nx > ord('h') or ny < 1 or ny > 8:
                    break
                moves.append(chr(nx) + str(ny))
        return moves

    # Queen
    elif ptype == 'Q':
        return get_attack_squares(sq, board, 'B') + get_attack_squares(sq, board, 'R')

    # Pawn
    elif ptype == 'P':
        x, y = ord(sq[0]), int(sq[1])
        moves = []
        if ptype == 'w':
            # Forward
            if y + 1 <= 8:
                moves.append(sq[0] + str(y + 1))
            # Two steps
            if y == 2:
                if sq[0] + str(y + 2) not in board and sq[0] + str(y + 1) not in board:
                    moves.append(sq[0] + str(y + 2))
            # Capture
            for dx in [-1, 1]:
                new_file = chr(x + dx)
                new_rank = y + 1
                if 'a' <= new_file <= 'h' and new_rank <= 8:
                    moves.append(new_file + str(new_rank))
        else:
            # Forward
            if y - 1 >= 1:
                moves.append(sq[0] + str(y - 1))
            # Two steps
            if y == 7:
                if sq[0] + str(y - 2) not in board and sq[0] + str(y - 1) not in board:
                    moves.append(sq[0] + str(y - 2))
            # Capture
            for dx in [-1, 1]:
                new_file = chr(x + dx)
                new_rank = y - 1
                if 'a' <= new_file <= 'h' and new_rank >= 1:
                    moves.append(new_file + str(new_rank))
        return moves

    return []

def policy(pieces: dict, to_play: str, memory: dict) -> tuple[str, dict]:
    legal_moves = generate_moves(pieces, to_play)

    current_color = 'w' if to_play == 'white' else 'b'
    king_sq = None
    for sq, pc in pieces.items():
        if pc == f"{current_color}K":
            king_sq = sq
            break

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        from_sq, to_sq = move[0], move[1]
        score = 0

        # Check if move is legal
        simulated = True
        # Dummy check only (not full check detection due to complexity)
        # New board simulation (simplified)
        new_board = dict(pieces)
        new_board[from_sq] = ""
        new_board[to_sq] = pieces[from_sq]

        # Check if king is in check
        king_sq_new = king_sq
        for sq, pc in new_board.items():
            if pc == f"{current_color}K":
                king_sq_new = sq
                break
        is_attacked = False
        for sq, pc in new_board.items():
            if pc[0] != current_color:
                for target in get_attack_squares(sq, new_board, pc[1]):
                    if target == king_sq_new:
                        is_attacked = True
        if is_attacked:
            continue

        # Evaluate the move
        captured_piece = pieces.get(to_sq, '')
        if captured_piece:
            score += piece_values[captured_piece[1]]
        if current_color == 'w' and to_sq in ['h8']:
            score += 10  # promotion to queen
        elif current_color == 'b' and to_sq in ['h1']:
            score += 10  # promotion to queen

        if from_sq == king_sq:
            score += 5  # king moved

        if score > best_score:
            best_score = score
            best_move = f"{move[0]}{move[1]}"

    if best_move is None:
        best_move = f"{list(legal_moves.keys())[0]}{list(legal_moves.keys())[1]}" if legal_moves else ""

    return (best_move, memory)
