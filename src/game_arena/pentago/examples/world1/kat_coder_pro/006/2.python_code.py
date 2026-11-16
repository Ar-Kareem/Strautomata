
import numpy as np
from typing import Tuple, List, Optional
import time

def policy(you, opponent) -> str:
    """Main policy function that returns the best move for Pentago."""
    
    # Convert inputs to numpy arrays if they aren't already
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    
    # Get current time to track computation limit
    start_time = time.time()
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(you_board, opp_board)
    
    if not legal_moves:
        # Fallback - should not happen according to constraints
        return "1,1,0,L"
    
    # If only one legal move, take it
    if len(legal_moves) == 1:
        return format_move(legal_moves[0])
    
    # Evaluate moves with different depth based on time
    # Use iterative deepening to ensure we return a valid move
    best_move = legal_moves[0]  # Default fallback
    best_score = float('-inf')
    
    # Try different search depths within time limit
    for depth in range(1, 4):  # Try depth 1, 2, 3
        if time.time() - start_time > 0.9:  # Leave some buffer
            break
            
        for move in legal_moves:
            score = minimax(you_board.copy(), opp_board.copy(), move, depth, 
                          float('-inf'), float('inf'), False, start_time)
            
            if score > best_score:
                best_score = score
                best_move = move
                
                # If we found a winning move, take it immediately
                if score >= 1000000:  # Arbitrary high score for winning
                    return format_move(best_move)
    
    return format_move(best_move)


def generate_legal_moves(you_board: np.ndarray, opp_board: np.ndarray) -> List[Tuple[int, int, int, str]]:
    """Generate all legal moves from the current position."""
    legal_moves = []
    
    # Find all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if you_board[r][c] == 0 and opp_board[r][c] == 0:
                empty_positions.append((r, c))
    
    # For each empty position, try both rotation directions for each quadrant
    for r, c in empty_positions:
        for quad in range(4):
            for direction in ['L', 'R']:
                legal_moves.append((r, c, quad, direction))
    
    return legal_moves


def format_move(move: Tuple[int, int, int, str]) -> str:
    """Format move as required: row,col,quad,dir (1-indexed)."""
    r, c, quad, direction = move
    return f"{r+1},{c+1},{quad},{direction}"


def apply_move(you_board: np.ndarray, opp_board: np.ndarray, 
               move: Tuple[int, int, int, str]) -> Tuple[np.ndarray, np.ndarray]:
    """Apply a move to the boards and return new boards."""
    r, c, quad, direction = move
    
    # Create copies
    new_you = you_board.copy()
    new_opp = opp_board.copy()
    
    # Place the marble
    new_you[r][c] = 1
    
    # Apply rotation
    new_you, new_opp = rotate_quadrant(new_you, new_opp, quad, direction)
    
    return new_you, new_opp


def rotate_quadrant(you_board: np.ndarray, opp_board: np.ndarray, 
                   quad: int, direction: str) -> Tuple[np.ndarray, np.ndarray]:
    """Rotate a quadrant 90 degrees."""
    # Define quadrant boundaries
    if quad == 0:  # Top-left
        r_start, r_end = 0, 3
        c_start, c_end = 0, 3
    elif quad == 1:  # Top-right
        r_start, r_end = 0, 3
        c_start, c_end = 3, 6
    elif quad == 2:  # Bottom-left
        r_start, r_end = 3, 6
        c_start, c_end = 0, 3
    else:  # Bottom-right
        r_start, r_end = 3, 6
        c_start, c_end = 3, 6
    
    # Extract sub-boards for this quadrant
    you_sub = you_board[r_start:r_end, c_start:c_end].copy()
    opp_sub = opp_board[r_start:r_end, c_start:c_end].copy()
    
    # Rotate
    if direction == 'L':
        you_sub = np.rot90(you_sub, k=1)  # 90 degrees counter-clockwise
        opp_sub = np.rot90(opp_sub, k=1)
    else:  # 'R'
        you_sub = np.rot90(you_sub, k=3)  # 90 degrees clockwise (3 * 90)
        opp_sub = np.rot90(opp_sub, k=3)
    
    # Place rotated sub-boards back
    you_board[r_start:r_end, c_start:c_end] = you_sub
    opp_board[r_start:r_end, c_start:c_end] = opp_sub
    
    return you_board, opp_board


