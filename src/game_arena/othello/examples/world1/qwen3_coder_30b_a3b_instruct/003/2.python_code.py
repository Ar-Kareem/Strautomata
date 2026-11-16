
import numpy as np
import random

def get_legal_moves(you, opponent):
    """Get all legal moves for the current player."""
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for dr, dc in directions:
                    # Check if there's a line of opponent discs that can be flipped
                    nr, nc = r + dr, c + dc
                    found_opponent = False
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        if opponent[nr][nc] == 1:
                            found_opponent = True
                        elif you[nr][nc] == 1 and found_opponent:
                            moves.append((r, c))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc
    return moves

def make_move(you, opponent, move_r, move_c):
    """Make a move and return new board states."""
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    # Place the disc
    new_you[move_r][move_c] = 1
    
    # Flip opponent discs in all directions
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    for dr, dc in directions:
        # Find the line to flip
        flips = []
        nr, nc = move_r + dr, move_c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if new_opponent[nr][nc] == 1:
                flips.append((nr, nc))
            elif new_you[nr][nc] == 1:
                # Flip all the opponent discs in this line
                for fr, fc in flips:
                    new_opponent[fr][fc] = 0
                    new_you[fr][fc] = 1
                break
            else:
                break
            nr += dr
            nc += dc
    
    return new_you, new_opponent

def evaluate_position(you, opponent):
    """Evaluate the current board position using multiple heuristics."""
    # Simple positional weights (corners and edges are more valuable)
    weights = np.array([
        [100, -10, 10,  5,  5, 10, -10, 100],
        [-10, -20, -2, -2, -2, -2, -20, -10],
        [ 10,  -2,  1,  1,  1,  1,  -2,  10],
        [  5,  -2,  1,  0,  0,  1,  -2,   5],
        [  5,  -2,  1,  0,  0,  1,  -2,   5],
        [ 10,  -2,  1,  1,  1,  1,  -2,  10],
        [-10, -20, -2, -2, -2, -2, -20, -10],
        [100, -10, 10,  5,  5, 10, -10, 100]
    ])
    
    # Count total discs
    your_discs = np.sum(you)
    opponent_discs = np.sum(opponent)
    
    # Positional score
    positional_score = np.sum(weights * you) - np.sum(weights * opponent)
    
    # Mobility (number of legal moves for both players)
    your_moves = len(get_legal_moves(you, opponent))
    opponent_moves = len(get_legal_moves(opponent, you))
    
    mobility_score = 0
    if your_moves + opponent_moves > 0:
        mobility_score = 10 * (your_moves - opponent_moves) / (your_moves + opponent_moves)
    
    return positional_score + mobility_score + 10 * (your_discs - opponent_discs)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function that returns the best move."""
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    # Try some heuristics to sort moves
    def sort_key(move):
        r, c = move
        # Prefer corners and edges
        if r in [0, 7] or c in [0, 7]:
            return 1000
        # Prefer moves near corners
        if (r in [0, 1] and c in [0, 1]) or \
           (r in [0, 1] and c in [6, 7]) or \
           (r in [6, 7] and c in [0, 1]) or \
           (r in [6, 7] and c in [6, 7]):
            return 500
        return 0  # Neutral score for middle positions
    
    # Sort moves so we prioritise corner & edge positions
    moves.sort(key=sort_key, reverse=True)
    
    best_move = moves[0]
    best_score = float('-inf')
    
    # Try first few moves to see immediate value
    for mv in moves[:min(4, len(moves))]:
        r, c = mv
        new_you, new_opponent = make_move(you, opponent, r, c)
        # Evaluate this move
        score = evaluate_position(new_you, new_opponent)
        if score > best_score:
            best_score = score
            best_move = mv
    
    # Convert best move to algebraic notation
    col_char = chr(ord('a') + best_move[1])
    row_num = str(8 - best_move[0])
    return col_char + row_num
