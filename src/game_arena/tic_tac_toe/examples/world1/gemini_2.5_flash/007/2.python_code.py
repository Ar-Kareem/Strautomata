
import math

# Helper Functions

def check_win(board, player):
    """
    Checks if the given player has won the game on the current board.
    Player: 1 (AI) or -1 (Opponent)
    """
    # Check rows
    for row in range(3):
        if all(board[row][col] == player for col in range(3)):
            return True
    
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
        
    return False

def is_draw(board):
    """
    Checks if the game is a draw. A draw occurs if the board is full and no player has won.
    """
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return False # Not a draw yet, there are empty cells
    
    # If we reached here, the board is full. Check if it's a win for anyone.
    return not check_win(board, 1) and not check_win(board, -1)

def get_empty_cells(board):
    """
    Returns a list of (row, col) tuples for all empty cells on the board.
    """
    empty_cells = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                empty_cells.append((r, c))
    return empty_cells

def minimax(board, depth, is_maximizing_player):
    """
    Implements the Minimax algorithm to find the optimal move.
    board: The current 3x3 game board.
    depth: Current depth of the search tree.
    is_maximizing_player: True if it's the AI's turn (player 1), False if it's the opponent's turn (player -1).
    """
    # Scores are relative to the maximizing player (AI, '1').

    # Check for terminal states
    if check_win(board, 1):  # AI wins
        return 10 - depth  # Prioritize faster wins
    if check_win(board, -1): # Opponent wins
        return -10 + depth # Prioritize delaying opponent's win
    if is_draw(board): # It's a draw if board is full and no one won
        return 0

    if is_maximizing_player:
        best_val = -math.inf
        for r, c in get_empty_cells(board):
            board[r][c] = 1 # Make the move for AI
            value = minimax(board, depth + 1, False) # Opponent plays next
            best_val = max(best_val, value)
            board[r][c] = 0 # Undo the move
        return best_val
    else: # Minimizing player (opponent)
        best_val = math.inf
        for r, c in get_empty_cells(board):
            board[r][c] = -1 # Make the move for opponent
            value = minimax(board, depth + 1, True) # AI plays next
            best_val = min(best_val, value)
            board[r][c] = 0 # Undo the move
        return best_val

# Main Policy Function
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best next move for the AI using the Minimax algorithm.
    board: A 3x3 list of lists representing the Tic-Tac-Toe board.
           0 (empty), 1 (you), -1 (opponent).
    Returns a tuple (row, col) for the chosen move.
    """
    best_move = (-1, -1)
    best_value = -math.inf

    empty_cells = get_empty_cells(board)

    # Optional: Heuristic for the very first move to take the center.
    # Minimax would find this, but it's a common and quick optimization.
    if len(empty_cells) == 9: # Completely empty board, it's our first move
        return (1, 1) # Take the center (1,1)

    # Iterate through all possible moves to find the best one using Minimax
    for r, c in empty_cells:
        board[r][c] = 1  # Simulate making the move for AI (player 1)
        # Evaluate the board state assuming opponent plays next.
        # depth starts at 0 for the node directly after our current move.
        move_value = minimax(board, 0, False) 
        board[r][c] = 0  # Undo the simulated move

        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
        # If `move_value == best_value`, the current best_move is kept,
        # which means the first equally-good option found is returned.

    return best_move
