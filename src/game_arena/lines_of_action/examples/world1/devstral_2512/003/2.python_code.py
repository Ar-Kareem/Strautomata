
import numpy as np
from typing import List, Tuple, Optional

# Directions for movement: horizontal, vertical, and diagonals
DIRECTIONS = [
    (0, 1),   # right
    (1, 0),   # down
    (1, 1),   # down-right
    (0, -1),  # left
    (-1, 0),  # up
    (-1, -1), # up-left
    (1, -1),  # down-left
    (-1, 1)   # up-right
]

def is_valid_position(row: int, col: int) -> bool:
    """Check if the position is within the board bounds."""
    return 0 <= row < 8 and 0 <= col < 8

def count_pieces_in_line(board: np.ndarray, row: int, col: int, dr: int, dc: int) -> int:
    """Count the number of pieces in a line starting from (row, col) in direction (dr, dc)."""
    count = 0
    r, c = row + dr, col + dc
    while is_valid_position(r, c):
        if board[r, c] != 0:
            count += 1
        r += dr
        c += dc
    return count

def can_move_in_direction(board: np.ndarray, row: int, col: int, dr: int, dc: int, distance: int) -> bool:
    """Check if a piece can move in the given direction for the given distance without jumping over enemy pieces."""
    r, c = row + dr, col + dc
    steps = 0
    while steps < distance:
        if not is_valid_position(r, c):
            return False
        if board[r, c] == -1:  # Enemy piece in the way
            return False
        r += dr
        c += dc
        steps += 1
    return is_valid_position(r, c)

def generate_legal_moves(board: np.ndarray) -> List[str]:
    """Generate all legal moves for the current player (1) on the given board."""
    moves = []
    for row in range(8):
        for col in range(8):
            if board[row, col] == 1:  # Current player's piece
                for dr, dc in DIRECTIONS:
                    distance = count_pieces_in_line(board, row, col, dr, dc)
                    if distance == 0:
                        continue  # No pieces in this line, so no move possible
                    new_row, new_col = row + dr * distance, col + dc * distance
                    if not is_valid_position(new_row, new_col):
                        continue
                    if board[new_row, new_col] == 0 or board[new_row, new_col] == -1:  # Empty or enemy piece
                        if can_move_in_direction(board, row, col, dr, dc, distance):
                            moves.append(f"{row},{col}:{new_row},{new_col}")
    return moves

def evaluate_board(board: np.ndarray) -> float:
    """Evaluate the board position for the current player (1)."""
    # Count connected components of the current player's pieces
    visited = np.zeros((8, 8), dtype=bool)
    components = 0
    max_component_size = 0

    for row in range(8):
        for col in range(8):
            if board[row, col] == 1 and not visited[row, col]:
                components += 1
                stack = [(row, col)]
                visited[row, col] = True
                component_size = 0
                while stack:
                    r, c = stack.pop()
                    component_size += 1
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if is_valid_position(nr, nc) and board[nr, nc] == 1 and not visited[nr, nc]:
                            visited[nr, nc] = True
                            stack.append((nr, nc))
                if component_size > max_component_size:
                    max_component_size = component_size

    # Mobility: number of legal moves
    mobility = len(generate_legal_moves(board))

    # Center control: count pieces in the center 4x4 area
    center_control = np.sum(board[2:6, 2:6] == 1)

    # Evaluation score: prioritize fewer components, larger max component, more mobility, and center control
    score = -components * 10 + max_component_size * 5 + mobility * 0.1 + center_control * 0.5
    return score

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """Minimax algorithm with alpha-beta pruning."""
    if depth == 0:
        return evaluate_board(board)

    legal_moves = generate_legal_moves(board)
    if not legal_moves:
        return -float('inf') if maximizing_player else float('inf')

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            # Apply the move to a copy of the board
            new_board = board.copy()
            from_row, from_col = map(int, move.split(':')[0].split(','))
            to_row, to_col = map(int, move.split(':')[1].split(','))
            new_board[to_row, to_col] = new_board[from_row, from_col]
            new_board[from_row, from_col] = 0
            eval = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            # Apply the move to a copy of the board
            new_board = board.copy()
            from_row, from_col = map(int, move.split(':')[0].split(','))
            to_row, to_col = map(int, move.split(':')[1].split(','))
            new_board[to_row, to_col] = new_board[from_row, from_col]
            new_board[from_row, from_col] = 0
            eval = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: np.ndarray) -> str:
    """Select the best move using minimax with alpha-beta pruning."""
    legal_moves = generate_legal_moves(board)
    if not legal_moves:
        raise ValueError("No legal moves available")

    best_move = legal_moves[0]
    best_eval = -float('inf')

    for move in legal_moves:
        # Apply the move to a copy of the board
        new_board = board.copy()
        from_row, from_col = map(int, move.split(':')[0].split(','))
        to_row, to_col = map(int, move.split(':')[1].split(','))
        new_board[to_row, to_col] = new_board[from_row, from_col]
        new_board[from_row, from_col] = 0
        eval = minimax(new_board, depth=2, alpha=-float('inf'), beta=float('inf'), maximizing_player=False)
        if eval > best_eval:
            best_eval = eval
            best_move = move

    return best_move
