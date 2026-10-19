
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Smart Connect 4 policy using minimax with alpha-beta pruning.
    
    Args:
        board: 6x7 grid where 0=empty, 1=current player, -1=opponent
        
    Returns:
        Column index (0-6) to drop the disc
    """
    player = 1
    opponent = -1
    
    # Get valid moves (columns that aren't full)
    valid_moves = [col for col in range(7) if board[0][col] == 0]
    if not valid_moves:
        return 0  # Should never happen, but fallback
    
    # Priority 1: Check if we can win immediately
    for col in valid_moves:
        if would_win(board, col, player):
            return col
    
    # Priority 2: Check if we need to block opponent's immediate win
    for col in valid_moves:
        if would_win(board, col, opponent):
            return col
    
    # Priority 3: Use minimax with alpha-beta pruning
    best_col = valid_moves[0]
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Order moves by strategic value (center first)
    sorted_moves = sorted(valid_moves, key=lambda c: abs(3 - c), reverse=True)
    
    for col in sorted_moves:
        new_board = make_move(board, col, player)
        score = minimax(new_board, depth=4, alpha=alpha, beta=beta, 
                       maximizing_player=False, player=player, opponent=opponent)
        
        if score > best_score:
            best_score = score
            best_col = col
        alpha = max(alpha, score)
    
    return best_col


def would_win(board: List[List[int]], col: int, player: int) -> bool:
    """Check if placing in column would result in a win."""
    temp_board = [row[:] for row in board]
    new_board = make_move(temp_board, col, player)
    return check_win(new_board, player)


def make_move(board: List[List[int]], col: int, player: int) -> List[List[int]]:
    """Create a new board with the move applied."""
    new_board = [row[:] for row in board]
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board


def check_win(board: List[List[int]], player: int) -> bool:
    """Check if player has a winning line."""
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row][col + i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if all(board[row + i][col] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            if all(board[row + i][col + i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            if all(board[row - i][col + i] == player for i in range(4)):
                return True
    
    return False


def minimax(board: List[List[int]], depth: int, alpha: float, beta: float,
           maximizing_player: bool, player: int, opponent: int) -> float:
    """
    Minimax algorithm with alpha-beta pruning.
    
    Returns:
        Evaluation score from perspective of 'player'
    """
    current_player = player if maximizing_player else opponent
    
    # Terminal conditions
    if check_win(board, player):
        return 10000
    if check_win(board, opponent):
        return -10000
    if depth == 0:
        return evaluate_board(board, player, opponent)
    
    valid_moves = [col for col in range(7) if board[0][col] == 0]
    if not valid_moves:
        return 0
    
    if maximizing_player:
        max_eval = float('-inf')
        for col in valid_moves:
            new_board = make_move(board, col, current_player)
            eval_score = minimax(new_board, depth - 1, alpha, beta, False, player, opponent)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in valid_moves:
            new_board = make_move(board, col, current_player)
            eval_score = minimax(new_board, depth - 1, alpha, beta, True, player, opponent)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def evaluate_board(board: List[List[int]], player: int, opponent: int) -> float:
    """
    Evaluate board position from player's perspective.
    Higher score = better for player.
    """
    score = 0
    
    # Center column preference
    center_col = 3
    center_count = sum(1 for row in range(6) if board[row][center_col] == player)
    score += center_count * 3
    
    # Evaluate horizontal windows
    for row in range(6):
        for col in range(4):
            score += evaluate_window([board[row][col + i] for i in range(4)], player, opponent)
    
    # Evaluate vertical windows
    for row in range(3):
        for col in range(7):
            score += evaluate_window([board[row + i][col] for i in range(4)], player, opponent)
    
    # Evaluate diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            score += evaluate_window([board[row + i][col + i] for i in range(4)], player, opponent)
    
    # Evaluate diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            score += evaluate_window([board[row - i][col + i] for i in range(4)], player, opponent)
    
    return score


def evaluate_window(window: List[int], player: int, opponent: int) -> float:
    """
    Evaluate a window of 4 cells.
    Returns score based on the composition of the window.
    """
    score = 0
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    # Prioritize creating our own lines
    if player_count == 4:
        score += 100
    elif player_count == 3 and empty_count == 1:
        score += 5
    elif player_count == 2 and empty_count == 2:
        score += 2
    
    # Block opponent lines
    if opponent_count == 3 and empty_count == 1:
        score -= 4
    
    return score
