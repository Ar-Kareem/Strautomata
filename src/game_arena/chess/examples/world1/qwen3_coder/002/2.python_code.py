
import collections

# Define piece values
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Define piece-square tables for basic piece positioning (simplified)
PST_PAWN = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10, 15, 15,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

PST_KNIGHT = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

PST_BISHOP = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

PST_ROOK = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

PST_QUEEN = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

PST_KING_MIDDLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

PST_KING_END = [
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
]

def square_to_index(sq):
    file = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return 8 * (7 - rank) + file

def index_to_square(idx):
    rank = 7 - (idx // 8)
    file = idx % 8
    return chr(ord('a') + file) + str(rank + 1)

def get_piece_at(square, board):
    return board.get(square, None)

def is_endgame(board):
    queens = 0
    minors = 0
    for piece in board.values():
        ptype = piece[1]
        if ptype == 'Q':
            queens += 1
        elif ptype in 'BN':
            minors += 1
    return queens == 0 or (queens == 1 and minors <= 2)

def evaluate_move(move, board, color):
    score = 0
    move_type = move
    if 'x' in move:
        # Extract captured piece
        # This is a bit tricky without full parsing, so we'll approximate
        # We'll just add a bonus for captures
        score += 50 # base capture bonus
    
    if '=' in move:
        # Promotion
        promo_piece = move[-1]
        score += PIECE_VALUES[promo_piece]
    
    if '+' in move or '#' in move:
        # Check or checkmate
        score += 1000 # encourage checks
    
    # Positional evaluation is complex, so we'll just add a general bonus for activity
    score += 10
    
    return score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Map color
    our_color = 'w' if to_play == 'white' else 'b'
    
    # Detect checkmate
    if not legal_moves:
        # Should not happen, but if no legal moves, return a dummy (though this is a loss)
        return 'a1a1' # This will be filtered out
    
    # Score each move
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(move, pieces, our_color)
        # Additional heuristics can be added here
        
        # Simple heuristic: prefer captures
        # But without full move parsing, it's approximate
        if 'x' in move:
            # Try to find the captured piece
            # This is hard without exact move parsing
            # Just give a bonus
            score += 100
        
        # Prefer queen promotions
        if '=Q' in move:
            score += 1000
            
        # Prefer king safety moves (castling) if available
        if move in ('O-O', 'O-O-O'):
            score += 200
            
        move_scores.append((score, move))
    
    # Sort moves by score descending
    move_scores.sort(reverse=True)
    
    # Return the best move
    return move_scores[0][1]
