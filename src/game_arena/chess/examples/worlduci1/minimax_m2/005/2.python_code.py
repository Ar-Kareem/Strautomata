
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Mapping of square coordinates to board indices
    file_to_col = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
    rank_to_row = {'1':7, '2':6, '3':5, '4':4, '5':3, '6':2, '7':1, '8':0}
    col_to_file = {v:k for k,v in file_to_col.items()}
    row_to_rank = {v:k for k,v in rank_to_row.items()}

    # Convert the pieces dictionary to a 8x8 board
    board = [[None for _ in range(8)] for _ in range(8)]
    for sq, piece in pieces.items():
        col = file_to_col[sq[0]]
        row = rank_to_row[sq[1]]
        board[row][col] = piece

    our_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if our_color == 'w' else 'w'
    
    # Material values for pieces
    piece_values = {'K': 0, 'Q':9, 'R':5, 'B':3, 'N':3, 'P':1}

    # Helper function to convert (row, col) to algebraic notation
    def square_from_coord(col, row):
        return col_to_file[col] + row_to_rank[row]

    # Generate all candidate moves for a piece at (row, col)
    def generate_piece_moves(board, row, col, piece, color):
        moves = []
        piece_type = piece[1]
        if piece_type == 'P':
            # Pawn moves
            direction = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            # Single move forward
            if 0 <= row + direction < 8 and board[row + direction][col] is None:
                if row + direction in [0, 7]:  # Promotion rank
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(square_from_coord(col, row) + square_from_coord(col, row + direction) + promo)
                else:
                    moves.append(square_from_coord(col, row) + square_from_coord(col, row + direction))
                # Double move forward from starting rank
                if row == start_row and board[row + 2*direction][col] is None:
                    moves.append(square_from_coord(col, row) + square_from_coord(col, row + 2*direction))
            # Captures
            for dc in [-1, 1]:
                new_col, new_row = col + dc, row + direction
                if 0 <= new_col < 8 and 0 <= new_row < 8:
                    target = board[new_row][new_col]
                    if target and target[0] != color:
                        if new_row in [0, 7]:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row) + promo)
                        else:
                            moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
        elif piece_type == 'N':
            # Knight moves
            for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = board[new_row][new_col]
                    if not target or target[0] != color:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
        elif piece_type == 'B':
            # Bishop moves
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                new_row, new_col = row + dr, col + dc
                while 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = board[new_row][new_col]
                    if not target:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
                    elif target[0] != color:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
                        break
                    else:
                        break
                    new_row += dr
                    new_col += dc
        elif piece_type == 'R':
            # Rook moves
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                new_row, new_col = row + dr, col + dc
                while 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = board[new_row][new_col]
                    if not target:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
                    elif target[0] != color:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
                        break
                    else:
                        break
                    new_row += dr
                    new_col += dc
        elif piece_type == 'Q':
            # Queen moves (bishop + rook)
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                new_row, new_col = row + dr, col + dc
                while 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = board[new_row][new_col]
                    if not target:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
                    elif target[0] != color:
                        moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
                        break
                    else:
                        break
                    new_row += dr
                    new_col += dc
        elif piece_type == 'K':
            # King moves and castling
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        target = board[new_row][new_col]
                        if not target or target[0] != color:
                            moves.append(square_from_coord(col, row) + square_from_coord(new_col, new_row))
            # Castling
            if color == 'w':
                king_start = (7, 4)  # e1
                if (row, col) == king_start and not board[7][5] and not board[7][6]:
                    # King side
                    if board[7][7] and board[7][7] == 'wR':
                        moves.append('e1g1')
                    # Queen side
                    if board[7][0] and board[7][0] == 'wR' and not board[7][1] and not board[7][2] and not board[7][3]:
                        moves.append('e1c1')
            else:
                king_start = (0, 4)  # e8
                if (row, col) == king_start and not board[0][5] and not board[0][6]:
                    # King side
                    if board[0][7] and board[0][7] == 'bR':
                        moves.append('e8g8')
                    # Queen side
                    if board[0][0] and board[0][0] == 'bR' and not board[0][1] and not board[0][2] and not board[0][3]:
                        moves.append('e8c8')
        return moves

    # Check if a king is in check
    def is_king_in_check(board, color):
        king_sq = None
        for r in range(8):
            for c in range(8):
                if board[r][c] == color + 'K':
                    king_sq = (r, c)
                    break
            if king_sq:
                break
        if not king_sq:
            return False
        kr, kc = king_sq
        opp_color = 'b' if color == 'w' else 'w'
        # Check pawn attacks
        for dc in [-1, 1]:
            r = kr + (1 if color == 'w' else -1)
            c = kc + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == opp_color + 'P':
                    return True
        # Check knight attacks
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            r, c = kr + dr, kc + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == opp_color + 'N':
                    return True
        # Check sliding pieces
        for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
            r, c = kr + dr, kc + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c]:
                    if board[r][c][0] == opp_color:
                        pt = board[r][c][1]
                        if (pt in ['Q', 'R']) or (pt == 'B' and dr != 0 and dc != 0) or (pt == 'R' and dr == 0 or dc == 0):
                            return True
                    break
                r += dr
                c += dc
        # Check opponent king
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = kr + dr, kc + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] == opp_color + 'K':
                        return True
        return False

    # Simulate a move and return new board
    def simulate_move(board, move):
        new_board = [row[:] for row in board]
        from_sq = move[:2]
        to_sq = move[2:4]
        promo = move[4:] if len(move) == 5 else None
        col_from = file_to_col[from_sq[0]]
        row_from = rank_to_row[from_sq[1]]
        col_to = file_to_col[to_sq[0]]
        row_to = rank_to_row[to_sq[1]]
        piece = new_board[row_from][col_from]
        # Handle promotion
        if promo:
            piece = piece[0] + promo.upper()
        # Handle castling
        if piece[1] == 'K' and abs(col_to - col_from) == 2:
            if col_to > col_from:  # King side
                new_board[row_from][7] = None
                new_board[row_from][5] = piece[0] + 'R'
            else:  # Queen side
                new_board[row_from][0] = None
                new_board[row_from][3] = piece[0] + 'R'
        # Move the piece
        new_board[row_from][col_from] = None
        new_board[row_to][col_to] = piece
        return new_board

    # Generate all legal moves
    legal_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[0] == our_color:
                moves = generate_piece_moves(board, r, c, piece, our_color)
                for move in moves:
                    new_board = simulate_move(board, move)
                    if not is_king_in_check(new_board, our_color):
                        legal_moves.append(move)

    # Check for checkmate
    for move in legal_moves:
        new_board = simulate_move(board, move)
        if not any(move for move in generate_legal_moves(new_board, opp_color)):
            if is_king_in_check(new_board, opp_color):
                return move

    # Select move with best material gain
    best_move = None
    best_gain = -999999
    for move in legal_moves:
        new_board = simulate_move(board, move)
        our_material = sum(piece_values[board[r][c][1]] for r in range(8) for c in range(8) if board[r][c] and board[r][c][0] == our_color)
        new_our_material = sum(piece_values[board[r][c][1]] for r in range(8) for c in range(8) if new_board[r][c] and new_board[r][c][0] == our_color)
        gain = new_our_material - our_material
        if gain > best_gain:
            best_gain = gain
            best_move = move

    return best_move if best_move else legal_moves[0]
