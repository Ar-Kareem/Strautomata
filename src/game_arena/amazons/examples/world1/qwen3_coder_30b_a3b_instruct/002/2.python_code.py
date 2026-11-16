
import numpy as np
import random

def policy(board) -> str:
    def get_valid_moves():
        # Get all my amazons
        my_amazons = np.where(board == 1)
        my_amazons = list(zip(my_amazons[0], my_amazons[1]))
        
        valid_moves = []
        
        # For each amazon, find all valid moves
        for from_row, from_col in my_amazons:
            # Find all valid destinations (queen-like movement)
            destinations = []
            # Directions: up, down, left, right, and diagonals
            directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
            
            for dr, dc in directions:
                r, c = from_row + dr, from_col + dc
                while 0 <= r < 6 and 0 <= c < 6:
                    if board[r, c] == 0:  # Empty square
                        destinations.append((r, c))
                    elif board[r, c] == 1 or board[r, c] == 2 or board[r, c] == -1:  # Blocked
                        break
                    r += dr
                    c += dc
            
            # For each destination, find all valid arrow shots
            for to_row, to_col in destinations:
                # Arrow shot directions (queen-like)
                arrow_positions = []
                for dr, dc in directions:
                    r, c = to_row + dr, to_col + dc
                    while 0 <= r < 6 and 0 <= c < 6:
                        if board[r, c] == 0 or board[r, c] == 2:  # Can shoot to empty or opponent
                            arrow_positions.append((r, c))
                        elif board[r, c] == 1 or board[r, c] == -1:  # Blocked
                            break
                        r += dr
                        c += dc
                
                # Valid moves for this amazon
                for arrow_row, arrow_col in arrow_positions:
                    valid_moves.append((from_row, from_col, to_row, to_col, arrow_row, arrow_col))
        
        return valid_moves
    
    # Get all valid moves
    moves = get_valid_moves()
    
    if not moves:
        # In the unlikely case that no moves are found, return a dummy valid move
        # This should never happen according to the problem assumptions
        raise Exception("No valid moves found")
    
    # Choose the move with the maximum number of opponent amazons reachable in the next turn
    def evaluate_move(from_row, from_col, to_row, to_col, arrow_row, arrow_col):
        # Temporarily make the move to simulate its effects
        # Create a copy of the board to simulate
        temp_board = board.copy()
        
        # The amazon moves
        temp_board[from_row, from_col] = 0
        temp_board[to_row, to_col] = 1
        
        # The arrow is shot
        temp_board[arrow_row, arrow_col] = -1
        
        # Count how many opponent amazons can be attacked from this arrow position
        count = 0
        
        # Look around the arrow position for opponent amazons
        directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        for dr, dc in directions:
            r, c = arrow_row + dr, arrow_col + dc
            while 0 <= r < 6 and 0 <= c < 6:
                if temp_board[r, c] == 2:  # Found an opponent
                    count += 1
                    break
                elif temp_board[r, c] != 0:  # Blocked
                    break
                r += dr
                c += dc
        
        return count
    
    # Score each move
    scores = []
    for move in moves:
        score = evaluate_move(*move)
        scores.append(score)
    
    # Find the maximum score
    max_score = max(scores)
    
    # Pick a random move with the maximum score to add some randomness
    best_moves = [m for m, s in zip(moves, scores) if s == max_score]
    
    # Return one of the best moves as a string
    selected_move = random.choice(best_moves)
    return f"{selected_move[0]},{selected_move[1]}:{selected_move[2]},{selected_move[3]}:{selected_move[4]},{selected_move[5]}"
