
import numpy as np

DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]

# Positional weights matrix (from literature)
POSITIONAL_WEIGHTS = np.array([
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100]
])

def get_legal_moves(board, opponent_board):
    """Generate all legal moves for the player represented by board"""
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 0:  # empty cell
                for dr, dc in DIRECTIONS:
                    if can_flip(board, opponent_board, r, c, dr, dc):
                        moves.append((r, c))
                        break
    return moves

def can_flip(board, opponent_board, r, c, dr, dc):
    """Check if placing a disc at (r, c) would flip any opponent discs in direction (dr, dc)"""
    nr, nc = r+dr, c+dc
    count = 0
    while 0 <= nr < 8 and 0 <= nc < 8 and opponent_board[nr][nc] == 1:
        count += 1
        nr += dr
        nc += dc
    return count > 0 and 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1

def make_move(board, opponent_board, move):
    """Apply a move and return updated boards"""
    r, c = move
    new_board = board.copy()
    new_opponent = opponent_board.copy()
    
    new_board[r][c] = 1
    
    for dr, dc in DIRECTIONS:
        flips = []
        nr, nc = r+dr, c+dc
        while 0 <= nr < 8 and 0 <= nc < 8 and new_opponent[nr][nc] == 1:
            flips.append((nr, nc))
            nr += dr
            nc += dc
        if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr][nc] == 1 and flips:
            for fr, fc in flips:
                new_board[fr][fc] = 1
                new_opponent[fr][fc] = 0
                
    return new_board, new_opponent

def static_evaluation(you, opponent):
    """Calculate static evaluation of board position"""
    disc_diff = np.sum(you) - np.sum(opponent)
    positional_score = np.sum(POSITIONAL_WEIGHTS * (you - opponent))
    your_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mobility_score = (your_moves - opp_moves) * 10
    
    return disc_diff * 10 + positional_score + mobility_score

def alphabeta(you, opponent, depth, player, alpha, beta):
    """Minimax search with alpha-beta pruning"""
    if depth == 0:
        return static_evaluation(you, opponent)
    
    if player == 0:  # Maximizing player (your turn)
        moves = get_legal_moves(you, opponent)
        if not moves:
            return alphabeta(you, opponent, depth-1, 1, alpha, beta)
        value = -np.inf
        for move in moves:
            new_you, new_opponent = make_move(you, opponent, move)
            score = alphabeta(new_you, new_opponent, depth-1, 1, alpha, beta)
            value = max(value, score)
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:  # Minimizing player (opponent's turn)
        moves = get_legal_moves(opponent, you)
        if not moves:
            return alphabeta(you, opponent, depth-1, 0, alpha, beta)
        value = np.inf
        for move in moves:
            new_opponent_board, new_you_board = make_move(opponent, you, move)
            score = alphabeta(new_you_board, new_opponent_board, depth-1, 0, alpha, beta)
            value = min(value, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return value

def policy(you, opponent):
    """Main policy function"""
    your_moves = get_legal_moves(you, opponent)
    if not your_moves:
        return "pass"
    
    best_score = -np.inf
    best_move = None
    
    for move in your_moves:
        new_you, new_opponent = make_move(you, opponent, move)
        score = alphabeta(new_you, new_opponent, 2, 1, -np.inf, np.inf)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        return "pass"  # Fallback
    
    col_char = chr(ord('a') + best_move[1])
    row_char = str(best_move[0] + 1)
    return col_char + row_char
