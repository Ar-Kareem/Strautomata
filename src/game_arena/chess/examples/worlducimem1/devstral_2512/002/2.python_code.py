
import random
from collections import defaultdict

# Piece values for evaluation
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

# Center squares for piece activity evaluation
CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'piece_values': defaultdict(int),
            'move_history': [],
            'game_phase': 'opening'  # opening, middlegame, endgame
        }

    # Determine opponent color
    opponent = 'black' if to_play == 'white' else 'white'
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'

    # Get all legal moves (this would be provided in the actual implementation)
    # For this example, we'll assume legal_moves is available
    legal_moves = get_legal_moves(pieces, to_play)  # This function would be provided

    if not legal_moves:
        return ('', memory)  # Shouldn't happen as per problem statement

    # Evaluate each move
    best_move = None
    best_score = -float('inf')
    move_scores = []

    for move in legal_moves:
        score = evaluate_move(move, pieces, to_play, memory)
        move_scores.append((move, score))

        if score > best_score:
            best_score = score
            best_move = move

    # If multiple moves have same score, choose randomly
    if best_move is None:
        best_move = random.choice(legal_moves)

    # Update memory
    memory['move_history'].append(best_move)
    memory['game_phase'] = determine_game_phase(pieces)

    return (best_move, memory)

def evaluate_move(move: str, pieces: dict[str, str], to_play: str, memory: dict) -> float:
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'

    # Create a temporary board state after the move
    temp_pieces = pieces.copy()
    from_sq = move[:2]
    to_sq = move[2:4]
    piece = temp_pieces[from_sq]
    temp_pieces[to_sq] = piece
    del temp_pieces[from_sq]

    # Handle pawn promotion
    if len(move) == 5:  # Promotion move
        temp_pieces[to_sq] = my_color + move[4].upper()

    score = 0

    # 1. Check if this move gives checkmate (simplified - in reality would need to check)
    if is_checkmate(temp_pieces, to_play):
        return float('inf')

    # 2. Material evaluation
    material_score = evaluate_material(temp_pieces, my_color, opp_color)
    score += material_score * 10

    # 3. Piece activity (center control)
    activity_score = evaluate_activity(temp_pieces, my_color)
    score += activity_score * 1

    # 4. King safety
    king_safety_score = evaluate_king_safety(temp_pieces, my_color)
    score += king_safety_score * 5

    # 5. Pawn structure
    pawn_score = evaluate_pawns(temp_pieces, my_color)
    score += pawn_score * 1

    # 6. Tactical patterns (simplified)
    tactical_score = evaluate_tactics(move, temp_pieces, my_color)
    score += tactical_score * 2

    # 7. Opening principles
    if memory['game_phase'] == 'opening':
        opening_score = evaluate_opening(move, temp_pieces, my_color)
        score += opening_score * 1

    return score

def evaluate_material(pieces: dict[str, str], my_color: str, opp_color: str) -> float:
    my_material = 0
    opp_material = 0

    for piece in pieces.values():
        if piece[0] == my_color:
            my_material += PIECE_VALUES[piece[1]]
        else:
            opp_material += PIECE_VALUES[piece[1]]

    return my_material - opp_material

def evaluate_activity(pieces: dict[str, str], my_color: str) -> float:
    activity = 0

    for square, piece in pieces.items():
        if piece[0] == my_color:
            if square in CENTER_SQUARES:
                activity += 1
            # Add small bonus for pieces on central files/ranks
            if square[0] in 'd e' or square[1] in '4 5':
                activity += 0.5

    return activity

def evaluate_king_safety(pieces: dict[str, str], my_color: str) -> float:
    # Find king position
    king_sq = None
    for sq, piece in pieces.items():
        if piece == my_color + 'K':
            king_sq = sq
            break

    if not king_sq:
        return 0

    # Penalize king in center in opening/middlegame
    if king_sq in CENTER_SQUARES:
        return -1

    # Check if king is on back rank (safer)
    if (my_color == 'w' and king_sq[1] == '1') or (my_color == 'b' and king_sq[1] == '8'):
        return 1

    return 0

def evaluate_pawns(pieces: dict[str, str], my_color: str) -> float:
    pawn_score = 0
    pawn_squares = []

    # Collect pawn positions
    for sq, piece in pieces.items():
        if piece == my_color + 'P':
            pawn_squares.append(sq)

    # Bonus for connected pawns
    for i, sq1 in enumerate(pawn_squares):
        for sq2 in pawn_squares[i+1:]:
            if are_pawns_connected(sq1, sq2):
                pawn_score += 0.5

    # Penalty for isolated pawns
    for sq in pawn_squares:
        if is_pawn_isolated(sq, pawn_squares):
            pawn_score -= 0.5

    return pawn_score

