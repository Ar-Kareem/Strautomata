
import numpy as np

PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

# Piece-square tables for midgame (from white's perspective, flipped for black)
PIECE_SQUARE_TABLES = {
    'P': np.array([
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10,-20,-20, 10, 10,  5,
        5, -5,-10,  0,  0,-10, -5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5,  5, 10, 25, 25, 10,  5,  5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0,  0,  0,  0,  0,  0,  0,  0
    ])/10.0,
    'N': np.array([
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ])/10.0,
    'B': np.array([
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0,  5, 10,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ])/10.0,
    'R': np.array([
        0,  0,  0,  5,  5,  0,  0,  0,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        5, 10, 10, 10, 10, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ])/10.0,
    'Q': np.array([
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -10,  5,  5,  5,  5,  5,  0,-10,
        0,  0,  5,  5,  5,  5,  0, -5,
        -5,  0,  5,  5,  5,  5,  0, -5,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ])/10.0,
    'K': np.array([
        20, 30, 10,  0,  0, 10, 30, 20,
        20, 20,  0,  0,  0,  0, 20, 20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30
    ])/10.0
}

def square_to_index(sq):
    file_ord = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return rank * 8 + file_ord

def evaluate_board(pieces, color):
    total = 0.0
    for sq, piece_code in pieces.items():
        piece_color = piece_code[0]
        piece_type = piece_code[1]
        idx = square_to_index(sq)
        if piece_color == 'w':
            if piece_type != 'K':
                total += PIECE_VALUES[piece_type]
            total += PIECE_SQUARE_TABLES[piece_type][idx]
        else:
            if piece_type != 'K':
                total -= PIECE_VALUES[piece_type]
            total -= PIECE_SQUARE_TABLES[piece_type][63 - idx]  # flipped for black
    return total if color == 'white' else -total

def generate_legal_moves(pieces, color_to_move):
    # This function is given in the environment, but we need a simulation version.
    # We'll implement a naive legal move generator for simulation.
    # Since we only need to simulate 2 plies, we can keep it simple.
    moves = []
    piece_color = 'w' if color_to_move == 'white' else 'b'
    for sq, piece_code in list(pieces.items()):
        if piece_code[0] != piece_color:
            continue
        piece_type = piece_code[1]
        idx = square_to_index(sq)
        rank, file_ = divmod(idx, 8)
        # Very basic move generation for simulation (not exhaustive but enough for quick evaluation)
        # Pawns
        if piece_type == 'P':
            direction = 1 if piece_color == 'w' else -1
            start_rank = 1 if piece_color == 'w' else 6
            # Forward
            new_rank = rank + direction
            if 0 <= new_rank < 8:
                new_sq = chr(ord('a') + file_) + str(new_rank + 1)
                if new_sq not in pieces:
                    moves.append(sq + new_sq)
                    # Double from start
                    if rank == start_rank:
                        new_rank2 = rank + 2 * direction
                        new_sq2 = chr(ord('a') + file_) + str(new_rank2 + 1)
                        if new_sq2 not in pieces:
                            moves.append(sq + new_sq2)
            # Captures
            for dx in (-1, 1):
                new_file = file_ + dx
                if 0 <= new_file < 8:
                    new_rank = rank + direction
                    new_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                    if new_sq in pieces and pieces[new_sq][0] != piece_color:
                        moves.append(sq + new_sq)
        # Knights
        elif piece_type == 'N':
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                new_rank = rank + dr
                new_file = file_ + dc
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    new_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                    if new_sq not in pieces or pieces[new_sq][0] != piece_color:
                        moves.append(sq + new_sq)
        # Kings (simple moves, castling ignored for simulation)
        elif piece_type == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    new_rank = rank + dr
                    new_file = file_ + dc
                    if 0 <= new_rank < 8 and 0 <= new_file < 8:
                        new_sq = chr(ord('a') + new_file) + str(new_rank + 1)
                        if new_sq not in pieces or pieces[new_sq][0] != piece_color:
                            moves.append(sq + new_sq)
        # Rooks, Bishops, Queens: simple sliding (no blocking detection for speed, but we'll add basic)
        elif piece_type in ('R', 'B', 'Q'):
            directions = []
            if piece_type in ('R', 'Q'):
                directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if piece_type in ('B', 'Q'):
                directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dr, dc in directions:
                r, c = rank, file_
                while True:
                    r += dr
                    c += dc
                    if not (0 <= r < 8 and 0 <= c < 8):
                        break
                    new_sq = chr(ord('a') + c) + str(r + 1)
                    if new_sq not in pieces:
                        moves.append(sq + new_sq)
                    elif pieces[new_sq][0] != piece_color:
                        moves.append(sq + new_sq)
                        break
                    else:
                        break
    # Add promotions (assume queen promotion)
    promoted_moves = []
    for mv in moves:
        if len(mv) == 4 and mv[:2] in pieces and pieces[mv[:2]][1] == 'P':
            from_rank = int(mv[1])
            to_rank = int(mv[3])
            if (piece_color == 'w' and to_rank == 8) or (piece_color == 'b' and to_rank == 1):
                promoted_moves.append(mv + 'q')
    moves = [m for m in moves if len(m) == 4]  # remove pawn moves that should be promotions
    moves.extend(promoted_moves)
    return moves

