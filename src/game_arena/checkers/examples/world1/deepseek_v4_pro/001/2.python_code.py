
import time

class TimeOutError(Exception):
    pass


def get_directions(piece_type, p_color):
    """Return list of (dr, dc) for a piece."""
    if piece_type == 1:  # man
        if p_color == 'b':
            return [(-1, -1), (-1, 1)]
        else:
            return [(1, -1), (1, 1)]
    else:  # king
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def get_capture_sequences(board, p_color, start_pos, sequence, all_sequences):
    """Recursively generate all complete capture sequences from start_pos.
       Modifies board in place and restores it."""
    r, c = start_pos
    piece_type = abs(board[r][c])
    directions = get_directions(piece_type, p_color)
    found_jump = False
    for dr, dc in directions:
        mid_r, mid_c = r + dr, c + dc
        land_r, land_c = r + 2*dr, c + 2*dc
        if 0 <= land_r < 8 and 0 <= land_c < 8:
            if board[mid_r][mid_c] < 0 and board[land_r][land_c] == 0:
                captured = board[mid_r][mid_c]
                original_piece = board[r][c]
                board[r][c] = 0
                board[mid_r][mid_c] = 0
                board[land_r][land_c] = original_piece

                promoted = False
                if original_piece == 1:  # man
                    if (p_color == 'b' and land_r == 0) or (p_color == 'w' and land_r == 7):
                        board[land_r][land_c] = 2
                        promoted = True

                new_sequence = sequence + [(land_r, land_c)]
                if promoted:
                    all_sequences.append(new_sequence)
                else:
                    get_capture_sequences(board, p_color, (land_r, land_c), new_sequence, all_sequences)

                # undo
                board[r][c] = original_piece
                board[mid_r][mid_c] = captured
                board[land_r][land_c] = 0
                found_jump = True

    if not found_jump and len(sequence) > 1:
        all_sequences.append(sequence)


def get_all_moves(board, p_color):
    """Return all legal move sequences for the player p_color.
       Each move is a list of squares [start, ..., end].
       Captures are mandatory when available."""
    captures = []
    for r in range(8):
        for c in range(8):
            if board[r][c] > 0:
                get_capture_sequences(board, p_color, (r, c), [(r, c)], captures)
    if captures:
        return captures

    non_captures = []
    for r in range(8):
        for c in range(8):
            if board[r][c] > 0:
                piece_type = board[r][c]
                for dr, dc in get_directions(piece_type, p_color):
                    land_r, land_c = r + dr, c + dc
                    if 0 <= land_r < 8 and 0 <= land_c < 8:
                        if board[land_r][land_c] == 0:
                            non_captures.append([(r, c), (land_r, land_c)])
    return non_captures


def apply_move(board, sequence, p_color):
    """Apply a move sequence to a copy of the board and return the new board."""
    new_board = [row[:] for row in board]
    for i in range(len(sequence) - 1):
        fr, fc = sequence[i]
        tr, tc = sequence[i+1]
        if abs(tr - fr) == 2:  # capture
            mid_r, mid_c = (fr + tr) // 2, (fc + tc) // 2
            new_board[mid_r][mid_c] = 0
        new_board[tr][tc] = new_board[fr][fc]
        new_board[fr][fc] = 0

    # handle promotion on final square
    final_r, final_c = sequence[-1]
    piece = new_board[final_r][final_c]
    if piece == 1:
        if (p_color == 'b' and final_r == 0) or (p_color == 'w' and final_r == 7):
            new_board[final_r][final_c] = 2
    return new_board


def flip_board(board):
    """Negate all pieces so that the opponent becomes the positive side."""
    return [[-x for x in row] for row in board]


def eval_board(board, p_color):
    """Evaluate board from perspective of p_color (positive pieces)."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == 1:  # my man
                score += 100
                if p_color == 'b':
                    score += (7 - r) * 2
                else:
                    score += r * 2
            elif piece == 2:  # my king
                score += 130
                score += 5 - abs(c - 3.5) * 2
            elif piece == -1:  # opp man
                score -= 100
                if p_color == 'b':
                    score -= r * 2
                else:
                    score -= (7 - r) * 2
            elif piece == -2:  # opp king
                score -= 130
                score -= 5 - abs(c - 3.5) * 2
    return score


def negamax(board, p_color, depth, alpha, beta, start_time, time_limit):
    """Negamax with alpha-beta pruning."""
    if time.time() - start_time > time_limit:
        raise TimeOutError
    if depth == 0:
        return eval_board(board, p_color)

    moves = get_all_moves(board, p_color)
    if not moves:
        # no moves means loss; prefer losing later
        return -10000 - depth

    # move ordering: captures first
    moves.sort(key=lambda m: len(m) == 2)

    for move in moves:
        new_board = apply_move(board, move, p_color)
        opp_color = 'w' if p_color == 'b' else 'b'
        flipped = flip_board(new_board)
        score = -negamax(flipped, opp_color, depth-1, -beta, -alpha, start_time, time_limit)
        if score >= beta:
            return score
        alpha = max(alpha, score)
    return alpha


def build_board(my_men, my_kings, opp_men, opp_kings, color):
    """Build initial board with our pieces positive."""
    board = [[0]*8 for _ in range(8)]
    for r, c in my_men:
        board[r][c] = 1
    for r, c in my_kings:
        board[r][c] = 2
    for r, c in opp_men:
        board[r][c] = -1
    for r, c in opp_kings:
        board[r][c] = -2
    return board


def policy(my_men, my_kings, opp_men, opp_kings, color):
    """Return a legal move as ((from_row, from_col), (to_row, to_col))."""
    start_time = time.time()
    time_limit = 0.95
    board = build_board(my_men, my_kings, opp_men, opp_kings, color)
    p_color = color

    best_move = None
    depth = 1
    while True:
        if time.time() - start_time > time_limit:
            break
        moves = get_all_moves(board, p_color)
        if not moves:
            break
        moves.sort(key=lambda m: len(m) == 2)  # captures first
        best_score = -float('inf')
        current_best = None
        alpha = -float('inf')
        beta = float('inf')
        try:
            for move in moves:
                new_board = apply_move(board, move, p_color)
                opp_color = 'w' if p_color == 'b' else 'b'
                flipped = flip_board(new_board)
                score = -negamax(flipped, opp_color, depth-1, -beta, -alpha, start_time, time_limit)
                if score > best_score:
                    best_score = score
                    current_best = move
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
        except TimeOutError:
            break

        if current_best is not None:
            best_move = current_best
        else:
            break
        depth += 1
        if depth > 30:
            break

    if best_move is None:
        moves = get_all_moves(board, p_color)
        if moves:
            best_move = moves[0]
        else:
            return ((0, 0), (0, 0))  # fallback (should not happen)

    # best_move is a sequence of squares; return the first step
    return (best_move[0], best_move[1])
