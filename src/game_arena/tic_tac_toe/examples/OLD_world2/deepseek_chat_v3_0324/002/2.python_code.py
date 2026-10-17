
import numpy as np
from math import inf
from random import choice

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Determine the best move for the current board state using minimax with alpha-beta pruning.
    
    Args:
        board: 4x4 list of lists with 0 (empty), 1 (you), -1 (opponent)
        
    Returns:
        Tuple of (row, column) indices (0-3, 0-3) for the best move
    """
    # Convert to numpy array for easier manipulation
    board_array = np.array(board, dtype=int)
    
    # If the board is empty, make a random move (optimization)
    if np.all(board_array == 0):
        return (choice(range(4)), choice(range(4)))
    
    # Find all empty positions
    empty_positions = [(i, j) for i in range(4) for j in range(4) if board_array[i, j] == 0]
    
    # If we can win in one move, do it
    for move in empty_positions:
        temp_board = board_array.copy()
        temp_board[move] = 1
        if check_win(temp_board, 1):
            return move
    
    # If opponent can win in one move, block them
    for move in empty_positions:
        temp_board = board_array.copy()
        temp_board[move] = -1
        if check_win(temp_board, -1):
            return move
    
    # Use minimax with alpha-beta pruning to find the best move
    best_score = -inf
    best_move = None
    alpha = -inf
    beta = inf
    
    for move in empty_positions:
        temp_board = board_array.copy()
        temp_board[move] = 1  # Make the move
        
        # Get the score for this move
        score = minimax(temp_board, 3, alpha, beta, False)  # Depth set to 3 for speed
        
        if score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, best_score)
    
    # If we haven't found a best move (shouldn't happen), choose randomly
    if best_move is None and empty_positions:
        return choice(empty_positions)
    
    return best_move

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
    """Minimax algorithm with alpha-beta pruning for Tic Tac Toe.
    
    Args:
        board: Current game state as numpy array
        depth: Current depth in the search tree
        alpha: Alpha value for pruning
        beta: Beta value for pruning
        is_maximizing: True if it's the maximizer's turn (AI), False for minimizer
        
    Returns:
        Heuristic score of the board position
    """
    # Evaluate terminal states
    if check_win(board, 1):  # AI wins
        return 10
    elif check_win(board, -1):  # Opponent wins
        return -10
    elif not (board == 0).any() or depth == 0:  # Draw or depth limit reached
        return evaluate(board)
    
    empty_positions = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    if is_maximizing:
        max_score = -inf
        for move in empty_positions:
            temp_board = board.copy()
            temp_board[move] = 1  # AI makes move
            score = minimax(temp_board, depth - 1, alpha, beta, False)
            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_score
    else:
        min_score = inf
        for move in empty_positions:
            temp_board = board.copy()
            temp_board[move] = -1  # Opponent makes move
            score = minimax(temp_board, depth - 1, alpha, beta, True)
            min_score = min(min_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_score

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has won.
    
    Args:
        board: Current game state
        player: 1 (AI) or -1 (opponent)
        
    Returns:
        True if the player has won, False otherwise
    """
    # Check rows and columns
    for i in range(4):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    
    # Check diagonals
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    
    # No win found
    return False

def evaluate(board: np.ndarray) -> float:
    """Evaluate the board position heuristically.
    
    Args:
        board: Current game state
        
    Returns:
        Heuristic score (higher is better for AI)
    """
    # Simple heuristic: count potential lines
    score = 0
    
    # Check all possible lines
    lines = []
    # Rows and columns
    for i in range(4):
        lines.append(board[i, :])  # row
        lines.append(board[:, i])  # column
    
    # Diagonals
    lines.append(np.diag(board))
    lines.append(np.diag(np.fliplr(board)))
    
    for line in lines:
        if (line == 1).sum() == 3 and (line == -1).sum() == 0:
            score += 2  # Potential win for AI
        elif (line == -1).sum() == 3 and (line == 1).sum() == 0:
            score -= 2  # Potential win for opponent
        elif (line == 1).sum() == 2 and (line == -1).sum() == 0:
            score += 1  # Two in a row for AI
        elif (line == -1).sum() == 2 and (line == 1).sum() == 0:
            score -= 1  # Two in a row for opponent
    
    return score
