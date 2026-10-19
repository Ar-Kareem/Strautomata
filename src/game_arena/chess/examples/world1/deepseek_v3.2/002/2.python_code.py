
import copy
import math
from collections import defaultdict

# Piece values
PIECE_VAL = {'P': 1, 'N': 3, 'B': 3.25, 'R': 5, 'Q': 9, 'K': 1000}

# Piece-square tables (midgame)
PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]
KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0
]
QUEEN_TABLE = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]
KING_MID_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20
]
KING_END_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

def square_to_index(sq):
    file = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return rank * 8 + file

def is_endgame(pieces):
    # Count queens and rooks
    queen_rook = 0
    for p in pieces.values():
        if p[1] in 'QR':
            queen_rook += 1
    return queen_rook <= 2

class Board:
    def __init__(self, pieces, to_play):
        self.pieces = pieces
        self.to_play = to_play
        self.endgame = is_endgame(pieces)

    def copy(self):
        return Board(copy.deepcopy(self.pieces), self.to_play)

    def evaluate(self):
        score = 0
        for sq, piece in self.pieces.items():
            idx = square_to_index(sq)
            val = PIECE_VAL[piece[1]]
            table = 0
            if piece[1] == 'P':
                table = PAWN_TABLE[idx if piece[0] == 'w' else 63 - idx]
            elif piece[1] == 'N':
                table = KNIGHT_TABLE[idx if piece[0] == 'w' else 63 - idx]
            elif piece[1] == 'B':
                table = BISHOP_TABLE[idx if piece[0] == 'w' else 63 - idx]
            elif piece[1] == 'R':
                table = ROOK_TABLE[idx if piece[0] == 'w' else 63 - idx]
            elif piece[1] == 'Q':
                table = QUEEN_TABLE[idx if piece[0] == 'w' else 63 - idx]
            elif piece[1] == 'K':
                table = KING_END_TABLE[idx if piece[0] == 'w' else 63 - idx] if self.endgame else KING_MID_TABLE[idx if piece[0] == 'w' else 63 - idx]
            if piece[0] == 'w':
                score += val + table * 0.1
            else:
                score -= val + table * 0.1
        return score

    def make_move(self, move_str):
        # Very simplified move making: assume move_str is like 'e2e4' or 'e7e8=Q'
        # This will not handle disambiguation, castling etc properly
        # But legal_moves are given, so we just need to update board accordingly
        # Since we don't have full move generator, we will approximate by assuming
        # the move is given in long algebraic: e.g., 'e2e4', 'e7e8q', 'e1g1' (castling)
        # Actually legal_moves might be in short algebraic, so we need to parse.
        # For simplicity, we'll do a naive update: find piece that can move to target.
        # This is a weak point but okay given time.
        pass

# Since building full move maker is complex, we'll use a simpler evaluation:
# Evaluate each legal move by immediate material gain and piece safety.

def policy(pieces, to_play, legal_moves):
    # If checkmate in one, do it
    for move in legal_moves:
        if move.endswith('#'):
            return move

    # If check, consider it
    checks = [m for m in legal_moves if m.endswith('+')]
    if checks:
        legal_moves = checks  # restrict to checks

    # Simple scoring based on capture and piece-square
    best_move = legal_moves[0]
    best_score = -999999
    my_color = 'w' if to_play == 'white' else 'b'

    # Opening book preferences
    opening_moves = {
        ('white', 'e2e4'): 100,
        ('white', 'd2d4'): 95,
        ('white', 'g1f3'): 90,
        ('black', 'e7e5'): 100 if 'e2e4' in [m.lower() for m in legal_moves] else 0,
        ('black', 'c7c5'): 95,
        ('black', 'e7e6'): 90,
        ('black', 'd7d5'): 90,
    }

    for move in legal_moves:
        score = 0
        # Opening bonus
        key = (to_play, move.lower())
        if key in opening_moves:
            score += opening_moves[key]

        # Parse move for capture
        if 'x' in move:
            # Guess captured piece value
            # We'll assume captured piece is at destination square in current board
            dest = move.split('x')[1][:2]
            if dest in pieces:
                captured = pieces[dest][1]
                score += PIECE_VAL.get(captured, 0) * 10

        # Encourage castling
        if move == 'O-O' or move == 'O-O-O':
            score += 50

        # Encourage center control
        center = ['d4', 'e4', 'd5', 'e5']
        if len(move) >= 2 and move[-2:] in center:
            score += 15

        # Penalize moving king in danger
        if move.startswith('K'):
            # If king moves to square attacked by low value pieces?
            # Skip for speed
            pass

        # Promotion bonus
        if '=Q' in move:
            score += 80
        elif '=R' in move or '=B' in move or '=N' in move:
            score += 40

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
