
import random
import numpy as np

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

PAWN_TABLE = np.array([
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
])

KNIGHT_TABLE = np.array([
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
])

BISHOP_TABLE = np.array([
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
])

ROOK_TABLE = np.array([
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
])

QUEEN_TABLE = np.array([
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
])

KING_TABLE = np.array([
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
])

KING_ENDGAME_TABLE = np.array([
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
])

def evaluate(pieces, to_play):
    score = 0
    piece_count = {'w': 0, 'b': 0}
    
    for square, piece in pieces.items():
        color, piece_type = piece[0], piece[1]
        piece_count[color] += 1
        
        # Material value
        value = PIECE_VALUES[piece_type]
        
        # Piece-square table bonus
        file, rank = ord(square[0]) - ord('a'), int(square[1]) - 1
        if color == 'w':
            rank = 7 - rank  # Flip rank for white
        else:
            value = -value  # Negative value for black pieces
            
        if piece_type == 'P':
            bonus = PAWN_TABLE[rank][file]
        elif piece_type == 'N':
            bonus = KNIGHT_TABLE[rank][file]
        elif piece_type == 'B':
            bonus = BISHOP_TABLE[rank][file]
        elif piece_type == 'R':
            bonus = ROOK_TABLE[rank][file]
        elif piece_type == 'Q':
            bonus = QUEEN_TABLE[rank][file]
        elif piece_type == 'K':
            # Use endgame table if few pieces left
            if piece_count['w'] + piece_count['b'] < 10:
                bonus = KING_ENDGAME_TABLE[rank][file]
            else:
                bonus = KING_TABLE[rank][file]
        else:
            bonus = 0
            
        if color == 'w':
            score += value + bonus
        else:
            score += value - bonus
            
    # Normalize score based on whose turn it is
    if to_play == 'black':
        score = -score
        
    return score

def is_check(pieces, to_play):
    # Simplified check detection (placeholder)
    return False

def minimax(pieces, to_play, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(pieces, to_play)
        
    # Generate pseudo-legal moves (simplified)
    moves = []
    for square, piece in pieces.items():
        if (to_play == 'white' and piece[0] == 'w') or (to_play == 'black' and piece[0] == 'b'):
            # Generate some moves for each piece (simplified)
            for i in range(8):
                for j in range(8):
                    target = chr(ord('a') + i) + str(j + 1)
                    if square != target:
                        moves.append(square + target)
                        
    # Filter to only legal moves (this would be done with a real chess library)
    # For now, we'll just shuffle and take a sample
    random.shuffle(moves)
    moves = moves[:20]  # Limit to 20 moves to save time
    
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            # Make move (simplified)
            new_pieces = pieces.copy()
            if move[2:] in new_pieces:
                del new_pieces[move[2:]]  # Capture
            if move[:2] in new_pieces:
                piece = new_pieces[move[:2]]
                del new_pieces[move[:2]]
                new_pieces[move[2:]] = piece
                
            # Recurse
            eval_score = minimax(new_pieces, 'black' if to_play == 'white' else 'white', depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            # Make move (simplified)
            new_pieces = pieces.copy()
            if move[2:] in new_pieces:
                del new_pieces[move[2:]]  # Capture
            if move[:2] in new_pieces:
                piece = new_pieces[move[:2]]
                del new_pieces[move[:2]]
                new_pieces[move[2:]] = piece
                
            # Recurse
            eval_score = minimax(new_pieces, 'black' if to_play == 'white' else 'white', depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # If only one legal move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    # Try to find a winning capture or checkmate (simplified)
    for move in legal_moves:
        # Capture
        if move[2:] in pieces and pieces[move[2:]].endswith('K'):
            return move  # Take the king if possible
            
    # Use minimax to evaluate moves (depth 2 for speed)
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves[:10]:  # Limit to 10 moves to save time
        # Make move (simplified)
        new_pieces = pieces.copy()
        if move[2:] in new_pieces:
            del new_pieces[move[2:]]  # Capture
        if move[:2] in new_pieces:
            piece = new_pieces[move[:2]]
            del new_pieces[move[:2]]
            new_pieces[move[2:]] = piece
            
        # Evaluate
        score = minimax(new_pieces, 'black' if to_play == 'white' else 'white', 2, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
