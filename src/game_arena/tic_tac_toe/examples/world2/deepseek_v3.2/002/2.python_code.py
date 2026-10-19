
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """Return the next move for player 1 on a 4x4 board."""
    # Find all empty positions
    empty_positions = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    # If board is empty, choose a good opening move (center or corner)
    if len(empty_positions) == 16:
        return (1, 1)  # Start near center
    
    # Check for immediate win
    for r, c in empty_positions:
        # Temporarily place my piece
        board[r][c] = 1
        if check_winner(board, 1):
            board[r][c] = 0  # Undo
            return (r, c)
        board[r][c] = 0  # Undo
    
    # Check for opponent's immediate win (need to block)
    for r, c in empty_positions:
        board[r][c] = -1
        if check_winner(board, -1):
            board[r][c] = 0  # Undo
            return (r, c)  # Block here
        board[r][c] = 0  # Undo
    
    # Use minimax with alpha-beta pruning for deeper lookahead
    best_move = empty_positions[0]
    best_value = -float('inf')
    depth = 4  # Search depth
    
    for r, c in empty_positions:
        board[r][c] = 1
        move_value = alphabeta(board, depth-1, -float('inf'), float('inf'), False, -1)
        board[r][c] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
        elif move_value == best_value:
            # Tie-breaker: prefer center squares
            center_squares = [(1,1), (1,2), (2,1), (2,2)]
            if (r, c) in center_squares and best_move not in center_squares:
                best_move = (r, c)
    
    return best_move

def check_winner(board: List[List[int]], player: int) -> bool:
    """Check if the given player has won."""
    # Check rows
    for r in range(4):
        if all(board[r][c] == player for c in range(4)):
            return True
    
    # Check columns
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True
    
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    
    # Check anti-diagonal
    if all(board[i][3-i] == player for i in range(4)):
        return True
    
    return False

def evaluate(board: List[List[int]]) -> int:
    """Evaluate the board from player 1's perspective."""
    score = 0
    
    # Define all winning lines (10 lines total)
    lines = []
    
    # Rows
    for r in range(4):
        lines.append([(r, c) for c in range(4)])
    
    # Columns
    for c in range(4):
        lines.append([(r, c) for r in range(4)])
    
    # Diagonals
    lines.append([(i, i) for i in range(4)])  # Main diagonal
    lines.append([(i, 3-i) for i in range(4)])  # Anti-diagonal
    
    # Evaluate each line
    for line in lines:
        my_count = 0
        opp_count = 0
        
        for r, c in line:
            if board[r][c] == 1:
                my_count += 1
            elif board[r][c] == -1:
                opp_count += 1
        
        # Score the line
        if my_count > 0 and opp_count == 0:
            # Line is favorable for me
            score += my_count * my_count  # Square to favor lines with more pieces
        elif opp_count > 0 and my_count == 0:
            # Line is favorable for opponent
            score -= opp_count * opp_count
        # If both have pieces, line is blocked and contributes 0
    
    return score

def alphabeta(board: List[List[int]], depth: int, alpha: float, beta: float, 
              maximizing: bool, player: int) -> int:
    """Alpha-beta pruning minimax search."""
    # Check for terminal states
    if check_winner(board, 1):
        return 1000  # Big positive for my win
    if check_winner(board, -1):
        return -1000  # Big negative for opponent win
    
    # If depth limit reached or board is full
    if depth == 0 or not any(0 in row for row in board):
        return evaluate(board)
    
    empty_positions = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    if maximizing:  # My turn (player 1)
        value = -float('inf')
        for r, c in empty_positions:
            board[r][c] = 1
            value = max(value, alphabeta(board, depth-1, alpha, beta, False, -1))
            board[r][c] = 0
            alpha = max(alpha, value)
            if value >= beta:
                break  # Beta cutoff
        return value
    else:  # Opponent's turn (player -1)
        value = float('inf')
        for r, c in empty_positions:
            board[r][c] = -1
            value = min(value, alphabeta(board, depth-1, alpha, beta, True, 1))
            board[r][c] = 0
            beta = min(beta, value)
            if value <= alpha:
                break  # Alpha cutoff
        return value