def make_move(pieces, move):
    new_pieces = pieces.copy()
    if len(move) == 4:
        src, dst = move[:2], move[2:]
        piece = new_pieces.pop(src)
        # Captures
        if dst in new_pieces:
            del new_pieces[dst]
        new_pieces[dst] = piece
    elif len(move) == 5:
        src, dst = move[:2], move[2:4]
        piece = new_pieces.pop(src)
        if dst in new_pieces:
            del new_pieces[dst]
        new_pieces[dst] = piece[0] + move[4]  # promoted piece
    return new_pieces

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    color = to_play
    opponent = 'black' if color == 'white' else 'white'
    
    # If memory contains precomputed legal moves, use them; else compute.
    if 'legal_moves' in memory and memory.get('prev_pieces') == pieces:
        legal_moves = memory['legal_moves']
    else:
        # We don't have the environment's legal_moves, so we must generate our own.
        legal_moves = generate_legal_moves(pieces, color)
        memory['legal_moves'] = legal_moves
        memory['prev_pieces'] = pieces
    
    if not legal_moves:
        return ('', memory)
    
    # Check for immediate checkmate
    for mv in legal_moves:
        new_board = make_move(pieces, mv)
        # See if opponent has any legal moves
        opp_moves = generate_legal_moves(new_board, opponent)
        if not opp_moves:
            # Might be checkmate or stalemate, we need to see if opponent king is in check.
            # Simple check: if opponent king is attacked.
            king_sq = None
            for sq, pc in new_board.items():
                if pc == ('bK' if opponent == 'black' else 'wK'):
                    king_sq = sq
                    break
            if king_sq:
                # Check if any of my pieces attack king_sq (simple simulation)
                my_color = 'w' if color == 'white' else 'b'
                attackers = False
                for sq, pc in new_board.items():
                    if pc[0] == my_color:
                        # generate pseudo-legal moves from sq
                        temp_moves = generate_legal_moves({sq: pc}, color)
                        for temp_mv in temp_moves:
                            if temp_mv[2:4] == king_sq:
                                attackers = True
                                break
                    if attackers:
                        break
                if attackers:
                    return (mv, memory)
    
    # Evaluate moves with 2-ply search
    best_move = None
    best_eval = -float('inf')
    for mv in legal_moves:
        new_board = make_move(pieces, mv)
        # Opponent's best reply (maximize their evaluation)
        opp_moves = generate_legal_moves(new_board, opponent)
        if not opp_moves:
            # If opponent has no moves, evaluate the board directly.
            eval_after = evaluate_board(new_board, color)
        else:
            worst_eval = float('inf')
            for opp_mv in opp_moves:
                board_after_opp = make_move(new_board, opp_mv)
                # Then my best reply (depth 2)
                my_reply_moves = generate_legal_moves(board_after_opp, color)
                if not my_reply_moves:
                    eval_pos = evaluate_board(board_after_opp, color)
                else:
                    eval_pos = max(evaluate_board(make_move(board_after_opp, my_reply), color) for my_reply in my_reply_moves[:5])  # limit to 5 replies for speed
                worst_eval = min(worst_eval, eval_pos)
            eval_after = worst_eval
        if eval_after > best_eval:
            best_eval = eval_after
            best_move = mv
    
    if best_move is None:
        best_move = legal_moves[0]
    
    return (best_move, memory)