def evaluate_board(you_board: np.ndarray, opp_board: np.ndarray) -> int:
    """Evaluate the board position from player's perspective."""
    score = 0
    
    # Check for winning conditions
    you_win = check_win(you_board)
    opp_win = check_win(opp_board)
    
    if you_win and opp_win:
        return 0  # Draw
    elif you_win:
        return 1000000  # Win
    elif opp_win:
        return -1000000  # Loss
    
    # Evaluate patterns and potential
    score += evaluate_patterns(you_board, is_player=True)
    score -= evaluate_patterns(opp_board, is_player=False)
    
    # Center control bonus
    center_bonus = 2
    for r in range(2, 4):
        for c in range(2, 4):
            if you_board[r][c] == 1:
                score += center_bonus
            elif opp_board[r][c] == 1:
                score -= center_bonus
    
    return score


def check_win(board: np.ndarray) -> bool:
    """Check if the player has 5 in a row."""
    # Check rows
    for r in range(6):
        for c in range(2):  # Only need to check starting positions 0, 1
            if all(board[r][c+i] == 1 for i in range(5)):
                return True
    
    # Check columns
    for c in range(6):
        for r in range(2):  # Only need to check starting positions 0, 1
            if all(board[r+i][c] == 1 for i in range(5)):
                return True
    
    # Check diagonals (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(board[r+i][c+i] == 1 for i in range(5)):
                return True
    
    # Check diagonals (top-right to bottom-left)
    for r in range(2):
        for c in range(4, 6):
            if all(board[r+i][c-i] == 1 for i in range(5)):
                return True
    
    return False


def evaluate_patterns(board: np.ndarray, is_player: bool) -> int:
    """Evaluate scoring patterns on the board."""
    score = 0
    
    # Weight based on number of consecutive marbles
    weights = {2: 10, 3: 100, 4: 1000}
    
    # Check rows
    for r in range(6):
        score += evaluate_line(board[r], weights)
    
    # Check columns
    for c in range(6):
        score += evaluate_line(board[:, c], weights)
    
    # Check diagonals
    # Main diagonals (top-left to bottom-right)
    for offset in range(-5, 6):
        diag = board.diagonal(offset)
        if len(diag) >= 5:
            score += evaluate_line(diag, weights)
    
    # Anti-diagonals (top-right to bottom-left)
    for offset in range(-5, 6):
        diag = np.fliplr(board).diagonal(offset)
        if len(diag) >= 5:
            score += evaluate_line(diag, weights)
    
    return score


def evaluate_line(line: np.ndarray, weights: dict) -> int:
    """Evaluate a single line for scoring patterns."""
    score = 0
    length = len(line)
    
    # Check all possible 5-cell windows
    for start in range(length - 4):
        window = line[start:start+5]
        count = np.sum(window)
        
        if count >= 2:
            score += weights.get(count, 0)
    
    return score


def minimax(you_board: np.ndarray, opp_board: np.ndarray, 
           move: Tuple[int, int, int, str], depth: int, 
           alpha: float, beta: float, is_maximizing: bool, 
           start_time: float) -> int:
    """Minimax algorithm with alpha-beta pruning."""
    
    # Time check
    if time.time() - start_time > 0.95:
        return evaluate_board(you_board, opp_board)
    
    # Apply the move
    new_you, new_opp = apply_move(you_board, opp_board, move)
    
    # Base case: reached depth limit or game over
    if depth == 0:
        return evaluate_board(new_you, new_opp)
    
    # Check for terminal states
    you_win = check_win(new_you)
    opp_win = check_win(new_opp)
    
    if you_win:
        return 1000000 + depth  # Prefer shorter wins
    elif opp_win:
        return -1000000 - depth  # Prefer longer losses
    
    # Generate opponent's legal moves
    opp_moves = generate_legal_moves(new_opp, new_you)
    
    if not opp_moves:
        # No moves available - likely a draw
        return 0
    
    if is_maximizing:
        max_eval = float('-inf')
        for opp_move in opp_moves:
            eval_score = minimax(new_opp, new_you, opp_move, depth - 1, 
                               alpha, beta, False, start_time)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return max_eval
    else:
        min_eval = float('inf')
        for opp_move in opp_moves:
            eval_score = minimax(new_opp, new_you, opp_move, depth - 1, 
                               alpha, beta, True, start_time)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return min_eval
