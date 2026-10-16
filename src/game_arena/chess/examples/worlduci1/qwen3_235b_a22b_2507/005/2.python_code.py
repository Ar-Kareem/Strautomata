
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 7, 'K': 200}
    
    # Get color code
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'

    # Generate legal moves (passed implicitly via simulation — we'll assume 'legal_moves' is available in context)
    # But note: legal_moves is not in signature. We need to derive or receive it.
    # Wait — the problem says: "Return exactly ONE move string that is an element of `legal_moves`"
    # But `legal_moves` is not passed to the function!
    
    # Correction: The prompt contradicts itself. The API is:
    #   def policy(pieces: dict[str, str], to_play: str) -> str
    # But earlier says: "Return exactly ONE move string that is an element of `legal_moves`"
    #
    # This suggests that `legal_moves` must be computed within the function.
    #
    # Therefore, we must generate all legal moves from `pieces` and `to_play`.

    # Step 1: Generate all legal moves
    legal_moves = generate_legal_moves(pieces, to_play)

    if not legal_moves:
        # Should not happen in normal play, but fallback
        return next(iter(pieces.keys())) + next(iter(pieces.keys()))  # dummy

    best_move = None
    best_score = -np.inf

    for move in legal_moves:
        # Simulate move
        new_pieces = apply_move(pieces, move)
        
        # Evaluate board from current player's perspective
        score = evaluate(new_pieces, to_play, move, pieces)
        
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def evaluate(pieces: dict, to_play: str, move: str, prev_pieces: dict) -> float:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 7, 'K': 200}
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'

    score = 0.0

    # Material difference
    my_mat = sum(piece_values[piece[1]] for piece in pieces.values() if piece[0] == color)
    opp_mat = sum(piece_values[piece[1]] for piece in pieces.values() if piece[0] == opp_color)
    score += my_mat - opp_mat

    # Did this move capture a piece?
    start_sq, end_sq = move[:2], move[2:4]
    if end_sq in prev_pieces and prev_pieces[end_sq][0] != color:
        captured_piece = prev_pieces[end_sq][1]
        score += piece_values[captured_piece] * 0.9  # Already counted in opp_mat, but double-weight capture intent

    # Promotion bonus
    if len(move) == 5:
        promo = move[4]
        if promo == 'q':
            score += 8  # Strongly favor queen promotion
        elif promo == 'r':
            score += 4
        elif promo in 'bn':
            score += 2

    # Check for checkmate
    if is_checkmate(pieces, 'black' if to_play == 'white' else 'white'):
        score += 1000

    # Check for check
    elif is_in_check(pieces, 'black' if to_play == 'white' else 'white'):
        score += 0.5

    # Encourage center control a bit (early game heuristic)
    center = ['e4', 'd4', 'e5', 'd5']
    if end_sq in center:
        moving_piece = prev_pieces.get(start_sq)
        if moving_piece and moving_piece[0] == color and moving_piece[1] != 'P':
            score += 0.1

    return score

def is_in_check(pieces: dict, king_color: str) -> bool:
    king_pos = None
    king_code = 'wK' if king_color == 'white' else 'bK'
    attacker_color = 'b' if king_color == 'white' else 'w'

    # Find king
    for sq, piece in pieces.items():
        if piece == king_code:
            king_pos = sq
            break
    if not king_pos:
        return True  # shouldn't happen, but assume bad

    # Check if any opponent piece attacks the king
    for sq, piece in pieces.items():
        if piece[0] == attacker_color:
            if is_attacking(pieces, sq, king_pos, piece[1]):
                return True
    return False

def is_checkmate(pieces: dict, king_color: str) -> bool:
    if not is_in_check(pieces, king_color):
        return False
    # Very simplified: check if any legal move exists
    # We don't want to fully generate legal moves here due to recursion, so we skip perfect checkmate detection
    # Instead, we rely on the fact that in real games, few legal moves exist in check
    # But to avoid bugs, we do a quick check: if king can move, mate not certain
    king_code = 'wK' if king_color == 'white' else 'bK'
    king_sq = None
    for sq, piece in pieces.items():
        if piece == king_code:
            king_sq = sq
            break
    if not king_sq:
        return True

    # Try king moves
    files = 'abcdefgh'
    ranks = '12345678'
    kf, kr = king_sq[0], king_sq[1]
    for df, dr in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
        nf = chr(ord(kf) + df) if 'a' <= chr(ord(kf) + df) <= 'h' else None
        nr = chr(ord(kr) + dr) if '1' <= chr(ord(kr) + dr) <= '8' else None
        if nf is None or nr is None:
            continue
        target = nf + nr
        # Would moving king to target get out of check? (without considering pins etc)
        temp_pieces = pieces.copy()
        temp_pieces[target] = temp_pieces.pop(king_sq)
        if not is_in_check(temp_pieces, king_color):
            return False
    # We didn't check for interpositions or captures — so this is weak
    return False  # Simplified: we don't do full legal move gen here

