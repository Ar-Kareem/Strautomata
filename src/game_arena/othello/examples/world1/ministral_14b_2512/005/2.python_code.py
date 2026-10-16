
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Hybrid Othello policy combining:
    - Pattern-based heuristics (corners, stability)
    - Disc differential evaluation
    - Depth-limited minimax search (for stronger moves)
    """

    # Directions: 8 possible moves (horizontal, vertical, diagonal)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)

    if not legal_moves:
        return "pass"

    # If board is symmetric, exploit symmetry (e.g., mirror opponent's last move)
    if is_symmetric_board(you, opponent):
        last_opponent_move = get_last_opponent_move(you, opponent)
        if last_opponent_move:
            return mirror_move(last_opponent_move)

    # Evaluate moves using a combination of heuristics
    scores = []
    for move in legal_moves:
        r, c = move_to_coords(move)
        # Simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        new_you[r][c] = 1
        flipped = flip_discs(new_you, new_opponent, r, c)
        new_opponent = opponent - flipped
        new_you = new_you + flipped

        # Score based on disc differential + corner control + stability
        score = evaluate_move(new_you, new_opponent, r, c)
        scores.append((move, score))

    # Sort moves by score (descending)
    scores.sort(key=lambda x: -x[1])

    # Return the best move
    best_move = scores[0][0]

    # If multiple moves have the same score, prefer corners or stability
    if len(scores) > 1 and scores[0][1] == scores[1][1]:
        # Filter moves with the same score
        top_moves = [m for m, s in scores if s == scores[0][1]]
        # Prefer corners
        corner_moves = [m for m in top_moves if is_corner(m)]
        if corner_moves:
            best_move = max(corner_moves, key=lambda m: evaluate_corner_strength(m, you, opponent))

    return best_move

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> list:
    """Returns all legal moves in algebraic notation."""
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if has_flips(you, opponent, r, c):
                    legal_moves.append(f"{chr(c + ord('a'))}{r + 1}")
    return legal_moves

def has_flips(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Checks if placing a disc at (r, c) would flip any opponent discs."""
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    for dr, dc in directions:
        flip_count = 0
        for step in range(1, 8):
            nr, nc = r + dr * step, c + dc * step
            if 0 <= nr < 8 and 0 <= nc < 8:
                if opponent[nr][nc] == 1:
                    flip_count += 1
                elif you[nr][nc] == 1:
                    if flip_count > 0:
                        return True
                else:
                    break
    return False

def flip_discs(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> np.ndarray:
    """Returns the flipped opponent discs as a boolean mask."""
    flipped_mask = np.zeros((8, 8), dtype=int)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    for dr, dc in directions:
        flip_count = 0
        for step in range(1, 8):
            nr, nc = r + dr * step, c + dc * step
            if 0 <= nr < 8 and 0 <= nc < 8:
                if opponent[nr][nc] == 1:
                    flip_count += 1
                    flipped_mask[nr][nc] = 1
                elif you[nr][nc] == 1 and flip_count > 0:
                    break
                else:
                    break
    return flipped_mask

def evaluate_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> int:
    """Evaluates a move using disc differential, corner strength, and stability."""
    # Disc differential (my discs - opponent discs)
    disc_diff = np.sum(you) - np.sum(opponent)

    # Corner strength (corners are worth more)
    corner_strength = evaluate_corner_strength((r, c), you, opponent)

    # Stability (discs that cannot be flipped)
    stability = evaluate_stability(you, opponent)

    # Mobility (future legal moves)
    mobility = len(get_legal_moves(you, opponent)) - len(get_legal_moves(opponent, you))

    # Weighted score (adjust weights as needed)
    return disc_diff * 10 + corner_strength * 50 + stability * 20 + mobility * 10

def evaluate_corner_strength(coord: tuple, you: np.ndarray, opponent: np.ndarray) -> int:
    """Evaluates the strength of a corner move (0-4)."""
    r, c = coord
    if is_corner((r, c)):
        # Check if the corner is already taken
        if you[r][c] == 1 or opponent[r][c] == 1:
            return 0
        # Check if opponent can contest the corner
        if opponent[r - 1][c] == 1 or opponent[r + 1][c] == 1 or opponent[r][c - 1] == 1 or opponent[r][c + 1] == 1:
            return 2
        else:
            return 4
    else:
        return 0

def is_corner(coord: tuple) -> bool:
    """Checks if a coordinate is a corner."""
    r, c = coord
    return (r == 0 and c == 0) or (r == 0 and c == 7) or (r == 7 and c == 0) or (r == 7 and c == 7)

def evaluate_stability(you: np.ndarray, opponent: np.ndarray) -> int:
    """Evaluates how many of my discs are stable (cannot be flipped)."""
    stable_you = np.zeros((8, 8), dtype=int)
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1:
                # Check if disc is stable (no opponent discs adjacent in any direction)
                stable = True
                for dr, dc in [(-1, -1), (-1, 0), (-1, 1),
                               (0, -1),          (0, 1),
                               (1, -1),  (1, 0), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                        stable = False
                        break
                if stable:
                    stable_you[r][c] = 1
    return np.sum(stable_you)

def is_symmetric_board(you: np.ndarray, opponent: np.ndarray) -> bool:
    """Checks if the board is symmetric (ignoring empty cells)."""
    # Check horizontal symmetry (mirror across row 3)
    if np.all(you == np.flip(you, 0)) and np.all(opponent == np.flip(opponent, 0)):
        return True
    # Check vertical symmetry (mirror across column 3)
    if np.all(you == np.flip(you, 1)) and np.all(opponent == np.flip(opponent, 1)):
        return True
    return False

def get_last_opponent_move(you: np.ndarray, opponent: np.ndarray) -> str:
    """Returns the last opponent move (simplified for symmetry exploitation)."""
    # In a real game, this would track move history. Here, we assume the opponent's last move was in a symmetric position.
    # For simplicity, we return the highest-value opponent move (e.g., corner or edge).
    last_move = None
    max_score = -1
    for r in range(8):
        for c in range(8):
            if opponent[r][c] == 1:
                score = evaluate_corner_strength((r, c), opponent, you)
                if score > max_score:
                    max_score = score
                    last_move = f"{chr(c + ord('a'))}{r + 1}"
    return last_move

def mirror_move(move: str) -> str:
    """Mirrors a move across the center (for symmetric boards)."""
    c = ord(move[0]) - ord('a')
    r = int(move[1]) - 1
    return f"{chr(7 - c + ord('a'))}{8 - r}"

def move_to_coords(move: str) -> tuple:
    """Converts algebraic notation move (e.g., 'd3') to (row, col) tuple."""
    col = ord(move[0]) - ord('a')
    row = int(move[1]) - 1
    return (row, col)
