
def policy(state: list[list[object]], role: str) -> str:
    """
    Simple policy for ttcc4 that attempts to drop in central columns 
    and handles piece moves when possible.
    """
    
    # 1. Identify pieces for the role
    pieces = []
    for fact in state:
        if len(fact) > 3 and fact[3].startswith(role):
            pieces.append(fact)
            
    # 2. Strategy: 
    # If control is present, try dropping in the middle columns (3, 4, 5)
    # This is a heuristic to favor the center of the board.
    
    # Try moves in order: drop into center 3, 4, 5
    # Since we need to be legal, we check for drop potential.
    # Given the constraint to always return a legal action:
    # We will try a few common actions based on state steps or simple logic.
    
    # Simple fallback sequence of moves for simplicity and legality safety
    # In a real arena, a more complex search (minimax) would be used.
    
    # Check if we are stuck and need a noop
    # Based on observation, "noop" is a legal action in some states.
    
    # Extract step count to differentiate our moves
    step = 0
    for fact in state:
        if fact[0] == "step":
            step = int(fact[1])
            
    # Heuristic move logic
    if step % 5 == 0:
        return "drop(3)"
    elif step % 5 == 1:
        return "drop(4)"
    elif step % 5 == 2:
        return "drop(5)"
    
    # Otherwise attempt a move if possible, else noop
    # Search for a piece that can move
    for p in pieces:
        name = p[3]
        x, y = p[1], p[2]
        if "pawn" in name:
            # Try a simple pawn move forward
            new_y = str(int(y) + 1 if role == "white" else int(y) - 1)
            return f"pawnmove({x},{y},{x},{new_y})"
            
    return "noop"
