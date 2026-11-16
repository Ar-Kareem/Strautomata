
import numpy as np
from typing import List, Tuple

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Pentago AI policy using minimax with alpha-beta pruning and heuristic evaluation.
    Prioritizes immediate threats/opportunities, symmetry, and quadrant control.
    """
    # Combine board states (you=1, opponent=-1, empty=0)
    board = you - opponent
    empty_cells = np.argwhere(board == 0)
    if len(empty_cells) == 0:
        return "3,3,0,L"  # Fallback (shouldn't happen per constraints)

    # Directions: horizontal, vertical, diagonal (2 types), and reverse diagonal
    directions = [
        [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],  # Horizontal
        [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],  # Vertical
        [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],  # Diagonal
        [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)]   # Reverse diagonal
    ]

    # Helper: Check if a player has 5-in-a-row in a given direction
    def has_five_in_a_row(player: np.ndarray, row: int, col: int, direction: List[Tuple[int, int]]) -> bool:
        for (dr, dc) in direction:
            r, c = row + dr, col + dc
            if 0 <= r < 6 and 0 <= c < 6 and player[r, c] != 1:
                return False
        return True

    # Helper: Rotate a quadrant 90° clockwise/anticlockwise
    def rotate_quadrant(quad: int, dir: str) -> np.ndarray:
        if dir == 'R':
            rotation = np.array([[0, 3, 6], [3, 4, 7], [6, 7, 8]])  # Clockwise
        else:
            rotation = np.array([[0, 7, 4], [3, 8, 5], [6, 1, 2]])  # Anticlockwise
        new_board = np.zeros_like(you)
        for r in range(6):
            for c in range(6):
                if quad == 0 and 0 <= r < 3 and 0 <= c < 3:
                    new_r, new_c = rotation[r % 3, c % 3]
                    new_board[r, c] = you[new_r, new_c] if new_r < 3 and new_c < 3 else 0
                elif quad == 1 and 0 <= r < 3 and 3 <= c < 6:
                    new_r, new_c = rotation[r % 3, (c - 3) % 3] + (3, 3)
                    new_board[r, c] = you[new_r, new_c] if new_r < 3 and new_c < 3 else 0
                elif quad == 2 and 3 <= r < 6 and 0 <= c < 3:
                    new_r, new_c = rotation[(r - 3) % 3, c % 3] + (3, 0)
                    new_board[r, c] = you[new_r, new_c] if new_r >= 3 and new_c < 3 else 0
                elif quad == 3 and 3 <= r < 6 and 3 <= c < 6:
                    new_r, new_c = rotation[(r - 3) % 3, (c - 3) % 3] + (3, 3)
                    new_board[r, c] = you[new_r, new_c] if new_r >= 3 and new_c >= 3 else 0
        return new_board

    # Heuristic: Evaluate board state (higher = better for you)
    def evaluate(board: np.ndarray) -> float:
        score = 0
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:  # Your marble
                    for direction in directions:
                        if has_five_in_a_row(you, r, c, direction):
                            return 10000  # Win
                        if has_five_in_a_row(opponent, r, c, direction):
                            return -10000  # Opponent win
                elif board[r, c] == -1:  # Opponent's marble
                    for direction in directions:
                        if has_five_in_a_row(opponent, r, c, direction):
                            return -10000
        # Count potential threats/opportunities
        for r in range(6):
            for c in range(6):
                if board[r, c] == 0:  # Empty cell
                    for direction in directions:
                        # Check if placing here creates 4-in-a-row
                        count = 1
                        for (dr, dc) in direction:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 1:
                                count += 1
                        if count == 4:
                            score += 100  # High-priority opportunity
                        count = 1
                        for (dr, dc) in direction:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == -1:
                                count += 1
                        if count == 4:
                            score -= 100  # High-priority threat
        # Quadrant imbalance (favor quadrants with more of your marbles)
        for quad in range(4):
            if quad == 0:
                sub = board[0:3, 0:3]
            elif quad == 1:
                sub = board[0:3, 3:6]
            elif quad == 2:
                sub = board[3:6, 0:3]
            else:
                sub = board[3:6, 3:6]
            your_count = np.sum(sub == 1)
            opp_count = np.sum(sub == -1)
            imbalance = your_count - opp_count
            score += imbalance * 10  # Weighted by quadrant control
        # Center preference (rows 2-3, cols 2-3 or 4-5)
        center_mask = (board[2:4, 2:4] == 1) | (board[2:4, 4:6] == 1) | (board[4:6, 2:4] == 1) | (board[4:6, 4:6] == 1)
        score += np.sum(center_mask) * 5
        return score

    # Generate all legal moves
    def generate_moves(board: np.ndarray, player: np.ndarray) -> List[str]:
        moves = []
        for (r, c) in empty_cells:
            for quad in range(4):
                for dir in ['L', 'R']:
                    # Place marble
                    new_you = player.copy()
                    new_you[r, c] = 1
                    # Rotate quadrant
                    new_you_rotated = rotate_quadrant(quad, dir)
                    # Check if rotation is valid (no overlap)
                    if np.all(new_you_rotated[new_you == 1] == 0) and np.all(new_you_rotated[opponent == 1] == 0):
                        moves.append(f"{r+1},{c+1},{quad},{dir}")
        return moves

    # Minimax with alpha-beta pruning (2 plies deep)
    def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[float, str]:
        if depth == 0:
            return evaluate(board), None
        legal_moves = generate_moves(board, you if maximizing_player else opponent)
        if not legal_moves:
            return evaluate(board), None
        best_score = -float('inf') if maximizing_player else float('inf')
        best_move = None
        for move in legal_moves:
            row, col, quad, dir = map(int, move[:-1]), move[-1]
            # Apply move
            new_board = board.copy()
            new_board[row-1, col-1] = 1 if maximizing_player else -1
            new_you = rotate_quadrant(quad, dir)
            new_board = new_board + new_you
            # Recurse
            score, _ = minimax(new_board, depth-1, alpha, beta, not maximizing_player)
            if maximizing_player and score > best_score:
                best_score = score
                best_move = move
                alpha = max(alpha, score)
            elif not maximizing_player and score < best_score:
                best_score = score
                best_move = move
                beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score, best_move

    # Check for immediate win/block
    for (r, c) in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                # Place marble
                new_you = you.copy()
                new_you[r, c] = 1
                # Rotate quadrant
                new_you_rotated = rotate_quadrant(quad, dir)
                # Check if placing here creates 5-in-a-row
                for direction in directions:
                    if has_five_in_a_row(new_you_rotated, r, c, direction):
                        return f"{r+1},{c+1},{quad},{dir}"
                # Check if opponent can win after your move
                for (op_r, op_c) in empty_cells:
                    if op_r == r and op_c == c:
                        continue
                    new_opponent = opponent.copy()
                    new_opponent[op_r, op_c] = 1
                    for op_quad in range(4):
                        for op_dir in ['L', 'R']:
                            new_opponent_rotated = rotate_quadrant(op_quad, op_dir)
                            if has_five_in_a_row(new_opponent_rotated, op_r, op_c, direction):
                                return f"{r+1},{c+1},{quad},{dir}"

    # If no immediate win/block, use minimax (depth=2)
    _, best_move = minimax(board, depth=2, alpha=-float('inf'), beta=float('inf'), maximizing_player=True)
    if best_move:
        return best_move

    # Fallback: Place in center and rotate best quadrant
    center_cells = [(2, 2), (2, 3), (2, 4), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3), (4, 4)]
    center_cells = [(r, c) for (r, c) in center_cells if board[r, c] == 0]
    if center_cells:
        r, c = center_cells[0]  # Pick first center cell (randomized in practice)
        # Rotate quadrant with highest imbalance (you > opponent)
        best_quad = 0
        best_imbalance = -float('inf')
        for quad in range(4):
            if quad == 0:
                sub = board[0:3, 0:3]
            elif quad == 1:
                sub = board[0:3, 3:6]
            elif quad == 2:
                sub = board[3:6, 0:3]
            else:
                sub = board[3:6, 3:6]
            your_count = np.sum(sub == 1)
            opp_count = np.sum(sub == -1)
            imbalance = your_count - opp_count
            if imbalance > best_imbalance:
                best_imbalance = imbalance
                best_quad = quad
        return f"{r+1},{c+1},{best_quad},L"  # Default to L (can randomize)

    # Final fallback: Place in first empty cell and rotate quadrant 0
    r, c = empty_cells[0]
    return f"{r+1},{c+1},0,L"
