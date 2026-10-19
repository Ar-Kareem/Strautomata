
import numpy as np
from typing import List, Tuple

# Directions for checking flips (8 possible directions)
DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),          (0,1),
              (1,-1),  (1,0),  (1,1)]

# Predefined strong opening moves (algebraic notation)
OPENING_BOOK = {
    (): ['d3', 'c4', 'f5', 'e6'],
    ('d3',): ['c4', 'f5', 'e6', 'd6'],
    ('c4',): ['d3', 'f5', 'e6', 'c3'],
    ('f5',): ['d3', 'c4', 'e6', 'f4'],
    ('e6',): ['d3', 'c4', 'f5', 'e3'],
}

# Weights for different board positions (higher for corners and center)
POSITION_WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 1, 1, 1, 1, -2, 10],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [10, -2, 1, 1, 1, 1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert to our internal representation
    board = np.zeros((8, 8), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = 2

    # Get all legal moves
    legal_moves = get_legal_moves(board, 1)

    # Check for opening book moves
    move_history = get_move_history(board)
    if tuple(move_history) in OPENING_BOOK:
        for move in OPENING_BOOK[tuple(move_history)]:
            if move in legal_moves:
                return move

    if not legal_moves:
        return "pass"

    # If only one move, take it
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Determine game phase (early, mid, late)
    empty_count = np.sum(board == 0)
    if empty_count > 40:
        phase = 'early'
    elif empty_count > 20:
        phase = 'mid'
    else:
        phase = 'late'

    # Evaluate each move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Make the move
        new_board = make_move(board, move, 1)

        # Evaluate the position
        score = evaluate_position(new_board, 1, phase)

        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def get_legal_moves(board: np.ndarray, player: int) -> List[str]:
    """Get all legal moves for the current player."""
    legal_moves = []
    opponent = 3 - player  # 1 vs 2

    for r in range(8):
        for c in range(8):
            if board[r][c] == 0:
                # Check if this is a legal move
                for dr, dc in DIRECTIONS:
                    if is_legal_move(board, r, c, player, dr, dc):
                        move = chr(ord('a') + c) + str(r + 1)
                        legal_moves.append(move)
                        break  # Only need one direction to be valid

    return legal_moves

def is_legal_move(board: np.ndarray, r: int, c: int, player: int, dr: int, dc: int) -> bool:
    """Check if placing at (r,c) flips discs in direction (dr,dc)."""
    opponent = 3 - player
    x, y = r + dr, c + dc
    count = 0

    while 0 <= x < 8 and 0 <= y < 8 and board[x][y] == opponent:
        x += dr
        y += dc
        count += 1

    return count > 0 and 0 <= x < 8 and 0 <= y < 8 and board[x][y] == player

def make_move(board: np.ndarray, move: str, player: int) -> np.ndarray:
    """Make a move on the board and return the new board state."""
    new_board = board.copy()
    c = ord(move[0]) - ord('a')
    r = int(move[1]) - 1
    opponent = 3 - player

    # Place the player's disc
    new_board[r][c] = player

    # Flip opponent discs in all directions
    for dr, dc in DIRECTIONS:
        x, y = r + dr, c + dc
        to_flip = []

        while 0 <= x < 8 and 0 <= y < 8 and new_board[x][y] == opponent:
            to_flip.append((x, y))
            x += dr
            y += dc

        if 0 <= x < 8 and 0 <= y < 8 and new_board[x][y] == player:
            for (fx, fy) in to_flip:
                new_board[fx][fy] = player

    return new_board

def evaluate_position(board: np.ndarray, player: int, phase: str) -> float:
    """Evaluate the board position from the player's perspective."""
    opponent = 3 - player

    # Count discs
    player_count = np.sum(board == player)
    opponent_count = np.sum(board == opponent)
    disc_diff = (player_count - opponent_count) * 10

    # Positional advantage
    pos_score = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pos_score += POSITION_WEIGHTS[r][c]
            elif board[r][c] == opponent:
                pos_score -= POSITION_WEIGHTS[r][c]

    # Mobility (number of legal moves)
    player_moves = len(get_legal_moves(board, player))
    opponent_moves = len(get_legal_moves(board, opponent))
    mobility = (player_moves - opponent_moves) * 5

    # Corner control
    corners = [(0,0), (0,7), (7,0), (7,7)]
    corner_score = 0
    for r, c in corners:
        if board[r][c] == player:
            corner_score += 25
        elif board[r][c] == opponent:
            corner_score -= 25

    # Stability (edge-adjacent discs are more stable)
    stability = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                if r == 0 or r == 7 or c == 0 or c == 7:
                    stability += 5
                elif r == 1 or r == 6 or c == 1 or c == 6:
                    stability += 2

    # Adjust weights based on game phase
    if phase == 'early':
        return 0.1 * disc_diff + 0.3 * pos_score + 0.4 * mobility + 0.2 * corner_score
    elif phase == 'mid':
        return 0.2 * disc_diff + 0.2 * pos_score + 0.3 * mobility + 0.3 * corner_score
    else:  # late game
        return 0.5 * disc_diff + 0.1 * pos_score + 0.1 * mobility + 0.3 * corner_score

def get_move_history(board: np.ndarray) -> List[str]:
    """Get the sequence of moves made so far (for opening book)."""
    moves = []
    # This is a simplified version - in a real implementation we'd track move order
    # For our purposes, we'll just count the number of discs
    total_discs = np.sum(board != 0)
    if total_discs <= 4:
        # Return empty list for first move
        return []
    return ['dummy']  # Placeholder - real implementation would track actual moves
