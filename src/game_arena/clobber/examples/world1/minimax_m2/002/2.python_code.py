
import numpy as np
import time

# Directions and their corresponding row/column changes
DIRECTIONS = {
    'U': (-1, 0),
    'R': (0, 1),
    'D': (1, 0),
    'L': (0, -1)
}

# Board dimensions
ROWS = 5
COLS = 6

def count_pieces(board):
    """Count the number of pieces on the board."""
    return np.count_nonzero(board)

def count_moves(you, opponent):
    """Count the number of legal moves for the current player."""
    moves = 0
    for r in range(ROWS):
        for c in range(COLS):
            if you[r, c] == 1:
                for _, (dr, dc) in DIRECTIONS.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and opponent[nr, nc] == 1:
                        moves += 1
    return moves

def evaluate(you, opponent):
    """Heuristic evaluation of the board state."""
    you_count = count_pieces(you)
    opponent_count = count_pieces(opponent)
    you_mobility = count_moves(you, opponent)
    opponent_mobility = count_moves(opponent, you)
    return 10 * (you_count - opponent_count) + (you_mobility - opponent_mobility)

def generate_moves(you, opponent):
    """Generate all legal moves for the current player."""
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r, c] == 1:
                for direction, (dr, dc) in DIRECTIONS.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and opponent[nr, nc] == 1:
                        moves.append((r, c, direction))
    return moves

def apply_move(you, opponent, move, is_you_turn):
    """Apply a move and return the new board state."""
    r, c, direction = move
    dr, dc = DIRECTIONS[direction]
    nr, nc = r + dr, c + dc
    new_you = you.copy()
    new_opponent = opponent.copy()
    if is_you_turn:
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opponent[nr, nc] = 0
    else:
        new_you[nr, nc] = 0
        new_opponent[r, c] = 0
        new_opponent[nr, nc] = 1
    return new_you, new_opponent

def minimax(you, opponent, depth, is_you_turn, alpha, beta):
    """Minimax with alpha-beta pruning. Returns (score, move)."""
    you_count = count_pieces(you)
    opponent_count = count_pieces(opponent)
    if you_count == 0:
        return -10000, None
    if opponent_count == 0:
        return 10000, None
    
    if depth == 0:
        return evaluate(you, opponent), None
    
    if is_you_turn:
        current_moves = count_moves(you, opponent)
        if current_moves == 0:
            return -10000, None
    else:
        current_moves = count_moves(opponent, you)
        if current_moves == 0:
            return 10000, None
    
    if is_you_turn:
        moves = generate_moves(you, opponent)
        best_score = -10000
        best_move = None
        for move in moves:
            new_you, new_opponent = apply_move(you, opponent, move, True)
            score, _ = minimax(new_you, new_opponent, depth - 1, False, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        moves = generate_moves(opponent, you)
        best_score = 10000
        best_move = None
        for move in moves:
            new_you, new_opponent = apply_move(you, opponent, move, False)
            score, _ = minimax(new_you, new_opponent, depth - 1, True, alpha, beta)
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score, best_move

def policy(you, opponent):
    """Main policy function to determine the best move."""
    start_time = time.time()
    moves = generate_moves(you, opponent)
    if not moves:
        # Should not happen per problem constraints, but return a default move
        return "0,0,U"
    
    best_move = moves[0]
    best_score = -10000
    
    # Iterative deepening up to depth 5, break if time exceeds 0.9 seconds
    for depth in range(1, 6):
        if time.time() - start_time > 0.9:
            break
        score, move = minimax(you, opponent, depth, True, -10000, 10000)
        if move is not None:
            best_move = move
            best_score = score
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
