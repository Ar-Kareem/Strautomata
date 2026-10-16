
import numpy as np

def get_neighbors(i, j):
    # Neighbors for hexagonal grid (excluding (i-1, j-1) and (i+1, j+1))
    return [
        (i - 1, j), (i - 1, j + 1), 
        (i, j - 1), (i, j + 1), 
        (i + 1, j), (i + 1, j - 1)
    ]

def is_within_bounds(i, j):
    return 0 <= i < 11 and 0 <= j < 11

def evaluate_position(board, color):
    opponent_color = 'w' if color == 'b' else 'b'
    player_count, opponent_count = 0, 0
    
    for i in range(11):
        for j in range(11):
            if board[i][j] == color:
                player_count += 1
            elif board[i][j] == opponent_color:
                opponent_count += 1
                
    # Favor positions occupied by our stones
    return player_count - opponent_count

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Initialize board
    board = np.full((11, 11), None)
    
    # Fill the board with current positions
    for x, y in me:
        board[x][y] = color
    for x, y in opp:
        board[x][y] = 'w' if color == 'b' else 'b'

    best_move = None
    best_score = float('-inf')

    for i in range(11):
        for j in range(11):
            if board[i][j] is None:  # If the cell is empty
                # Simulate placing my stone
                board[i][j] = color
                
                # Evaluate the position
                score = evaluate_position(board, color)
                
                # Check if this is the best score
                if score > best_score:
                    best_score = score
                    best_move = (i, j)

                # Undo the move
                board[i][j] = None
    
    return best_move if best_move else (0, 0)  # Fallback move