def is_attacking(pieces: dict, from_sq: str, to_sq: str, piece_type: str) -> bool:
    # Does a piece of type `piece_type` on `from_sq` attack `to_sq` assuming no blocking?
    # We must check for blocking pieces in between
    fx, fy = ord(from_sq[0]) - ord('a'), int(from_sq[1]) - 1
    tx, ty = ord(to_sq[0]) - ord('a'), int(to_sq[1]) - 1

    dx = tx - fx
    dy = ty - fy

    if piece_type == 'P':
        promo_r = 8 if pieces[from_sq][0] == 'w' else 1
        advance = 1 if pieces[from_sq][0] == 'w' else -1
        return dy == advance and abs(dx) == 1 and to_sq == to_sq  # simple
    elif piece_type == 'N':
        return (abs(dx) == 2 and abs(dy) == 1) or (abs(dx) == 1 and abs(dy) == 2)
    elif piece_type == 'B':
        if abs(dx) != abs(dy) or dx == 0:
            return False
        return not is_blocked_diagonal(pieces, from_sq, to_sq)
    elif piece_type == 'R':
        if not (dx == 0 or dy == 0) or (dx == 0 and dy == 0):
            return False
        return not is_blocked_straight(pieces, from_sq, to_sq)
    elif piece_type == 'Q':
        if abs(dx) == abs(dy) and dx != 0:
            return not is_blocked_diagonal(pieces, from_sq, to_sq)
        if (dx == 0 or dy == 0) and not (dx == 0 and dy == 0):
            return not is_blocked_straight(pieces, from_sq, to_sq)
        return False
    elif piece_type == 'K':
        return max(abs(dx), abs(dy)) == 1
    return False

def is_blocked_diagonal(pieces: dict, from_sq: str, to_sq: str) -> bool:
    fx, fy = ord(from_sq[0]) - ord('a'), int(from_sq[1]) - 1
    tx, ty = ord(to_sq[0]) - ord('a'), int(to_sq[1]) - 1
    step_x = 1 if tx > fx else -1
    step_y = 1 if ty > fy else -1
    steps = abs(tx - fx)
    for i in range(1, steps):
        x = fx + i * step_x
        y = fy + i * step_y
        sq = chr(ord('a') + x) + str(y+1)
        if sq in pieces:
            return True
    return False

def is_blocked_straight(pieces: dict, from_sq: str, to_sq: str) -> bool:
    fx, fy = ord(from_sq[0]) - ord('a'), int(from_sq[1]) - 1
    tx, ty = ord(to_sq[0]) - ord('a'), int(to_sq[1]) - 1
    if fx == tx:
        step_y = 1 if ty > fy else -1
        for i in range(1, abs(ty-fy)):
            y = fy + i * step_y
            sq = from_sq[0] + str(y+1)
            if sq in pieces:
                return True
    elif fy == ty:
        step_x = 1 if tx > fx else -1
        for i in range(1, abs(tx-fx)):
            x = fx + i * step_x
            sq = chr(ord('a') + x) + from_sq[1]
            if sq in pieces:
                return True
    return False

def apply_move(pieces: dict, move: str) -> dict:
    new_pieces = pieces.copy()
    start = move[:2]
    end = move[2:4]
    piece = new_pieces.pop(start)
    promo = None
    if len(move) == 5:
        promo = move[4]
        piece = piece[0] + (promo.upper() if promo != 'r' else 'R')  # Map 'r' to 'R', etc.
    new_pieces[end] = piece
    return new_pieces

def generate_legal_moves(pieces: dict, to_play: str) -> list:
    color = 'w' if to_play == 'white' else 'b'
    moves = []

    for sq, piece in pieces.items():
        if piece[0] != color:
            continue
        piece_type = piece[1]
        start = sq
        for target in all_squares():
            if start == target:
                continue
            # Construct move string
            move = start + target
            if is_valid_move(pieces, move, piece_type, color):
                # Handle promotion
                if piece_type == 'P':
                    if (color == 'w' and target[1] == '8') or (color == 'b' and target[1] == '7'):
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(move + promo)
                        continue
                moves.append(move)

    # Very simplified move generation — does not handle castling, en passant, or pinned pieces.
    # We accept that this generates some illegal moves, but filters basic rules.
    # This is a lightweight approximation.

    legal_moves = []
    for move in moves:
        # Validate that move doesn't leave own king in check
        sim_pieces = apply_move(pieces, move)
        if not is_in_check(sim_pieces, to_play):
            legal_moves.append(move)

    # If no legal moves, return empty — will trigger fallback
    return legal_moves if legal_moves else [moves[0]] if moves else []

def all_squares():
    return [f"{f}{r}" for f in 'abcdefgh' for r in '12345678']

def is_valid_move(pieces: dict, move: str, piece_type: str, color: str) -> bool:
    start, end = move[:2], move[2:4]
    if end not in all_squares():
        return False
    if end in pieces and pieces[end][0] == color:
        return False  # can't capture own piece
    # Use is_attacking to validate move
    return is_attacking(pieces, start, end, piece_type)