def evaluate_tactics(move: str, pieces: dict[str, str], my_color: str) -> float:
    # Simplified tactical evaluation
    # Check if move captures a piece
    if move[2:4] in pieces and pieces[move[2:4]][0] != my_color:
        # Check if the captured piece is defended
        if not is_square_defended(move[2:4], pieces, my_color):
            return 1  # Undefended capture

    # Check for discovered attacks (simplified)
    from_sq = move[:2]
    to_sq = move[2:4]
    piece = pieces[from_sq]

    # If moving a piece that was blocking an attack
    if piece[1] != 'K':  # Not the king
        # Check if any of our pieces can now attack opponent pieces
        for sq, p in pieces.items():
            if p[0] == my_color and p[1] != 'K':
                if can_attack(sq, to_sq, p[1]) and to_sq in pieces and pieces[to_sq][0] != my_color:
                    return 0.5

    return 0

def evaluate_opening(move: str, pieces: dict[str, str], my_color: str) -> float:
    # Encourage developing knights and bishops to good squares
    piece = pieces[move[:2]]
    if piece[1] in 'NB':
        # Bonus for moving to center or good development squares
        if move[2:4] in CENTER_SQUARES or move[2:4] in {'f3', 'c3', 'f6', 'c6'}:
            return 1

    # Encourage castling
    if piece[1] == 'K' and abs(ord(move[0]) - ord(move[2])) > 1:
        return 2

    return 0

def is_checkmate(pieces: dict[str, str], to_play: str) -> bool:
    # Simplified checkmate detection
    # In a real implementation, this would check if the opponent has no legal moves
    # and their king is in check
    return False

def is_square_defended(square: str, pieces: dict[str, str], attacker_color: str) -> bool:
    # Check if any of the attacker's pieces can attack this square
    for sq, piece in pieces.items():
        if piece[0] == attacker_color and can_attack(sq, square, piece[1]):
            return True
    return False

def can_attack(from_sq: str, to_sq: str, piece_type: str) -> bool:
    # Simplified attack detection
    if piece_type == 'P':
        # Pawn attacks
        file_diff = abs(ord(from_sq[0]) - ord(to_sq[0]))
        rank_diff = abs(int(from_sq[1]) - int(to_sq[1]))
        return file_diff == 1 and rank_diff == 1
    elif piece_type == 'N':
        # Knight moves
        file_diff = abs(ord(from_sq[0]) - ord(to_sq[0]))
        rank_diff = abs(int(from_sq[1]) - int(to_sq[1]))
        return (file_diff == 2 and rank_diff == 1) or (file_diff == 1 and rank_diff == 2)
    elif piece_type == 'B':
        # Bishop moves (diagonal)
        return abs(ord(from_sq[0]) - ord(to_sq[0])) == abs(int(from_sq[1]) - int(to_sq[1]))
    elif piece_type == 'R':
        # Rook moves (straight)
        return from_sq[0] == to_sq[0] or from_sq[1] == to_sq[1]
    elif piece_type == 'Q':
        # Queen moves (any direction)
        return (abs(ord(from_sq[0]) - ord(to_sq[0])) == abs(int(from_sq[1]) - int(to_sq[1]))) or \
               (from_sq[0] == to_sq[0] or from_sq[1] == to_sq[1])
    elif piece_type == 'K':
        # King moves
        file_diff = abs(ord(from_sq[0]) - ord(to_sq[0]))
        rank_diff = abs(int(from_sq[1]) - int(to_sq[1]))
        return file_diff <= 1 and rank_diff <= 1
    return False

def are_pawns_connected(sq1: str, sq2: str) -> bool:
    # Check if two pawns are on adjacent files
    return abs(ord(sq1[0]) - ord(sq2[0])) == 1

def is_pawn_isolated(sq: str, pawn_squares: list[str]) -> bool:
    # Check if pawn has no friendly pawns on adjacent files
    file = sq[0]
    adjacent_files = [chr(ord(file)-1), chr(ord(file)+1)]

    for pawn_sq in pawn_squares:
        if pawn_sq[0] in adjacent_files:
            return False
    return True

def determine_game_phase(pieces: dict[str, str]) -> str:
    # Simplified game phase detection
    # Count major pieces (queens and rooks)
    major_pieces = 0
    for piece in pieces.values():
        if piece[1] in 'QR':
            major_pieces += 1

    if major_pieces >= 6:  # Opening/middlegame
        return 'opening'
    elif major_pieces >= 2:  # Middlegame
        return 'middlegame'
    else:  # Endgame
        return 'endgame'

# This function would be provided by the environment in the actual implementation
def get_legal_moves(pieces: dict[str, str], to_play: str) -> list[str]:
    # In a real implementation, this would return all legal moves
    # For this example, we'll return a dummy list
    return ['e2e4', 'd2d4', 'g1f3', 'b1c3']  # Example moves
