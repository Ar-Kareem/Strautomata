
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Positional weights for an 8x8 Othello board
    weights = np.array([
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [ 10,  -2,   5,   1,   1,   5,  -2,  10],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [ 10,  -2,   5,   1,   1,   5,  -2,  10],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [100, -20,  10,   5,   5,  10, -20, 100]
    ])

    def get_legal_moves(player, opp):
        legal_moves = []
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for r in range(8):
            for c in range(8):
                if player[r][c] == 0 and opp[r][c] == 0:
                    total_flipped = 0
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        count = 0
                        while 0 <= nr < 8 and 0 <= nc < 8 and opp[nr][nc] == 1:
                            nr += dr
                            nc += dc
                            count += 1
                        if count > 0 and 0 <= nr < 8 and 0 <= nc < 8 and player[nr][nc] == 1:
                            total_flipped += count
                    
                    if total_flipped > 0:
                        legal_moves.append((r, c, total_flipped))
        return legal_moves

    def to_algebraic(r, c):
        return f"{chr(ord('a') + c)}{r + 1}"

    moves = get_legal_moves(you, opponent)
    
    if not moves:
        return "pass"

    best_score = -float('inf')
    best_move = None

    for r, c, flipped in moves:
        # Score is primarily based on position, secondarily on flips
        # We add the weight to a small fraction of flipped coins
        move_score = weights[r][c] + (flipped * 0.5)
        
        # Priority 1: High weight positions (Corners)
        # Priority 2: Higher score based on heuristic
        if move_score > best_score:
            best_score = move_score
            best_move = (r, c)

    return to_algebraic(best_move[0], best_move[1])
