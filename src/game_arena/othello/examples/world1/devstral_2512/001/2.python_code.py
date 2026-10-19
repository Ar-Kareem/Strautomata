
import numpy as np
from typing import List, Tuple

# Directions for checking flips (8 directions)
DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),          (0,1),
              (1,-1),  (1,0),  (1,1)]

# Predefined opening moves (strong openings)
OPENING_BOOK = {
    (): ['d3', 'c4', 'f5', 'e6'],
    ('d3',): ['c4', 'f5', 'e6', 'd6'],
    ('c4',): ['d3', 'f5', 'e6', 'c3'],
    ('f5',): ['d3', 'c4', 'e6', 'f6'],
    ('e6',): ['d3', 'c4', 'f5', 'e3'],
}

# Position weights for different game phases
OPENING_WEIGHTS = np.array([
    [120, -20, 20, 5, 5, 20, -20, 120],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [120, -20, 20, 5, 5, 20, -20, 120]
])

MIDGAME_WEIGHTS = np.array([
    [200, -50, 30, 10, 10, 30, -50, 200],
    [-50, -100, -10, -10, -10, -10, -100, -50],
    [30, -10, 20, 5, 5, 20, -10, 30],
    [10, -10, 5, 5, 5, 5, -10, 10],
    [10, -10, 5, 5, 5, 5, -10, 10],
    [30, -10, 20, 5, 5, 20, -10, 30],
    [-50, -100, -10, -10, -10, -10, -100, -50],
    [200, -50, 30, 10, 10, 30, -50, 200]
])

ENDGAME_WEIGHTS = np.array([
    [1000, -200, 100, 50, 50, 100, -200, 1000],
    [-200, -500, -50, -50, -50, -50, -500, -200],
    [100, -50, 100, 25, 25, 100, -50, 100],
    [50, -50, 25, 25, 25, 25, -50, 50],
    [50, -50, 25, 25, 25, 25, -50, 50],
    [100, -50, 100, 25, 25, 100, -50, 100],
    [-200, -500, -50, -50, -50, -50, -500, -200],
    [1000, -200, 100, 50, 50, 100, -200, 1000]
])

def is_legal_move(board: np.ndarray, player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Check if a move is legal at (r,c) for the current player."""
    if board[r][c] != 0:
        return False

    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        flip_count = 0

        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            flip_count += 1
            nr += dr
            nc += dc

        if flip_count > 0 and 0 <= nr < 8 and 0 <= nc < 8 and player[nr][nc] == 1:
            return True

    return False

def get_legal_moves(board: np.ndarray, player: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Get all legal moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_legal_move(board, player, opponent, r, c):
                moves.append((r, c))
    return moves

def get_flips(board: np.ndarray, player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> List[Tuple[int, int]]:
    """Get all discs that would be flipped by placing at (r,c)."""
    flips = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        temp_flips = []

        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            temp_flips.append((nr, nc))
            nr += dr
            nc += dc

        if len(temp_flips) > 0 and 0 <= nr < 8 and 0 <= nc < 8 and player[nr][nc] == 1:
            flips.extend(temp_flips)

    return flips

def evaluate_move(board: np.ndarray, player: np.ndarray, opponent: np.ndarray, r: int, c: int, move_history: List[str]) -> float:
    """Evaluate a potential move using multiple factors."""
    # Get the current game phase
    empty_count = np.sum(board == 0)
    if empty_count > 50:
        phase = 'opening'
        weights = OPENING_WEIGHTS
    elif empty_count > 20:
        phase = 'midgame'
        weights = MIDGAME_WEIGHTS
    else:
        phase = 'endgame'
        weights = ENDGAME_WEIGHTS

    # Positional value
    pos_value = weights[r][c]

    # Mobility - count potential future moves
    temp_board = board.copy()
    temp_player = player.copy()
    temp_opponent = opponent.copy()

    # Simulate the move
    temp_board[r][c] = 1
    temp_player[r][c] = 1
    flips = get_flips(board, player, opponent, r, c)
    for fr, fc in flips:
        temp_board[fr][fc] = 1
        temp_player[fr][fc] = 1
        temp_opponent[fr][fc] = 0

    # Count opponent's potential moves after this move
    opponent_moves = len(get_legal_moves(temp_board, temp_opponent, temp_player))
    mobility = -opponent_moves * 0.5  # Negative because we want to minimize opponent's options

    # Disc difference
    disc_diff = len(flips)  # Immediate gain

    # Corner control
    corner_value = 0
    if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
        corner_value = 50

    # Edge control (but avoid early edge moves)
    edge_value = 0
    if r in [0,7] or c in [0,7]:
        if phase != 'opening' or (r not in [0,7] or c not in [0,7]):  # Avoid pure edges in opening
            edge_value = 10

    # Stability - count how many of the flipped discs are stable
    stable_count = 0
    for fr, fc in flips:
        if fr in [0,7] or fc in [0,7]:
            stable_count += 1

    # Combine all factors with different weights based on phase
    if phase == 'opening':
        score = (pos_value * 0.4 +
                 mobility * 0.3 +
                 disc_diff * 0.1 +
                 corner_value * 0.2 +
                 edge_value * 0.1 +
                 stable_count * 0.1)
    elif phase == 'midgame':
        score = (pos_value * 0.3 +
                 mobility * 0.2 +
                 disc_diff * 0.2 +
                 corner_value * 0.2 +
                 edge_value * 0.1 +
                 stable_count * 0.2)
    else:  # endgame
        score = (pos_value * 0.2 +
                 mobility * 0.1 +
                 disc_diff * 0.4 +
                 corner_value * 0.1 +
                 edge_value * 0.1 +
                 stable_count * 0.3)

    return score

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function that returns the best move."""
    board = you + opponent  # 1 where occupied, 0 where empty

    # Get all legal moves
    legal_moves = get_legal_moves(board, you, opponent)

    if not legal_moves:
        return "pass"

    # Check if we can use opening book
    move_history = []  # In a real implementation, this would track actual move history
    if len(move_history) < 4:
        key = tuple(move_history)
        if key in OPENING_BOOK:
            for move in OPENING_BOOK[key]:
                r = int(move[1]) - 1
                c = ord(move[0]) - ord('a')
                if (r, c) in legal_moves:
                    return move

    # Evaluate all legal moves
    best_move = None
    best_score = -float('inf')

    for r, c in legal_moves:
        score = evaluate_move(board, you, opponent, r, c, move_history)
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Convert to algebraic notation
    if best_move:
        r, c = best_move
        return f"{chr(ord('a') + c)}{r + 1}"

    # Fallback (shouldn't happen as we checked legal_moves)
    return "pass"
