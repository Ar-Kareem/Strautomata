
import copy

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Create board: 8x8, row 0 = rank 1, col 0 = file a
    board = [['' for _ in range(8)] for _ in range(8)]
    for sq, p in pieces.items():
        col = ord(sq[0]) - ord('a')
        row = int(sq[1]) - 1
        board[row][col] = p
    
    player_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if player_color == 'w' else 'w'
    
    # Find king's position
    player_king_sq = None
    for r in range(8):
        for c in range(8):
            if board[r][c] == player_color + 'K':
                player_king_sq = (r, c)
                break
    if not player_king_sq:
        # Fallback, though shouldn't happen
        return 'e2e4', memory  # Dummy move
    
    # Generate candidate moves (ignoring check for now)
    candidate_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if len(piece) != 2 or piece[0] != player_color:
                continue
            piece_type = piece[1]
            if piece_type == 'P':
                candidate_moves.extend(get_pawn_moves(board, r, c, player_color))
            elif piece_type == 'N':
                candidate_moves.extend(get_knight_moves(board, r, c, player_color))
            elif piece_type == 'B':
                candidate_moves.extend(get_bishop_moves(board, r, c, player_color))
            elif piece_type == 'R':
                candidate_moves.extend(get_rook_moves(board, r, c, player_color))
            elif piece_type == 'Q':
                candidate_moves.extend(get_queen_moves(board, r, c, player_color))
            elif piece_type == 'K':
                candidate_moves.extend(get_king_moves(board, r, c, player_color))
    
    # Filter to legal moves (simulate and check king safety)
    legal_moves = []
    for move in candidate_moves:
        if is_legal_move(board, move, player_color, opp_color, player_king_sq):
            legal_moves.append(move)
    if not legal_moves:
        return 'e2e4', memory  # Dummy fallback
    
    # Evaluate each legal move greedily (1-ply material)
    best_move = None
    best_score = float('-inf')
    mat_vals = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    for move in legal_moves:
        score = evaluate_board_after_move(board, move, player_color, opp_color, mat_vals)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Convert move to string
    r1, c1, r2, c2 = move[0], move[1], move[2], move[3]
    from_sq = chr(c1 + ord('a')) + str(r1 + 1)
    to_sq = chr(c2 + ord('a')) + str(r2 + 1)
    move_str = from_sq + to_sq
    # Handle promotion (assume to queen)
    piece = board[r1][c1]
    if piece[1] == 'P' and ((player_color == 'w' and r2 == 7) or (player_color == 'b' and r2 == 0)):
        move_str += 'q'
    
    return move_str, memory

def get_pawn_moves(board, r, c, color):
    moves = []
    dir = 1 if color == 'w' else -1
    # Forward one
    nr = r + dir
    if 0 <= nr < 8 and board[nr][c] == '':
        moves.append((r, c, nr, c))
        # Two steps from start
        if (color == 'w' and r == 1) or (color == 'b' and r == 6):
            nr2 = r + 2 * dir
            if 0 <= nr2 < 8 and board[nr2][c] == '':
                moves.append((r, c, nr2, c))
    # Captures
    for dc in [-1, 1]:
        nc = c + dc
        nr = r + dir
        if 0 <= nc < 8 and 0 <= nr < 8 and board[nr][nc] != '' and board[nr][nc][0] != color:
            moves.append((r, c, nr, nc))
    return moves

def get_knight_moves(board, r, c, color):
    moves = []
    deltas = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and (board[nr][nc] == '' or board[nr][nc][0] != color):
            moves.append((r, c, nr, nc))
    return moves

def get_bishop_moves(board, r, c, color):
    moves = []
    deltas = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in deltas:
        nr, nc = r, c
        while True:
            nr += dr
            nc += dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            if board[nr][nc] == '':
                moves.append((r, c, nr, nc))
            elif board[nr][nc][0] != color:
                moves.append((r, c, nr, nc))
                break
            else:
                break  # Blocked by own piece
    return moves

def get_rook_moves(board, r, c, color):
    moves = []
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in deltas:
        nr, nc = r, c
        while True:
            nr += dr
            nc += dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            if board[nr][nc] == '':
                moves.append((r, c, nr, nc))
            elif board[nr][nc][0] != color:
                moves.append((r, c, nr, nc))
                break
            else:
                break
    return moves

def get_queen_moves(board, r, c, color):
    moves = get_rook_moves(board, r, c, color) + get_bishop_moves(board, r, c, color)
    return moves

def get_king_moves(board, r, c, color):
    moves = []
    deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and (board[nr][nc] == '' or board[nr][nc][0] != color):
            moves.append((r, c, nr, nc))
    # Note: Castling not implemented for simplicity
    return moves

def is_legal_move(board, move, player_color, opp_color, player_king_sq):
    r1, c1, r2, c2 = move
    # Simulate
    orig_from = board[r1][c1]
    orig_to = board[r2][c2]
    board[r2][c2] = orig_from
    board[r1][c1] = ''
    # Updated king sq if king moved
    curr_king_sq = player_king_sq if orig_from != player_color + 'K' else (r2, c2)
    # Check if king attacked
    legal = not is_under_attack(board, curr_king_sq, opp_color)
    # Undo
    board[r1][c1] = orig_from
    board[r2][c2] = orig_to
    return legal

def is_under_attack(board, kr, kc, attacking_color):
    # Knights
    deltas = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
    for dr, dc in deltas:
        nr, nc = kr + dr, kc + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == attacking_color + 'N':
            return True
    # Pawns
    pawn_dir = -1 if attacking_color == 'w' else 1
    for dc in [-1, 1]:
        nr, nc = kr + pawn_dir, kc + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == attacking_color + 'P':
            return True
    # Rooks/Queens horizontal/vertical
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in deltas:
        nr, nc = kr, kc
        while True:
            nr += dr
            nc += dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            piece = board[nr][nc]
            if piece != '':
                if piece[0] == attacking_color and piece[1] in ['R', 'Q']:
                    return True
                break
    # Bishops/Queens diagonals
    deltas = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in deltas:
        nr, nc = kr, kc
        while True:
            nr += dr
            nc += dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            piece = board[nr][nc]
            if piece != '':
                if piece[0] == attacking_color and piece[1] in ['B', 'Q']:
                    return True
                break
    # Kings (adjacent)
    deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in deltas:
        nr, nc = kr + dr, kc + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == attacking_color + 'K':
            return True
    return False

def evaluate_board_after_move(board, move, player_color, opp_color, mat_vals):
    def mat_count(board, color):
        m = 0
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if len(p) == 2 and p[0] == color:
                    m += mat_vals[p[1]]
        return m
    r1, c1, r2, c2 = move
    orig_from = board[r1][c1]
    orig_to = board[r2][c2]
    # Simulate
    board[r2][c2] = orig_from
    board[r1][c1] = ''
    new_player = mat_count(board, player_color)
    new_opp = mat_count(board, opp_color)
    score = new_player - new_opp  # Positive favors player
    # Undo
    board[r1][c1] = orig_from
    board[r2][c2] = orig_to
    return score
