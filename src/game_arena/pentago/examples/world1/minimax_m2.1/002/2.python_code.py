
import numpy as np
from typing import Tuple, List

def policy(you, opponent) -> str:
    """
    Pentago AI policy function.
    
    Args:
        you: 6x6 numpy array where you[r][c] == 1 means your marble is at row r, col c
        opponent: 6x6 numpy array where opponent[r][c] == 1 means opponent's marble is at row r, col c
        
    Returns:
        A string move formatted as "row,col,quad,dir" where:
        - row, col are 1-indexed positions (1..6)
        - quad is quadrant 0..3 (0: top-left, 1: top-right, 2: bottom-left, 3: bottom-right)
        - dir is 'L' (90 degrees anticlockwise) or 'R' (90 degrees clockwise)
    """
    
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)
    
    # Find empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if you_board[r, c] == 0 and opp_board[r, c] == 0:
                empty_positions.append((r, c))
    
    # Quadrant definitions (0-indexed)
    quadrant_cells = {
        0: [(r, c) for r in range(3) for c in range(3)],
        1: [(r, c) for r in range(3) for c in range(3, 6)],
        2: [(r, c) for r in range(3, 6) for c in range(3)],
        3: [(r, c) for r in range(3, 6) for c in range(3, 6)]
    }
    
    directions = ['L', 'R']
    
    def check_winner(board):
        """Check if there's a 5-in-a-row on the board."""
        # Check horizontal
        for r in range(6):
            for c in range(2):
                if all(board[r, c+i] == 1 for i in range(5)):
                    return True
        
        # Check vertical
        for r in range(2):
            for c in range(6):
                if all(board[r+i, c] == 1 for i in range(5)):
                    return True
        
        # Check diagonal (top-left to bottom-right)
        for r in range(2):
            for c in range(2):
                if all(board[r+i, c+i] == 1 for i in range(5)):
                    return True
        
        # Check diagonal (top-right to bottom-left)
        for r in range(2):
            for c in range(3, 6):
                if all(board[r+i, c-i] == 1 for i in range(5)):
                    return True
        
        return False
    
    def simulate_move(row, col, quad, direction, board_you, board_opp):
        """Simulate placing a marble and rotating a quadrant."""
        # Create copies of boards
        new_you = board_you.copy()
        new_opp = board_opp.copy()
        
        # Place marble
        new_you[row, col] = 1
        
        # Get cells for the quadrant
        cells = quadrant_cells[quad]
        
        # Extract quadrant values
        quad_you = np.zeros((3, 3), dtype=int)
        quad_opp = np.zeros((3, 3), dtype=int)
        
        for idx, (r, c) in enumerate(cells):
            quad_r, quad_c = idx // 3, idx % 3
            quad_you[quad_r, quad_c] = new_you[r, c]
            quad_opp[quad_r, quad_c] = new_opp[r, c]
        
        # Rotate quadrant
        if direction == 'L':
            rotated_you = np.rot90(quad_you, k=1)
            rotated_opp = np.rot90(quad_opp, k=1)
        else:  # direction == 'R'
            rotated_you = np.rot90(quad_you, k=-1)
            rotated_opp = np.rot90(quad_opp, k=-1)
        
        # Place rotated values back
        for idx, (r, c) in enumerate(cells):
            quad_r, quad_c = idx // 3, idx % 3
            new_you[r, c] = rotated_you[quad_r, quad_c]
            new_opp[r, c] = rotated_opp[quad_r, quad_c]
        
        return new_you, new_opp
    
    def count_potential_lines(board, player):
        """Count potential lines of 4 or 5 for a player."""
        count = 0
        # Horizontal
        for r in range(6):
            for c in range(3):
                line = [board[r, c+i] for i in range(4)]
                if line.count(1) >= 3 and line.count(0) == 0:
                    count += line.count(1) * 10
        
        # Vertical
        for r in range(3):
            for c in range(6):
                line = [board[r+i, c] for i in range(4)]
                if line.count(1) >= 3 and line.count(0) == 0:
                    count += line.count(1) * 10
        
        # Diagonal
        for r in range(3):
            for c in range(3):
                line = [board[r+i, c+i] for i in range(4)]
                if line.count(1) >= 3 and line.count(0) == 0:
                    count += line.count(1) * 10
        
        return count
    
    def evaluate_move(row, col, quad, direction, board_you, board_opp):
        """Evaluate a move and return a score."""
        new_you, new_opp = simulate_move(row, col, quad, direction, board_you, board_opp)
        
        # Check for immediate win
        if check_winner(new_you):
            return 10000
        
        # Check if opponent would win (bad move unless it's a draw)
        if check_winner(new_opp):
            return -10000
        
        # Count potential lines
        my_lines = count_potential_lines(new_you, 1)
        opp_lines = count_potential_lines(new_opp, 0)
        
        # Center control bonus
        center_control = 0
        if 1 <= row <= 4 and 1 <= col <= 4:
            center_control += 5
        
        # Positional bonus based on distance from edges
        edge_distance = min(row, 5-row, col, 5-col)
        center_control += edge_distance * 2
        
        return my_lines - opp_lines * 1.5 + center_control
    
    # Try to find immediate winning move
    for row, col in empty_positions:
        for quad in range(4):
            for direction in directions:
                new_you, new_opp = simulate_move(row, col, quad, direction, you_board, opp_board)
                if check_winner(new_you):
                    return f"{row+1},{col+1},{quad},{direction}"
    
    # Try to block opponent's immediate win
    for row, col in empty_positions:
        for quad in range(4):
            for direction in directions:
                new_you, new_opp = simulate_move(row, col, quad, direction, you_board, opp_board)
                if check_winner(new_opp):
                    # This blocks opponent's win, but prefer winning moves first
                    # Return this as a fallback if no winning move found
                    best_move = (row, col, quad, direction)
                    break
            else:
                continue
            break
    else:
        # No immediate threats to block, evaluate all moves
        best_move = None
        best_score = -float('inf')
        
        for row, col in empty_positions:
            for quad in range(4):
                for direction in directions:
                    score = evaluate_move(row, col, quad, direction, you_board, opp_board)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col, quad, direction)
        
        if best_move is None:
            # Fallback to first legal move
            row, col = empty_positions[0]
            return f"{row+1},{col+1},0,R"
    
    row, col, quad, direction = best_move
    return f"{row+1},{col+1},{quad},{direction}"
