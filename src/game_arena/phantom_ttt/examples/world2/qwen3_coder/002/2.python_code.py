
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    Smart Phantom Tic Tac Toe policy that evaluates immediate tactical moves
    before falling back to positional strategy.
    
    Args:
        board: 3x3 list of lists with 1 for confirmed player marks, 0 otherwise
        
    Returns:
        tuple: (row, col) representing the chosen move
    """
    # Convert to numpy for easier manipulation
    board_array = np.array(board)
    
    # Get all unconfirmed cells (0s) - potential moves
    potential_moves = []
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:  # Not confirmed as ours
                potential_moves.append((i, j))
    
    # If no moves available, which shouldn't happen, return first cell
    if not potential_moves:
        return (0, 0)
        
    # Tactical priority: Look for winning moves first
    for move in potential_moves:
        # Simulate placing our mark
        test_board = board_array.copy()
        test_board[move[0], move[1]] = 1
        
        # Check if this creates a winning line
        if _check_win(test_board, 1):
            return move
    
    # Defensive priority: Block opponent threats  
    for move in potential_moves:
        # Simulate opponent placing mark here
        test_board = board_array.copy()
        test_board[move[0], move[1]] = -1  # Using -1 to represent opponent
        
        # Check if opponent could win here 
        if _check_win(test_board, -1):
            return move
            
    # Positional strategy: prefer center, then corners, then edges
    # Order: center, corners, edges
    strategic_order = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
    
    for move in strategic_order:
        if board_array[move[0], move[1]] == 0:  # Not confirmed as ours
            return move
            
    # Fallback to first available
    return potential_moves[0]

def _check_win(board, player):
    """Check if player has won on the board."""
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
            
    # Check columns
    for col in range(3):
        if all(board[row, col] == player for row in range(3)):
            return True
            
    # Check diagonals
    if all(board[i, i] == player for i in range(3)):
        return True
    if all(board[i, 2-i] == player for i in range(3)):
        return True
        
    return False
