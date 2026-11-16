
import random

def policy(state: list[list[object]], role: str) -> str:
    # Identify the current phase
    phase = "place"
    for fact in state:
        if fact[0] == "phase":
            phase = fact[1]
    
    # Extract existing marks to check for occupancy
    occupied = set()
    for fact in state:
        if fact[0] == "cellholds":
            # State format: ["cellholds", board, row, col, color]
            occupied.add((fact[1], fact[2], fact[3]))
            
    if phase == "place":
        # Iterate over all quadrants, rows, and columns to find an empty spot
        # Quadrants are 1-4, rows 1-3, columns 1-3
        for b in ["1", "2", "3", "4"]:
            for r in ["1", "2", "3"]:
                for c in ["1", "2", "3"]:
                    if (b, r, c) not in occupied:
                        return f"place({b},{r},{c})"
        # Fallback if no space found (should not happen in valid game)
        return "place(1,1,1)"
        
    elif phase == "rotate":
        # During rotation, perform a simple rotation on the first board
        # The game allows rotate(board, direction)
        return "rotate(1,clockwise)"
        
    return ""
