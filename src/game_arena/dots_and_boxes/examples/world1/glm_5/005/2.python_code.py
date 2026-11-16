
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Determines the next move for a 4x4 Dots and Boxes game.
    
    Strategy:
    1. Capture any available box (completes a box with 3 sides).
    2. If no captures, play a 'safe' move (does not create a 3-sided box for the opponent).
    3. If no safe moves, play a move that creates the fewest 3-sided boxes (minimize damage).
    """
    
    # Helper to count filled edges for a box at (r, c)
    # Returns -1 if box is out of bounds
    def count_edges(r, c):
        if not (0 <= r < 4 and 0 <= c < 4):
            return -1
        
        cnt = 0
        # Top edge: horizontal[r, c]
        if horizontal[r, c] != 0: cnt += 1
        # Bottom edge: horizontal[r+1, c]
        if horizontal[r+1, c] != 0: cnt += 1
        # Left edge: vertical[r, c]
        if vertical[r, c] != 0: cnt += 1
        # Right edge: vertical[r, c+1]
        if vertical[r, c+1] != 0: cnt += 1
        
        return cnt

    # Lists to store candidate moves
    capture_moves = []
    safe_moves = []
    forced_moves = [] # Stores (move_str, count_of_3s_created)

    # Check all horizontal edges
    # Valid indices: row 0-4, col 0-3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                # Determine adjacent boxes
                # Top box: (r-1, c) valid if r > 0
                # Bottom box: (r, c) valid if r < 4
                neighbors = []
                if r > 0: neighbors.append((r-1, c))
                if r < 4: neighbors.append((r, c))
                
                is_capture = False
                unsafe_count = 0
                
                for br, bc in neighbors:
                    edges = count_edges(br, bc)
                    if edges == 3:
                        is_capture = True
                    elif edges == 2:
                        # Filling this edge makes it 3
                        unsafe_count += 1
                
                move_str = f"{r},{c},H"
                
                if is_capture:
                    capture_moves.append(move_str)
                elif unsafe_count == 0:
                    safe_moves.append(move_str)
                else:
                    forced_moves.append((move_str, unsafe_count))

    # Check all vertical edges
    # Valid indices: row 0-3, col 0-4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                # Determine adjacent boxes
                # Left box: (r, c-1) valid if c > 0
                # Right box: (r, c) valid if c < 4
                neighbors = []
                if c > 0: neighbors.append((r, c-1))
                if c < 4: neighbors.append((r, c))
                
                is_capture = False
                unsafe_count = 0
                
                for br, bc in neighbors:
                    edges = count_edges(br, bc)
                    if edges == 3:
                        is_capture = True
                    elif edges == 2:
                        unsafe_count += 1
                
                move_str = f"{r},{c},V"
                
                if is_capture:
                    capture_moves.append(move_str)
                elif unsafe_count == 0:
                    safe_moves.append(move_str)
                else:
                    forced_moves.append((move_str, unsafe_count))

    # Select move based on priority
    if capture_moves:
        return random.choice(capture_moves)
    
    if safe_moves:
        return random.choice(safe_moves)
    
    if forced_moves:
        # Sort by number of 3-sided boxes created (ascending)
        forced_moves.sort(key=lambda x: x[1])
        return forced_moves[0][0]

    # Fallback (should not be reached in a valid game state)
    return "0,0,H"
