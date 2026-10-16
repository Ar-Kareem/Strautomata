
import random

def material_value(piece):
    if piece == 'Q':
        return 9
    elif piece == 'R':
        return 5
    elif piece == 'B':
        return 3
    elif piece == 'N':
        return 3
    elif piece == 'P':
        return 1
    else:
        return 0

def evaluate_capture(move, pieces):
    if 'x' in move:
        captured_piece_square = move[move.index('x')+1:move.index('x')+3]
        if captured_piece_square in pieces:
            captured_piece = pieces[captured_piece_square][1] # Just the piece type
            return material_value(captured_piece)
    return 0

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:

    # 1. Checkmate
    for move in legal_moves:
        if '#' in move:
            return move, memory

    # 2. Captures
    best_capture_move = None
    best_capture_value = -1
    for move in legal_moves:
        capture_value = evaluate_capture(move, pieces)
        if capture_value > best_capture_value:
            best_capture_value = capture_value
            best_capture_move = move

    if best_capture_move:
        return best_capture_move, memory

    # 3. King Safety (basic) - if in check, respond
    for move in legal_moves:
        if '+' in move: # Respond to check
            return move, memory

    # 4. Development
    development_moves = []
    for move in legal_moves:
         # Prioritize Knight and Bishop moves, but not queen moves
        if len(move) > 2 and (move[0] == 'N' or move[0] == 'B') :
            development_moves.append(move)

    if len(development_moves) > 0:
        return random.choice(development_moves), memory

    # 5. Random Move (Fallback)
    return random.choice(legal_moves), memory
