
import numpy as np

# Piece values (centipawns)
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}

# Cache for fast square-to-index conversion
SQUARE_TO_IDX = {f"{file}{rank}": (ord(file)-97, int(rank)-1) 
                 for file in 'abcdefgh' for rank in '12345678'}

def parse_board(pieces):
    """Convert pieces dictionary to 8x8 numpy array."""
    board = np.full((8, 8), '', dtype='<U2')
    for square, piece in pieces.items():
        f, r = SQUARE_TO_IDX[square]
        board[r, f] = piece
    return board

def apply_move(board, move):
    """Apply UCI move to board and return new board state."""
    new_board = board.copy()
    sf, sr = SQUARE_TO_IDX[move[:2]]
    df, dr = SQUARE_TO_IDX[move[2:4]]
    
    piece = new_board[sr, sf]
    new_board[sr, sf] = ''
    
    # Handle promotion
    if len(move) == 5:
        piece = piece[0] + move[4].upper()
    
    new_board[dr, df] = piece
    return new_board

def evaluate(board, color):
    """Evaluate position from perspective of color."""
    opp = 'b' if color == 'w' else 'w'
    score = 0
    
    # Material and central positioning
    for r in range(8):
        for f in range(8):
            piece = board[r, f]
            if not piece:
                continue
            
            value = PIECE_VALUES[piece[1]]
            if piece[0] == color:
                score += value
                # Central square bonus
                if 3 <= f <= 4 and 3 <= r <= 4:
                    score += 10
            else:
                score -= value
    
    # King safety - prefer corners and edges
    king_mask = (board == color + 'K')
    if king_mask.any():
        r, f = np.where(king_mask)
        r, f = r[0], f[0]
        if f in [0, 7] and r in [0, 7]:
            score += 50
        elif f in [0, 7] or r in [0, 7]:
            score += 20
    
    return score

def policy(pieces, to_play, memory, legal_moves=None):
    """
    Select best move using greedy evaluation.
    
    Note: legal_moves parameter is required per problem description
    but missing from the official API signature.
    """
    # Fallback for missing legal_moves parameter
    if legal_moves is None:
        legal_moves = memory.get('legal_moves', [])
    
    if not legal_moves:
        return '', memory
    
    if len(legal_moves) == 1:
        return legal_moves[0], memory
    
    board = parse_board(pieces)
    color = 'w' if to_play == 'white' else 'b'
    opp = 'b' if color == 'w' else 'w'
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Evaluate each legal move
    for move in legal_moves:
        temp_board = apply_move(board, move)
        
        # Checkmate detection: opponent king missing
        if opp + 'K' not in temp_board:
            return move, memory
        
        # Base evaluation
        score = evaluate(temp_board, color)
        
        # Capture bonus
        df, dr = SQUARE_TO_IDX[move[2:4]]
        captured = board[dr, df]
        if captured:
            score += PIECE_VALUES[captured[1]] * 1.5
        
        # Promotion bonus
        if len(move) == 5:
            promoted_type = move[4].upper()
            score += PIECE_VALUES[promoted_type] - PIECE_VALUES['P']
        
        # Castling bonus (king moves two squares horizontally)
        sf, sr = SQUARE_TO_IDX[move[:2]]
        piece = board[sr, sf]
        if piece == color + 'K' and abs(df - sf) == 2:
            score += 75
        
        # Track best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
