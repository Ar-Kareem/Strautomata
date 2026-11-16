
import numpy as np
from typing import List, Tuple, Optional

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opponent_board = np.array(opponent, dtype=int)

    # Directions: U, R, D, L
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    # Generate all legal moves
    legal_moves = []
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                for dr, dc, dir in directions:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent_board[nr, nc] == 1:
                        legal_moves.append((row, col, dir))

    if not legal_moves:
        return ""  # Should not happen per problem statement

    # If no moves, return empty (but problem says you always have a move)
    # Now, evaluate all legal moves using a heuristic or search
    best_move = None
    best_score = -float('inf')

    # Use a simple heuristic for now (can be replaced with minimax)
    for move in legal_moves:
        row, col, dir = move
        # Evaluate the move based on opponent's piece position
        # Higher score for capturing in center, lower for edges/corners
        nr, nc = row + (dir == 'U') - (dir == 'D'), col + (dir == 'R') - (dir == 'L')
        # Center bias: higher score for center captures
        center_bias = 1 - (abs(nr - 2) + abs(nc - 2)) / 4.0
        # Edge/corner penalty: lower score for edge/corner captures
        edge_penalty = 0.0
        if (nr == 0 or nr == 4) and (nc == 0 or nc == 5):
            edge_penalty = 0.5  # corners
        elif nr == 0 or nr == 4 or nc == 0 or nc == 5:
            edge_penalty = 0.2  # edges
        # Score = center_bias - edge_penalty + randomness to avoid ties
        score = center_bias - edge_penalty + 0.1 * np.random.rand()
        if score > best_score:
            best_score = score
            best_move = move

    # If no move found (should not happen), pick the first legal move
    if best_move is None:
        best_move = legal_moves[0]

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

# The above is a simple heuristic. For a stronger policy, replace with minimax.
# Here's a more advanced version with minimax and alpha-beta pruning:

def evaluate_board(you_board: np.ndarray, opponent_board: np.ndarray) -> float:
    # Material: your pieces - opponent pieces
    material = np.sum(you_board) - np.sum(opponent_board)

    # Center control: higher for pieces in center
    center_control = 0.0
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                center_control += 1 - (abs(row - 2) + abs(col - 2)) / 4.0
            if opponent_board[row, col] == 1:
                center_control -= 1 - (abs(row - 2) + abs(col - 2)) / 4.0

    # Edge/corner control: higher for pieces on edges/corners
    edge_control = 0.0
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                if (row == 0 or row == 4) and (col == 0 or col == 5):
                    edge_control += 0.5  # corners
                elif row == 0 or row == 4 or col == 0 or col == 5:
                    edge_control += 0.2  # edges
            if opponent_board[row, col] == 1:
                if (row == 0 or row == 4) and (col == 0 or col == 5):
                    edge_control -= 0.5
                elif row == 0 or row == 4 or col == 0 or col == 5:
                    edge_control -= 0.2

    # Mobility: number of legal moves for both players
    mobility = len(generate_legal_moves(you_board, opponent_board)) - len(generate_legal_moves(opponent_board, you_board))

    # Combine all factors
    return material * 1.0 + center_control * 0.5 + edge_control * 0.3 + mobility * 0.2

def generate_legal_moves(board: np.ndarray, opponent_board: np.ndarray) -> List[Tuple[int, int, str]]:
    legal_moves = []
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    for row in range(5):
        for col in range(6):
            if board[row, col] == 1:
                for dr, dc, dir in directions:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent_board[nr, nc] == 1:
                        legal_moves.append((row, col, dir))
    return legal_moves

def minimax(you_board: np.ndarray, opponent_board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[float, Optional[str]]:
    if depth == 0:
        return evaluate_board(you_board, opponent_board), None

    legal_moves = generate_legal_moves(you_board, opponent_board)
    if not legal_moves:
        return -float('inf') if maximizing_player else float('inf'), None

    if maximizing_player:
        best_score = -float('inf')
        best_move = None
        for move in legal_moves:
            row, col, dir = move
            nr, nc = row + (dir == 'U') - (dir == 'D'), col + (dir == 'R') - (dir == 'L')
            new_you = you_board.copy()
            new_opponent = opponent_board.copy()
            new_you[row, col] = 0
            new_you[nr, nc] = 1
            new_opponent[nr, nc] = 0
            score, _ = minimax(new_you, new_opponent, depth - 1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = f"{row},{col},{dir}"
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        best_move = None
        for move in generate_legal_moves(opponent_board, you_board):
            row, col, dir = move
            nr, nc = row + (dir == 'U') - (dir == 'D'), col + (dir == 'R') - (dir == 'L')
            new_you = you_board.copy()
            new_opponent = opponent_board.copy()
            new_opponent[row, col] = 0
            new_opponent[nr, nc] = 1
            new_you[nr, nc] = 0
            score, _ = minimax(new_you, new_opponent, depth - 1, alpha, beta, True)
            if score < best_score:
                best_score = score
                best_move = f"{row},{col},{dir}"
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    you_board = np.array(you, dtype=int)
    opponent_board = np.array(opponent, dtype=int)

    legal_moves = generate_legal_moves(you_board, opponent_board)
    if not legal_moves:
        return ""  # Should not happen per problem statement

    # Use minimax with depth 3 (adjust based on performance)
    _, best_move = minimax(you_board, opponent_board, 3, -float('inf'), float('inf'), True)
    if best_move is None:
        # Fallback to heuristic if minimax fails (should not happen)
        best_move = f"{legal_moves[0][0]},{legal_moves[0][1]},{legal_moves[0][2]}"

    return best_move
