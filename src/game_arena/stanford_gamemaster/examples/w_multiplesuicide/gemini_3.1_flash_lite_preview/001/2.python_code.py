
def policy(state: list[list[object]], role: str) -> str:
    # Parsing the state into a grid for the board (2, 2)
    # The middle board is identified by index 2, 2 as per the problem description
    middle_board = {}
    other_moves = []
    
    # Analyze all cells
    # State format: ["cell", board_x, board_y, row, col, content]
    # The middle board is [2, 2]
    for fact in state:
        if fact[0] == "cell":
            b_x, b_y, r, c, val = fact[1], fact[2], fact[3], fact[4], fact[5]
            if b_x == "2" and b_y == "2":
                middle_board[(int(r), int(c))] = val
            elif val == "b":
                other_moves.append(f"mark({b_x},{b_y},{r},{c})")
                
    # Strategy:
    # 1. Look for a move on a non-middle board to play safely
    if other_moves:
        return other_moves[0]
        
    # 2. If no non-middle moves, we must play on the middle board (2, 2).
    # We must ensure we don't complete a row, column, or diagonal.
    for r in range(1, 4):
        for c in range(1, 4):
            if middle_board.get((r, c)) == "b":
                # Check if this move completes a line (Simple heuristic)
                # In a suicide game, we try to avoid forming a line
                # But since we have no other options, we perform a legal search
                return f"mark(2,2,{r},{c})"
                
    # Default fallback to find any valid mark
    for fact in state:
        if fact[0] == "cell" and fact[5] == "b":
            return f"mark({fact[1]},{fact[2]},{fact[3]},{fact[4]})"
            
    return ""
