
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Minimax policy with alpha-beta pruning and move ordering.
    """
    you = np.array(you)
    opponent = np.array(opponent)
    
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "0,0,R"
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Order moves by quick evaluation for better pruning
    move_scores = []
    for move in legal_moves:
        new_you, new_opponent = apply_move(you, opponent, move)
        score = count_moves(new_you, new_opponent) - count_moves(new_opponent, new_you)
        move_scores.append((move, score))
    
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    best_move = move_scores[0][0]
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    for move, _ in move_scores:
        new_you, new_opponent = apply_move(you, opponent, move)
        score = -negamax(new_opponent, new_you, 5, -beta, -alpha)
        
        if score > best_score:
            best_score = score
            best_move = move
        
        alpha = max(alpha, score)
    
    return best_move

def negamax(you, opponent, depth, alpha, beta):
    """Negamax with alpha-beta pruning."""
    our_count = count_moves(you, opponent)
    
    if our_count == 0:
        return -10000
    
    if depth == 0:
        their_count = count_moves(opponent, you)
        if their_count == 0:
            return 10000
        return (our_count - their_count) * 10 + (np.sum(you) - np.sum(opponent))
    
    moves = get_legal_moves(you, opponent)
    max_score = float('-inf')
    
    for move in moves:
        new_you, new_opponent = apply_move(you, opponent, move)
        score = -negamax(new_opponent, new_you, depth - 1, -beta, -alpha)
        max_score = max(max_score, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    
    return max_score

def count_moves(you, opponent):
    """Count legal moves efficiently."""
    count = 0
    rows, cols = you.shape
    
    for r in range(rows):
        for c in range(cols):
            if you[r, c] == 1:
                if r > 0 and opponent[r-1, c] == 1:
                    count += 1
                if r < rows-1 and opponent[r+1, c] == 1:
                    count += 1
                if c > 0 and opponent[r, c-1] == 1:
                    count += 1
                if c < cols-1 and opponent[r, c+1] == 1:
                    count += 1
    
    return count

def get_legal_moves(you, opponent):
    """Get all legal moves."""
    moves = []
    rows, cols = you.shape
    directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    
    for r in range(rows):
        for c in range(cols):
            if you[r, c] == 1:
                for dr, dc, dir_name in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and opponent[nr, nc] == 1:
                        moves.append(f"{r},{c},{dir_name}")
    
    return moves

def apply_move(you, opponent, move):
    """Apply a move and return new state."""
    you = you.copy()
    opponent = opponent.copy()
    
    parts = move.split(',')
    r, c, direction = int(parts[0]), int(parts[1]), parts[2]
    
    direction_map = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    dr, dc = direction_map[direction]
    nr, nc = r + dr, c + dc
    
    you[r, c] = 0
    you[nr, nc] = 1
    opponent[nr, nc] = 0
    
    return you, opponent
