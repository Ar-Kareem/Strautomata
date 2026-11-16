
import numpy as np
from typing import List, Tuple

# Constants for the board dimensions and players
EMPTY = 0
PLAYER = 1
OPPONENT = -1

# Directions for checking lines in 3D Tic Tac Toe (rows, columns, diagonals in each layer)
DIRECTIONS_3D = [
    # Rows in each layer (i fixed)
    [(0, j, k), (1, j, k), (2, j, k)] for j in range(3) for k in range(3)
] + [
    # Columns in each layer (j fixed)
    [(i, 0, k), (i, 1, k), (i, 2, k)] for i in range(3) for k in range(3)
] + [
    # Depth lines (k fixed)
    [(i, j, 0), (i, j, 1), (i, j, 2)] for i in range(3) for j in range(3)
] + [
    # Space diagonals (i == j == k)
    [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
    [(0, 1, 2), (1, 1, 1), (2, 1, 0)],
    [(0, 2, 1), (1, 1, 1), (2, 0, 1)],
    [(2, 0, 0), (1, 1, 1), (0, 2, 2)],
    [(2, 1, 0), (1, 1, 1), (0, 1, 2)],
    [(2, 2, 1), (1, 1, 1), (0, 2, 0)],
    # Layer diagonals (i == j or i + j == 2, k fixed)
    [(i, i, k) for i in range(3) for k in range(3)] + [(i, 2 - i, k) for i in range(3) for k in range(3)]
]

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Hybrid minimax + heuristic policy for 3D Tic Tac Toe.
    - First checks for immediate win/block moves.
    - Uses depth-limited minimax (depth=5) with alpha-beta pruning if no immediate move.
    - Falls back to heuristic evaluation (center control, layer dominance).
    - Returns a random legal move if no winning/blocking moves are found.
    """
    # Convert board to numpy array for easier manipulation
    np_board = np.array(board, dtype=int)

    # Check for immediate win/block moves
    immediate_move = find_immediate_win_or_block(np_board, PLAYER)
    if immediate_move is not None:
        return immediate_move
    immediate_move = find_immediate_win_or_block(np_board, OPPONENT)
    if immediate_move is not None:
        return immediate_move

    # If no immediate move, use depth-limited minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    # Generate all possible legal moves
    legal_moves = get_legal_moves(np_board)

    # Evaluate each move using minimax with depth limit
    for move in legal_moves:
        new_board = np_board.copy()
        new_board[move] = PLAYER
        score = minimax(new_board, OPPONENT, alpha, beta, depth=5)
        if score > best_score:
            best_score = score
            best_move = move
        # Alpha-beta pruning
        if best_score >= beta:
            break

    if best_move is not None:
        return best_move

    # Fallback to heuristic: prefer center or layer control
    return heuristic_move(np_board)

def find_immediate_win_or_block(board: np.ndarray, player: int) -> Tuple[int, int, int]:
    """
    Checks if the player can win or block the opponent in the current move.
    Returns the move if found, else None.
    """
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == EMPTY:
                    # Try the move
                    board[i, j, k] = player
                    if check_win(board, player):
                        board[i, j, k] = EMPTY
                        return (i, j, k)
                    board[i, j, k] = EMPTY
    return None

def minimax(board: np.ndarray, player: int, alpha: float, beta: float, depth: int) -> float:
    """
    Minimax algorithm with alpha-beta pruning for 3D Tic Tac Toe.
    Evaluates the best possible move for the current player.
    """
    if check_win(board, PLAYER):
        return 1
    if check_win(board, OPPONENT):
        return -1
    if depth == 0 or np.all(board != EMPTY):
        return evaluate_heuristic(board, player)

    # Generate all possible legal moves
    legal_moves = get_legal_moves(board)

    if player == PLAYER:
        value = -float('inf')
        for move in legal_moves:
            new_board = board.copy()
            new_board[move] = PLAYER
            value = max(value, minimax(new_board, OPPONENT, alpha, beta, depth - 1))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in legal_moves:
            new_board = board.copy()
            new_board[move] = OPPONENT
            value = min(value, minimax(new_board, PLAYER, alpha, beta, depth - 1))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def evaluate_heuristic(board: np.ndarray, player: int) -> float:
    """
    Heuristic evaluation function for 3D Tic Tac Toe.
    Prioritizes center control, layer dominance, and opponent threats.
    """
    score = 0
    # Evaluate lines (rows, columns, depth lines)
    for line in DIRECTIONS_3D:
        if len(line) == 3:
            cells = [board[move] for move in line]
            if all(c == PLAYER for c in cells):
                score += 1000
            elif all(c == OPPONENT for c in cells):
                score -= 1000
            elif all(c == player for c in cells):
                score += 10
            elif all(c == OPPONENT for c in cells):
                score -= 10
            elif all(c == EMPTY for c in cells):
                score += 1  # Empty line is neutral but can be filled

    # Prefer center move (1,1,1)
    if board[1, 1, 1] == EMPTY:
        score += 5

    # Prefer moves that create more potential lines for the player
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == EMPTY:
                    # Simulate the move
                    board[i, j, k] = player
                    # Count potential lines for the player
                    potential_lines = 0
                    for line in DIRECTIONS_3D:
                        if len(line) == 3:
                            cells = [board[move] for move in line]
                            if cells.count(player) == 2 and cells.count(EMPTY) == 1:
                                potential_lines += 1
                    board[i, j, k] = EMPTY
                    score += potential_lines * 2  # Weight potential lines

    return score

def heuristic_move(board: np.ndarray) -> Tuple[int, int, int]:
    """
    Selects a move based on heuristic evaluation (center, layer control).
    """
    best_move = None
    best_score = -float('inf')
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == EMPTY:
                    # Simulate the move
                    board[i, j, k] = PLAYER
                    score = evaluate_heuristic(board, PLAYER)
                    board[i, j, k] = EMPTY
                    if score > best_score:
                        best_score = score
                        best_move = (i, j, k)
    return best_move

def get_legal_moves(board: np.ndarray) -> List[Tuple[int, int, int]]:
    """
    Returns all legal moves (empty cells) in the board.
    """
    return [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i, j, k] == EMPTY]

def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the player has won in the current board state.
    """
    # Check all lines in DIRECTIONS_3D
    for line in DIRECTIONS_3D:
        if len(line) == 3:
            cells = [board[move] for move in line]
            if all(c == player for c in cells):
                return True
    return False
