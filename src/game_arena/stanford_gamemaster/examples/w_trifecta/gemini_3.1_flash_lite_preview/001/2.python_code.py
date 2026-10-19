
def policy(state: list[list[object]], role: str) -> str:
    """
    Analyzes the state to find an available cell 'b' and returns a legal mark(r, c) action.
    """
    # Create a set or dictionary of available moves based on the "cell" facts
    # The state contains facts like ["cell", "1", "1", "b"]
    # We look for all cells that have "b" as the fourth element.
    available_moves = []
    
    for fact in state:
        if len(fact) == 4 and fact[0] == "cell" and fact[3] == "b":
            row = fact[1]
            col = fact[2]
            available_moves.append(f"mark({row},{col})")
    
    # If there are available moves, pick the first one.
    # In a real competitive scenario, one might prioritize specific cells,
    # but for this game, picking any legal move is sufficient to ensure validity.
    if available_moves:
        return available_moves[0]
    
    # Fallback return (should not be reached if the game logic is sound)
    return "mark(1,1)"
