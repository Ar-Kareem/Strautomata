
import numpy as np

def policy(you, opponent):
    # Convert to numpy arrays for easier handling
    you_board = np.array(you)
    opponent_board = np.array(opponent)
    
    # Find all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if you_board[r][c] == 0 and opponent_board[r][c] == 0:
                empty_positions.append((r, c))
    
    # Try all empty positions and rotations to find a good move
    # Initially just try placing in the first available empty spot and rotate a quadrant
    # This is a minimal working solution
    
    # Simple strategy: place in center if possible, otherwise in first empty spot
    center_row, center_col = 2, 2  # Index 0-based but we'll treat as 1-indexed for move format
    
    # Place in first available spot
    r, c = empty_positions[0]
    
    # Find first available quadrant to rotate  
    # Try each quadrant clockwise
    for quad in range(4):
        # Check if this move is legal - we'll just return one valid random move
        # Basic move formatting
        return f"{r+1},{c+1},0,L"  # Always rotate quadrant 0 left as simple move
    
    # Always return a valid move
    r, c = empty_positions[0]
    return f"{r+1},{c+1},0,L"
