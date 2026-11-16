
import numpy as np
from typing import List, Tuple

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Precompute board state
    board = you + opponent
    empty = (board == 0)
    your_discs = np.sum(you)
    opponent_discs = np.sum(opponent)
    total_discs = your_discs + opponent_discs

    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)

    if not legal_moves:
        return "pass"

    # Early game: prioritize corners
    if total_discs < 20:
        # Corners in order of preference (a1, a8, h1, h8, b1, etc.)
        corners = [
            (0, 0), (0, 7), (7, 0), (7, 7),
            (0, 1), (0, 6), (1, 0), (6, 0), (7, 1), (7, 6),
            (1, 7), (6, 7), (1, 1), (6, 6), (2, 0), (5, 0),
            (0, 2), (0, 5), (2, 7), (5, 7), (7, 2), (7, 5)
        ]
        # Filter corners that are legal
        corner_moves = [(r, c) for (r, c) in corners if empty[r, c] and (r, c) in legal_moves]
        if corner_moves:
            # Choose the corner with the highest stability (no opponent adjacent)
            def corner_score(r, c):
                score = 0
                for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc]:
                        score -= 1
                return score
            best_corner = max(corner_moves, key=lambda pos: corner_score(*pos))
            return f"{chr(ord('a') + best_corner[1])}{best_corner[0] + 1}"

    # Mid/late game: evaluate moves based on flips, stability, and disc parity
    best_move = None
    best_score = -float('inf')

    for (r, c) in legal_moves:
        # Simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        new_you[r, c] = 1
        flipped = get_flipped_discs(new_you, new_opponent, r, c)
        new_opponent[r, c] = 1
        for (fr, fc) in flipped:
            new_opponent[fr, fc] = 0
            new_you[fr, fc] = 1

        # Evaluate the move
        score = evaluate_move(new_you, new_opponent, r, c, total_discs + 1)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move:
        return f"{chr(ord('a') + best_move[1])}{best_move[0] + 1}"
    else:
        # Fallback: choose any legal move (shouldn't happen if legal_moves is correct)
        return f"{chr(ord('a') + legal_moves[0][1])}{legal_moves[0][0] + 1}"

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    legal_moves = []
    empty = (you + opponent == 0)
    for r in range(8):
        for c in range(8):
            if empty[r, c]:
                if has_legal_flips(you, opponent, r, c):
                    legal_moves.append((r, c))
    return legal_moves

def has_legal_flips(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]
    for dr, dc in directions:
        flipped = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc]:
            flipped.append((nr, nc))
            nr += dr
            nc += dc
        if flipped and (0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc]):
            return True
    return False

def get_flipped_discs(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> List[Tuple[int, int]]:
    flipped = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc]:
            flipped.append((nr, nc))
            nr += dr
            nc += dc
        if flipped and (0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc]):
            pass  # Valid flip direction
        else:
            flipped = []  # Reset for this direction
    return flipped

def evaluate_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int, total_discs: int) -> float:
    # Positional weights (corners > edges > center)
    position_weights = np.array([
        [1000, -100,  100,  50,  50,  100, -100, 1000],
        [-100,  -50,  -50,   0,   0,  -50,  -50, -100],
        [ 100,  -50,   0,   0,   0,   0,  -50,  100],
        [  50,    0,   0,   0,   0,   0,    0,   50],
        [  50,    0,   0,   0,   0,   0,    0,   50],
        [ 100,  -50,   0,   0,   0,   0,  -50,  100],
        [-100,  -50,  -50,   0,   0,  -50,  -50, -100],
        [1000, -100,  100,  50,  50,  100, -100, 1000]
    ])

    # Flips (opponent discs flipped)
    flipped = get_flipped_discs(you, opponent, r, c)
    flips = len(flipped)

    # Stability (no opponent adjacent)
    stability = 0
    for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc]:
            stability -= 1

    # Disc parity (odd/even)
    parity = 1 if (total_discs + 1) % 2 == 1 else -1

    # Future mobility (number of legal moves after this move)
    new_you = you.copy()
    new_opponent = opponent.copy()
    new_you[r, c] = 1
    for (fr, fc) in flipped:
        new_opponent[fr, fc] = 0
        new_you[fr, fc] = 1
    future_moves = len(get_legal_moves(new_you, new_opponent))

    # Score components
    positional = position_weights[r, c]
    flip_bonus = flips * 10
    stability_bonus = stability * 5
    mobility_bonus = future_moves * 2
    parity_bonus = parity * 100

    # Combine scores
    score = positional + flip_bonus + stability_bonus + mobility_bonus + parity_bonus
    return score
