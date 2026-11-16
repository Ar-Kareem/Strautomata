
import random
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Step 1: Probabilistic opponent move estimation
    opponent_moves = estimate_opponent_moves(board_np)

    # Step 2: Generate possible opponent configurations
    possible_opponent_boards = generate_possible_boards(board_np, opponent_moves)

    # Step 3: Evaluate best move using minimax with imperfect info
    best_move = minimax_with_imperfect_info(board_np, possible_opponent_boards, depth=3)

    # Step 4: Fallback to greedy if minimax is too slow or uncertain
    if best_move is None:
        best_move = greedy_move(board_np)

    return best_move

def estimate_opponent_moves(board: np.ndarray) -> np.ndarray:
    """Estimate opponent's likely moves based on current board."""
    # Count our confirmed moves
    our_moves = np.sum(board == 1)
    # Total possible moves (9 cells)
    total_moves = 9
    # Opponent's likely moves: total_moves - our_moves - empty_cells
    empty_cells = np.sum(board == 0)
    opponent_moves = total_moves - our_moves - empty_cells

    # Initialize opponent move probability (0: empty, 1: ours, 2: opponent)
    opponent_prob = np.zeros_like(board, dtype=int)
    opponent_prob[board == 0] = 2  # Assume all 0s are opponent's moves

    # Adjust probabilities based on our_moves and opponent_moves
    # This is a simplified approach; a full Bayesian update would be more accurate
    return opponent_prob

def generate_possible_boards(board: np.ndarray, opponent_moves: np.ndarray) -> List[np.ndarray]:
    """Generate possible opponent configurations."""
    possible_boards = []
    # For simplicity, assume opponent has at most 5 moves (since we have at most 5)
    max_opponent_moves = np.sum(opponent_moves == 2)
    for _ in range(min(3, max_opponent_moves + 1)):  # Limit to 3 possibilities
        # Randomly sample opponent moves (this is a placeholder; real implementation would use probabilities)
        candidate_board = board.copy()
        # Mark some 0s as opponent's moves (2)
        zero_indices = np.argwhere(candidate_board == 0)
        if len(zero_indices) > 0:
            sample_indices = random.sample(range(len(zero_indices)), min(3, len(zero_indices)))
            for idx in sample_indices:
                row, col = zero_indices[idx]
                candidate_board[row, col] = 2
        possible_boards.append(candidate_board)
    return possible_boards

def minimax_with_imperfect_info(board: np.ndarray, possible_opponent_boards: List[np.ndarray], depth: int) -> Tuple[int, int]:
    """Minimax with imperfect information (simplified)."""
    best_score = -float('inf')
    best_move = None

    # Try all possible moves (avoid our confirmed moves)
    for row in range(3):
        for col in range(3):
            if board[row, col] == 1:
                continue  # Skip our confirmed moves
            # Simulate placing our move
            new_board = board.copy()
            new_board[row, col] = 1
            # Evaluate against possible opponent boards
            scores = []
            for opp_board in possible_opponent_boards:
                # Simulate opponent's turn (they will try to win or block)
                opp_move = greedy_move(opp_board)
                if opp_move is not None:
                    opp_row, opp_col = opp_move
                    opp_board[opp_row, opp_col] = 2
                # Evaluate the resulting board
                score = evaluate_board(new_board)
                scores.append(score)
            # Average score across possible opponent boards
            avg_score = np.mean(scores)
            if avg_score > best_score:
                best_score = avg_score
                best_move = (row, col)
    return best_move

def greedy_move(board: np.ndarray) -> Tuple[int, int]:
    """Greedy move selection (fallback)."""
    # Prioritize center, then corners, then edges
    priorities = [
        (1, 1),  # Center
        (0, 0), (0, 2), (2, 0), (2, 2),  # Corners
        (0, 1), (1, 0), (1, 2), (2, 1)   # Edges
    ]
    for row, col in priorities:
        if board[row, col] == 0:
            return (row, col)
    return None  # Should not happen for a 3x3 board

def evaluate_board(board: np.ndarray) -> float:
    """Evaluate board state (higher is better for us)."""
    # Check rows, columns, diagonals for wins
    lines = [
        [board[0, 0], board[0, 1], board[0, 2]],
        [board[1, 0], board[1, 1], board[1, 2]],
        [board[2, 0], board[2, 1], board[2, 2]],
        [board[0, 0], board[1, 0], board[2, 0]],
        [board[0, 1], board[1, 1], board[2, 1]],
        [board[0, 2], board[1, 2], board[2, 2]],
        [board[0, 0], board[1, 1], board[2, 2]],
        [board[0, 2], board[1, 1], board[2, 0]],
    ]
    score = 0
    for line in lines:
        if np.all(line == 1):
            score += 100  # We win
        elif np.all(line == 2):
            score -= 100  # Opponent wins
        elif np.sum(line == 1) == 2:
            score += 10   # Two in a row (potential win)
        elif np.sum(line == 2) == 2:
            score -= 10   # Opponent has two in a row
    return score
