
import numpy as np
from typing import List, Tuple

# Directions for checking flips (8 possible directions)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

# Precomputed weights for board evaluation (higher for corners and edges)
WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

def is_valid_move(board: np.ndarray, player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Check if placing a disc at (r, c) is a valid move."""
    if player[r][c] or opponent[r][c]:
        return False

    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
            # Check if there's a line of opponent discs ending with player's disc
            while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and player[nr][nc]:
                return True
    return False

def get_valid_moves(board: np.ndarray, player: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Get all valid moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, player, opponent, r, c):
                moves.append((r, c))
    return moves

def apply_move(board: np.ndarray, player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> Tuple[np.ndarray, np.ndarray]:
    """Apply a move and return new player and opponent boards."""
    new_player = player.copy()
    new_opponent = opponent.copy()
    new_player[r][c] = 1

    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        flips = []
        while 0 <= nr < 8 and 0 <= nc < 8 and new_opponent[nr][nc]:
            flips.append((nr, nc))
            nr += dr
            nc += dc
        if 0 <= nr < 8 and 0 <= nc < 8 and new_player[nr][nc]:
            for fr, fc in flips:
                new_opponent[fr][fc] = 0
                new_player[fr][fc] = 1
    return new_player, new_opponent

def evaluate_board(player: np.ndarray, opponent: np.ndarray) -> float:
    """Evaluate the board using weights, mobility, and stability."""
    # Material advantage
    player_count = np.sum(player)
    opponent_count = np.sum(opponent)
    material = (player_count - opponent_count) * 10

    # Mobility (number of valid moves)
    player_moves = len(get_valid_moves(None, player, opponent))
    opponent_moves = len(get_valid_moves(None, opponent, player))
    mobility = (player_moves - opponent_moves) * 5

    # Stability (weighted by board position)
    stability = np.sum(WEIGHTS * player) - np.sum(WEIGHTS * opponent)

    return material + mobility + stability

def minimax(player: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_board(player, opponent)

    valid_moves = get_valid_moves(None, player, opponent)
    if not valid_moves:
        # If no moves, pass and let opponent play
        opponent_moves = get_valid_moves(None, opponent, player)
        if not opponent_moves:
            return evaluate_board(player, opponent)  # Game over
        return minimax(opponent, player, depth - 1, alpha, beta, False)

    if maximizing:
        max_eval = -float('inf')
        for r, c in valid_moves:
            new_player, new_opponent = apply_move(None, player, opponent, r, c)
            eval = minimax(new_opponent, new_player, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in valid_moves:
            new_player, new_opponent = apply_move(None, opponent, player, r, c)
            eval = minimax(new_player, new_opponent, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the best move using minimax with alpha-beta pruning."""
    valid_moves = get_valid_moves(None, you, opponent)
    if not valid_moves:
        return "pass"

    best_move = None
    best_eval = -float('inf')
    depth = 3  # Adjust depth based on time constraints

    for r, c in valid_moves:
        new_you, new_opponent = apply_move(None, you, opponent, r, c)
        eval = minimax(new_opponent, new_you, depth, -float('inf'), float('inf'), False)
        if eval > best_eval:
            best_eval = eval
            best_move = (r, c)

    if best_move is None:
        return "pass"

    # Convert to algebraic notation
    col = chr(ord('a') + best_move[1])
    row = str(best_move[0] + 1)
    return col + row
