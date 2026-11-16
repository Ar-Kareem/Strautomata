
import numpy as np

# Pre-compute valid directions and positional weights
DIRECTIONS = {
    'U': (-1, 0), 'R': (0, 1),
    'D': (1, 0), 'L': (0, -1)
}

# Heuristic positional weights (central control preferred)
POSITION_WEIGHTS = np.array([
    [1, 2, 3, 3, 2, 1],
    [2, 4, 5, 5, 4, 2],
    [3, 5, 6, 6, 5, 3],
    [2, 4, 5, 5, 4, 2],
    [1, 2, 3, 3, 2, 1]
])

def get_legal_moves(you, opponent):
    moves = []
    for r in range(5):
        for c in range(6):
            if you[r, c]:
                for d, (dr, dc) in DIRECTIONS.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent[nr, nc]:
                        moves.append((r, c, d))
    return moves

def make_move(you, opponent, move):
    r, c, d = move
    dr, dc = DIRECTIONS[d]
    nr, nc = r + dr, c + dc
    new_you = you.copy()
    new_opponent = opponent.copy()
    new_you[r, c] = 0
    new_opponent[nr, nc] = 0
    new_you[nr, nc] = 1
    return new_you, new_opponent

def evaluate(you, opponent):
    # Mobility: number of legal moves available
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))  # swap roles
    
    # Positional value
    my_value = np.sum(you * POSITION_WEIGHTS)
    opp_value = np.sum(opponent * POSITION_WEIGHTS)
    
    # Heuristic score
    score = (
        10 * (my_moves - opp_moves) +
        1 * (my_value - opp_value)
    )
    
    return score

def minimax(you, opponent, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(you, opponent)
    
    moves = get_legal_moves(you, opponent)
    if not moves:
        return -1000 if maximizing else 1000  # losing state

    if maximizing:
        max_eval = -np.inf
        # Sort moves by heuristic to improve pruning
        moves = sorted(moves, key=lambda m: evaluate(*make_move(you, opponent, m)), reverse=True)
        for move in moves:
            new_you, new_opponent = make_move(you, opponent, move)
            eval_score = minimax(new_opponent, new_you, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        moves = get_legal_moves(you, opponent)
        moves = sorted(moves, key=lambda m: evaluate(*make_move(you, opponent, m)))
        for move in moves:
            new_you, new_opponent = make_move(you, opponent, move)
            eval_score = minimax(new_opponent, new_you, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(you: list, opponent: list) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        # Should not happen, but fallback
        for r in range(5):
            for c in range(6):
                if you[r, c]:
                    for d in DIRECTIONS:
                        dr, dc = DIRECTIONS[d]
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and opponent[nr, nc]:
                            return f"{r},{c},{d}"
        # Last resort: return first valid move pattern (should not reach)
        return "0,0,R"
    
    # If only one move, return it
    if len(moves) == 1:
        r, c, d = moves[0]
        return f"{r},{c},{d}"
    
    # Order moves by immediate heuristic
    def move_score(move):
        new_you, new_opponent = make_move(you, opponent, move)
        return evaluate(new_you, new_opponent)
    
    moves = sorted(moves, key=move_score, reverse=True)
    
    # Use depth 3 if plenty of moves, else 2
    depth = 2
    if len(moves) <= 8:
        depth = 3

    best_move = moves[0]
    best_value = -np.inf

    for move in moves:
        new_you, new_opponent = make_move(you, opponent, move)
        value = minimax(new_opponent, new_you, depth - 1, -np.inf, np.inf, False)
        if value > best_value:
            best_value = value
            best_move = move

    r, c, d = best_move
    return f"{r},{c},{d}"
