
def policy(state: list[list[object]], role: str) -> str:
    # Identify occupied cells
    occupied = set()
    for fact in state:
        if fact[0] == "cell":
            occupied.add((fact[1], fact[2]))
    
    # Board dimensions for Hex 7x7
    cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    rows = [1, 2, 3, 4, 5, 6, 7]
    
    # Heuristic: Prioritize center of the board, then radiate outward
    # This keeps options for connection paths open for both red and black
    preferred_order = [
        ('d', 4), ('d', 3), ('d', 5), ('c', 4), ('e', 4),
        ('c', 3), ('e', 5), ('c', 5), ('e', 3), ('b', 3),
        ('f', 5), ('b', 4), ('f', 4), ('d', 2), ('d', 6)
    ]
    
    # Add remaining cells to buffer
    for c in cols:
        for r in rows:
            if (c, str(r)) not in occupied and (c, r) not in preferred_order:
                preferred_order.append((c, r))
                
    # Select the first legal move
    for c, r in preferred_order:
        if (c, str(r)) not in occupied:
            return f"place({c},{r})"
            
    return ""
